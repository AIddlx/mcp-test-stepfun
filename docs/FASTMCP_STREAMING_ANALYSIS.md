# FastMCP "流式"响应分析

> 日期: 2026-03-12 | SDK 版本: mcp 1.26.0 | 平台: Windows 11

---

## 结论

**FastMCP 没有 `stream=True` 参数。** MCP 协议层面 `tools/call` 返回单个 `CallToolResult`，不支持逐步返回内容。

控制台测试中看到的"流式"效果，实际上是 `ctx.report_progress()` 发送的 `notifications/progress` 作为中间 SSE 事件逐行到达。

---

## 一、MCP 协议限制

### 1.1 `tools/call` 是原子的

MCP 规范（2025-11-25）定义 `CallToolResult` 返回单个 `content` 数组：

```json
{
  "content": [{"type": "text", "text": "完整结果"}],
  "isError": false
}
```

没有"部分结果"、"流式内容"的定义。详见 [STEPFUN_STREAMING_LIMITATION.md](./STEPFUN_STREAMING_LIMITATION.md)。

### 1.2 唯一的中间反馈机制

`notifications/progress` 是协议中唯一的服务器→客户端中间通知：

```
请求 ──→ notification(progress 1/5) ──→ notification(progress 2/5) ──→ ... ──→ 最终响应
```

但这是**元数据**（进度计数 + 消息），不是工具内容。

---

## 二、FastMCP 的"流式"实现

### 2.1 `ctx.report_progress()`

FastMCP 提供 `Context.report_progress()` 方法：

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("my-server")

@mcp.tool
async def long_task(ctx: Context) -> str:
    for i in range(5):
        await ctx.report_progress(progress=i+1, total=5, message=f"步骤 {i+1}/5")
    return "完成"
```

### 2.2 底层实现（SDK 1.26.0 源码）

```python
# mcp/server/fastmcp/context.py
async def report_progress(self, progress, total=None, message=None):
    progress_token = (
        self.request_context.meta.progressToken
        if self.request_context.meta else None
    )
    if progress_token is None:
        return  # 客户端未提供 progressToken → 静默跳过
    await self.request_context.session.send_progress_notification(
        progress_token=progress_token,
        progress=progress,
        total=total,
        message=message,
        # ← 缺少 related_request_id 参数！
    )
```

**两个问题**：

1. **客户端必须发送 `progressToken`** — 阶跃客户端不发送，所以 `report_progress()` 直接 return
2. **缺少 `related_request_id`** — 即使有 token，在 Streamable HTTP `stateless=True` 模式下通知会被路由丢弃

### 2.3 路由问题详解

Streamable HTTP 的消息路由逻辑（`mcp/server/streamable_http.py`）：

```
消息带有 id 字段（响应）         → 路由到对应 POST 流
消息带有 related_request_id（通知）→ 路由到对应 POST 流
两者都没有                       → 路由到 GET_STREAM_KEY（stateless=True 时不存在）
```

FastMCP 的 `report_progress()` 不传 `related_request_id`，通知被路由到不存在的 GET 流 → **静默丢弃**。

### 2.4 各模式对比

| 模式 | progress 可见性 | 原因 |
|------|----------------|------|
| stdio | ✅ 可见（协议层） | 消息直接通过 stdout，无路由 |
| HTTP `stateless=False` + GET SSE | ✅ 可见 | 无 `related_request_id` 的通知路由到 GET 流 |
| HTTP `stateless=True` | ❌ 丢弃 | 无 GET 流，缺少 `related_request_id` 导致路由失败 |

---

## 三、控制台测试为何能看到"流式"

使用 `curl -N` 测试 HTTP 服务器时：

```bash
curl -N -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"long_task","arguments":{},"_meta":{"progressToken":"token-1"}}}'
```

输出（实时逐行到达）：
```
event: message
data: {"method":"notifications/progress","params":{"progress":1,"total":5,"message":"步骤 1/5"}}

event: message
data: {"method":"notifications/progress","params":{"progress":2,"total":5,"message":"步骤 2/5"}}

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"完成"}]}}
```

视觉效果像"流式"，实际是多个独立的 SSE 事件。最终只有 `result` 中的内容被提交给 LLM。

---

## 四、绕过 SDK Bug 的正确写法

如需在 HTTP `stateless=True` 模式下发送进度通知，必须绕过 FastMCP 的 `report_progress()`，使用 Low-Level API：

```python
from mcp.server.lowlevel import Server

server = Server("my-server")

@server.call_tool()
async def call_tool(name, arguments):
    ctx = server.request_context
    request_id = str(ctx.request_id) if ctx.request_id else None

    if ctx.meta and ctx.meta.progressToken and request_id:
        await ctx.session.send_progress_notification(
            progress_token=ctx.meta.progressToken,
            progress=1,
            total=5,
            message="步骤 1/5",
            related_request_id=request_id,  # ← 关键！
        )
    return [types.TextContent(type="text", text="完成")]
```

详见 [SSE_PROGRESS_DESIGN_NOTES.md](./SSE_PROGRESS_DESIGN_NOTES.md)。

---

## 五、对开发的实际影响

| 场景 | 建议 |
|------|------|
| 需要逐步返回内容给用户 | **不可能**。MCP 协议不支持。使用异步轮询（start_task → get_status） |
| 需要告知用户进度 | `ctx.report_progress()` 在 stdio/`stateless=False` HTTP 模式可用 |
| 阶跃客户端 | 不支持进度通知（不发送 progressToken）。无论用什么 API 都不行 |
| HTTP `stateless=True` 开发 | 必须用 Low-Level API + 手动传 `related_request_id` |

---

*记录时间: 2026-03-12*
