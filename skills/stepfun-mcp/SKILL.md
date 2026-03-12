---
name: stepfun-mcp
description: 帮助编写阶跃 AI 桌面助手兼容的 MCP 服务器
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# 阶跃 MCP 服务器开发 Skill

> 基于 **Windows 11 + 阶跃桌面助手 v0.2.13** 实测。其他平台未测试。

<p align="center">
  <a href="https://github.com/AIddlx/mcp-test-stepfun">
    <img src="https://img.shields.io/github/stars/AIddlx/mcp-test-stepfun?style=social" alt="GitHub stars">
  </a>
  <a href="https://github.com/AIddlx/mcp-test-stepfun">
    <img src="https://img.shields.io/github/forks/AIddlx/mcp-test-stepfun?style=social" alt="GitHub forks">
  </a>
</p>

---

## 🔗 完整项目资源

> **Skill 只包含精华摘要。完整代码、详细文档、实测案例都在 GitHub 仓库中。**

**GitHub**: https://github.com/AIddlx/mcp-test-stepfun

| 资源 | 位置 | 说明 |
|------|------|------|
| **35 个测试工具** | `stdio/npx/`, `stdio/uvx/`, `http/` | 完整可运行的服务器实现 |
| **SDK 实战案例** | `sdk/npx/`, `sdk/uvx/` | Node.js SDK + Python SDK (Low-Level API) |
| **FastMCP 案例** | `stdio/uvx/` | 完整的 FastMCP 服务器 |
| **HTTP 服务器** | `http/full_test_server.py` | 手写 Streamable HTTP，含完整协议处理 |
| **问题汇总** | `docs/stdio/uvx/ISSUES.md` | UVX 五层缓存、Defender 锁文件、版本号绑定 |
| **SDK Bug 分析** | `docs/SSE_PROGRESS_DESIGN_NOTES.md` | HTTP stateless 下 progress 丢失根因 |
| **FastMCP 原理** | `docs/FASTMCP_STREAMING_ANALYSIS.md` | report_progress 机制详解 |
| **测试报告** | `docs/stdio/*/TEST_REPORT.md` | NPX/UVX 35工具全部通过 |
| **约束详细说明** | `constraints/01~04-*.md` | 17条约束的完整版 |

---

## 致命规则（违反必崩）

> **必须先读这些。** 违反任何一条会导致 Connection closed、报错、或功能失效。

### R001: 不要声明 outputSchema

