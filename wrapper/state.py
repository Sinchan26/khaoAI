"""Persistent, ownership-aware chat session service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from wrapper.db_models import ChatMessage as ChatMessageRecord
from wrapper.db_models import ChatSession
from wrapper.models import ChatMessage, FoodItemDTO


def _message_dto(record: ChatMessageRecord) -> ChatMessage:
    recommendations = None
    if record.recommendations:
        recommendations = [FoodItemDTO.model_validate(item) for item in record.recommendations]
    return ChatMessage(
        id=str(record.id), role=record.role, content=record.content,
        recommendations=recommendations, created_at=record.created_at.isoformat(),
        meal_type=record.meal_type, location=record.location,
    )


class ChatService:
    async def get_or_create_session(
        self, db: AsyncSession, user_id: str, session_id: str | None = None,
        first_message: str | None = None,
    ) -> str:
        resolved_id = session_id or str(uuid.uuid4())
        record = await db.get(ChatSession, resolved_id)
        if record:
            if str(record.user_id) != user_id:
                raise PermissionError("Chat session does not belong to this user")
            return resolved_id
        db.add(ChatSession(
            id=resolved_id, user_id=uuid.UUID(user_id),
            title=(first_message or "New conversation")[:160],
        ))
        await db.flush()
        return resolved_id

    async def add_message(
        self, db: AsyncSession, session_id: str, role: str, content: str,
        recommendations: list[FoodItemDTO] | None = None,
        meal_type: str | None = None, location: str | None = None,
    ) -> ChatMessage:
        record = ChatMessageRecord(
            session_id=session_id, role=role, content=content,
            recommendations=[item.model_dump(mode="json") for item in recommendations] if recommendations else None,
            meal_type=meal_type, location=location,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return _message_dto(record)

    async def get_messages(
        self, db: AsyncSession, session_id: str, user_id: str, limit: int = 50,
    ) -> list[ChatMessage]:
        chat_session = await db.get(ChatSession, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            raise PermissionError("Chat session was not found")
        result = await db.scalars(
            select(ChatMessageRecord)
            .where(ChatMessageRecord.session_id == session_id)
            .order_by(ChatMessageRecord.created_at.desc()).limit(limit)
        )
        records = list(reversed(result.all()))
        return [_message_dto(record) for record in records]

    async def clear_session(self, db: AsyncSession, session_id: str, user_id: str) -> None:
        chat_session = await db.get(ChatSession, session_id)
        if not chat_session or str(chat_session.user_id) != user_id:
            raise PermissionError("Chat session was not found")
        await db.execute(delete(ChatMessageRecord).where(ChatMessageRecord.session_id == session_id))
        chat_session.updated_at = datetime.now(timezone.utc)
        await db.commit()


chat_service = ChatService()
