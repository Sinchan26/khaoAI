import json
import logging
import azure.functions as func
from ..models.schemas import FoodSearchRequest, FoodSearchResponse
from ..utils.http_client import TWIGGY_SERVICE_URL, fetch_from_simulator

bp = func.Blueprint()

@bp.route(route="twiggy/search", methods=["POST", "GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def twiggy_search(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Executing Twiggy search tool.")
    try:
        if req.method == "POST":
            req_body = req.get_json()
            search_params = FoodSearchRequest(**req_body).model_dump(exclude_none=True)
        else:
            search_params = {
                "query": req.params.get("query"),
                "location": req.params.get("location"),
                "meal_type": req.params.get("meal_type"),
                "max_price": int(req.params.get("max_price")) if req.params.get("max_price") else None,
                "is_veg": req.params.get("is_veg") == "true" if req.params.get("is_veg") else None,
                "limit": int(req.params.get("limit", 15))
            }

        data = await fetch_from_simulator(
            base_url=TWIGGY_SERVICE_URL,
            path="search",
            params=search_params
        )

        return func.HttpResponse(
            body=json.dumps(data),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in twiggy_search: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e), "platform": "Twiggy", "results": []}),
            status_code=500,
            mimetype="application/json"
        )

@bp.route(route="twiggy/restaurant/{restaurant_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def twiggy_restaurant(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Executing Twiggy restaurant detail tool.")
    try:
        rest_id = req.route_params.get("restaurant_id")
        meal_type = req.params.get("meal_type")
        is_veg = req.params.get("is_veg")

        data = await fetch_from_simulator(
            base_url=TWIGGY_SERVICE_URL,
            path=f"restaurants/{rest_id}/menu",
            params={"meal_type": meal_type, "is_veg": is_veg}
        )

        return func.HttpResponse(
            body=json.dumps(data),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in twiggy_restaurant: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
