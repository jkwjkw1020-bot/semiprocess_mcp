from src.server import mcp_asgi

# Expose ASGI app directly (no extra routing/redirects)
app = mcp_asgi

__all__ = ["app"]
