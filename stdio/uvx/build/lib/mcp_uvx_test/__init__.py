"""
MCP UVX 测试服务器

用于阶跃客户端 stdio 模式测试的 Python 版本 MCP 服务器
包含 35 个测试工具，与 NPX 模式功能一致
"""

from .server import mcp

__all__ = ["mcp"]
__version__ = "1.0.0"


def main():
    """入口点"""
    mcp.run()
