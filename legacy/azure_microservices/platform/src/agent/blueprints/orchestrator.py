import json
import logging
import azure.functions as func
from ..graph.builder import food_graph
from ..graph.state import FoodAgentState

bp = func.Blueprint()

@bp.route(route="orchestrate", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
async def orchestrate_chat(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Agent Function App: Processing orchestration request.")
    try:
        req_body = req.get_json()
        user_message = req_body.get("message", "").strip()
        user_location = req_body.get("location") or "Salt Lake, Sector V"
        food_preferences = req_body.get("preferences") or {}

        if not user_message:
            return func.HttpResponse(
                body=json.dumps({"error": "Message is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Initial state
        initial_state: FoodAgentState = {
            "messages": [],
            "user_query": user_message,
            "user_location": user_location,
            "meal_type": None,
            "detected_time": None,
            "intent": None,
            "extracted_entities": None,
            "food_preferences": food_preferences,
            "search_results": None,
            "ranked_results": None,
            "final_reply": None,
            "current_step": "init",
            "error": None
        }

        # Invoke LangGraph
        result = await food_graph.ainvoke(initial_state)

        response_payload = {
            "reply": result.get("final_reply") or "Here are recommendations based on your preferences.",
            "recommendations": result.get("ranked_results") or [],
            "meal_type": result.get("meal_type") or "meal",
            "location": result.get("user_location") or user_location,
            "intent": result.get("intent") or "food_query"
        }

        return func.HttpResponse(
            body=json.dumps(response_payload, ensure_ascii=False),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in agent orchestrate: {str(e)}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({
                "error": str(e),
                "reply": "Sorry, I ran into an issue finding recommendations right now. Please try again in a moment.",
                "recommendations": []
            }),
            status_code=500,
            mimetype="application/json"
        )
