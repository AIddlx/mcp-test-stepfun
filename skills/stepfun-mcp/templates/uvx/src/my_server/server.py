#!/usr/bin/env python3
"""
MCP stdio 服务器（UVX 模式）

使用 Python FastMCP 框架。
兼容阶跃桌面助手 v0.2.13。

约束检查:
- R001/D002: 不声明 outputSchema
- R002/K001: main() 必须同步（如通过 uvx 启动）
- K003: import from mcp.server（不是 mcp.server.mcpserver）
- K005: 返回值只用 content
"""

import json
from datetime import datetime

from mcp.server import FastMCP

# ==================== 服务器实例 ====================

mcp = FastMCP("my-mcp-server")


# ==================== 工具定义 ====================

@mcp.tool()
def hello(name: str) -> str:
    """打招呼工具。输入名字，返回问候语。"""
    result = {
        "success": True,
        "message": f"你好, {name}!"
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== 入口点 ====================

if __name__ == "__main__":
    mcp.run()
