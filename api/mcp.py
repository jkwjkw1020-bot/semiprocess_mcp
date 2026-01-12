from fastapi import FastAPI

from src.server import mcp_asgi, health

app = FastAPI()
app.add_api_route("/mcp", mcp_asgi, methods=["GET", "POST"])
app.add_api_route("/mcp/", mcp_asgi, methods=["GET", "POST"])
app.add_api_route("/health", health, methods=["GET"])

__all__ = ["app"]
