import logging
from langgraph.graph import StateGraph, START, END
from .state import FoodAgentState
from .nodes.intent_classifier import classify_intent_node
from .nodes.context_resolver import resolve_context_node
from .nodes.food_searcher import food_searcher_node
from .nodes.ranker import ranker_node
from .nodes.response_formatter import response_formatter_node

def route_after_intent(state: FoodAgentState) -> str:
    intent = state.get("intent", "food_query")
    if intent == "general_chat":
        return "response_formatter"
    return "context_resolver"

def build_food_graph():
    graph = StateGraph(FoodAgentState)

    # Register nodes
    graph.add_node("intent_classifier", classify_intent_node)
    graph.add_node("context_resolver", resolve_context_node)
    graph.add_node("food_searcher", food_searcher_node)
    graph.add_node("ranker", ranker_node)
    graph.add_node("response_formatter", response_formatter_node)

    # Add edges
    graph.add_edge(START, "intent_classifier")
    graph.add_conditional_edges(
        "intent_classifier",
        route_after_intent,
        {
            "context_resolver": "context_resolver",
            "response_formatter": "response_formatter"
        }
    )
    graph.add_edge("context_resolver", "food_searcher")
    graph.add_edge("food_searcher", "ranker")
    graph.add_edge("ranker", "response_formatter")
    graph.add_edge("response_formatter", END)

    app = graph.compile()
    return app

# Singleton compiled graph
food_graph = build_food_graph()
