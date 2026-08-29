"""LLM factory, LangGraph compilation, and the top-level ``orchestrate()`` function.

This module is the single place where:
  - OpenAI / ChatOpenAI is configured
  - The 5-node food graph is compiled (once, at import time)
  - ``orchestrate()`` runs the graph for a chat request, collecting a full
    GraphTrace and pushing it into the TRACE_BUFFER for debugging.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from wrapper.config import settings
from wrapper.graph.nodes import (
    classify_intent_node,
    food_searcher_node,
    ranker_node,
    resolve_context_node,
    response_formatter_node,
)
from wrapper.graph.state import FoodAgentStateSchema
from wrapper.log import (
    TRACE_BUFFER,
    GraphTrace,
    clear_current_trace,
    get_logger,
    set_current_trace,
)

_log = get_logger("graph")


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Return a configured ChatOpenAI instance."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        api_key=settings.openai_api_key,
        max_tokens=800,
        timeout=20,
        max_retries=2,
    )


# ---------------------------------------------------------------------------
# Graph compilation (singleton)
# ---------------------------------------------------------------------------

def _route_after_intent(state: dict) -> str:
    intent = state.get("intent", "food_query")
    target = "response_formatter" if intent == "general_chat" else "context_resolver"
    _log.info(
        "|-- Route: intent_classifier -> %s  (condition: intent=%s)",
        target, intent,
    )
    return target


def _build_food_graph() -> Any:
    graph = StateGraph(FoodAgentStateSchema)

    graph.add_node("intent_classifier", classify_intent_node)
    graph.add_node("context_resolver", resolve_context_node)
    graph.add_node("food_searcher", food_searcher_node)
    graph.add_node("ranker", ranker_node)
    graph.add_node("response_formatter", response_formatter_node)

    graph.add_edge(START, "intent_classifier")
    graph.add_conditional_edges(
        "intent_classifier",
        _route_after_intent,
        {
            "context_resolver": "context_resolver",
            "response_formatter": "response_formatter",
        },
    )
    graph.add_edge("context_resolver", "food_searcher")
    graph.add_edge("food_searcher", "ranker")
    graph.add_edge("ranker", "response_formatter")
    graph.add_edge("response_formatter", END)

    compiled = graph.compile(checkpointer=MemorySaver())
    _log.info("[+] LangGraph compiled: 5 nodes, 6 edges")
    _log.info("Graph topology:")
    _log.info("  START -> intent_classifier")
    _log.info("  intent_classifier ->(conditional)-> context_resolver | response_formatter")
    _log.info("  context_resolver -> food_searcher")
    _log.info("  food_searcher -> ranker")
    _log.info("  ranker -> response_formatter")
    _log.info("  response_formatter -> END")
    return compiled


food_graph = _build_food_graph()


# ---------------------------------------------------------------------------
# Orchestrate
# ---------------------------------------------------------------------------

async def orchestrate(
    *,
    message: str,
    location: Optional[str] = None,
    preferences: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
    session_id: str,
    user_id: str,
    history: Optional[list[dict[str, Any]]] = None,
    provider_context: Any | None = None,
) -> dict[str, Any]:
    """Run the food-recommendation graph end-to-end.

    Returns a dict with ``reply``, ``recommendations``, ``meal_type``,
    ``location``, and ``graph_trace``.
    """
    trace = GraphTrace(query=message, owner_user_id=user_id)
    if request_id:
        trace.request_id = request_id
    trace.started_at = time.perf_counter()

    set_current_trace(trace)

    _log.info("/-- Graph START  (request_id=%s)", trace.request_id)

    prefs = preferences or {}
    graph_messages = []
    for item in history or []:
        content = str(item.get("content") or "")
        message_id = str(item.get("id") or "") or None
        if item.get("role") == "assistant":
            graph_messages.append(AIMessage(content=content, id=message_id))
        else:
            graph_messages.append(HumanMessage(content=content, id=message_id))
    initial_state: dict[str, Any] = {
        "user_query": message,
        "user_location": location or prefs.get("default_location") or settings.default_location,
        "food_preferences": prefs,
        "messages": graph_messages,
        "current_step": "start",
    }

    provider_context_token = None
    try:
        if provider_context is not None:
            from wrapper.providers.swiggy import set_runtime_context
            provider_context_token = set_runtime_context(provider_context)
        result = await food_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": f"{user_id}:{session_id}"}},
        )

        trace.total_duration_ms = (time.perf_counter() - trace.started_at) * 1000
        path_str = " -> ".join(trace.path)
        _log.info(
            "\\-- Graph END  [+]  (%dms)  path=[%s]",
            int(trace.total_duration_ms), path_str,
        )

        TRACE_BUFFER.append(trace)

        return {
            "reply": result.get("final_reply", "Here are your food recommendations."),
            "recommendations": result.get("ranked_results") or [],
            "meal_type": result.get("meal_type"),
            "location": result.get("user_location"),
            "graph_trace": trace.to_dict(),
        }

    except Exception as exc:
        trace.total_duration_ms = (time.perf_counter() - trace.started_at) * 1000
        trace.error = str(exc)
        path_str = " -> ".join(trace.path)
        _log.error(
            "\\-- Graph END  [x]  (%dms)  path=[%s]  error=%s",
            int(trace.total_duration_ms), path_str, exc,
        )
        TRACE_BUFFER.append(trace)
        raise

    finally:
        if provider_context_token is not None:
            from wrapper.providers.swiggy import reset_runtime_context
            reset_runtime_context(provider_context_token)
        clear_current_trace()
