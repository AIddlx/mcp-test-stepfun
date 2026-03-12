# HTTP URL 模式 - 测试指南

> **操作系统**: Windows 11 Pro 10.0.26200
> **传输模式**: HTTP URL (Streamable HTTP)
> **协议版本**: MCP 2025-11-25
> **测试客户端**: 阶跃桌面助手 v0.2.13

## 测试工具列表 (31个)

### A 类 - 核心能力

| 工具 | 说明 |
|------|------|
| `test_ping` | 连通性测试 |
| `test_protocol_version` | 协议版本协商 |
| `test_capabilities` | 能力声明 |
| `test_tool_call` | 工具调用基础 |
| `test_all_types` | 类型系统（8种类型验证） |

### B 类 - 重要能力

| 工具 | 说明 |
|------|------|
| `test_complex_params` | 复杂参数（嵌套对象、数组、枚举） |
| `test_large_data` | 大数据传输 |
| `test_long_operation` | 长时间操作（支持进度通知） |
| `test_concurrent` | 并发请求 |
| `test_unicode` | Unicode/中文支持 |
| `test_error_codes` | 错误处理 |

### C 类 - 高级能力

| 工具 | 说明 |
|------|------|
| `test_progress_notification` | 进度通知 |
| `test_cancellation` | 请求取消 |
| `test_sampling` | LLM Sampling |
| `test_batch_request` | 批量请求 |
| `test_completion` | 自动补全 |

### D 类 - 边界条件

| 工具 | 说明 |
|------|------|
| `test_empty_params` | 空参数 |
| `test_long_string` | 超长字符串 |
| `test_special_chars` | 特殊字符 |
| `test_idempotency` | 幂等性 |
| `test_rapid_fire` | 快速请求 |
| `test_empty_values` | 空值处理 |
| `test_deep_nesting` | 深层嵌套 |
| `test_large_array` | 大数组 |

### E 类 - 极端条件

| 工具 | 说明 |
|------|------|
| `test_timeout_boundary` | 超时边界 |

### G 类 - GUI Agent

| 工具 | 说明 |
|------|------|
| `gui_desktop_info` | 获取桌面信息 |
| `gui_take_screenshot` | 截图 |
| `gui_mouse_click` | 鼠标点击 |
| `gui_mouse_move` | 鼠标移动 |
| `gui_keyboard_input` | 键盘输入 |
| `gui_send_message` | 发送消息（多步操作） |
| `gui_automation_demo` | 自动化演示 |

### H/I 类 - 新特性 (2025-11-25)

| 工具 | 说明 |
|------|------|
| `test_elicitation_form` | 表单式 Elicitation |
| `test_elicitation_url` | URL 式 Elicitation |
| `test_sampling_basic` | 基础 Sampling |
| `test_sampling_with_tools` | 带工具的 Sampling |
| `test_server_elicitation` | 服务端发起 Elicitation |
| `test_server_sampling` | 服务端发起 Sampling |

---

## MCP 方法支持

### Tools
- `tools/list` - 工具列表（支持分页）
- `tools/call` - 工具调用（支持任务模式）

### Resources
- `resources/list` - 资源列表
- `resources/read` - 读取资源
- `resources/subscribe` - 订阅资源更新
- `resources/unsubscribe` - 取消订阅
- `resources/templates/list` - 资源模板

### Prompts
- `prompts/list` - 提示词列表
- `prompts/get` - 获取提示词

### 其他
- `ping` - 心跳
- `logging/setLevel` - 日志级别设置
- `completion/complete` - 自动补全

---

## 服务器能力

```json
{
  "protocolVersion": "2025-11-25",
  "capabilities": {
    "tools": { "listChanged": true, "sublist": true },
    "resources": { "subscribe": true, "listChanged": true },
    "prompts": { "listChanged": true },
    "logging": {}
  }
}
```

---

## 测试指令示例

### 基础测试
```
请调用 test_ping 工具测试连接
```

### 类型验证
```
请调用 test_all_types 工具，传入各种类型的参数
```

### 并发测试
```
请同时调用 test_ping 和 test_protocol_version 工具
```

### 错误处理
```
请调用 test_error_codes 工具，测试各种错误码
```
