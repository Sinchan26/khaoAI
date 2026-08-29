"""Consolidated Pydantic models for auth, chat, settings, and food items."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    display_name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class UserSettings(BaseModel):
    user_id: Optional[str] = None
    default_location: str = "Salt Lake, Sector V"
    dietary_preference: str = "all"        # 'all' | 'veg' | 'non-veg'
    budget_preference: str = "medium"      # 'budget' | 'medium' | 'premium'
    max_delivery_time: int = 45


# ---------------------------------------------------------------------------
# Food / Chat
# ---------------------------------------------------------------------------

class FoodItemDTO(BaseModel):
    id: str
    restaurant_id: str
    restaurant_name: str
    platform: str
    location: str
    name: str
    price: int
    meal_type: str
    cuisine: str
    is_veg: bool
    rating: float
    ratings_count: int
    delivery_time_mins: int
    description: str
    image_url: str
    composite_score: Optional[float] = None
    badges: Optional[list[str]] = []


class ChatMessage(BaseModel):
    id: str
    role: str  # 'user' | 'assistant'
    content: str
    recommendations: Optional[list[FoodItemDTO]] = None
    created_at: str
    meal_type: Optional[str] = None
    location: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    location: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    recommendations: list[FoodItemDTO] = []
    meal_type: Optional[str] = None
    location: Optional[str] = None
    graph_trace: Optional[dict[str, Any]] = None
