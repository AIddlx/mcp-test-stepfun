# MCP stdio 模式测试指南

## 测试目的

验证阶跃桌面助手在 **stdio 模式**下是否能够：

1. **接收服务端主动通知** - `notifications/progress`, `notifications/message`
2. **响应服务端采样请求** - `sampling/createMessage`
3. **调用 Resources API** - `resources/list`, `resources/read`
4. **调用 Prompts API** - `prompts/list`, `prompts/get`

## 配置方法

阶跃桌面助手只支持 `npx` 命令，配置如下：

```json
{
  "mcpServers": {
    "stdio-test": {
      "command": "npx",
      "args": ["-y", "<项目路径>", "--stdio-test"]
    }
  }
}
```

**说明**: `--stdio-test` 参数会启动完整能力的 stdio 测试服务器。

## 与 HTTP 模式的区别

| 特性 | HTTP 模式 | stdio 模式 |
|------|-----------|------------|
| **通信方式** | HTTP POST | stdin/stdout |
| **服务端推送** | ❌ 需要 SSE | ✅ 直接支持 |
| **生命周期** | 持续运行 | 每次调用启动新进程 |
| **状态保持** | ✅ 有状态 | ❌ 无状态 |

## 测试清单

### 测试 1：基础连通性

**工具**: `ping`

**预期结果**:
```json
{
  "pong": true,
  "timestamp": "2026-03-09T...",
  "mode": "stdio"
}
```

**验证点**: `mode: "stdio"` 确认使用 stdio 模式

---

### 测试 2：服务端主动通知

**工具**: `test_notification`

**参数**:
```json
{
  "count": 3
}
```

**预期行为**:
- 服务端发送 3 个 `notifications/progress` 通知
- 服务端发送 1 个 `notifications/message` 通知

**验证点**:
- ⬜ 是否收到了进度通知？
- ⬜ 通知内容是否正确？
- ⬜ 通知是实时到达还是批量返回？

---

### 测试 3：采样请求

**工具**: `request_sampling`

**参数**:
```json
{
  "prompt": "What is 2+2?",
  "max_tokens": 100
}
```

**预期行为**:
- 服务端发送 `sampling/createMessage` 请求到客户端
- 客户端（阶跃）应该用 LLM 回答并返回结果

**验证点**:
- ⬜ 服务端是否发送了采样请求？
- ⬜ 阶跃是否响应了采样请求？
- ⬜ 如果响应，LLM 的回答是什么？

**重要**: 这是测试阶跃是否支持 `sampling/createMessage` 回调的关键测试。

---

### 测试 4：Resources API

**工具**: `list_resources`

**预期结果**:
```json
{
  "success": true,
  "resources": [
    {"uri": "config://server", "name": "Server Configuration"},
    {"uri": "file://test.txt", "name": "Test Text File"},
    {"uri": "status://live", "name": "Live Status"}
  ]
}
```

**附加测试**: 阶跃是否**主动调用**了 `resources/list`？

**验证点**:
- ⬜ 工具调用返回资源列表
- ⬜ 阶跃是否在初始化后自动请求 `resources/list`？
- ⬜ 阶跃 UI 中是否有资源浏览入口？

---

### 测试 5：Prompts API

**工具**: `list_prompts`

**预期结果**:
```json
{
  "success": true,
  "prompts": [
    {"name": "analyze_data", "description": "Analyze data..."},
    {"name": "summarize", "description": "Summarize..."},
    {"name": "test_sampling", "description": "Test sampling..."}
  ]
}
```

**附加测试**: 阶跃是否**主动调用**了 `prompts/list`？

**验证点**:
- ⬜ 工具调用返回提示模板列表
- ⬜ 阶跃是否在初始化后自动请求 `prompts/list`？
- ⬜ 阶跃 UI 中是否有提示模板入口？

---

### 测试 6：资源更新通知

**工具**: `simulate_resource_update`

