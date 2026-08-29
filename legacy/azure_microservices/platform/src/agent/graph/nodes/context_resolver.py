import logging
from datetime import datetime
from ..state import FoodAgentState

def determine_meal_type_from_hour(hour: int) -> str:
    if 6 <= hour < 11:
        return "breakfast"
    elif 11 <= hour < 16:
        return "lunch"
    elif 16 <= hour < 19:
        return "snacks"
    elif 19 <= hour < 23:
        return "dinner"
    else:
        return "late_night"

async def resolve_context_node(state: FoodAgentState) -> dict:
    logging.info("Node: Context Resolver")
    now = datetime.now()
    detected_meal_type = determine_meal_type_from_hour(now.hour)

    user_query = (state.get("user_query") or "").lower()
    extracted_entities = state.get("extracted_entities") or {}

    # Override meal_type if explicitly mentioned by user
    if "breakfast" in user_query:
        meal_type = "breakfast"
    elif "lunch" in user_query:
        meal_type = "lunch"
    elif "snack" in user_query or "tea" in user_query or "chai" in user_query:
        meal_type = "snacks"
    elif "dinner" in user_query:
        meal_type = "dinner"
    elif "midnight" in user_query or "late night" in user_query:
        meal_type = "late_night"
    else:
        meal_type = detected_meal_type

    # Resolve location: priority -> extracted from query > user_location in state > default
    extracted_loc = extracted_entities.get("extracted_location")
    if extracted_loc and len(extracted_loc.strip()) > 2:
        final_location = extracted_loc.strip()
    else:
        final_location = state.get("user_location") or "Salt Lake, Sector V"

    return {
        "meal_type": meal_type,
        "detected_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "user_location": final_location,
        "current_step": "context_resolved"
    }
