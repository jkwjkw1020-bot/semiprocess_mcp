from src.server import mcp_asgi

# Expose raw ASGI app
app = mcp_asgi

__all__ = ["app"]
