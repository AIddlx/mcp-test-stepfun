# MCP 综合能力测试指南 V5（协议能力完整测试）

## 新增测试项目（测试 19-26）

本文档记录 MCP 协议完整能力的测试项目，请在完成 V1-V4 测试后再执行。

---

## 测试 19：MCP Ping 心跳

**工具**: `mcp_ping`

**测试目的**: 验证 MCP 协议级别的心跳检测能力。

**测试步骤**:

1. **基础心跳**:
   ```json
   {}
   ```

2. **带 echo 参数**:
   ```json
   {
     "echo": "heartbeat_test"
   }
   ```

**预期结果**:
```json
{
  "success": true,
  "pong": true,
  "echo": "heartbeat_test",
  "timestamp": "2026-03-09T..."
}
```

**通过条件**: 返回 `pong: true`，echo 正确返回

---

## 测试 20：日志级别设置

**工具**: `set_log_level`

**测试目的**: 验证 MCP `logging/setLevel` 能力。

**测试步骤**:

依次测试不同日志级别：

1. `{"level": "debug"}`
2. `{"level": "info"}`
3. `{"level": "warning"}`
4. `{"level": "error"}`

**预期结果**:
```json
{
  "success": true,
  "previous_level": "info",
  "current_level": "debug",
  "message": "Log level set to debug"
}
```

**通过条件**: 日志级别正确设置，返回前后级别

---

## 测试 21：进度通知

**工具**: `progress_operation`

**测试目的**: 验证 MCP `notifications/progress` 进度通知能力。

**测试步骤**:

1. **短进度测试**:
   ```json
   {
     "steps": 5,
     "step_delay_ms": 500
   }
   ```
   预期：5 步，每步 500ms，总耗时约 2.5 秒

2. **长进度测试**:
   ```json
   {
     "steps": 10,
     "step_delay_ms": 1000
   }
   ```
   预期：10 步，每步 1 秒，总耗时约 10 秒

**预期结果**:
```json
{
  "success": true,
  "completed": true,
  "steps": 5,
  "progress_updates": [
    {"step": 1, "progress": 20.0},
    {"step": 2, "progress": 40.0},
    ...
  ]
}
```

**通过条件**: 进度更新完整，百分比正确

---

## 测试 22：取消操作

**工具**: `cancellable_operation`

**测试目的**: 验证 MCP `notifications/cancelled` 取消操作能力。

**测试步骤**:

1. **正常完成**:
   ```json
   {
     "duration_seconds": 5,
     "cancel_after_seconds": 0
   }
   ```
   预期：正常完成

2. **取消操作**:
   ```json
   {
     "duration_seconds": 20,
     "cancel_after_seconds": 3
   }
   ```
   预期：3 秒后被取消

**预期结果（取消时）**:
```json
{
  "success": false,
  "cancelled": true,
  "cancel_reason": "Client requested cancellation",
  "elapsed_seconds": 3.5,
  "progress_at_cancel": 17.5
}
```

**通过条件**: 取消信号正确触发，返回取消点进度

---

## 测试 23：自动补全

**工具**: `test_completion`

**测试目的**: 验证 MCP `completion/complete` 自动补全能力。

**测试步骤**:

1. **资源补全**:
   ```json
   {
     "ref_type": "ref/resource",
     "partial_value": "conf"
   }
   ```

2. **提示补全**:
   ```json
   {
     "ref_type": "ref/prompt",
     "partial_value": "ana"
   }
   ```

**预期结果**:
```json
{
  "success": true,
  "completions": ["config://server", "config://settings", "config://database"],
  "total": 3,
  "has_more": false
}
```

**通过条件**: 返回匹配的补全建议

---

## 测试 24：采样请求

**工具**: `request_sampling`

**测试目的**: 验证 MCP `sampling/createMessage` LLM 采样能力。

**测试步骤**:

1. **简单采样**:
   ```json
   {
     "prompt": "What is 2+2?",
     "max_tokens": 100
   }
   ```

2. **复杂采样**:
   ```json
   {
     "prompt": "Explain quantum computing in one sentence.",
     "max_tokens": 200
   }
   ```

**预期结果**:
```json
{
  "success": true,
  "sampling_requested": true,
  "prompt": "What is 2+2?",
  "sampling_params": {
    "messages": [{"role": "user", "content": "..."}],
    "maxTokens": 100
  },
  "simulated_response": "4",
  "note": "Actual sampling requires client support"
}
```

**通过条件**: 采样请求正确构造，注意实际采样需要客户端支持

**重要**: 这是服务端请求客户端进行 LLM 采样的能力，需要阶跃客户端支持 `sampling/createMessage` 方法。

