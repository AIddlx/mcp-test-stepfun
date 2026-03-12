#!/usr/bin/env python3
"""
MCP UVX 服务器启动脚本 - 阶跃客户端专用
"""

import sys
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')

# 添加源代码路径到 sys.path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入并运行服务器
from mcp_uvx_test import main

if __name__ == "__main__":
    main()
