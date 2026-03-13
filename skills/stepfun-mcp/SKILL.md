---
name: stepfun-mcp
description: 帮助编写阶跃 AI 桌面助手兼容的 MCP 服务器。适用于 (1) 创建新的 MCP 服务器 (2) 调试 Connection closed 错误 (3) 配置 NPX/UVX/HTTP 传输模式 (4) 理解阶跃客户端限制 (5) 选择 FastMCP 或 Low-Level API。基于 Windows 11 + 阶跃 v0.2.13 实测。
license: MIT
---

# 阶跃 MCP 服务器开发

> 基于 **Windows 11 + 阶跃桌面助手 v0.2.13** 实测。其他平台未测试。
>
> **完整项目资源**: https://github.com/AIddlx/mcp-test-stepfun
> - 35 个测试工具、3 种传输模式、完整代码
> - 踩坑记录（UVX 缓存、Defender 锁文件、SDK Bug）
> - 如有疑难问题需要积极查询该仓库

---

## 致命规则（违反必崩）

| ID | 规则 | 后果 |
|----|------|------|
| R001 | 不要声明 `outputSchema` | -32600 错误 |
| R002 | UVX 入口点 `main()` 必须同步 | Connection closed |
| R003 | 命令只支持裸命令名 `npx`/`uvx` | unknown command |
| R004 | 不要依赖进度通知（客户端不发送 progressToken） | 功能失效 |
| R005 | 工具执行 < 55 秒 | 超时 |
| R006 | Windows 路径用正斜杠 | 配置错误 |

详细说明见 [references/constraints.md](./references/constraints.md)。

---

## Connection closed 决策树

```
MCP error -32000: Connection closed
│
├── 日志中有 "coroutine ... was never awaited"
│   └── R002: async def main() → 改为同步函数
│
├── 日志中有 "Failed to install: xxx.whl" + "os error -2147024786"
│   └── P005: Defender 锁文件 → 加排除列表或重试
│
├── 日志中有 "ModuleNotFoundError"
│   └── K003: import 路径错误 → from mcp.server import FastMCP
│
├── 日志显示 "Installed N packages" 但行为是旧代码
│   └── P004: UVX 缓存 → 清 5 个缓存 + 更新版本号
│
├── 日志中有 "unknown command: xxx"
│   └── P001: 命令格式错误 → 只用裸命令名 npx/uvx
│
└── 日志无明确错误
    └── 检查进程存活 + 超时 (R005)
```

日志位置：`%APPDATA%/stepfun-desktop/logs/`

---

## 传输模式选择

| 场景 | 选择 | 原因 |
|------|------|------|
| **本地编写调试** | HTTP | 修改即生效，无需构建 |
| **阶跃 stdio 测试** | NPX | `npx -y C:/path`，修改即生效 |
| **阶跃生产部署** | NPX 或 UVX | UVX 可用但**不推荐开发时用** |

### UVX 为什么不推荐开发

五层独立缓存 + 版本号绑定，每次改代码需：删配置 → 清 5 个缓存 → 更版本号 → 重新添加。详见 [references/constraints.md](./references/constraints.md#p004)。

---

## API 选择

| 场景 | 选择 | 原因 |
|------|------|------|
| 入门 / 简单工具 | **FastMCP** | 装饰器自动注册，代码最少 |
| 精细控制（进度、资源、提示） | **Low-Level Server** | 手动定义 schema，更接近协议 |
| HTTP 传输 | Low-Level + StreamableHTTPSessionManager | 更灵活 |

两个 API 都在 `mcp[cli]>=1.0.0` 包内。

### FastMCP（入门推荐）

```python
from mcp.server import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def hello(name: str) -> str:
    return json.dumps({"message": f"你好, {name}!"})

if __name__ == "__main__":
    mcp.run()
```

### Low-Level Server（精细控制）

```python
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

server = Server("my-server", version="1.0.0")

@server.list_tools()
async def list_tools():
    return [types.Tool(name="hello", description="...", inputSchema={...})]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "hello":
        return [types.TextContent(type="text", text=json.dumps({...}))]

# R002: main() 必须是同步函数
def main():
    import asyncio
    async def _run():
        async with stdio_server() as (read, write):
            await server.run(read, write,
                server.create_initialization_options(NotificationOptions(tools_changed=True)))
    asyncio.run(_run())
```

---

## 阶跃客户端配置

### NPX

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "C:/path/to/project"]
    }
  }
}
```

### UVX

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["--from", "C:/path/to/project", "my-server"]
    }
  }
}
```

### HTTP

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

---

## 项目模板 (assets/)

模板文件用于复制到用户项目，包含三种传输模式的完整代码。

| 模式 | 目录 | API |
|------|------|-----|
| NPX | [assets/npx/](./assets/npx/) | 手写 JSON-RPC / Low-Level SDK |
| UVX | [assets/uvx/](./assets/uvx/) | FastMCP |
| HTTP | [assets/http/](./assets/http/) | 手写 Starlette |

---

## 参考

- MCP 规范: https://modelcontextprotocol.io/
- 协议版本: 2025-11-25
- [UVX 问题汇总](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/stdio/uvx/ISSUES.md)
- [SDK 路由 Bug](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/SSE_PROGRESS_DESIGN_NOTES.md)
- [FastMCP "流式"原理](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/FASTMCP_STREAMING_ANALYSIS.md)
