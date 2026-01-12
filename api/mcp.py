from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.server import mcp_asgi, health, MCP_SPEC_VERSION

app = FastAPI()

# MCP entry (JSON-RPC) - supports both /mcp and /mcp/
app.add_api_route("/mcp", mcp_asgi, methods=["GET", "POST"])
app.add_api_route("/mcp/", mcp_asgi, methods=["GET", "POST"])

# Health and root for basic validation
app.add_api_route("/health", health, methods=["GET"])

@app.get("/")
async def root():
    return {
        "service": "SemiProcess MCP",
        "spec": MCP_SPEC_VERSION,
        "health": "/health",
        "mcp": "/mcp",
    }

__all__ = ["app"]
