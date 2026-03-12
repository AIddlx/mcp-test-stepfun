# 设计阶段约束

> 阶跃 MCP 服务器设计时需要考虑的协议和架构限制。

---

## D001: tools/call 是原子的

**MCP 规范设计，不是客户端缺陷。**

`tools/call` 返回单个 `CallToolResult`，没有"部分结果"或"流式内容"的概念。

```json
{
  "content": [{"type": "text", "text": "完整结果"}],
  "isError": false
}
```

**影响**：GUI Agent 的多步操作（点击→输入→等待→截图）无法实时反馈给用户。

**替代方案**：
- **异步轮询**：`start_task → get_task_status → get_result`
- **分段工具调用**：拆分为多个短工具（`click → type → wait → screenshot`）

**参考**：[docs/STEPFUN_STREAMING_LIMITATION.md](../../../docs/STEPFUN_STREAMING_LIMITATION.md)

---

## D002: 不要声明 outputSchema

阶跃不消费 `outputSchema` 和 `structuredContent`，只读取 `content` 中的文本。

**影响**：
- 声明 outputSchema → `-32600: Tool xxx has an output schema but did not return structured content`
- 返回 structuredContent 但格式不匹配 → 同上错误

**规则**：工具定义中不写 `outputSchema`，返回值只用 `content` 数组。

**测试依据**：实测删除 outputSchema 后所有工具正常运行。

---

## D003: 进度通知不可靠

`notifications/progress` 是 MCP 协议中唯一的服务器→客户端中间通知机制，但在阶跃中存在两层问题：

1. **阶跃不发送 `progressToken`** — 服务端无法发送进度通知
2. **SDK 有路由 Bug** — `report_progress()` 和 `progress()` 都缺少 `related_request_id`，在 HTTP `stateless=True` 模式下通知被路由丢弃

**结论**：不要设计依赖进度通知的功能。长任务必须使用异步轮询模式。

### SDK Bug 详情

- `mcp/server/fastmcp/context.py`: `report_progress()` 调用 `send_progress_notification()` 时不传 `related_request_id`
- `mcp/shared/progress.py`: `progress()` 上下文管理器同样缺少此参数
- 路由逻辑：无 `id`（响应）、无 `related_request_id`（通知）→ 路由到 GET 流（`stateless=True` 时不存在）→ 静默丢弃

### 各模式进度通知可用性

| 模式 | progress 可见性 | 原因 |
|------|----------------|------|
| stdio | ✅ 可用（协议层） | 消息直接通过 stdout，无路由 |
| HTTP `stateless=False` + GET SSE | ✅ 可用 | 无 `related_request_id` 的通知路由到 GET 流 |
| HTTP `stateless=True` | ❌ 丢弃 | 无 GET 流 + 缺少 `related_request_id` |
| 任何模式（阶跃客户端） | ❌ 全部无效 | 客户端不发送 `progressToken` |

**参考**：
- [docs/FASTMCP_STREAMING_ANALYSIS.md](../../../docs/FASTMCP_STREAMING_ANALYSIS.md)
- [docs/SSE_PROGRESS_DESIGN_NOTES.md](../../../docs/SSE_PROGRESS_DESIGN_NOTES.md)

---

## D004: 服务器→客户端能力受限

阶跃 v0.2.13 对以下能力未实现客户端支持：

| 能力 | 实测观察 |
|------|---------|
| `resources/subscribe` | 客户端未发起订阅 |
| `sampling/createMessage` | 客户端未响应 |
| `elicitation/create` | 客户端未响应 |
| `notifications/tools/list_changed` | 未测试 |
| `logging/setLevel` | 未测试 |

**规则**：可以声明这些能力，但不要依赖客户端消费它们。后续版本可能变化。

---

## D005: FastMCP 没有 stream=True

FastMCP **不存在** `stream=True` 参数。控制台测试中看到的"流式"效果是 `notifications/progress` 作为中间 SSE 事件逐行到达。

```
请求 ──→ notification(progress 1/5) ──→ notification(progress 2/5) ──→ ... ──→ 最终响应
```

视觉效果像"流式"，实际是多个独立的 SSE 事件。最终只有 `result` 中的内容被提交给 LLM。

这是 SDK API 误用的常见来源。正确的用法是通过 `ctx.report_progress()` 发送进度，但如 D003 所述，在阶跃中无效。

**参考**：[docs/FASTMCP_STREAMING_ANALYSIS.md](../../../docs/FASTMCP_STREAMING_ANALYSIS.md)
