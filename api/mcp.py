from fastapi import FastAPI
import logging

from src.server import MCP_SPEC_VERSION, health, mcp_asgi

app = FastAPI()
app.router.redirect_slashes = False
logger = logging.getLogger("mcp_entry")


@app.get("/")
async def root():
    return {
        "service": "SemiProcess MCP",
        "spec": MCP_SPEC_VERSION,
        "health": "/health",
        "mcp": "/mcp",
    }


# Health endpoint (redundant with src.server but exposed here too)
app.add_api_route("/health", health, methods=["GET"])

# ASGI logging wrapper to inspect incoming requests (scope only)
async def logging_wrapper(scope, receive, send):
    logger.info(
        "mcp_request type=%s method=%s path=%s headers=%s",
        scope.get("type"),
        scope.get("method"),
        scope.get("path"),
        scope.get("headers"),
    )
    await mcp_asgi(scope, receive, send)


# Mount ASGI transport with logging wrapper
app.mount("/mcp", logging_wrapper)
app.mount("/mcp/", logging_wrapper)
app.mount("/api/mcp", logging_wrapper)
app.mount("/api/mcp/", logging_wrapper)


__all__ = ["app"]
