# SSE 模式 Progress Notification 设计经验

> 日期: 2026-03-12 | SDK 版本: mcp[cli]>=1.0.0 | 平台: Windows 11

---

## 一、背景

MCP Streamable HTTP 传输支持两种响应模式：

| 参数 | 模式 | Content-Type | 适用场景 |
|------|------|-------------|---------|
| `json_response=True` | JSON 模式 | `application/json` | 简单请求-响应，无中间通知 |
| `json_response=False` | SSE 模式 | `text/event-stream` | 需要中间 progress notification |

```python
session_manager = StreamableHTTPSessionManager(
    app=server,
    stateless=True,
    json_response=False,   # True=JSON / False=SSE
)
```

---

## 二、关键发现：SDK `progress()` 上下文管理器的路由 Bug

### 2.1 问题现象

使用 SDK 提供的 `progress()` 上下文管理器发送进度通知时，服务器日志显示 `progress_sent: true`，但客户端 SSE 流中**没有收到任何 `notifications/progress` 事件**（0 events）。

### 2.2 根因分析

**Bug 位置**: `mcp/shared/progress.py` 第 35-37 行

```python
# SDK 源码 (有问题的版本)
async def progress(self, amount: float, message: str | None = None) -> None:
    self.current += amount
    await self.session.send_progress_notification(
        self.progress_token, self.current, total=self.total, message=message
    )  # ← 缺少 related_request_id 参数!
```

**路由机制**: `mcp/server/streamable_http.py` 的 `message_router` 函数（约 991-1039 行）负责将服务器发出的消息路由到对应的 SSE 流。路由逻辑：

1. 消息带有 `id` 字段（响应）→ 匹配 request ID 对应的流
2. 消息带有 `related_request_id` 字段（通知）→ 匹配对应请求的流
3. **两者都没有 → 路由到 `GET_STREAM_KEY`（GET 请求的 SSE 流）**

在 `stateless=True` 模式下，没有持久的 GET SSE 流，`GET_STREAM_KEY` 对应的流不存在。因此 progress notification **被静默丢弃**。

### 2.3 调用链路图

```
progress() context manager
    └── progress(amount, message)
        └── session.send_progress_notification(token, current, total, message)
            │   # related_request_id 缺失!
            │
            └── StreamableHTTPServerTransport (内部)
                └── message_router(msg)
                    ├── msg.id?           → POST stream (匹配请求ID)
                    ├── msg.related_request_id? → POST stream (匹配关联请求ID)
                    └── 都没有 → GET_STREAM_KEY (不存在，丢弃!)
```

### 2.4 修复方案

绕过 SDK 的 `progress()` 上下文管理器，直接调用 `session.send_progress_notification()` 并手动传入 `related_request_id`：

```python
from mcp.server.lowlevel import Server

server = Server("mcp-http-sdk")

@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    ctx = server.request_context
    request_id = str(ctx.request_id) if ctx.request_id else None

    # 检查客户端是否提供了 progressToken
    if ctx.meta and ctx.meta.progressToken and request_id:
        for i in range(steps):
            await asyncio.sleep(delay_ms / 1000)
            # 直接调用，传入 related_request_id
            await ctx.session.send_progress_notification(
                progress_token=ctx.meta.progressToken,
                progress=float(i + 1),
                total=float(steps),
                message=f"步骤 {i + 1}/{steps} 完成",
                related_request_id=request_id,   # ← 关键!
            )
```

**核心要点**:
- `related_request_id` 必须设置为当前请求的 ID (`ctx.request_id`)
- 这样 `message_router` 才能将通知路由到正确的 POST SSE 流

---

## 三、SSE 模式客户端要求

### 3.1 Accept 头

SSE 模式要求客户端发送 `Accept: application/json, text/event-stream`。缺少此头会返回 HTTP 406：

```json
{"error": {"code": -32600, "message": "Not Acceptable: Client must accept both application/json and text/event-stream"}}
```

### 3.2 progressToken

客户端必须在请求的 `_meta` 字段中携带 `progressToken`，服务器才能发送 progress notification：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "test_progress_sse",
    "arguments": {"steps": 5, "delay_ms": 100},
    "_meta": {
      "progressToken": "client-token-123"
    }
  }
}
```

### 3.3 SSE 事件格式

响应流中的每个事件格式：

```
event: message
data: {"method":"notifications/progress","params":{"progressToken":"client-token-123","progress":1.0,"total":5.0,"message":"步骤 1/5 完成"}}

event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}]}}

```

- 中间的 `notifications/progress` 事件没有 `id` 字段，依赖 `related_request_id` 路由
- 最终的 `result` 事件带有 `id` 字段，通过 request ID 路由

---

## 四、客户端 SSE 解析注意事项

### 4.1 Python requests 库

`requests.post(..., stream=True).iter_lines()` 可以解析 SSE，但偶发丢失中间事件（TCP 层的行缓冲导致）。

```python
def parse_sse_response(response) -> dict:
    progress_events = []
    final_response = None
    current_data = ""

    for line in response.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line.startswith("data:"):
            current_data = line[5:].strip()
        elif line == "" and current_data:
            msg = json.loads(current_data)
            if msg.get("method") == "notifications/progress":
                progress_events.append(msg["params"])
            elif "result" in msg or "error" in msg:
                final_response = msg
            current_data = ""

    return {"response": final_response, "progress_events": progress_events}
