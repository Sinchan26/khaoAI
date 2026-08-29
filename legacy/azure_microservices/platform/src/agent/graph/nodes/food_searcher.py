import asyncio
import logging
from ...tools.mcp_client import mcp_client
from ..state import FoodAgentState

async def food_searcher_node(state: FoodAgentState) -> dict:
    logging.info("Node: Food Searcher (MCP Tools)")
    location = state.get("user_location")
    meal_type = state.get("meal_type")
    extracted_entities = state.get("extracted_entities") or {}
    prefs = state.get("food_preferences") or {}

    query = extracted_entities.get("extracted_dish") or extracted_entities.get("extracted_cuisine")
    if not query and state.get("user_query"):
        # If no specific dish extracted, search by user query tokens if not generic
        raw_q = state.get("user_query")
        if not any(w in raw_q.lower() for w in ["what should i eat", "hungry", "suggest something", "recommend"]):
            query = raw_q

    # Handle veg/non-veg filter
    is_veg = extracted_entities.get("is_veg")
    if is_veg is None and prefs.get("dietary_preference"):
        if prefs.get("dietary_preference") == "veg":
            is_veg = True
        elif prefs.get("dietary_preference") == "non-veg":
            is_veg = False

    max_price = extracted_entities.get("max_budget")

    # Run searches concurrently across Tomato and Twiggy
    tomato_task = mcp_client.search_tomato(
        query=query,
        location=location,
        meal_type=meal_type,
        max_price=max_price,
        is_veg=is_veg,
        limit=20
    )
    twiggy_task = mcp_client.search_twiggy(
        query=query,
        location=location,
        meal_type=meal_type,
        max_price=max_price,
        is_veg=is_veg,
        limit=20
    )

    tomato_results, twiggy_results = await asyncio.gather(
        tomato_task,
        twiggy_task,
        return_exceptions=True
    )

    all_items = []
    if isinstance(tomato_results, list):
        all_items.extend(tomato_results)
    else:
        logging.error(f"Tomato search error: {tomato_results}")

    if isinstance(twiggy_results, list):
        all_items.extend(twiggy_results)
    else:
        logging.error(f"Twiggy search error: {twiggy_results}")

    return {
        "search_results": all_items,
        "current_step": "food_searched"
    }
