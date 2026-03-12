# NPX 模式 - 测试指南

> **操作系统**: Windows 11 Pro 10.0.26200
> **传输模式**: stdio (标准输入输出)
> **协议版本**: MCP 2025-11-25
> **测试客户端**: 阶跃桌面助手

## 一、测试工具列表 (35个)

### A 类 - 核心能力（5个）

| 工具 | 说明 | 测试指令 |
|------|------|----------|
| `test_ping` | 连通性测试 | `请调用 test_ping` |
| `test_protocol_version` | 协议版本协商 | `请调用 test_protocol_version` |
| `test_capabilities` | 能力声明 | `请调用 test_capabilities` |
| `test_tool_call` | 工具调用基础 | `请调用 test_tool_call，input_value 设为 "hello"` |
| `test_all_types` | 全类型验证 | `请调用 test_all_types，传入各种类型参数` |

### B 类 - 重要能力（6个）

| 工具 | 说明 | 测试指令 |
|------|------|----------|
| `test_complex_params` | 复杂参数 | `请调用 test_complex_params` |
| `test_large_data` | 大数据传输 | `请调用 test_large_data，size_kb 设为 10` |
| `test_long_operation` | 长时间操作 | `请调用 test_long_operation，duration_seconds 设为 3` |
| `test_concurrent` | 并发请求 | `请调用 test_concurrent` |
| `test_unicode` | Unicode 支持 | `请调用 test_unicode，text 设为 "你好世界 🌍"` |
| `test_error_codes` | 错误处理 | `请调用 test_error_codes，error_type 设为 "invalid_params"` |

### C 类 - 高级能力（4个）

| 工具 | 说明 | 测试指令 |
|------|------|----------|
| `test_progress_notification` | 进度通知 | `请调用 test_progress_notification` |
| `test_cancellation` | 请求取消 | `请调用 test_cancellation` |
| `test_batch_request` | 批量请求 | `请调用 test_batch_request` |
| `test_completion` | 自动补全 | `请调用 test_completion，partial_value 设为 "test"` |

### D 类 - 边界条件（9个）

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

### E 类 - 极端条件（1个）

| 工具 | 说明 |
|------|------|
| `test_timeout_boundary` | 超时边界 |

### G 类 - GUI Agent（7个）

| 工具 | 说明 |
|------|------|
| `gui_desktop_info` | 获取桌面信息 |
| `gui_take_screenshot` | 截图 |
| `gui_mouse_click` | 鼠标点击 |
| `gui_mouse_move` | 鼠标移动 |
| `gui_keyboard_input` | 键盘输入 |
| `gui_send_message` | 发送消息 |
| `gui_automation_demo` | 自动化演示 |

### H/I 类 - 新特性（4个）

| 工具 | 说明 |
|------|------|
| `test_elicitation_form` | 表单式 Elicitation |
| `test_elicitation_url` | URL 式 Elicitation |
| `test_sampling_basic` | 基础 Sampling |
| `test_sampling_with_tools` | 带工具的 Sampling |

## 二、日志说明

### 2.1 日志位置

NPX 模式的日志写入文件，不干扰 stdio 通信：

```
npx/logs/mcp-stdio-YYYYMMDD.log
```

### 2.2 查看日志

```bash
# 查看最新日志
cat npx/logs/mcp-stdio-*.log | tail -50

# 实时监控（ PowerShell）
Get-Content npx/logs/mcp-stdio-*.log -Wait
```

### 2.3 日志级别

通过环境变量设置：
```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "mcp-npx-test"],
      "env": {
        "MCP_LOG_LEVEL": "debug"
      }
    }
  }
}
```

## 三、与 HTTP URL 模式对比

| 测试项 | NPX 结果 | HTTP URL 结果 | 说明 |
|--------|----------|---------------|------|
| 工具数量 | 35个 | 35个 | 相同 |
| 传输方式 | stdio | HTTP | 不同 |
| 认证 | 不需要 | 需要 | 不同 |
| 进度通知 | ⚠️ 待测 | ⚠️ 有限 | 需验证 |

## 四、测试建议

1. **先测试 A 类**：确认基础功能正常
2. **再测试 B 类**：验证数据处理能力
3. **最后测试高级功能**：进度通知、取消等

## 五、测试命令示例

```
=== 基础测试 ===
请调用 test_ping 工具

=== 类型测试 ===
请调用 test_all_types 工具，设置：
- string_value: "测试字符串"
- integer_value: 42
- float_value: 3.14
- boolean_value: true
- array_value: [1, 2, 3]

=== 中文测试 ===
请调用 test_unicode 工具，text 设为 "你好，世界！🎉"

=== 错误测试 ===
请调用 test_error_codes 工具，error_type 设为 "not_found"
```
