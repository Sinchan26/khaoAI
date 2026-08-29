"""LangGraph agent state definition."""
from __future__ import annotations

from typing import Annotated, Any, Optional

from langgraph.graph.message import add_messages


class FoodAgentState(dict):
    """Typed state for the food recommendation graph.

    Using dict subclass with annotations so LangGraph can inspect the schema
    while we keep runtime flexibility.
    """
    pass


# The actual schema is declared as a TypedDict for LangGraph's StateGraph:
from typing import TypedDict


class FoodAgentStateSchema(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    user_query: str
    user_location: str
    meal_type: Optional[str]
    detected_time: Optional[str]
    intent: Optional[str]
    extracted_entities: Optional[dict[str, Any]]
    food_preferences: Optional[dict[str, Any]]
    search_results: Optional[list[dict[str, Any]]]
    ranked_results: Optional[list[dict[str, Any]]]
    final_reply: Optional[str]
    current_step: str
    error: Optional[str]
