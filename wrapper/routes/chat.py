"""Chat API routes — REST, WebSocket, and debug endpoint.

Calls the LangGraph agent in-process via ``wrapper.llm.orchestrate()``.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from wrapper.auth import auth_service, decode_access_token, get_current_user
from wrapper.log import TRACE_BUFFER, get_logger
from wrapper.models import ChatMessage, ChatRequest, ChatResponse, FoodItemDTO, UserProfile
from wrapper.state import chat_service

_log = get_logger("api")

router = APIRouter(prefix="/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# REST endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def post_chat_message(
    request: ChatRequest,
    user: Optional[UserProfile] = Depends(get_current_user),
):
    request_id = uuid.uuid4().hex[:12]
    _log.info("[>] Chat request received  (request_id=%s, query=%r)", request_id, request.message[:80])

    session_id = chat_service.get_or_create_session(request.session_id)
    chat_service.add_message(session_id, role="user", content=request.message)

    try:
        from wrapper.llm import orchestrate

        agent_data = await orchestrate(
            message=request.message,
            location=request.location,
            preferences=request.preferences,
            request_id=request_id,
        )
        reply = agent_data.get("reply", "Here are your food recommendations.")
        recs_raw = agent_data.get("recommendations", [])
        meal_type = agent_data.get("meal_type")
        location = agent_data.get("location")
        graph_trace = agent_data.get("graph_trace")

        recommendations = [FoodItemDTO(**item) for item in recs_raw]

        chat_service.add_message(
            session_id, role="assistant", content=reply,
            recommendations=recommendations, meal_type=meal_type, location=location,
        )

        _log.info(
            "[<] Chat response sent  (request_id=%s, recommendations=%d)",
            request_id, len(recommendations),
        )

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            recommendations=recommendations,
            meal_type=meal_type,
            location=location,
            graph_trace=graph_trace,
        )
    except Exception as e:
        _log.error("Chat endpoint error  (request_id=%s): %s", request_id, e)
        error_msg = (
            "Sorry, I had trouble processing your request. "
            "Please make sure your OpenAI API key is configured in .env."
        )
        chat_service.add_message(session_id, role="assistant", content=error_msg)
        return ChatResponse(session_id=session_id, reply=error_msg, recommendations=[])


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

@router.get("/history/{session_id}", response_model=list[ChatMessage])
def get_session_history(session_id: str):
    return chat_service.get_messages(session_id)


@router.delete("/history/{session_id}")
def clear_session_history(session_id: str):
    chat_service.clear_session(session_id)
    return {"message": "Session history cleared"}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
):
    await websocket.accept()
    chat_service.get_or_create_session(session_id)

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

            request_id = uuid.uuid4().hex[:12]
            _log.info(
                "[>] WS chat  (request_id=%s, session=%s, query=%r)",
                request_id, session_id, user_msg[:80],
            )

            chat_service.add_message(session_id, role="user", content=user_msg)

            # Status: thinking
            await websocket.send_text(json.dumps({
                "type": "status",
                "content": "Analyzing craving, meal time & location...",
            }))
            await asyncio.sleep(0.2)

            # Status: searching
            await websocket.send_text(json.dumps({
                "type": "status",
                "content": "Comparing deals across Tomato 🍅 and Twiggy 🌿...",
            }))

            try:
                from wrapper.llm import orchestrate

                agent_res = await orchestrate(
                    message=user_msg,
                    location=location,
                    preferences=preferences,
                    request_id=request_id,
                )

                reply_full = agent_res.get("reply", "Here are recommendations based on your preferences.")
                recs_raw = agent_res.get("recommendations", [])
                meal_type = agent_res.get("meal_type")
                loc = agent_res.get("location")
                graph_trace = agent_res.get("graph_trace")
                recs = [FoodItemDTO(**r) for r in recs_raw]

                # Stream tokens for natural typing effect
                words = reply_full.split(" ")
                for idx, word in enumerate(words):
                    chunk = word + (" " if idx < len(words) - 1 else "")
                    await websocket.send_text(json.dumps({
                        "type": "token",
                        "content": chunk,
                    }))
                    await asyncio.sleep(0.02)

                # Completion event with rich data
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "reply": reply_full,
                    "recommendations": [r.model_dump() for r in recs],
                    "meal_type": meal_type,
                    "location": loc,
                    "graph_trace": graph_trace,
                }))

                chat_service.add_message(
                    session_id, role="assistant", content=reply_full,
                    recommendations=recs, meal_type=meal_type, location=loc,
                )

                _log.info(
                    "[<] WS response sent  (request_id=%s, recommendations=%d)",
                    request_id, len(recs),
                )

            except Exception as e:
                _log.error("WS agent error  (request_id=%s): %s", request_id, e)
                err_text = (
                    "I couldn't process your request right now. "
                    "Check the server logs for details."
                )
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "reply": err_text,
                    "recommendations": [],
                }))
                chat_service.add_message(session_id, role="assistant", content=err_text)

    except WebSocketDisconnect:
        _log.info("WebSocket disconnected: session=%s", session_id)
    except Exception as e:
        _log.error("WebSocket unexpected error: %s", e)


# ---------------------------------------------------------------------------
# Debug endpoint
# ---------------------------------------------------------------------------

@router.get("/debug/last-run")
def get_last_graph_trace():
    """Return the most recent graph execution trace for debugging."""
    if not TRACE_BUFFER:
        return {"message": "No graph traces recorded yet"}
    return TRACE_BUFFER[-1].to_dict()


@router.get("/debug/traces")
def get_all_graph_traces():
    """Return all buffered graph traces (last 20)."""
    return [t.to_dict() for t in TRACE_BUFFER]