```

### 4.2 curl 验证

curl 是最可靠的 SSE 验证工具，不存在行缓冲问题：

```bash
curl -N -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"test_progress_sse","arguments":{"steps":5,"delay_ms":100},"_meta":{"progressToken":"test-token"}}}'
```

---

## 五、`stateless=True` 模式的影响

在 `stateless=True` 模式下：

1. **每个 POST 请求创建独立的传输层** — 没有跨请求的会话状态
2. **没有持久的 GET SSE 流** — `GET_STREAM_KEY` 不存在
3. **progress notification 必须带有 `related_request_id`** — 否则无法路由
4. **`progress()` 上下文管理器不可用** — 因其不传 `related_request_id`

在 `stateless=False` 模式下，如果有活跃的 GET SSE 连接，未带 `related_request_id` 的通知会路由到 GET 流，行为可能不同。

---

## 六、阶跃客户端实测：progressToken 缺失导致全部降级

### 6.1 现象

> 日志来源: `logs/http_sdk_20260312_154915.jsonl`（阶跃客户端调用，2026-03-12 15:49-15:53）

阶跃客户端 v0.2.13 在调用 `tools/call` 时**未在 `_meta` 中携带 `progressToken`**，导致所有设计为流式进度的工具降级为一次性返回。

### 6.2 各工具实际行为

| 工具 | test_id | 设计模式 | 实际行为 | 日志证据 |
|------|---------|---------|---------|---------|
| `test_progress_sse` | J1 | SSE 流式进度 | 降级为 sleep，一次性返回 | `"progress_sent": false` |
| `test_streaming_workflow` | J2 | SSE 流式工作流 | 降级为 sleep（1s = 5步×200ms），一次性返回 | `"progress_sent": false` |
| `test_progress_notification` | C1 | SDK progress() | sleep 后一次性返回，无 `progress_sent` 字段 | 返回 `"Progress notifications completed"` |
| `gui_send_message` | G6 | 流式推送 4 步 | sleep 后一次性返回（0.8s = 4步×200ms） | `"elapsed_ms": 800` |
| `gui_automation_demo` | G7 | 一次性返回（设计如此） | 一次性返回，无流式 | `"mode": "batch"` |

### 6.3 日志原文

```
# J1 — progress_sent: false
{"direction":"OUT","result":{"test_id":"J1","success":true,"steps":3,"delay_ms":100,
  "progress_sent":false,"message":"无 progressToken 或 request_id，进度通知未发送（降级为 sleep）"}}

# G6 — sleep 了 800ms 但 progress 未被客户端接收
{"direction":"OUT","result":{"test_id":"G6","success":true,"contact":"TestUser",
  "mode":"streaming","steps":["查找联系人","打开对话","输入消息","发送"],"elapsed_ms":800}}

# J2 — progress_sent: false
{"direction":"OUT","result":{"test_id":"J2","success":true,"workflow":"data_pipeline",
  "progress_sent":false,"message":"无 progressToken 或 request_id，进度通知未发送（降级为 sleep）"}}
```

### 6.4 原因分析

这是**两个独立问题叠加**的结果：

1. **阶跃客户端不发送 `progressToken`** — 客户端在 `_meta` 中未提供 `progressToken`，服务端的 `ctx.meta.progressToken` 为空
2. **SDK `progress()` 不传 `related_request_id`** — 即使客户端提供了 `progressToken`，C1/G6 使用的 SDK `progress()` 上下文管理器仍会因缺少 `related_request_id` 导致通知被路由丢弃

因此：
- **J1/J2** — 服务端代码正确检查了 `progressToken`，直接降级（设计合理）
- **C1/G6** — 使用 SDK `progress()`，即使有 `progressToken` 也会因路由 Bug 丢弃（但当前连 `progressToken` 都没有，所以根本没走到那一步）

### 6.5 结论

在阶跃客户端 v0.2.13 环境下，SSE 模式虽然已启用（`json_response=False`），但**所有工具调用实际上都是一次性返回**。要实现真正的流式进度推送，需要客户端在请求中携带 `progressToken`，且服务端需要绕过 SDK `progress()` 直接发送通知。

---

## 七、相关文件索引

| 文件 | 说明 |
|------|------|
| `sdk/http/src/mcp_http_sdk/server.py` | HTTP SDK 服务器（含 J1/J2 SSE 工具） |
| `sdk/http/run_test_sse.py` | SSE 模式测试脚本（37 个工具） |
| `mcp/shared/progress.py` | SDK progress 上下文管理器源码（Bug 所在） |
| `mcp/server/streamable_http.py` | SDK SSE 消息路由器源码 |
| `mcp/shared/context.py` | SDK RequestContext 定义 |
| `docs/STEPFUN_STREAMING_LIMITATION.md` | 阶跃客户端 progress 通知 UI 限制 |

---

*记录时间: 2026-03-12 | 阶跃实测数据更新: 2026-03-12*
