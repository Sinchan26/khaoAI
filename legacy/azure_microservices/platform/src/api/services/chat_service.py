import uuid
from datetime import datetime
from typing import Dict, List, Optional
from ..models.chat import ChatMessage, FoodItemDTO

# In-memory dictionary of session_id -> list of ChatMessage
SESSIONS_DB: Dict[str, List[ChatMessage]] = {}

class ChatService:
    @staticmethod
    def get_or_create_session(session_id: Optional[str] = None) -> str:
        if not session_id or session_id not in SESSIONS_DB:
            new_id = session_id or str(uuid.uuid4())
            SESSIONS_DB[new_id] = []
            return new_id
        return session_id

    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        recommendations: Optional[List[FoodItemDTO]] = None,
        meal_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> ChatMessage:
        if session_id not in SESSIONS_DB:
            SESSIONS_DB[session_id] = []

        msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            recommendations=recommendations,
            created_at=datetime.utcnow().isoformat(),
            meal_type=meal_type,
            location=location
        )
        SESSIONS_DB[session_id].append(msg)
        return msg

    @staticmethod
    def get_messages(session_id: str) -> List[ChatMessage]:
        return SESSIONS_DB.get(session_id, [])

    @staticmethod
    def clear_session(session_id: str):
        if session_id in SESSIONS_DB:
            SESSIONS_DB[session_id] = []

chat_service = ChatService()
