"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from src.server import app

# Expose only ASGI app (FastAPI) for Vercel autodetection.
__all__ = ["app"]
