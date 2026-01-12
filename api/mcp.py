from src.server import app

# Expose the ASGI app directly for /api/mcp
__all__ = ["app"]
from src.server import mcp_asgi

# Expose ASGI app directly (no extra routing/redirects)
app = mcp_asgi

__all__ = ["app"]
