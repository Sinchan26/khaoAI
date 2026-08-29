from wrapper.graph.nodes import _calculate_composite_score, _deterministic_entities


def candidate(name: str, price: float, rating: float, availability: str = "AVAILABLE"):
    return {
        "id": name, "restaurant_id": "r", "restaurant_name": "Restaurant", "platform": "Swiggy",
        "location": "", "name": name, "price": price, "meal_type": "", "cuisine": "",
        "is_veg": True, "rating": rating, "ratings_count": 10, "delivery_time_mins": None,
        "distance_km": None, "availability": availability, "description": "", "image_url": "",
        "is_bestseller": False,
    }


def test_filters_budget_and_stock_before_ranking() -> None:
    ranked = _calculate_composite_score(
        [candidate("Value", 120, 4.2), candidate("Expensive", 400, 4.9), candidate("Unavailable", 100, 5.0, "OUT_OF_STOCK")],
        {"budget_preference": "budget", "max_delivery_time": 45}, {},
    )
    assert [item["name"] for item in ranked] == ["Value"]


def test_followup_uses_previous_food_context() -> None:
    entities = _deterministic_entities("make it veg under 250", "I want chicken biryani")
    assert entities["is_veg"] is True
    assert entities["max_budget"] == 250
    assert entities["extracted_dish"] == "biryani"
