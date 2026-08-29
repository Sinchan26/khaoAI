import azure.functions as func
import logging
from blueprints.orchestrator import bp as orchestrator_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register Blueprints
app.register_functions(orchestrator_bp)

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Agent Function App health check.")
    return func.HttpResponse(
        body='{"status":"healthy","service":"khaoAI Agent Function App (LangGraph)"}',
        status_code=200,
        mimetype="application/json"
    )
