import json
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from .models import Restaurant, MenuItem, SearchResponse

router = APIRouter()

# Load data on module import
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

with open(os.path.join(DATA_DIR, "restaurants.json"), "r", encoding="utf-8") as f:
    RESTAURANTS_RAW: List[dict] = json.load(f)

with open(os.path.join(DATA_DIR, "menu_items.json"), "r", encoding="utf-8") as f:
    MENU_ITEMS_RAW: List[dict] = json.load(f)

RESTAURANTS: List[Restaurant] = [Restaurant(**r) for r in RESTAURANTS_RAW]
MENU_ITEMS: List[MenuItem] = [MenuItem(**m) for m in MENU_ITEMS_RAW]

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Tomato Simulator",
        "restaurants_count": len(RESTAURANTS),
        "menu_items_count": len(MENU_ITEMS)
    }

@router.get("/restaurants", response_model=List[Restaurant])
def list_restaurants(
    location: Optional[str] = None,
    cuisine: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: int = 20
):
    results = RESTAURANTS
    if location:
        loc_clean = location.lower()
        results = [r for r in results if loc_clean in r.location.lower()]
    if cuisine:
        c_clean = cuisine.lower()
        results = [r for r in results if c_clean in r.cuisine.lower()]
    if min_rating is not None:
        results = [r for r in results if r.rating >= min_rating]
    return results[:limit]

@router.get("/restaurants/{restaurant_id}/menu", response_model=List[MenuItem])
def get_restaurant_menu(
    restaurant_id: str,
    meal_type: Optional[str] = None,
    is_veg: Optional[bool] = None
):
    items = [m for m in MENU_ITEMS if m.restaurant_id == restaurant_id]
    if not items:
        raise HTTPException(status_code=404, detail="Restaurant not found or menu empty")
    if meal_type:
        items = [m for m in items if m.meal_type == meal_type.lower()]
    if is_veg is not None:
        items = [m for m in items if m.is_veg == is_veg]
    return items

@router.get("/search", response_model=SearchResponse)
def search_food(
    query: Optional[str] = None,
    location: Optional[str] = None,
    meal_type: Optional[str] = None,
    is_veg: Optional[bool] = None,
    max_price: Optional[int] = None,
    sort_by: Optional[str] = "default",
    limit: int = 20
):
    results = MENU_ITEMS

    if location:
        loc_clean = location.lower()
        # Check if restaurant location or specific keyword matches
        loc_words = [w for w in loc_clean.replace(",", " ").split() if len(w) > 2]
        if loc_words:
            results = [
                m for m in results
                if any(w in m.location.lower() for w in loc_words)
            ]

    if meal_type:
        results = [m for m in results if m.meal_type == meal_type.lower()]

    if is_veg is not None:
        results = [m for m in results if m.is_veg == is_veg]

    if max_price is not None:
        results = [m for m in results if m.price <= max_price]

    if query:
        q = query.lower().strip()
        q_tokens = [t for t in q.split() if len(t) > 2]
        if q_tokens:
            results = [
                m for m in results
                if any(tok in m.name.lower() or tok in m.cuisine.lower() or tok in m.restaurant_name.lower() for tok in q_tokens)
            ]

    if sort_by == "price_asc":
        results = sorted(results, key=lambda x: x.price)
    elif sort_by == "rating_desc":
        results = sorted(results, key=lambda x: x.rating, reverse=True)
    elif sort_by == "delivery_asc":
        results = sorted(results, key=lambda x: x.delivery_time_mins)

    return SearchResponse(
        platform="Tomato",
        total=len(results),
        results=results[:limit]
    )
