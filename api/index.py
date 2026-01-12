"""
Vercel serverless entrypoint.

Uses Mangum to adapt the FastAPI ASGI app to Vercel's Lambda-style runtime.
"""

from mangum import Mangum

# Import the FastAPI app
from src.server import app

# Disable lifespan to avoid double startup in Lambda-style environments
handler = Mangum(app, lifespan="off")
