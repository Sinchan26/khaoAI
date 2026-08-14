import logging
from typing import List, Dict, Any
from ..state import FoodAgentState

def calculate_composite_score(
    items: List[Dict[str, Any]],
    w_price: float = 0.40,
    w_rating: float = 0.30,
    w_delivery: float = 0.30
) -> List[Dict[str, Any]]:
    if not items:
        return []

    prices = [item["price"] for item in items]
    ratings = [item["rating"] for item in items]
    deliveries = [item["delivery_time_mins"] for item in items]

    min_p, max_p = min(prices), max(prices)
    min_r, max_r = min(ratings), max(ratings)
    min_d, max_d = min(deliveries), max(deliveries)

    p_range = max_p - min_p if max_p != min_p else 1.0
    r_range = max_r - min_r if max_r != min_r else 1.0
    d_range = max_d - min_d if max_d != min_d else 1.0

    ranked = []
    for item in items:
        # Inverse price: cheapest gets highest value 1.0
        norm_inv_price = (max_p - item["price"]) / p_range
        # Rating: highest gets 1.0
        norm_rating = (item["rating"] - min_r) / r_range
        # Inverse delivery: lowest time gets 1.0
        norm_inv_delivery = (max_d - item["delivery_time_mins"]) / d_range

        score = (w_price * norm_inv_price) + (w_rating * norm_rating) + (w_delivery * norm_inv_delivery)

        item_copy = dict(item)
        item_copy["composite_score"] = round(score, 3)

        # Assign badge
        badges = []
        if item["price"] == min_p:
            badges.append("Cheapest Pick")
        if item["rating"] >= 4.7:
            badges.append("Top Rated")
        if item["delivery_time_mins"] <= 20:
            badges.append("Superfast Delivery")
        item_copy["badges"] = badges

        ranked.append(item_copy)

    # Sort descending by composite score
    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked

async def ranker_node(state: FoodAgentState) -> dict:
    logging.info("Node: Ranker & Prioritizer")
    search_results = state.get("search_results") or []
    ranked_items = calculate_composite_score(search_results)

    # Pick top 6 recommendations
    top_picks = ranked_items[:6]

    return {
        "ranked_results": top_picks,
        "current_step": "food_ranked"
    }
