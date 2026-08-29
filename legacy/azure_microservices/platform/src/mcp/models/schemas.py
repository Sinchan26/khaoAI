from pydantic import BaseModel, Field
from typing import Optional, List

class FoodSearchRequest(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    meal_type: Optional[str] = None
    is_veg: Optional[bool] = None
    max_price: Optional[int] = None
    sort_by: Optional[str] = "default"
    limit: int = 15

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

class FoodSearchResponse(BaseModel):
    platform: str
    total: int
    results: List[FoodItemDTO]
