import contextlib
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import mcp.types as types
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.shared.exceptions import McpError

from src.tools import (
    register_defect_tools,
    register_monitoring_tools,
    register_recipe_tools,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("semiprocess")

MCP_SPEC_VERSION = "2025-03-26"

server = Server("SemiProcess", version=MCP_SPEC_VERSION)
TOOLS: Dict[str, Dict[str, Any]] = {}
register_defect_tools(TOOLS)
register_recipe_tools(TOOLS)
register_monitoring_tools(TOOLS)


@server.list_tools()
async def list_tools(request: types.ListToolsRequest) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name=name,
                description=tool["description"],
                input_schema=tool["schema"],
            )
            for name, tool in TOOLS.items()
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any] | None) -> list[types.Content]:
    tool = TOOLS.get(name)
    if not tool:
        raise McpError(f"Unknown tool '{name}'")
    handler = tool["handler"]
    args = arguments or {}
    try:
        result = await handler(**args)
    except TypeError as exc:
        raise McpError(f"Invalid arguments for tool '{name}': {exc}") from exc
    return [result]

session_manager = StreamableHTTPSessionManager(
    server,
    json_response=True,  # prefer JSON responses for serverless compatibility
    stateless=True,
)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with session_manager.run():
        yield


app = FastAPI(
    title="SemiProcess MCP Server",
    version=MCP_SPEC_VERSION,
    description="MCP server for semiconductor process management",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


async def mcp_asgi(scope, receive, send):
    """ASGI entrypoint for Streamable HTTP/SSE transport."""
    if scope.get("type") != "http":
        return await JSONResponse({"detail": "Unsupported scope"}, status_code=400)(scope, receive, send)
    await session_manager.handle_request(scope, receive, send)


app.mount("/mcp", mcp_asgi)


@app.get("/")
async def root():
    return {
        "service": "SemiProcess MCP",
        "spec": MCP_SPEC_VERSION,
        "health": "/health",
        "mcp": "/mcp",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    import uvicorn

    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=False)