---

## 测试 25：订阅更新通知

**工具**: `subscribe_updates`

**测试目的**: 验证 MCP 列表变更通知订阅能力。

**测试步骤**:

1. **订阅全部**:
   ```json
   {
     "subscribe_type": "all"
   }
   ```

2. **订阅工具变更**:
   ```json
   {
     "subscribe_type": "tools"
   }
   ```

3. **订阅资源变更**:
   ```json
   {
     "subscribe_type": "resources"
   }
   ```

**预期结果**:
```json
{
  "success": true,
  "subscribed": true,
  "subscribe_type": "all",
  "notifications_expected": {
    "tools": "notifications/tools/listChanged",
    "resources": "notifications/resources/listChanged",
    "prompts": "notifications/prompts/listChanged"
  }
}
```

**通过条件**: 订阅成功，返回预期通知类型

---

## 测试 26：资源订阅

**工具**: `resource_subscribe`

**测试目的**: 验证 MCP 资源更新通知订阅能力。

**测试步骤**:

1. **订阅服务器配置**:
   ```json
   {
     "uri": "config://server"
   }
   ```

2. **订阅文件资源**:
   ```json
   {
     "uri": "file://test.txt"
   }
   ```

**预期结果**:
```json
{
  "success": true,
  "subscribed": true,
  "uri": "config://server",
  "notification_type": "notifications/resources/updated"
}
```

**通过条件**: 资源订阅成功，返回通知类型

---

## 新增测试结果汇总表

| 编号 | 测试项 | 状态 | 备注 |
|------|--------|------|------|
| 19 | mcp_ping | ✅ 通过 | 基础心跳和带 echo 参数均正常 |
| 20 | set_log_level | ✅ 通过 | debug/info/warning/error 四级均可设置 |
| 21 | progress_operation | ✅ 通过 | 短进度(5步)和长进度(10步)均正确完成 |
| 22 | cancellable_operation | ✅ 通过 | 正常完成和取消中断均符合预期 |
| 23 | test_completion | ✅ 通过 | 资源补全返回3个匹配项 |
| 24 | request_sampling | ✅ 通过 | 采样参数正确构造，需客户端支持 |
| 25 | subscribe_updates | ✅ 通过 | all/tools/resources 三种订阅均成功 |
| 26 | resource_subscribe | ✅ 通过 | config://server 和 file://test.txt 均订阅成功 |

**通过率**: 8/8 = 100%

---

## 测试完成后

**测试日期**: 2026-03-09

1. **Ping**: 心跳响应是否正常？
   - ✅ 是。`pong: true` 正确返回，echo 参数原样回传

2. **Logging**: 日志级别设置是否生效？
   - ✅ 是。四个日志级别均可正确设置

3. **Progress**: 进度通知是否能正确接收？
   - ✅ 是（模拟）。在单次工具调用响应中模拟返回所有进度更新

4. **Cancellation**: 取消操作是否能正确中断？
   - ✅ 是（模拟）。服务端模拟取消行为正确

5. **Completion**: 自动补全建议是否正确？
   - ✅ 是。资源补全返回 3 个匹配项

6. **Sampling**: 阶跃是否支持服务端发起的 LLM 采样？
   - ⚠️ 服务端正确构造了采样参数，但实际 LLM 采样需要阶跃客户端实现 `sampling/createMessage` 回调

7. **Notifications**: 各类订阅通知是否能正确接收？
   - ✅ 订阅注册均成功

---

## MCP 协议能力完整清单

| 能力类别 | 能力名称 | 方法 | 测试状态 |
|----------|----------|------|----------|
| **Tools** | 工具调用 | `tools/list`, `tools/call` | ✅ V1 已测试 |
| **Resources** | 资源读取 | `resources/list`, `resources/read` | ⚠️ 阶跃未调用 |
| **Prompts** | 提示模板 | `prompts/list`, `prompts/get` | ⚠️ 阶跃未调用 |
| **Ping** | 心跳 | `ping` | 🔄 V5 测试 |
| **Logging** | 日志 | `logging/setLevel` | 🔄 V5 测试 |
| **Progress** | 进度 | `notifications/progress` | 🔄 V5 测试 |
| **Cancellation** | 取消 | `notifications/cancelled` | 🔄 V5 测试 |
| **Completion** | 补全 | `completion/complete` | 🔄 V5 测试 |
| **Sampling** | 采样 | `sampling/createMessage` | 🔄 V5 测试 |
| **Roots** | 根目录 | `roots/list` | ⏭️ 跳过 |
