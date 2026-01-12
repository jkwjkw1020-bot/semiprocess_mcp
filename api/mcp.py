from src.server import mcp_asgi

# Expose ASGI callable directly
app = mcp_asgi

__all__ = ["app"]
