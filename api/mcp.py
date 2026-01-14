"""
Thin wrapper to expose the FastAPI app defined in api/index.py
so that Vercel /api/mcp uses the same 15-tool implementation.
"""

from api.index import app

__all__ = ["app"]
