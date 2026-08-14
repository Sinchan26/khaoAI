from pydantic import BaseModel, Field
from typing import Optional, List

class Restaurant(BaseModel):
    id: str
    name: str
    platform: str
    location: str
    cuisine: str
    rating: float
    ratings_count: int
    avg_delivery_time_mins: int
    price_for_two: int
    is_pure_veg: bool
    is_open: bool = True

class MenuItem(BaseModel):
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

class SearchResponse(BaseModel):
    platform: str
    total: int
    results: List[MenuItem]
