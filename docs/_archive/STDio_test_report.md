# MCP stdio 模式测试报告

**测试日期**: 2026-03-09  
**测试环境**: Windows / 阶跃桌面助手  
**MCP 服务器**: stdio-test (npx 启动)

---

## 测试结果总览

| 编号 | 测试项 | 工具调用 | 通知接收 | 采样响应 | 结果 |
|------|--------|----------|----------|----------|------|
| 1 | ping | ✅ 成功 | - | - | ✅ 通过 |
| 2 | test_notification | ✅ 成功 | ⚠️ 无法确认 | - | ⚠️ 部分通过 |
| 3 | request_sampling | ✅ 成功 | - | ❌ 未响应 | ❌ 未通过 |
| 4 | list_resources | ✅ 成功 | - | - | ✅ 通过 |
| 5 | list_prompts | ✅ 成功 | - | - | ✅ 通过 |
| 6 | simulate_resource_update | ✅ 成功 | ⚠️ 无法确认 | - | ⚠️ 部分通过 |
| 7 | long_operation_with_progress | ✅ 成功 | ⚠️ 无法确认 | - | ⚠️ 部分通过 |

---

## 各测试项详细结果

### 测试 1：基础连通性 (ping)

- **状态**: ✅ 通过
- **返回结果**:
  ```json
  {
    "pong": true,
    "timestamp": "2026-03-09T10:50:37.336Z",
    "mode": "stdio"
  }
  ```
- **分析**: `mode: "stdio"` 确认使用 stdio 模式通信，基础连通性正常。

---

### 测试 2：服务端主动通知 (test_notification)

- **状态**: ⚠️ 部分通过
- **返回结果**:
  ```json
  {
    "success": true,
    "message": "Will send 3 notifications",
    "mode": "stdio"
  }
  ```
- **分析**: 
  - 工具调用本身成功，服务端声称将发送 3 个 `notifications/progress` 通知。
  - 从 AI 助手侧无法直接观察到通知是否被客户端接收并展示。
  - 在对话界面中未看到实时进度通知的展示效果。
  - **结论**: 服务端发送通知的能力正常，但客户端（阶跃桌面助手）是否接收并处理了通知**无法确认**。从用户可见的交互来看，通知未被显式展示。

---

### 测试 3：采样请求 (request_sampling)

- **状态**: ❌ 未通过
- **返回结果**:
  ```json
  {
    "success": true,
    "message": "Sampling request sent",
    "request_id": 1,
    "prompt": "What is 2+2?",
    "note": "Server sent sampling/createMessage request to client"
  }
  ```
- **分析**:
  - 服务端成功发送了 `sampling/createMessage` 请求。
  - 返回结果中仅包含"请求已发送"的确认信息，**没有包含客户端 LLM 的回答内容**。
  - 这说明阶跃桌面助手**未响应** `sampling/createMessage` 回调请求，或者响应未被服务端正确接收。
  - **结论**: 阶跃桌面助手在 stdio 模式下**不支持** `sampling/createMessage` 回调。

---

### 测试 4：Resources API (list_resources)

- **状态**: ✅ 通过
- **返回结果**:
  ```json
  {
    "success": true,
    "resources": [
      {"uri": "config://server", "name": "Server Configuration", "mimeType": "application/json"},
      {"uri": "file://test.txt", "name": "Test Text File", "mimeType": "text/plain"},
      {"uri": "status://live", "name": "Live Status", "mimeType": "application/json"}
    ]
  }
  ```
- **分析**:
  - 通过工具调用 `list_resources` 成功获取了 3 个资源。
  - **关于是否主动调用**: 阶跃桌面助手将 `list_resources` 暴露为可调用的工具（tool），AI 助手通过工具调用的方式获取资源列表。这说明阶跃**没有在初始化阶段自动/主动调用 `resources/list`**，而是将其封装为工具供 AI 按需调用。
  - 阶跃 UI 中未观察到专门的资源浏览入口。

---

### 测试 5：Prompts API (list_prompts)

- **状态**: ✅ 通过
- **返回结果**:
  ```json
  {
    "success": true,
    "prompts": [
      {"name": "analyze_data", "description": "Analyze data"},
      {"name": "summarize", "description": "Summarize content"},
      {"name": "test_sampling", "description": "Test sampling capability", "arguments": [{"name": "question", "required": true}]}
    ]
  }
  ```
