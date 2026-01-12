from fastapi import FastAPI

from src.server import MCP_SPEC_VERSION, health, mcp_asgi

app = FastAPI()


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

# Mount ASGI transport directly to avoid FastAPI param parsing
app.mount("/mcp", mcp_asgi)
app.mount("/mcp/", mcp_asgi)
app.mount("/api/mcp", mcp_asgi)
app.mount("/api/mcp/", mcp_asgi)


__all__ = ["app"]
