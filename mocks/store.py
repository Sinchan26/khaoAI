"""In-memory data store for Tomato and Twiggy mock food-delivery platforms.

Loads restaurant and menu-item JSON files once at startup, then exposes
pure-Python ``search_tomato()`` and ``search_twiggy()`` functions that do
the same filtering the original simulator REST routes did — but without
any HTTP overhead.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from wrapper.log import get_logger

_log = get_logger("mocks")

# ---------------------------------------------------------------------------
# Data containers (populated by ``load()``)
# ---------------------------------------------------------------------------

_tomato_restaurants: list[dict[str, Any]] = []
_tomato_items: list[dict[str, Any]] = []
_twiggy_restaurants: list[dict[str, Any]] = []
_twiggy_items: list[dict[str, Any]] = []

_DATA_ROOT = Path(__file__).resolve().parent.parent / "platform" / "src" / "services"


def _load_json(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def load() -> None:
    """Load all JSON data files into memory.  Called from the FastAPI lifespan."""
    global _tomato_restaurants, _tomato_items, _twiggy_restaurants, _twiggy_items

    tomato_dir = _DATA_ROOT / "tomato_simulator" / "data"
    twiggy_dir = _DATA_ROOT / "twiggy_simulator" / "data"

    _tomato_restaurants = _load_json(tomato_dir / "restaurants.json")
    _tomato_items = _load_json(tomato_dir / "menu_items.json")
    _log.info(
        "Loaded Tomato: %d restaurants, %d menu items",
        len(_tomato_restaurants), len(_tomato_items),
    )

    _twiggy_restaurants = _load_json(twiggy_dir / "restaurants.json")
    _twiggy_items = _load_json(twiggy_dir / "menu_items.json")
    _log.info(
        "Loaded Twiggy: %d restaurants, %d menu items",
        len(_twiggy_restaurants), len(_twiggy_items),
    )


# ---------------------------------------------------------------------------
# Search helpers (shared logic)
# ---------------------------------------------------------------------------

def _filter_items(
    items: list[dict[str, Any]],
    *,
    query: Optional[str] = None,
    location: Optional[str] = None,
    meal_type: Optional[str] = None,
    is_veg: Optional[bool] = None,
    max_price: Optional[int] = None,
    sort_by: str = "default",
    limit: int = 20,
) -> list[dict[str, Any]]:
    results = items

    if location:
        loc_words = [w for w in location.lower().replace(",", " ").split() if len(w) > 2]
        if loc_words:
            results = [
                m for m in results
                if any(w in m["location"].lower() for w in loc_words)
            ]

    if meal_type:
        mt = meal_type.lower()
        results = [m for m in results if m["meal_type"] == mt]

    if is_veg is not None:
        results = [m for m in results if m["is_veg"] == is_veg]

    if max_price is not None:
        results = [m for m in results if m["price"] <= max_price]

    if query:
        q_tokens = [t for t in query.lower().split() if len(t) > 2]
        if q_tokens:
            results = [
                m for m in results
                if any(
                    tok in m["name"].lower()
                    or tok in m["cuisine"].lower()
                    or tok in m["restaurant_name"].lower()
                    for tok in q_tokens
                )
            ]

    if sort_by == "price_asc":
        results = sorted(results, key=lambda x: x["price"])
    elif sort_by == "rating_desc":
        results = sorted(results, key=lambda x: x["rating"], reverse=True)
    elif sort_by == "delivery_asc":
        results = sorted(results, key=lambda x: x["delivery_time_mins"])

    return results[:limit]


# ---------------------------------------------------------------------------
# Public search functions
# ---------------------------------------------------------------------------

def search_tomato(
    *,
    query: Optional[str] = None,
    location: Optional[str] = None,
    meal_type: Optional[str] = None,
    is_veg: Optional[bool] = None,
    max_price: Optional[int] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search Tomato menu items — pure in-process, no HTTP."""
    t0 = time.perf_counter()
    results = _filter_items(
        _tomato_items,
        query=query, location=location, meal_type=meal_type,
        is_veg=is_veg, max_price=max_price, limit=limit,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    _log.debug(
        "Tomato search: location=%s, meal=%s, query=%s → %d hits (%.0fms)",
        location, meal_type, query, len(results), elapsed,
    )
    return results


def search_twiggy(
    *,
    query: Optional[str] = None,
    location: Optional[str] = None,
    meal_type: Optional[str] = None,
    is_veg: Optional[bool] = None,
    max_price: Optional[int] = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search Twiggy menu items — pure in-process, no HTTP."""
    t0 = time.perf_counter()
    results = _filter_items(
        _twiggy_items,
        query=query, location=location, meal_type=meal_type,
        is_veg=is_veg, max_price=max_price, limit=limit,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    _log.debug(
        "Twiggy search: location=%s, meal=%s, query=%s → %d hits (%.0fms)",
        location, meal_type, query, len(results), elapsed,
    )
    return results
