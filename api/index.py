"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from src.server import app

# Export both app and handler for Vercel autodetection.
handler = app
