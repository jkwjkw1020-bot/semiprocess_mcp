import contextlib
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
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
    stateless=False,
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
# Keep default trailing-slash redirects enabled to ensure /mcp is matched.
app.router.redirect_slashes = True


@app.middleware("http")
async def restore_original_path(request, call_next):
    """
    Vercel rewrite 시 원본 경로를 복원한다. /api/index.py 접두어 제거 + 헤더 기반 복원.
    """
    path = request.scope.get("path", "")
    original_path = path

    # 1) vercel python runtime가 /api/index.py 접두어를 붙인 경우 제거
    prefix = "/api/index.py"
    if path.startswith(prefix):
        path = path[len(prefix) :] or "/"

    # 2) 헤더에 실린 원본 경로가 있으면 사용
    headers = request.headers
    original = headers.get("x-original-pathname") or headers.get("x-vercel-original-pathname") or headers.get("x-matched-path")
    if original:
        path = original

    # FastAPI 내부가 path 기반으로 라우팅하므로 scope의 path만 수정
    request.scope["path"] = path
    logger.info("path_restore original=%s restored=%s host=%s", original_path, path, headers.get("host"))
    return await call_next(request)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon_ico():
    # Return empty response to avoid 404 on favicon requests
    return Response(status_code=204)


@app.get("/favicon.png")
async def favicon_png():
    return Response(status_code=204)


async def mcp_asgi(scope, receive, send):
    """ASGI entrypoint for Streamable HTTP/SSE transport."""
    logger.info("mcp_asgi scope path=%s method=%s headers=%s", scope.get("path"), scope.get("method"), scope.get("headers"))
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