阶跃不消费 `outputSchema` 和 `structuredContent`。声明了会报 `-32600` 错误。详见 [D002](./constraints/01-design.md#d002-不要声明-outputschema)。

```json
// ❌ 错误
{ "name": "tool", "inputSchema": {...}, "outputSchema": {...} }

// ✅ 正确
{ "name": "tool", "inputSchema": {...} }
```

### R002: UVX 入口点 main() 必须是同步函数

hatch 入口点同步调用 `main()`。`async def main()` 会导致 `coroutine 'main' was never awaited` → Connection closed。详见 [K001](./constraints/02-coding.md#k001-uvx-入口点-main-必须同步)。

```python
# ❌ 崩溃
async def main():
    async with stdio_server() as (read, write):
        await server.run(...)

# ✅ 正确
def main():
    import asyncio
    async def _run():
        async with stdio_server() as (read, write):
            await server.run(...)
    asyncio.run(_run())
```

### R003: 命令只支持裸命令名

阶跃只识别 `npx` 和 `uvx`，不识别 `node`、`python` 或任何路径。详见 [P001](./constraints/03-deployment.md#p001-命令格式限制)。

```
✅ "command": "npx"      ❌ "command": "node"
✅ "command": "uvx"      ❌ "command": "C:\\...\\uvx.exe"
```

### R004: 不要依赖进度通知

阶跃 v0.2.13 **不发送 `progressToken`**。无论服务端实现如何，进度通知都不会被触发。详见 [D003](./constraints/01-design.md#d003-进度通知不可靠)。

替代方案：异步轮询 `start_task → get_task_status → get_result`。

### R005: 工具执行 < 55 秒

55 秒通过，60 秒超时。长任务拆分为多步调用。详见 [P002](./constraints/03-deployment.md#p002-工具执行超时)。

### R006: Windows 路径用正斜杠

详见 [K002](./constraints/02-coding.md#k002-windows-路径统一正斜杠)。

```
✅ "C:/Project/my-server"     ❌ "C:\Project\my-server"
```

---

## 传输模式决策

| 场景 | 选择 | 原因 |
|------|------|------|
| **本地编写调试** | HTTP | 修改即生效，无需构建 |
| **阶跃 stdio 测试** | NPX | `npx -y C:/path`，修改即生效 |
| **阶跃生产部署** | NPX 或 UVX | UVX 可用但**不推荐开发时用** |

### UVX 为什么不推荐开发

五层独立缓存 + 版本号绑定，每次改代码需：删配置 → 清 5 个缓存 → 更版本号 → 重新添加。详见 [P004](./constraints/03-deployment.md#p004-uvx-缓存问题不推荐开发时用)。

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

完整排查指南：[04-debugging.md](./constraints/04-debugging.md)。

---

## 约束清单

| 阶段 | 文件 | 约束范围 |
|------|------|---------|
| 设计 | [01-design.md](./constraints/01-design.md) | D001-D005 协议限制 + API 设计 |
| 编码 | [02-coding.md](./constraints/02-coding.md) | K001-K007 代码写法 + SDK 使用 |
| 部署 | [03-deployment.md](./constraints/03-deployment.md) | P001-P005 配置 + 缓存 + 超时 |
| 排查 | [04-debugging.md](./constraints/04-debugging.md) | 错误决策树 + 排查工具 |

---

## API 选择

### 怎么选

| 场景 | 选择 | 原因 |
|------|------|------|
| 入门 / 简单工具 | **FastMCP** | 装饰器自动注册，代码最少 |
| 需要精细控制（进度通知、资源、提示） | **Low-Level Server** | 手动定义 schema 和路由，更接近协议 |
| HTTP 传输 | **Low-Level Server + StreamableHTTPSessionManager** | FastMCP 的 `run(transport="streamable-http")` 也可用，但 Low-Level 更灵活 |

**两个 API 都在同一个 `mcp` 包内**，安装 `mcp[cli]>=1.0.0` 即可，不需要额外依赖。

**FastMCP 的局限**：
- `ctx.report_progress()` 在阶跃中无效（D003：客户端不发送 progressToken）
- HTTP `stateless=True` 下有路由 Bug（K004：缺少 `related_request_id`）
- 但对简单工具来说这些都不影响

**Low-Level Server 的注意点**：
- 手动定义 `inputSchema`（JSON Schema），代码量更多
- UVX 模式下 `main()` 必须是同步函数（R002）
- 可以绕过 SDK Bug 手动发送 progress 通知（K004）

### FastMCP（入门推荐）

```python
from mcp.server import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def hello(name: str) -> str:
    return json.dumps({"message": f"你好, {name}!"})  # D002: 返回 JSON 字符串

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

### HTTP 传输（Streamable HTTP）

```python
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Route

server = Server("my-server")
session_manager = StreamableHTTPSessionManager(
    app=server, stateless=True, json_response=True)

app = Starlette(
    lifespan=session_manager.run,
    routes=[Route("/mcp", session_manager.handle_request,
                 methods=["GET", "POST", "DELETE"])])

import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
```

### 进度通知的 SDK Bug

FastMCP 的 `ctx.report_progress()` 和 Low-Level API 的 `progress()` 上下文管理器，在 HTTP `stateless=True` 模式下**都不工作**（缺少 `related_request_id`，通知被路由丢弃）。详见 [K004](./constraints/02-coding.md#k004-http-statelesstrue-下绕过-sdk-progress)。

---

## 返回值格式

```json
{
  "content": [{"type": "text", "text": "结果文本或 JSON 字符串"}],
  "isError": false
}
```

- 协议错误：JSON-RPC error（`-32602 Invalid params`）
- 业务错误：`isError: true` + content 描述错误
- 数据类型：string/integer/float/boolean/null/array/object 全部正常

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

## 项目模板

| 模式 | 目录 | API | 实测 |
|------|------|-----|------|
| NPX | [templates/npx/](./templates/npx/) | 手写 JSON-RPC / Low-Level SDK | 35 工具通过 |
| UVX | [templates/uvx/](./templates/uvx/) | FastMCP | 35 工具通过 |
| HTTP | [templates/http/](./templates/http/) | 手写 Starlette | 35 工具通过 |

---

## 参考

- MCP 规范: https://modelcontextprotocol.io/
- 协议版本: 2025-11-25
- [docs/stdio/uvx/ISSUES.md](../../docs/stdio/uvx/ISSUES.md) — UVX 问题汇总
- [docs/SSE_PROGRESS_DESIGN_NOTES.md](../../docs/SSE_PROGRESS_DESIGN_NOTES.md) — SDK 路由 Bug
- [docs/FASTMCP_STREAMING_ANALYSIS.md](../../docs/FASTMCP_STREAMING_ANALYSIS.md) — FastMCP "流式"原理
- [docs/STEPFUN_STREAMING_LIMITATION.md](../../docs/STEPFUN_STREAMING_LIMITATION.md) — 流式限制分析
- [docs/stdio/uvx/TEST_REPORT.md](../../docs/stdio/uvx/TEST_REPORT.md) — UVX 测试报告
- [docs/stdio/npx/TEST_REPORT.md](../../docs/stdio/npx/TEST_REPORT.md) — NPX 测试报告
