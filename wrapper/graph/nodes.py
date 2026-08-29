"""All five LangGraph nodes for the food recommendation pipeline.

Each node is wrapped with ``@traced_node`` for verbose enter/exit logging,
timing, and trace-step recording.  The logic inside each node is preserved
from the original ``platform/src/agent/graph/nodes/`` modules.

Node order:
  1. classify_intent   — LLM or fast-path intent detection
  2. resolve_context   — meal-type + location resolution
  3. food_searcher     — in-process search across Tomato + Twiggy
  4. ranker            — composite-score ranking
  5. response_formatter — LLM-generated conversational reply
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from wrapper.log import get_logger, traced_node
from wrapper.prompts import FORMAT_RESPONSE_SYSTEM_PROMPT, INTENT_SYSTEM_PROMPT

_log = get_logger("graph")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Intent Classifier
# ═══════════════════════════════════════════════════════════════════════════

def _intent_summary(result: dict) -> dict[str, Any]:
    return {
        "intent": result.get("intent", "?"),
        "entities": {
            k: v for k, v in (result.get("extracted_entities") or {}).items()
            if v is not None and k != "reasoning"
        } or "none",
    }


@traced_node("intent_classifier", summary_fn=_intent_summary)
async def classify_intent_node(state: dict) -> dict:
    user_query = state.get("user_query", "")

    # Fast deterministic check for common greetings
    q_lower = user_query.lower().strip()
    if q_lower in ("hi", "hello", "hey", "hola", "help", "who are you"):
        _log.info("│  └─ Fast path: greeting detected, skipping LLM")
        return {
            "intent": "general_chat",
            "extracted_entities": {},
            "current_step": "intent_classified",
        }

    try:
        from wrapper.llm import get_llm
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=f"User Message: {user_query}"),
        ]
        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # Parse JSON from LLM output safely
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        intent = data.get("intent", "food_query")
        return {
            "intent": intent,
            "extracted_entities": data,
            "current_step": "intent_classified",
        }
    except Exception as e:
        _log.warning("│  └─ Fallback: defaulting intent=food_query  (%s)", e)
        return {
            "intent": "food_query",
            "extracted_entities": {},
            "current_step": "intent_classified",
        }


# ═══════════════════════════════════════════════════════════════════════════
# 2. Context Resolver
# ═══════════════════════════════════════════════════════════════════════════

def _determine_meal_type_from_hour(hour: int) -> str:
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


def _context_summary(result: dict) -> dict[str, Any]:
    return {
        "meal_type": result.get("meal_type", "?"),
        "location": result.get("user_location", "?"),
    }


@traced_node("context_resolver", summary_fn=_context_summary)
async def resolve_context_node(state: dict) -> dict:
    now = datetime.now()
    detected_meal_type = _determine_meal_type_from_hour(now.hour)

    user_query = (state.get("user_query") or "").lower()
    extracted_entities = state.get("extracted_entities") or {}

    # Override meal_type if explicitly mentioned by user
    if "breakfast" in user_query:
        meal_type = "breakfast"
    elif "lunch" in user_query:
        meal_type = "lunch"
    elif any(w in user_query for w in ("snack", "tea", "chai")):
        meal_type = "snacks"
    elif "dinner" in user_query:
        meal_type = "dinner"
    elif any(w in user_query for w in ("midnight", "late night")):
        meal_type = "late_night"
    else:
        meal_type = detected_meal_type

    if meal_type != detected_meal_type:
        _log.info("│  └─ Meal type overridden by user text: %s → %s", detected_meal_type, meal_type)

    # Resolve location
    extracted_loc = extracted_entities.get("extracted_location")
    if extracted_loc and len(extracted_loc.strip()) > 2:
        final_location = extracted_loc.strip()
    else:
        final_location = state.get("user_location") or "Salt Lake, Sector V"

    return {
        "meal_type": meal_type,
        "detected_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "user_location": final_location,
        "current_step": "context_resolved",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. Food Searcher
# ═══════════════════════════════════════════════════════════════════════════

def _searcher_summary(result: dict) -> dict[str, Any]:
    items = result.get("search_results") or []
    tomato = sum(1 for i in items if i.get("platform") == "Tomato")
    twiggy = sum(1 for i in items if i.get("platform") == "Twiggy")
    return {"tomato_hits": tomato, "twiggy_hits": twiggy, "total": len(items)}


@traced_node("food_searcher", summary_fn=_searcher_summary)
async def food_searcher_node(state: dict) -> dict:
    from mocks.store import search_tomato, search_twiggy

    location = state.get("user_location")
    meal_type = state.get("meal_type")
    extracted_entities = state.get("extracted_entities") or {}
    prefs = state.get("food_preferences") or {}

    query = extracted_entities.get("extracted_dish") or extracted_entities.get("extracted_cuisine")
    if not query and state.get("user_query"):
        raw_q = state.get("user_query")
        generic_phrases = ("what should i eat", "hungry", "suggest something", "recommend")
        if not any(w in raw_q.lower() for w in generic_phrases):
            query = raw_q

    # Handle veg/non-veg filter
    is_veg = extracted_entities.get("is_veg")
    if is_veg is None and prefs.get("dietary_preference"):
        if prefs["dietary_preference"] == "veg":
            is_veg = True
        elif prefs["dietary_preference"] == "non-veg":
            is_veg = False

    max_price = extracted_entities.get("max_budget")

    _log.info("│  └─ Searching Tomato (location=%s, meal=%s, query=%s)", location, meal_type, query)
    tomato_results = search_tomato(
        query=query, location=location, meal_type=meal_type,
        max_price=max_price, is_veg=is_veg, limit=20,
    )

    _log.info("│  └─ Searching Twiggy (location=%s, meal=%s, query=%s)", location, meal_type, query)
    twiggy_results = search_twiggy(
        query=query, location=location, meal_type=meal_type,
        max_price=max_price, is_veg=is_veg, limit=20,
    )

    all_items = tomato_results + twiggy_results
    return {
        "search_results": all_items,
        "current_step": "food_searched",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. Ranker
# ═══════════════════════════════════════════════════════════════════════════

def _calculate_composite_score(
    items: list[dict[str, Any]],
    w_price: float = 0.40,
    w_rating: float = 0.30,
    w_delivery: float = 0.30,
) -> list[dict[str, Any]]:
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
        norm_inv_price = (max_p - item["price"]) / p_range
        norm_rating = (item["rating"] - min_r) / r_range
        norm_inv_delivery = (max_d - item["delivery_time_mins"]) / d_range

        score = (w_price * norm_inv_price) + (w_rating * norm_rating) + (w_delivery * norm_inv_delivery)

        item_copy = dict(item)
        item_copy["composite_score"] = round(score, 3)

        badges: list[str] = []
        if item["price"] == min_p:
            badges.append("Cheapest Pick")
        if item["rating"] >= 4.7:
            badges.append("Top Rated")
        if item["delivery_time_mins"] <= 20:
            badges.append("Superfast Delivery")
        item_copy["badges"] = badges

        ranked.append(item_copy)

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked


def _ranker_summary(result: dict) -> dict[str, Any]:
    ranked = result.get("ranked_results") or []
    if ranked:
        top = ranked[0]
        return {
            "top_pick": f"{top['name']} ₹{top['price']} ⭐{top['rating']}",
            "ranked": len(ranked),
        }
    return {"ranked": 0}


@traced_node("ranker", summary_fn=_ranker_summary)
async def ranker_node(state: dict) -> dict:
    search_results = state.get("search_results") or []
    ranked_items = _calculate_composite_score(search_results)
    top_picks = ranked_items[:6]
    return {
        "ranked_results": top_picks,
        "current_step": "food_ranked",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. Response Formatter
# ═══════════════════════════════════════════════════════════════════════════

def _formatter_summary(result: dict) -> dict[str, Any]:
    reply = result.get("final_reply") or ""
    return {"reply_len": len(reply), "has_reply": bool(reply)}


@traced_node("response_formatter", summary_fn=_formatter_summary)
async def response_formatter_node(state: dict) -> dict:
    intent = state.get("intent", "food_query")
    user_query = state.get("user_query", "")

    if intent == "general_chat":
        reply = (
            "Hey there! 👋 I'm **khaoAI**, your smart food concierge. Tell me what you're craving or just ask "
            "'*What should I eat now?*' and I'll find you the cheapest, highest-rated, and fastest delivery options "
            "across **Tomato 🍅** and **Twiggy 🌿**!"
        )
        return {"final_reply": reply, "current_step": "completed"}

    ranked = state.get("ranked_results") or []
    location = state.get("user_location", "your area")
    meal_type = (state.get("meal_type") or "meal").capitalize()

    if not ranked:
        reply = (
            f"I searched across Tomato 🍅 and Twiggy 🌿 around {location} for {meal_type}, "
            "but couldn't find exact matches right now. Try searching for a cuisine or adjusting filters!"
        )
        return {"final_reply": reply, "current_step": "completed"}

    top_item = ranked[0]
    items_summary = "\n".join([
        f"- {item['name']} from {item['restaurant_name']} on {item['platform']} "
        f"(₹{item['price']}, ⭐{item['rating']}, {item['delivery_time_mins']} mins)"
        for item in ranked[:4]
    ])

    try:
        from wrapper.llm import get_llm
        llm = get_llm(temperature=0.5)
        prompt_text = (
            f"User asked: '{user_query}'\n"
            f"Current meal time: {meal_type}\n"
            f"Location: {location}\n"
            f"Top ranked items found across Tomato & Twiggy:\n{items_summary}\n\n"
            f"Top choice is: {top_item['name']} from {top_item['restaurant_name']} "
            f"on {top_item['platform']} at ₹{top_item['price']}.\n"
            f"Write a friendly 2-3 sentence personalized recommendation to the user."
        )
        messages = [
            SystemMessage(content=FORMAT_RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=prompt_text),
        ]
        resp = await llm.ainvoke(messages)
        final_reply = resp.content.strip()
        _log.info("│  └─ LLM response generated (%d chars)", len(final_reply))
    except Exception as e:
        _log.warning("│  └─ LLM formatting fallback: %s", e)
        final_reply = (
            f"Looking for {meal_type.lower()} around **{location}**? "
            f"I compared options across **Tomato 🍅** and **Twiggy 🌿**! "
            f"Our top pick is the **{top_item['name']}** from **{top_item['restaurant_name']}** "
            f"on {top_item['platform']} for just **₹{top_item['price']}** "
            f"(⭐{top_item['rating']}, {top_item['delivery_time_mins']} mins delivery). "
            f"Check out the top ranked recommendations below!"
        )

    return {"final_reply": final_reply, "current_step": "completed"}
