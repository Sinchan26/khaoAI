"""Five-node, Swiggy-only recommendation graph."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from wrapper.config import settings
from wrapper.log import get_logger, traced_node
from wrapper.prompts import FORMAT_RESPONSE_SYSTEM_PROMPT, INTENT_SYSTEM_PROMPT
from wrapper.providers.swiggy import (
    SwiggyAuthenticationRequired,
    SwiggyProviderError,
    current_runtime_context,
    normalize_menu_response,
)

_log = get_logger("graph")


def _recent_user_context(state: dict) -> str:
    previous = []
    for message in (state.get("messages") or [])[-8:]:
        if isinstance(message, HumanMessage):
            previous.append(str(message.content))
    current = str(state.get("user_query") or "").strip()
    if previous and previous[-1].strip() == current:
        previous.pop()
    return "\n".join(previous[-3:])


def _deterministic_entities(query: str, previous_context: str = "") -> dict[str, Any]:
    lower = query.lower().strip()
    combined = f"{previous_context}\n{query}".lower()
    budget_match = re.search(r"(?:under|below|within|max(?:imum)?|₹|rs\.?)[\s₹:]*(\d{2,5})", lower)
    is_veg = True if re.search(r"\b(veg|vegetarian|vegan)\b", lower) else None
    if re.search(r"\b(non[- ]?veg|chicken|mutton|fish|egg|prawn)\b", lower):
        is_veg = False

    stop = {
        "show", "find", "give", "want", "some", "food", "please", "suggest", "recommend",
        "under", "below", "near", "best", "rated", "cheap", "cheapest", "make", "options",
        "breakfast", "lunch", "dinner", "snack", "snacks", "veg", "vegetarian", "nonveg", "with",
        "what", "should", "eat", "now", "craving", "hungry", "anything", "something",
    }
    tokens = re.findall(r"[a-zA-Z]+", lower)
    dish_tokens = [token for token in tokens if token not in stop and len(token) > 2]
    dish = " ".join(dish_tokens[:4]) or None
    if not dish and previous_context:
        previous_tokens = re.findall(r"[a-zA-Z]+", previous_context.lower())
        previous_dish = [token for token in previous_tokens if token not in stop and len(token) > 2]
        if is_veg is True:
            previous_dish = [
                token for token in previous_dish
                if token not in {"chicken", "mutton", "fish", "egg", "prawn", "prawns"}
            ]
        dish = " ".join(previous_dish[-4:]) or None

    return {
        "intent": "general_chat" if lower in {"hi", "hello", "hey", "hola", "who are you"} else "food_query",
        "extracted_location": None,
        "extracted_cuisine": None,
        "extracted_dish": dish,
        "is_veg": is_veg,
        "max_budget": int(budget_match.group(1)) if budget_match else None,
        "reasoning": "deterministic fallback",
        "combined_context": combined[-500:],
    }


def _intent_summary(result: dict) -> dict[str, Any]:
    return {
        "intent": result.get("intent", "?"),
        "entities": {
            key: value for key, value in (result.get("extracted_entities") or {}).items()
            if value is not None and key not in {"reasoning", "combined_context"}
        } or "none",
    }


@traced_node("intent_classifier", summary_fn=_intent_summary)
async def classify_intent_node(state: dict) -> dict:
    user_query = state.get("user_query", "")
    previous_context = _recent_user_context(state)
    fallback = _deterministic_entities(user_query, previous_context)
    if fallback["intent"] == "general_chat" or not settings.openai_api_key:
        return {"intent": fallback["intent"], "extracted_entities": fallback, "current_step": "intent_classified"}

    try:
        from wrapper.llm import get_llm
        llm = get_llm(temperature=0.1)
        prompt = f"Recent conversation:\n{previous_context or '(none)'}\n\nUser Message: {user_query}"
        response = await llm.ainvoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT), HumanMessage(content=prompt),
        ])
        content = str(response.content).strip()
        if content.startswith("```"):
            content = content.split("```", 2)[1].removeprefix("json").strip()
        data = json.loads(content)
        merged = fallback.copy()
        merged.update({key: value for key, value in data.items() if value is not None})
        return {
            "intent": data.get("intent", fallback["intent"]),
            "extracted_entities": merged,
            "current_step": "intent_classified",
        }
    except Exception as exc:
        _log.warning("Intent LLM unavailable; deterministic extraction used (%s)", type(exc).__name__)
        return {"intent": fallback["intent"], "extracted_entities": fallback, "current_step": "intent_classified"}


def _determine_meal_type(hour: int) -> str:
    if 6 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 16:
        return "lunch"
    if 16 <= hour < 19:
        return "snacks"
    if 19 <= hour < 23:
        return "dinner"
    return "late_night"


def _context_summary(result: dict) -> dict[str, Any]:
    return {"meal_type": result.get("meal_type", "?"), "location": result.get("user_location", "?")}


@traced_node("context_resolver", summary_fn=_context_summary)
async def resolve_context_node(state: dict) -> dict:
    now = datetime.now(ZoneInfo(settings.local_timezone))
    query = (state.get("user_query") or "").lower()
    explicit = next((name for name in ("breakfast", "lunch", "dinner") if name in query), None)
    if any(word in query for word in ("snack", "tea", "chai")):
        explicit = "snacks"
    meal_type = explicit or _determine_meal_type(now.hour)
    runtime = current_runtime_context()
    location = runtime.address_label if runtime else state.get("user_location") or settings.default_location
    return {
        "meal_type": meal_type,
        "detected_time": now.isoformat(),
        "user_location": location,
        "current_step": "context_resolved",
    }


def _searcher_summary(result: dict) -> dict[str, Any]:
    return {
        "provider": "Swiggy",
        "total": len(result.get("search_results") or []),
        "error": result.get("provider_error"),
    }


@traced_node("food_searcher", summary_fn=_searcher_summary)
async def food_searcher_node(state: dict) -> dict:
    entities = state.get("extracted_entities") or {}
    prefs = state.get("food_preferences") or {}
    query = entities.get("extracted_dish") or entities.get("extracted_cuisine")
    if not query:
        return {
            "search_results": [],
            "provider_error": "Tell me a dish or cuisine to search on Swiggy.",
            "current_step": "food_searched",
        }
    is_veg = entities.get("is_veg")
    if is_veg is None:
        is_veg = True if prefs.get("dietary_preference") == "veg" else None

    runtime = current_runtime_context()
    if runtime:
        try:
            payload = await runtime.client.search_menu(runtime.address_id, query, veg_only=is_veg is True)
            items = normalize_menu_response(payload)
        except (SwiggyAuthenticationRequired, SwiggyProviderError) as exc:
            return {"search_results": [], "provider_error": str(exc), "current_step": "food_searched"}
    elif settings.fixture_provider_enabled:
        from mocks.store import search_tomato
        items = search_tomato(query=query, is_veg=is_veg, limit=20)
        items = [{**item, "platform": "Swiggy Fixture"} for item in items]
    else:
        return {
            "search_results": [],
            "provider_error": "Connect Swiggy and choose a delivery address in Settings.",
            "current_step": "food_searched",
        }

    if entities.get("is_veg") is False or prefs.get("dietary_preference") == "non-veg":
        items = [item for item in items if item.get("is_veg") is False]
    return {"search_results": items, "current_step": "food_searched"}


def _normalize_inverse(value: float, minimum: float, maximum: float) -> float:
    return 1.0 if maximum == minimum else (maximum - value) / (maximum - minimum)


def _normalize(value: float, minimum: float, maximum: float) -> float:
    return 1.0 if maximum == minimum else (value - minimum) / (maximum - minimum)


def _calculate_composite_score(items: list[dict[str, Any]], preferences: dict, entities: dict) -> list[dict[str, Any]]:
    items = [item for item in items if item.get("availability") != "OUT_OF_STOCK"]
    budget_caps = {"budget": 150, "medium": 350, "premium": None}
    max_price = entities.get("max_budget") or budget_caps.get(preferences.get("budget_preference"))
    if max_price:
        items = [item for item in items if item["price"] <= max_price]
    max_delivery = preferences.get("max_delivery_time")
    if max_delivery:
        items = [
            item for item in items
            if item.get("delivery_time_mins") is None or item["delivery_time_mins"] <= max_delivery
        ]
    if not items:
        return []

    prices = [float(item["price"]) for item in items]
    ratings = [float(item["rating"]) for item in items if item.get("rating") is not None]
    deliveries = [float(item["delivery_time_mins"]) for item in items if item.get("delivery_time_mins") is not None]
    ranked = []
    for item in items:
        price_score = _normalize_inverse(float(item["price"]), min(prices), max(prices))
        rating_score = (
            _normalize(float(item["rating"]), min(ratings), max(ratings)) if item.get("rating") is not None and ratings else 0.5
        )
        delivery_score = (
            _normalize_inverse(float(item["delivery_time_mins"]), min(deliveries), max(deliveries))
            if item.get("delivery_time_mins") is not None and deliveries else 0.5
        )
        preference_score = 1.0 if item.get("is_bestseller") else 0.5
        score = 0.35 * price_score + 0.25 * rating_score + 0.25 * delivery_score + 0.15 * preference_score
        candidate = dict(item)
        candidate["composite_score"] = round(score, 3)
        badges = []
        if item["price"] == min(prices):
            badges.append("Best Value")
        if item.get("rating") is not None and item["rating"] >= 4.5:
            badges.append("Top Rated")
        if item.get("delivery_time_mins") is not None and item["delivery_time_mins"] <= 20:
            badges.append("Fast Delivery")
        if item.get("is_bestseller"):
            badges.append("Bestseller")
        candidate["badges"] = badges
        ranked.append(candidate)
    return sorted(ranked, key=lambda item: item["composite_score"], reverse=True)


def _ranker_summary(result: dict) -> dict[str, Any]:
    ranked = result.get("ranked_results") or []
    return {"top_pick": ranked[0]["name"] if ranked else None, "ranked": len(ranked)}


@traced_node("ranker", summary_fn=_ranker_summary)
async def ranker_node(state: dict) -> dict:
    ranked = _calculate_composite_score(
        state.get("search_results") or [],
        state.get("food_preferences") or {},
        state.get("extracted_entities") or {},
    )
    return {"ranked_results": ranked[:6], "current_step": "food_ranked"}


def _formatter_summary(result: dict) -> dict[str, Any]:
    reply = result.get("final_reply") or ""
    return {"reply_len": len(reply), "has_reply": bool(reply)}


def _item_line(item: dict) -> str:
    parts = [f"₹{item['price']:.0f}"]
    if item.get("rating") is not None:
        parts.append(f"⭐{item['rating']}")
    if item.get("delivery_time_mins") is not None:
        parts.append(f"{item['delivery_time_mins']} mins")
    return f"- {item['name']} from {item['restaurant_name']} ({', '.join(parts)})"


@traced_node("response_formatter", summary_fn=_formatter_summary)
async def response_formatter_node(state: dict) -> dict:
    if state.get("intent") == "general_chat":
        return {
            "final_reply": "Hey! 👋 I'm **khaoAI**. Connect Swiggy, choose your delivery address, and tell me a dish or cuisine to rank.",
            "current_step": "completed",
        }
    ranked = state.get("ranked_results") or []
    if not ranked:
        return {
            "final_reply": state.get("provider_error") or "I couldn't find matching available Swiggy items. Try another dish or relax your filters.",
            "current_step": "completed",
        }
    top = ranked[0]
    if settings.openai_api_key:
        try:
            from wrapper.llm import get_llm
            summary = "\n".join(_item_line(item) for item in ranked[:4])
            response = await get_llm(0.4).ainvoke([
                SystemMessage(content=FORMAT_RESPONSE_SYSTEM_PROMPT),
                HumanMessage(content=f"User: {state.get('user_query')}\nSwiggy results:\n{summary}"),
            ])
            return {"final_reply": str(response.content).strip(), "current_step": "completed"}
        except Exception as exc:
            _log.warning("Response LLM unavailable; deterministic response used (%s)", type(exc).__name__)
    rating = f", ⭐{top['rating']}" if top.get("rating") is not None else ""
    return {
        "final_reply": (
            f"My top Swiggy pick is **{top['name']}** from **{top['restaurant_name']}** "
            f"for **₹{top['price']:.0f}**{rating}. I ranked the available choices using price, rating, "
            "delivery information when available, and your saved preferences."
        ),
        "current_step": "completed",
    }
