# 阶跃桌面助手流式进度通知限制

> 阶跃 AI 桌面助手 v0.2.13 | Windows 11 | 最后更新: 2026-03-12

---

## 结论

**阶跃桌面助手 v0.2.13 不支持实时显示 MCP `notifications/progress` 进度通知。**

这是客户端集成层的设计选择，而非 MCP 协议本身的限制。所有三个传输模式（HTTP / NPX / UVX）的行为一致。

---

## MCP 协议层面的限制

### 为什么不能"逐步返回内容"

MCP 的 `tools/call` 是原子性的——一个请求对应一个 `CallToolResult`，协议没有定义"部分结果流式返回"的机制。

#### 规范原文证据

**1. `tools/call` 返回单个 `CallToolResult`**（schema.json:185）

```json
"CallToolResult": {
  "description": "The server's response to a tool call.",
  "properties": {
    "content": { "type": "array", "items": { "$ref": "ContentBlock" } },
    "isError": { "type": "boolean" },
    "structuredContent": { "type": "object" }
  },
  "required": ["content"]
}
```

没有"分块结果"、"流式内容"的定义。

**2. 传输层只有两种响应方式**（transports.mdx:103-106）

> If the input is a JSON-RPC request, the server MUST either return `Content-Type: text/event-stream`, to initiate an SSE stream, or `Content-Type: application/json`, to return **one JSON object**.

SSE 流中可以放多个 JSON-RPC 消息，但每个消息都是**完整的** JSON-RPC message，不是结果的一部分。

**3. SSE 流中能发什么**（transports.mdx:119-123）

> The SSE stream SHOULD eventually include a JSON-RPC **response** for the JSON-RPC request.
> The server MAY send JSON-RPC **requests** and **notifications** before sending the response.

即：`notification (progress)` → `notification (progress)` → ... → `response (最终结果)`。没有"部分 response"的概念。

**4. `progressToken` 是可选的**（progress.mdx）

> When a party wants to **receive** progress updates for a request, it includes a `progressToken` in the request metadata.
> The receiver **MAY** choose not to send any progress notifications.

明确是"想要接收"才提供，不是必须。且 progress notification 是"带外"的（out-of-band），跟最终结果独立。

#### Streamable HTTP 的两种反馈方式对比

| 方式 | 需要什么 | 阶跃支持 |
|------|---------|---------|
| 自然流式（逐步返回内容） | 协议不支持，`tools/call` 返回是原子的 | 不适用 |
| 进度通知（`notifications/progress`） | 客户端发送 `progressToken` | 阶跃不发送 |

**结论：在阶跃客户端当前行为下，MCP `tools/call` 只能一次性返回最终结果，没有协议层面的其他出路。**

### 这不是 Streamable HTTP 传输的缺陷

Streamable HTTP 作为传输层是完备的：
- 支持双向通信（POST + GET SSE）
- 支持中间 notifications 和 requests
- 问题在于 **MCP 协议层的 `tools/call` 语义就是原子性的**，跟传输方式无关

---

## 测试证据

### 三模式对比

| 模式 | 传输通道 | 服务器发送 | 客户端渲染 | 结论 |
|------|---------|-----------|-----------|------|
| HTTP (StreamableHTTP) | SSE 流 | 5 次 `notifications/progress` | 只返回最终结果 | 协议层接收，UI 不展示中间状态 |
| NPX (stdio) | stdin/stdout | 5 次 `notifications/progress` | 只返回最终结果 | 同上 |
| UVX (stdio) | stdin/stdout | N 次 `notifications/progress` | 只返回最终结果 | 同上 |

### 各模式测试详情

#### HTTP 模式（2026-03-10 首次发现）

- 工具: `test_progress_notification`，参数: `{"total_steps": 5, "step_delay_ms": 2000}`
- HTTP 请求头正确: `Accept: application/json, text/event-stream`
- 服务器正确发送 5 次 SSE 事件
- 客户端只在最后一次性返回 `"Streaming completed"`，中间步骤未展示

#### NPX 模式（2026-03-10）

- 工具: `test_progress_notification`，参数: steps=3, delay=100ms
- 服务器通过 `sendNotification('notifications/progress', ...)` 发送通知
- 阶跃返回 `"Streaming completed"`，无中间步骤

#### UVX 模式（2026-03-11 确认）

- 工具: `test_progress_notification`（C1）和 `gui_send_message`（G6）
- 服务器使用 Python FastMCP `ctx.report_progress()` 发送通知
- 阶跃日志中只有 `[progress] chatSessionId`（阶跃自身的聊天进度），无 MCP 协议层 progress 消息
- 工具调用正常完成，但只有最终 return 值被提交给 LLM

### 技术分析

| 层面 | 状态 | 说明 |
|------|------|------|
| MCP 协议 | ✅ 正确 | 服务器按规范发送 `notifications/progress` |
| 传输层 | ✅ 正确 | HTTP SSE / stdio 均正确传输 |
| 客户端接收 | ✅ 成功 | 协议层收到通知（HTTP 模式已确认） |
| **LLM 集成层** | ❌ 丢弃 | 中间事件被静默丢弃，只有最终结果提交给 LLM |

---

## 对 GUI Agent 场景的影响

GUI Agent 任务通常执行时间长、需要实时反馈，当前限制意味着：

1. **无法实时看到进度** — 用户不知道任务执行到哪一步
2. **无法中途取消** — 请求已发出，只能等待完成
3. **超时风险** — 超过 55~60 秒的任务会被客户端截断

---

## 推荐方案

### 方案 A：异步任务 + 轮询（首选）

```python
TOOLS = [
    {"name": "start_gui_task", "description": "启动任务，立即返回 task_id"},
    {"name": "get_task_status", "description": "查询任务状态和进度"},
    {"name": "cancel_task", "description": "取消任务"},
]
```

调用流程:
```
1. start_gui_task(...) → task_id="abc123", status="running"
2. get_task_status("abc123") → {progress: 30%, step: "点击按钮"}
3. get_task_status("abc123") → {progress: 60%, step: "输入文本"}
4. get_task_status("abc123") → {progress: 100%, status: "completed"}
```

### 方案 B：分段工具调用

将长任务拆分为多个短工具：
```
1. gui_click(x, y) → 1s
2. gui_type(text) → 1s
3. gui_wait(element) → 2s
4. gui_screenshot() → 0.5s
```

每一步都是独立的工具调用，LLM 可以看到每步结果后再决定下一步。

---

## 相关文件

- [NPX 测试报告](./stdio/npx/TEST_REPORT.md) — C1/G6 测试结果
- [UVX 测试报告](./stdio/uvx/TEST_REPORT.md) — C1/G6 测试结果
- [UVX 问题汇总](./stdio/uvx/ISSUES.md) — UVX 模式排障记录
- [HTTP 兼容性](./http/COMPATIBILITY.md) — HTTP 模式兼容性说明
