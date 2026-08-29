import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from ...core.llm import get_llm
from ...prompts.intent import INTENT_SYSTEM_PROMPT
from ..state import FoodAgentState

async def classify_intent_node(state: FoodAgentState) -> dict:
    logging.info("Node: Intent Classifier")
    user_query = state.get("user_query", "")

    # Fast deterministic check for common greetings
    q_lower = user_query.lower().strip()
    if q_lower in ["hi", "hello", "hey", "hola", "help", "who are you"]:
        return {
            "intent": "general_chat",
            "extracted_entities": {},
            "current_step": "intent_classified"
        }

    try:
        llm = get_llm(temperature=0.1)
        messages = [
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=f"User Message: {user_query}")
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
            "current_step": "intent_classified"
        }
    except Exception as e:
        logging.warning(f"Intent classification fallback triggered: {e}")
        # Default to food_query so user gets recommendations
        return {
            "intent": "food_query",
            "extracted_entities": {},
            "current_step": "intent_classified"
        }
