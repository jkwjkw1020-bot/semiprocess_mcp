"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from src.server import app

# Export FastAPI ASGI app directly for Vercel's Python runtime autodetection.
# (Mangum wrapper removed to avoid BaseHTTPRequestHandler subclass checks.)
