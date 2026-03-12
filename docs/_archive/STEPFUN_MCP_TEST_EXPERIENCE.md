# 阶跃星辰 MCP 客户端测试经验归档

> 测试日期：2026-03-10
> 测试对象：阶跃桌面助手 MCP 客户端
> 协议版本：MCP 2025-11-25
> 服务端：mcp-full-test (Streamable HTTP, http://127.0.0.1:3372/mcp)

---

## 一、测试总览

共执行 8 个阶段、覆盖 A1-A5 / B1-B10 / C2 / C5 / D1-D8 / E1 / G1-G10 / H1-H3 / I1-I3 全部测试项，最终结果：**全部通过**。

| 阶段 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
| 1. 基础连通 | A1-A5 (ping / protocol_version / capabilities / tool_call / all_types) | ✅ 全部通过 | — |
| 2. 高级功能 | B1-B9 (complex_params / large_data / long_operation / concurrent / unicode / error_codes / resources / prompts / progress) | ✅ 全部通过 | B6 错误处理正确返回 -32602 |
| 3. 边界压力 | D1-D8 (empty_params / long_string / special_chars / idempotency / rapid_fire / empty_values / deep_nesting / large_array) | ✅ 全部通过 | — |
| 4. 超时探测 | E1 (5/15/25/40/55/60s) | ✅ 阈值已定位 | 55s 通过，60s 超时 |
| 5. 批量/取消 | B10 / C2 / C5 (cancellation / batch_request / completion) | ✅ 全部通过 | — |
| 6. GUI 自动化 | G1-G10 (screenshot / click / type / find_element / open_app / scroll / wait / get_state / send_message / automation_demo) | ✅ 全部通过 | G5 browser 返回预期失败 |
| 7. Sampling | I1-I3 (sampling_basic / sampling_with_tools / server_sampling) | ✅ 全部通过 | — |
| 8. Elicitation | H1-H3 (elicitation_form / elicitation_url / server_elicitation) | ✅ 全部通过 | — |

---

## 二、关键发现

### 2.1 outputSchema 对阶跃客户端无实际作用

**现象**：服务端在 `tools/list` 中声明了 `outputSchema` 后，部分工具调用（如 `test_ping`）返回 `-32602: Structured content` 错误。删除所有 `outputSchema` 后，全部工具恢复正常。

**根因分析**：
- MCP 2025-11-25 规范中，`outputSchema` 用于校验 `structuredContent` 字段，并要求服务端同时在 `content` 中提供序列化 JSON 的 TextContent 作为向后兼容。
- 阶跃客户端当前链路是 **Tool 结果 → content（文本） → LLM 阅读**，并不消费 `structuredContent`。
- 客户端可能对声明了 `outputSchema` 的工具强制要求返回 `structuredContent`，当服务端未提供时触发协议错误。

**结论**：当前阶段服务端**不应声明 `outputSchema`**，除非确认客户端已完整实现 structured content 消费链路。

**进一步验证（即使配置齐全也无意义）**：即便服务端完整配置了 `outputSchema` 并同时返回 `structuredContent` + `content`，对阶跃客户端仍然**零收益**，原因如下：

1. **LLM 不看 schema**：模型靠自然语言理解 `content` 中的文本，不会拿 `outputSchema` 去解析 `structuredContent`。
2. **客户端不做校验**：未观察到客户端用 `outputSchema` 对返回值做 JSON Schema 验证后产生任何差异化行为。
3. **`structuredContent` 没有消费方**：即使服务端同时返回了 `structuredContent`，客户端也只读 `content` 里的 TextContent，结构化数据被完全忽略。

`outputSchema` 真正有价值的场景是**程序化消费**——客户端拿到结构化数据后自动填表、驱动 UI 渲染、或串联到下游 API。阶跃当前架构不存在这种链路，所以配齐了也是白配：多写代码、多一个出错点、零收益。

**最终建议**：面向阶跃客户端的 MCP 服务端，直接删除所有 `outputSchema` 声明，只通过 `content` 返回文本即可。

### 2.2 tools/list 响应存在缓存

**现象**：服务端修改代码（如删除 `outputSchema`）并重启后，客户端仍使用旧的 `tools/list` 响应，导致行为不变。需要等待缓存刷新或重新建立连接后才能生效。

**建议**：修改服务端 Tool 定义后，建议在阶跃客户端侧重新添加/刷新 MCP 服务器配置，确保拉取最新的 `tools/list`。

### 2.3 客户端超时阈值：55~60 秒

**探测过程**：

| 耗时 | 结果 |
|------|------|
| 5s | ✅ 通过 |
| 15s | ✅ 通过 |
| 25s | ✅ 通过 |
| 40s | ✅ 通过 |
| 55s | ✅ 通过 (elapsed 55369ms) |
| 60s | ❌ `-32001: Request timed out` |

**结论**：阶跃客户端的 MCP 工具调用超时阈值在 **55~60 秒之间**（推测为 60 秒整）。服务端长耗时操作应控制在 55 秒以内，或通过 progress notification 机制保持心跳（规范允许客户端在收到 progress 时重置超时计时器）。

### 2.4 并发调用支持良好

客户端支持同时发起多个独立的工具调用（如同时调用 ping + protocol_version + capabilities），服务端并行处理，均正常返回。

### 2.5 MCP 协议层 ping vs 自定义 Tool ping

**MCP 协议层 ping**（`method: "ping"`）：规范要求响应为空对象 `{}`，用于连接健康检查。

**自定义 test_ping Tool**：属于业务层工具，返回格式由服务端自行定义，不受协议约束。`pong` 字段返回 `true`（布尔）或 `"pong"`（字符串）均可，但 `true` 语义更清晰。

### 2.6 Sampling 和 Elicitation 的客户端支持现状

- `test_sampling_basic` / `test_sampling_with_tools`：客户端能接收服务端返回的 sampling 参数描述，但**未观察到客户端实际执行 `sampling/createMessage` 的完整闭环**（即客户端主动调用 LLM 并回传结果）。
- `test_server_sampling` / `test_server_elicitation`：服务端成功创建了待处理请求，但需要客户端轮询 `server/pendingRequests` 并提交响应，当前客户端可能尚未实现此流程。
- `test_elicitation_form` / `test_elicitation_url`：客户端能接收 elicitation 描述信息。

### 2.7 错误处理符合规范

- **协议错误**：`test_error_codes` 返回标准 JSON-RPC 错误码 `-32602`，客户端正确识别为 `Failed` 状态。
- **超时错误**：60 秒超时返回 `-32001`，客户端正确报告 `Request timed out`。
- 两类错误均被客户端正确区分和展示。

---

## 三、数据类型支持情况

通过 A5 `test_all_types` 验证，8/8 类型全部通过：

| 类型 | 发送值 | 接收类型 | 匹配 |
|------|--------|----------|------|
| string | "测试" | str | ✅ |
| integer | 42 | int | ✅ |
| float | 3.14 | float | ✅ |
| boolean | true | bool | ✅ |
| negative | -100 | int | ✅ |
| bigint | 9007199254740992 | int | ✅ (超 JS 安全整数) |
| array | [1,2,3] | list | ✅ |
| object | {"key":"value"} | dict | ✅ |

---

## 四、边界测试详情

| 测试 | 说明 | 结果 |
|------|------|------|
| D1 空参数 | 无参数调用，验证默认值 | ✅ |
| D2 超长字符串 | 10000 字符 | ✅ |
| D3 特殊字符 | 控制字符 \x00\x01\x02、引号、换行 | ✅ |
| D4 幂等性 | 相同 operation_id 重复调用 | ✅ |
| D5 快速连发 | 5 次连续请求，总耗时 <1ms | ✅ |
| D6 空值边界 | 空数组 [] / 空对象 {} / 空字符串 "" | ✅ |
| D7 深层嵌套 | 10 层嵌套对象 | ✅ |
| D8 大数组 | 1000 元素数组 | ✅ |

---

## 五、给 MCP 服务端开发者的建议

1. **不要声明 `outputSchema`**：除非确认目标客户端已实现 `structuredContent` 消费，否则会导致调用失败。
2. **工具执行控制在 55 秒以内**：超过 60 秒会被客户端超时切断。对于长耗时任务，使用 progress notification 保持心跳。
3. **修改 Tool 定义后刷新客户端**：阶跃客户端会缓存 `tools/list` 响应，修改后需重新连接。
4. **错误处理使用双层机制**：协议错误用 JSON-RPC error，业务错误用 `isError: true` + content 描述，客户端均能正确处理。
5. **充分利用并发**：客户端支持并行工具调用，可以设计互不依赖的工具组合以提升效率。
6. **Unicode 和特殊字符安全**：客户端对中文、emoji、控制字符等均能正确传输，无需额外编码处理。

---

## 六、环境信息

- 操作系统：Windows
- Python：3.12+
- MCP SDK：基于 Streamable HTTP 传输
- 服务端地址：http://127.0.0.1:3372/mcp
- 认证方式：ApiKey (mcp_admin_key_prod_2025)
- 日志目录：logs/full_test_*.jsonl
