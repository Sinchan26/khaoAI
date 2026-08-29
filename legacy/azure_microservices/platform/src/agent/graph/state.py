from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class FoodAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    user_location: str
    meal_type: Optional[str]
    detected_time: Optional[str]
    intent: Optional[str]
    extracted_entities: Optional[Dict[str, Any]]
    food_preferences: Optional[Dict[str, Any]]
    search_results: Optional[List[Dict[str, Any]]]
    ranked_results: Optional[List[Dict[str, Any]]]
    final_reply: Optional[str]
    current_step: str
    error: Optional[str]
