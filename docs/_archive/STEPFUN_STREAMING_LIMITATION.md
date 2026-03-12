# 阶跃桌面助手流式进度通知限制

**发现日期**: 2026-03-10
**测试工具**: `test_progress_notification`
**参数**: `{"total_steps": 5, "step_delay_ms": 2000}`

---

## 测试现象

### 预期行为
服务器发送 5 次进度通知（每 2 秒一次），客户端逐步显示：
```
Step 1/5 (20%)
Step 2/5 (40%)
Step 3/5 (60%)
Step 4/5 (80%)
Step 5/5 (100%)
完成
```

### 实际行为
客户端只在最后一次性返回：
```
Streaming completed
```

---

## 技术分析

| 层面 | 状态 | 说明 |
|------|------|------|
| HTTP 请求头 | ✅ 正确 | `Accept: application/json, text/event-stream` |
| 服务器响应 | ✅ 正确 | 发送了 5 次 `notifications/progress` |
| 客户端接收 | ✅ 成功 | 协议层收到了 SSE 流 |
| **实时显示** | ❌ 不支持 | 中间状态未传递给用户/LLM |

### 原因
这是 **客户端集成层的设计选择**，而非 MCP 协议本身的限制。阶跃助手将流式响应的最终结果一次性提交给 LLM，而不是逐条处理中间通知。

---

## 对 GUI Agent 场景的影响

### 问题
GUI Agent 任务通常：
- 执行时间长（数分钟）
- 需要实时反馈（当前步骤、截图、日志）
- 可能需要中途取消

### 当前阶跃的限制
1. **无法实时看到进度** - 用户不知道任务执行到哪一步
2. **无法中途取消** - 请求已发出，只能等待完成
3. **超时风险** - 超过 30s 的任务可能被截断

---

## 推荐方案

### 方案 A：异步任务模式（首选）

```python
# 工具设计
TOOLS = [
    {
        "name": "start_gui_task",
        "description": "启动 GUI 自动化任务，立即返回 task_id",
        "inputSchema": {...}
    },
    {
        "name": "get_task_status",
        "description": "查询任务状态和进度",
        "inputSchema": {"task_id": "string"}
    },
    {
        "name": "cancel_task",
        "description": "取消正在执行的任务",
        "inputSchema": {"task_id": "string"}
    }
]
```

**调用流程**:
```
1. start_gui_task(...) → task_id="abc123", status="running"
2. get_task_status("abc123") → {progress: 30%, step: "点击按钮", screenshot: "..."}
3. get_task_status("abc123") → {progress: 60%, step: "输入文本"}
4. get_task_status("abc123") → {progress: 100%, status: "completed", result: ...}
```

### 方案 B：MCP Resources

```python
# 资源设计
RESOURCES = [
    {"uri": "task://abc123/status", "name": "任务状态", "mimeType": "application/json"},
    {"uri": "task://abc123/screenshot", "name": "当前截图", "mimeType": "image/png"},
    {"uri": "task://abc123/log", "name": "执行日志", "mimeType": "text/plain"}
]
```

**LLM 可以主动查询资源获取实时状态**。

### 方案 C：分段工具调用

将长任务拆分为多个短工具：
```
1. gui_click(x, y) → 1s
2. gui_type(text) → 1s
3. gui_wait(element) → 2s
4. gui_screenshot() → 0.5s
```

每一步都是独立的工具调用，LLM 可以看到每步结果后再决定下一步。

---

## 结论

**阶跃桌面助手 v0.2.13 不支持实时显示流式进度通知**。

对于 GUI Agent 场景，建议：
1. 采用**异步任务 + 轮询**模式
2. 或将任务**拆分为多个短步骤**
3. 不要依赖 `notifications/progress` 作为唯一的进度反馈机制
