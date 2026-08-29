"""Authenticated REST/WebSocket chat with persistent ownership and history."""
from __future__ import annotations

import asyncio
import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.auth import authenticate_token, require_current_user
from wrapper.db import get_db_session
from wrapper.log import get_logger
from wrapper.models import ChatMessage, ChatRequest, ChatResponse, FoodItemDTO, UserProfile
from wrapper.providers.swiggy import SwiggyAuthenticationRequired, build_runtime_context
from wrapper.routes.config import get_preference_record, preference_dto
from wrapper.state import chat_service

_log = get_logger("api")
router = APIRouter(prefix="/chat", tags=["Chat"])


async def _run_chat(
    request: ChatRequest,
    user: UserProfile,
    db: AsyncSession,
    request_id: str,
) -> ChatResponse:
    try:
        session_id = await chat_service.get_or_create_session(
            db, user.id, request.session_id, first_message=request.message,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await chat_service.add_message(db, session_id, "user", request.message)
    history_dtos = await chat_service.get_messages(db, session_id, user.id, limit=30)
    history = [message.model_dump(mode="json") for message in history_dtos]
    preferences = preference_dto(await get_preference_record(db, user.id)).model_dump()
    if request.preferences:
        preferences.update({
            key: value for key, value in request.preferences.items()
            if key in {"dietary_preference", "budget_preference", "max_delivery_time"}
        })

    provider_context = None
    try:
        provider_context = await build_runtime_context(db, user.id)
    except SwiggyAuthenticationRequired:
        pass  # the graph returns a user-facing connect/select-address message

    from wrapper.llm import orchestrate
    agent_data = await orchestrate(
        message=request.message,
        location=request.location,
        preferences=preferences,
        request_id=request_id,
        session_id=session_id,
        user_id=user.id,
        history=history,
        provider_context=provider_context,
    )
    recommendations = [FoodItemDTO.model_validate(item) for item in agent_data.get("recommendations", [])]
    reply = agent_data.get("reply", "I couldn't prepare a recommendation.")
    await chat_service.add_message(
        db, session_id, "assistant", reply,
        recommendations=recommendations,
        meal_type=agent_data.get("meal_type"),
        location=agent_data.get("location"),
    )
    return ChatResponse(
        session_id=session_id, reply=reply, recommendations=recommendations,
        meal_type=agent_data.get("meal_type"), location=agent_data.get("location"),
        graph_trace=agent_data.get("graph_trace"),
    )


@router.post("", response_model=ChatResponse)
async def post_chat_message(
    request: ChatRequest,
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    request_id = uuid.uuid4().hex[:12]
    _log.info("Chat request received (request_id=%s, user_id=%s)", request_id, user.id)
    try:
        return await _run_chat(request, user, db, request_id)
    except HTTPException:
        raise
    except Exception as exc:
        _log.exception("Chat request failed (request_id=%s)", request_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The recommendation service is temporarily unavailable",
        ) from exc


@router.get("/history/{session_id}", response_model=list[ChatMessage])
async def get_session_history(
    session_id: str,
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        return await chat_service.get_messages(db, session_id, user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session_history(
    session_id: str,
    user: UserProfile = Depends(require_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        await chat_service.clear_session(db, session_id, user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    await websocket.accept()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", session_id):
        await websocket.close(code=4400, reason="Invalid session identifier")
        return
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        if auth_message.get("type") != "auth" or not auth_message.get("token"):
            await websocket.close(code=4401, reason="Authentication required")
            return
        user = await authenticate_token(auth_message["token"], db)
        if not user:
            await websocket.close(code=4401, reason="Invalid authentication")
            return
        await websocket.send_json({"type": "authenticated"})

        while True:
            data = await websocket.receive_json()
            user_message = str(data.get("message") or "").strip()
            if not user_message:
                continue
            await websocket.send_json({"type": "status", "content": "Searching live Swiggy menu results..."})
            request_id = uuid.uuid4().hex[:12]
            response = await _run_chat(
                ChatRequest(
                    message=user_message, session_id=session_id,
                    location=data.get("location"), preferences=data.get("preferences"),
                ),
                user, db, request_id,
            )
            words = response.reply.split(" ")
            for index, word in enumerate(words):
                await websocket.send_json({
                    "type": "token",
                    "content": word + (" " if index < len(words) - 1 else ""),
                })
            await websocket.send_text(json.dumps({
                "type": "complete",
                "reply": response.reply,
                "recommendations": [item.model_dump(mode="json") for item in response.recommendations],
                "meal_type": response.meal_type,
                "location": response.location,
                "graph_trace": response.graph_trace,
            }))
    except WebSocketDisconnect:
        _log.info("WebSocket disconnected (session=%s)", session_id)
    except asyncio.TimeoutError:
        await websocket.close(code=4401, reason="Authentication timed out")
    except Exception:
        _log.exception("WebSocket request failed (session=%s)", session_id)
        try:
            await websocket.send_json({
                "type": "error", "content": "The recommendation service is temporarily unavailable",
            })
        except Exception:
            pass