**参数**:
```json
{
  "uri": "status://live"
}
```

**预期行为**:
- 服务端发送 `notifications/resources/updated` 通知

**验证点**:
- ⬜ 是否收到资源更新通知？
- ⬜ 阶跃如何处理这个通知？

---

### 测试 7：长时间操作进度

**工具**: `long_operation_with_progress`

**参数**:
```json
{
  "steps": 5,
  "delay_ms": 500
}
```

**预期行为**:
- 服务端发送 5 个 `notifications/progress` 通知
- 每个通知包含进度百分比

**验证点**:
- ⬜ 进度通知是否实时到达？
- ⬜ 进度百分比是否正确递增？

---

## 关键观察点

### 1. 服务端日志

服务端会输出详细日志到 stderr（不影响 JSON-RPC 通信）：

```
[18:30:45.123] [INFO] MCP stdio 测试服务器启动
[18:30:45.125] [INFO] 收到请求: initialize (id=0)
[18:30:45.130] [INFO] 发送通知: notifications/message
```

### 2. 客户端行为

观察阶跃是否：

| 行为 | HTTP 模式 | stdio 模式预期 |
|------|-----------|----------------|
| 接收服务端通知 | ❌ 不支持 | ✅ 应该支持 |
| 响应采样请求 | ❌ 不支持 | ⚠️ 待验证 |
| 调用 resources/list | ❌ 不调用 | ⚠️ 待验证 |
| 调用 prompts/list | ❌ 不调用 | ⚠️ 待验证 |

### 3. 交互日志

检查服务端日志中是否有：
- `客户端请求资源列表!` → 阶跃主动调用 resources/list
- `客户端请求提示模板列表!` → 阶跃主动调用 prompts/list
- `收到采样响应:` → 阶跃响应 sampling/createMessage

---

## 测试结果记录表 ✅ (2026-03-09)

| 编号 | 测试项 | 工具调用 | 通知接收 | 采样响应 | 结果 |
|------|--------|----------|----------|----------|------|
| 1 | ping | ✅ | - | - | ✅ 通过 |
| 2 | test_notification | ✅ | ⚠️ 无法确认 | - | ⚠️ 部分通过 |
| 3 | request_sampling | ✅ | - | ❌ 未响应 | ❌ 未通过 |
| 4 | list_resources | ✅ | - | - | ✅ 通过 |
| 5 | list_prompts | ✅ | - | - | ✅ 通过 |
| 6 | simulate_resource_update | ✅ | ⚠️ 无法确认 | - | ⚠️ 部分通过 |
| 7 | long_operation_with_progress | ✅ | ⚠️ 无法确认 | - | ⚠️ 部分通过 |

---

## 额外验证

### 阶跃是否主动调用 Resources/Prompts API?

**结果**: ❌ 未主动调用

服务端日志中**没有**出现 `客户端请求资源列表!` 或 `客户端请求提示模板列表!` 的记录。

这说明阶跃在 stdio 模式下**不会**主动调用这些 API，而是将它们封装为工具供 AI 按需调用。

---

## 实际结论

| 功能 | HTTP 模式 | stdio 模式 | 结论 |
|------|-----------|------------|------|
| **Tools API** | ✅ 支持 | ✅ 支持 | 两种模式均完全支持 |
| **服务端通知** | ❌ 不支持 | ⚠️ 无法确认 | stdio 未带来改善 |
| **Sampling** | ❌ 不支持 | ❌ 不支持 | 两种模式均不支持 |
| **Resources（主动调用）** | ❌ 不调用 | ❌ 不调用 | 两种模式均不调用 |
| **Prompts（主动调用）** | ❌ 不调用 | ❌ 不调用 | 两种模式均不调用 |

**最终结论**: stdio 模式相比 HTTP 模式**并未**带来更好的高级 MCP 功能支持。对于 scrcpy-py-ddlx 项目，推荐使用 HTTP 模式。


