import logging
from langchain_core.messages import SystemMessage, HumanMessage
from ...core.llm import get_llm
from ...prompts.response_format import FORMAT_RESPONSE_SYSTEM_PROMPT
from ..state import FoodAgentState

async def response_formatter_node(state: FoodAgentState) -> dict:
    logging.info("Node: Response Formatter")
    intent = state.get("intent", "food_query")
    user_query = state.get("user_query", "")

    if intent == "general_chat":
        reply = (
            "Hey there! 👋 I'm **khaoAI**, your smart food concierge. Tell me what you're craving or just ask "
            "'*What should I eat now?*' and I'll find you the cheapest, highest-rated, and fastest delivery options "
            "across **Tomato 🍅** and **Twiggy 🌿**!"
        )
        return {
            "final_reply": reply,
            "current_step": "completed"
        }

    ranked = state.get("ranked_results") or []
    location = state.get("user_location", "your area")
    meal_type = (state.get("meal_type") or "meal").capitalize()

    if not ranked:
        reply = f"I searched across Tomato 🍅 and Twiggy 🌿 around {location} for {meal_type}, but couldn't find exact matches right now. Try searching for a cuisine or adjusting filters!"
        return {
            "final_reply": reply,
            "current_step": "completed"
        }

    # Generate personalized response using LLM or structured template
    top_item = ranked[0]
    items_summary = "\n".join([
        f"- {item['name']} from {item['restaurant_name']} on {item['platform']} (₹{item['price']}, ⭐{item['rating']}, {item['delivery_time_mins']} mins)"
        for item in ranked[:4]
    ])

    try:
        llm = get_llm(temperature=0.5)
        prompt_text = (
            f"User asked: '{user_query}'\n"
            f"Current meal time: {meal_type}\n"
            f"Location: {location}\n"
            f"Top ranked items found across Tomato & Twiggy:\n{items_summary}\n\n"
            f"Top choice is: {top_item['name']} from {top_item['restaurant_name']} on {top_item['platform']} at ₹{top_item['price']}.\n"
            f"Write a friendly 2-3 sentence personalized recommendation to the user."
        )

        messages = [
            SystemMessage(content=FORMAT_RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=prompt_text)
        ]
        resp = await llm.ainvoke(messages)
        final_reply = resp.content.strip()
    except Exception as e:
        logging.warning(f"LLM formatting fallback: {e}")
        final_reply = (
            f"Looking for {meal_type.lower()} around **{location}**? I compared options across **Tomato 🍅** and **Twiggy 🌿**! "
            f"Our top pick is the **{top_item['name']}** from **{top_item['restaurant_name']}** on {top_item['platform']} for just **₹{top_item['price']}** "
            f"(⭐{top_item['rating']}, {top_item['delivery_time_mins']} mins delivery). Check out the top ranked recommendations below!"
        )

    return {
        "final_reply": final_reply,
        "current_step": "completed"
    }
