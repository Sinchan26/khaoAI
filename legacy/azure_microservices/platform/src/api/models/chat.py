from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

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
    badges: Optional[List[str]] = []

class ChatMessage(BaseModel):
    id: str
    role: str # 'user' | 'assistant'
    content: str
    recommendations: Optional[List[FoodItemDTO]] = None
    created_at: str
    meal_type: Optional[str] = None
    location: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    location: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    recommendations: List[FoodItemDTO] = []
    meal_type: Optional[str] = None
    location: Optional[str] = None
