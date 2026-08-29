"""Consolidated Pydantic models for auth, chat, settings, and food items."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
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
    max_delivery_time: int = Field(default=45, ge=10, le=120)
    selected_swiggy_address_id: Optional[str] = None
    selected_swiggy_address_label: Optional[str] = None

    @field_validator("dietary_preference")
    @classmethod
    def validate_diet(cls, value: str) -> str:
        if value not in {"all", "veg", "non-veg"}:
            raise ValueError("dietary_preference must be all, veg, or non-veg")
        return value

    @field_validator("budget_preference")
    @classmethod
    def validate_budget(cls, value: str) -> str:
        if value not in {"budget", "medium", "premium"}:
            raise ValueError("budget_preference must be budget, medium, or premium")
        return value


# ---------------------------------------------------------------------------
# Food / Chat
# ---------------------------------------------------------------------------

class FoodItemDTO(BaseModel):
    id: str
    restaurant_id: str
    restaurant_name: str
    platform: str
    location: str = ""
    name: str
    price: float
    meal_type: str = ""
    cuisine: str = ""
    is_veg: Optional[bool] = None
    rating: Optional[float] = None
    ratings_count: int = 0
    delivery_time_mins: Optional[int] = None
    distance_km: Optional[float] = None
    availability: str = "AVAILABLE"
    description: str = ""
    image_url: str = ""
    composite_score: Optional[float] = None
    badges: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    id: str
    role: str  # 'user' | 'assistant'
    content: str
    recommendations: Optional[list[FoodItemDTO]] = None
    created_at: str
    meal_type: Optional[str] = None
    location: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    location: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message cannot be empty")
        return value


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    recommendations: list[FoodItemDTO] = Field(default_factory=list)
    meal_type: Optional[str] = None
    location: Optional[str] = None
    graph_trace: Optional[dict[str, Any]] = None


class SwiggyConnectionStatus(BaseModel):
    connected: bool
    token_expires_at: Optional[str] = None
    selected_address_id: Optional[str] = None
    selected_address_label: Optional[str] = None
    needs_reauthentication: bool = False


class SwiggyConnectResponse(BaseModel):
    authorization_url: str


class SwiggyAddressSelection(BaseModel):
    address_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=255)
