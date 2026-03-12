#!/usr/bin/env python3
"""
MCP HTTP 服务器（Streamable HTTP 模式）

使用 Starlette + uvicorn，兼容阶跃桌面助手 v0.2.13。

约束检查:
- R001/D002: 不声明 outputSchema
- R004/D003: 不依赖进度通知（阶跃不发送 progressToken）
- R005: 工具执行 < 55 秒
- K005: 返回值只用 content + isError

启动: python server.py
依赖: pip install starlette uvicorn
"""

import json
from datetime import datetime
from typing import Any

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import uvicorn


# ==================== 工具定义 ====================

def get_tools():
    return [
        {
            "name": "hello",
            "description": "打招呼工具。输入名字，返回问候语。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "名字"}
                },
                "required": ["name"]
            }
        }
    ]


# ==================== 工具实现 ====================

def call_tool(name: str, args: dict) -> dict:
    if name == "hello":
        return {
            "success": True,
            "message": f"你好, {args.get('name', '')}!"
        }

    return {"success": False, "error": f"Unknown tool: {name}"}


# ==================== 请求处理 ====================

def handle_request(req: dict) -> dict:
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "serverInfo": {
                    "name": "my-mcp-server",
                    "version": "1.0.0"
                },
                "instructions": "MCP HTTP 服务器"
            }
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": get_tools()}
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = call_tool(tool_name, tool_args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "isError": result.get("success") is False
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }


# ==================== CORS ====================

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


async def handle_options(request: Request) -> Response:
    """CORS 预检请求"""
    return Response(status_code=204, headers=CORS_HEADERS)


# ==================== MCP 端点 ====================

async def handle_mcp(request: Request) -> Response:
    body = await request.json()
    result = handle_request(body)
    headers = {**CORS_HEADERS, "Content-Type": "application/json"}
    return Response(
        json.dumps(result),
        status_code=200,
        headers=headers
    )


# ==================== 应用 ====================

app = Starlette(routes=[
    Route("/mcp", handle_mcp, methods=["POST"]),
    Route("/mcp", handle_options, methods=["OPTIONS"]),
])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3372)
