import azure.functions as func
import logging
from blueprints.tomato_tools import bp as tomato_bp
from blueprints.twiggy_tools import bp as twiggy_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register Blueprints
app.register_functions(tomato_bp)
app.register_functions(twiggy_bp)

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("MCP Function App health check.")
    return func.HttpResponse(
        body='{"status":"healthy","service":"khaoAI MCP Function App"}',
        status_code=200,
        mimetype="application/json"
    )
