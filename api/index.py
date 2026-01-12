"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from mangum import Mangum

from src.server import app

# Allow FastAPI lifespan so StreamableHTTPSessionManager can start.
handler = Mangum(app, lifespan="auto")
