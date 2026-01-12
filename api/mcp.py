from src.server import app

# Export only ASGI app for Vercel (@vercel/python expects 'app')
__all__ = ["app"]
