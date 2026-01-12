"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from src.server import app

# Expose ASGI app (FastAPI) and handler alias for Vercel.
handler = app
__all__ = ["app", "handler"]