- **分析**:
  - 通过工具调用 `list_prompts` 成功获取了 3 个提示模板。
  - **关于是否主动调用**: 与 Resources API 类似，阶跃将 `list_prompts` 暴露为可调用的工具，AI 助手通过工具调用获取。阶跃**没有在初始化阶段自动/主动调用 `prompts/list`**。
  - 阶跃 UI 中未观察到专门的提示模板入口。

---

### 测试 6：资源更新通知 (simulate_resource_update)

- **状态**: ⚠️ 部分通过
- **返回结果**:
  ```json
  {
    "success": true,
    "message": "Notification sent for status://live"
  }
  ```
- **分析**:
  - 服务端声称已发送 `notifications/resources/updated` 通知。
  - 客户端侧无明显反应，未观察到资源自动刷新或通知提示。
  - **结论**: 客户端可能未处理此类通知。

---

### 测试 7：长时间操作进度 (long_operation_with_progress)

- **状态**: ⚠️ 部分通过
- **返回结果**:
  ```json
  {
    "success": true,
    "message": "Started 5 steps",
    "delay_ms": 500
  }
  ```
- **分析**:
  - 服务端执行了 5 步操作（每步 500ms），预期发送 5 个进度通知。
  - 工具调用在约 2.5 秒后返回最终结果，说明服务端确实执行了延时操作。
  - 但在等待期间，对话界面中**未看到实时进度百分比的展示**。
  - **结论**: 进度通知可能被客户端接收但未在 UI 层面展示，或者未被处理。

---

## 三项重点验证结论

### 1. 是否能收到服务端主动发送的通知（notifications/progress）

**结论: ⚠️ 无法明确确认**

- 测试 2（test_notification）和测试 7（long_operation_with_progress）中，服务端均声称发送了通知。
- 从 AI 助手的视角，工具调用正常返回了最终结果，但在等待过程中**未观察到实时进度通知的展示**。
- 可能的情况：(a) 客户端在协议层接收了通知但未向 AI/UI 层传递；(b) 客户端直接忽略了通知。

### 2. 是否能响应服务端的采样请求（sampling/createMessage）

**结论: ❌ 不支持**

- 测试 3（request_sampling）中，服务端成功发送了 `sampling/createMessage` 请求。
- 返回结果仅包含"请求已发送"的确认，**没有包含 LLM 的回答**。
- 阶跃桌面助手在 stdio 模式下**不支持 `sampling/createMessage` 回调**。

### 3. 是否主动调用了 resources/list 和 prompts/list

**结论: ❌ 未主动调用**

- 阶跃桌面助手将 `resources/list` 和 `prompts/list` 封装为可调用的工具（`list_resources` 和 `list_prompts`），供 AI 按需调用。
- 阶跃**没有在 MCP 初始化阶段自动/主动调用这两个 API**。
- 阶跃 UI 中也没有专门的资源浏览或提示模板入口。

---

## 功能支持对比表

| 功能 | HTTP 模式 | stdio 模式 |
|------|-----------|------------|
| **Tools API** | ✅ 支持 | ✅ 支持 |
| **服务端通知** | ❌ 不支持 | ⚠️ 无法确认（未在 UI 展示） |
| **Sampling 回调** | ❌ 不支持 | ❌ 不支持 |
| **Resources API（工具调用）** | ❌ 不调用 | ✅ 可通过工具调用获取 |
| **Resources API（主动调用）** | ❌ 不调用 | ❌ 不主动调用 |
| **Prompts API（工具调用）** | ❌ 不调用 | ✅ 可通过工具调用获取 |
| **Prompts API（主动调用）** | ❌ 不调用 | ❌ 不主动调用 |

---

## 总结

阶跃桌面助手在 stdio 模式下：

1. **基础 Tools API 完全正常**，所有 7 个工具均可成功调用并返回结果。
2. **Resources 和 Prompts API** 被封装为工具可按需调用，但不会在初始化时主动调用。
3. **服务端通知** 的接收情况无法从 AI 侧明确确认，UI 层面未见实时进度展示。
4. **Sampling 回调** 不被支持，服务端发送的 `sampling/createMessage` 请求未得到客户端响应。
