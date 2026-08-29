import json
import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from ..models.chat import ChatRequest, ChatResponse, ChatMessage, FoodItemDTO
from ..models.auth import UserProfile
from ..services.chat_service import chat_service
from ..services.agent_client import agent_client
from ..middleware.auth_middleware import get_current_user
from ..utils.security import decode_access_token
from ..services.auth_service import auth_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def post_chat_message(request: ChatRequest, user: Optional[UserProfile] = Depends(get_current_user)):
    session_id = chat_service.get_or_create_session(request.session_id)
    chat_service.add_message(session_id, role="user", content=request.message)

    try:
        agent_data = await agent_client.orchestrate(
            message=request.message,
            location=request.location,
            preferences=request.preferences
        )
        reply = agent_data.get("reply", "Here are your food recommendations.")
        recs_raw = agent_data.get("recommendations", [])
        meal_type = agent_data.get("meal_type")
        location = agent_data.get("location")

        recommendations = [FoodItemDTO(**item) for item in recs_raw]

        chat_service.add_message(
            session_id,
            role="assistant",
            content=reply,
            recommendations=recommendations,
            meal_type=meal_type,
            location=location
        )

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            recommendations=recommendations,
            meal_type=meal_type,
            location=location
        )
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        error_msg = "Sorry, I had trouble connecting to the food agent. Please make sure the Agent service is running."
        chat_service.add_message(session_id, role="assistant", content=error_msg)
        return ChatResponse(
            session_id=session_id,
            reply=error_msg,
            recommendations=[]
        )

@router.get("/history/{session_id}", response_model=List[ChatMessage])
def get_session_history(session_id: str):
    return chat_service.get_messages(session_id)

@router.delete("/history/{session_id}")
def clear_session_history(session_id: str):
    chat_service.clear_session(session_id)
    return {"message": "Session history cleared"}

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, token: Optional[str] = Query(None)):
    await websocket.accept()
    chat_service.get_or_create_session(session_id)

    # Optional authentication check from token query parameter
    authenticated_user = None
    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            authenticated_user = auth_service.get_user_by_id(payload["sub"])

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                data = json.loads(data_text)
            except Exception:
                data = {"message": data_text}

            user_msg = data.get("message", "").strip()
            location = data.get("location")
            preferences = data.get("preferences")

            if not user_msg:
                continue

            # Record user message in memory
            chat_service.add_message(session_id, role="user", content=user_msg)

            # Send Status 1: Thinking & Understanding Query
            await websocket.send_text(json.dumps({
                "type": "status",
                "content": "Analyzing craving, meal time & location..."
            }))
            await asyncio.sleep(0.3)

            # Send Status 2: Searching Platforms
            await websocket.send_text(json.dumps({
                "type": "status",
                "content": "Comparing deals across Tomato 🍅 and Twiggy 🌿..."
            }))

            try:
                agent_res = await agent_client.orchestrate(
                    message=user_msg,
                    location=location,
                    preferences=preferences
                )

                reply_full = agent_res.get("reply", "Here are recommendations based on your preferences.")
                recs_raw = agent_res.get("recommendations", [])
                meal_type = agent_res.get("meal_type")
                loc = agent_res.get("location")
                recs = [FoodItemDTO(**r) for r in recs_raw]

                # Stream tokens to client for real-time responsiveness
                words = reply_full.split(" ")
                accumulated = ""
                for idx, word in enumerate(words):
                    chunk = word + (" " if idx < len(words) - 1 else "")
                    accumulated += chunk
                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "content": chunk
                    }))
                    await asyncio.sleep(0.02) # Natural smooth typing pace

                # Send completion event with rich recommendations
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "reply": reply_full,
                    "recommendations": [r.model_dump() for r in recs],
                    "meal_type": meal_type,
                    "location": loc
                }))

                # Persist assistant response in session
                chat_service.add_message(
                    session_id,
                    role="assistant",
                    content=reply_full,
                    recommendations=recs,
                    meal_type=meal_type,
                    location=loc
                )

            except Exception as e:
                logging.error(f"WebSocket agent error: {e}")
                err_text = "I couldn't reach the food agent services. Please ensure the agent function app is running on port 7071."
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "reply": err_text,
                    "recommendations": []
                }))
                chat_service.add_message(session_id, role="assistant", content=err_text)

    except WebSocketDisconnect:
        logging.info(f"WebSocket client disconnected for session {session_id}")
    except Exception as e:
        logging.error(f"WebSocket unexpected error: {e}")
