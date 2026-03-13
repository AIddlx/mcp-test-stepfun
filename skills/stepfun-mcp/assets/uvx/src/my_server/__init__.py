"""
My MCP Server for StepFun

Python MCP 服务器，兼容阶跃桌面助手 v0.2.13。
使用 Python FastMCP 框架。

测试: uvx --from ./path/to/project my-mcp-server
"""

from .server import mcp

__all__ = ["mcp"]
__version__ = "1.0.0"


def main():
    """入口点"""
    mcp.run()
