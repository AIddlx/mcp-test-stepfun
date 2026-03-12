# MCP 综合能力测试指南

## 测试目的

本测试用于验证阶跃桌面助手对 MCP 协议的各项支持能力，包括：
- 工具调用（Tools）
- 资源读取（Resources）
- 提示模板（Prompts）
- 错误处理
- 复杂参数
- 认证机制

---

## 测试环境

- **服务器地址**: `http://127.0.0.1:3370/mcp`
- **认证Token**: `test-token-comprehensive`
- **协议版本**: `2024-11-05`

---

## 测试清单

请按顺序执行以下测试，并记录结果。

### 测试 1：基础连通性

**工具**: `ping`

**测试步骤**:
1. 调用 `ping` 工具（无需参数）
2. 检查返回结果

**预期结果**:
```json
{
  "success": true,
  "message": "pong",
  "timestamp": "2026-03-09T..."
}
```

**通过条件**: 返回 `success: true` 且包含 `pong` 消息

---

### 测试 2：大响应处理

**工具**: `get_large_data`

**测试步骤**:
1. 调用 `get_large_data`，参数 `count: 100`
2. 调用 `get_large_data`，参数 `count: 1000`
3. 观察是否能正确处理大量数据

**预期结果**:
```json
{
  "success": true,
  "count": 100,
  "total_items": 100,
  "note": "Generated 100 items, showing first 5"
}
```

**通过条件**: 能正确返回并显示数据摘要

---

### 测试 3：分页功能

**工具**: `list_items`

**测试步骤**:
1. 调用 `list_items`，参数 `page: 1`, `page_size: 5`
2. 检查返回的 `pagination` 字段
3. 使用返回的 `next_cursor` 获取下一页

**预期结果**:
```json
{
  "success": true,
  "items": [{"id": 0, "name": "Item 0"}, ...],
  "pagination": {
    "page": 1,
    "page_size": 5,
    "total": 100,
    "has_more": true,
    "next_cursor": "5"
  }
}
```

**通过条件**: 返回正确分页信息，`has_more` 为 true

---

### 测试 4：批量操作

**工具**: `batch_execute`

**测试步骤**:
1. 调用 `batch_execute`，参数：
```json
{
  "operations": [
    {"action": "double", "value": 10},
    {"action": "double", "value": 20},
    {"action": "copy", "value": 5}
  ]
}
```

**预期结果**:
```json
{
  "success": true,
  "executed": 3,
  "results": [
    {"action": "double", "input": 10, "result": 20},
    {"action": "double", "input": 20, "result": 40},
    {"action": "copy", "input": 5, "result": 5}
  ]
}
```

**通过条件**: 正确执行所有操作，返回 3 个结果

---

### 测试 5：超时测试

**工具**: `slow_operation`

**测试步骤**:
1. 调用 `slow_operation`，参数 `delay_seconds: 3`
2. 观察阶跃是否等待完成
3. 如果超时，记录错误信息

**预期结果**:
```json
{
  "success": true,
  "message": "Waited 3 seconds",
  "delay": 3
}
```

**通过条件**: 3 秒后返回成功结果

**注意**: 如果阶跃有超时限制（如 30 秒），测试 `delay_seconds: 5` 应该也能通过

---

### 测试 6：错误恢复

**工具**: `flaky_operation`

**测试步骤**:
1. 调用 `flaky_operation`，参数 `success_rate: 0.3`
2. 如果失败，观察阶跃是否会重试
3. 记录重试行为

**预期结果（成功时）**:
```json
{
  "success": true,
  "message": "Operation succeeded",
  "rate": 0.3
}
```

**预期结果（失败时）**:
```json
{
  "success": false,
  "error": "Random failure occurred",
  "hint": "Try again, or increase success_rate"
}
```

**通过条件**: 阶跃能正确处理失败，最好能自动重试

---

### 测试 7：复杂参数类型

**工具**: `complex_params`

**测试步骤**:
1. 调用 `complex_params`，参数：
```json
{
  "config": {
    "name": "test-config",
    "options": ["opt1", "opt2", "opt3"],
    "settings": {
      "enabled": true,
      "mode": "auto"
    }
  },
  "tags": ["tag1", "tag2"]
}
```

**预期结果**:
```json
{
  "success": true,
  "received": {
    "config": {...},
    "tags": ["tag1", "tag2"]
  },
  "summary": {
    "config_name": "test-config",
    "options_count": 3,
    "tags_count": 2
  }
}
```

**通过条件**: 正确解析嵌套对象和数组

---

### 测试 8：认证检查

**工具**: `check_auth`

**测试步骤**:
1. 调用 `check_auth` 工具
2. 检查返回的认证信息

**预期结果**:
```json
{
  "success": true,
  "auth_received": true,
  "auth_header": "Bearer test-token-compre...",
  "valid": true
}
```

**通过条件**: `valid: true` 表示认证头正确传递

---

### 测试 9：协议信息

**工具**: `get_protocol_info`

**测试步骤**:
1. 调用 `get_protocol_info` 工具
2. 检查返回的协议版本和能力

**预期结果**:
```json
{
  "success": true,
  "protocol_version": "2024-11-05",
  "capabilities": {
    "tools": {"listChanged": false},
    "resources": {"subscribe": true},
    "prompts": {"listChanged": false}
  },
  "server_info": {
    "name": "mcp-comprehensive-test",
    "version": "1.0.0"
  }
}
```

**通过条件**: 返回正确的协议版本和能力声明

---

### 测试 10：Unicode/特殊字符

**工具**: `unicode_test`

**测试步骤**:
1. 调用 `unicode_test`，默认参数
2. 调用 `unicode_test`，参数 `text: "你好世界 🎉 مرحبا こんにちは"`
3. 调用 `unicode_test`，参数包含特殊字符：换行符、制表符、引号

**预期结果**:
```json
{
  "success": true,
  "echo": "你好世界 🎉 مرحبا こんにちは",
  "length": 20,
  "has_emoji": true,
  "has_chinese": true,
  "has_arabic": true
}
```

**通过条件**: Unicode 字符正确返回，Emoji 正确识别

---

### 测试 11：错误码处理

**工具**: `error_test`

**测试步骤**:
1. 调用 `error_test`，参数 `error_type: "invalid_params"`
2. 调用 `error_test`，参数 `error_type: "not_found"`
3. 调用 `error_test`，参数 `error_type: "internal_error"`
4. 调用 `error_test`，参数 `error_type: "unauthorized"`

**预期结果**（每种类型返回对应错误）:
```json
{
  "success": false,
  "error": "Invalid parameters: ...",
  "error_code": "invalid_params",
  "mcp_error_code": -32602
}
```

**通过条件**: 阶跃能正确处理各种错误码

---

### 测试 12：参数验证

**工具**: `validate_params`

**测试步骤**:
1. 调用 `validate_params`，参数 `required_string: "test"`（正常）
2. 调用 `validate_params`，参数 `range_value: 150`（超出范围，应报错）
3. 调用 `validate_params`，参数 `range_value: 50`（正常）
4. 调用 `validate_params`，不提供 `required_string`（缺少必需参数，应报错）

**预期结果（正常时）**:
```json
{
  "success": true,
  "received": {
    "required_string": "test",
    "optional_number": 42,
    "range_value": 50
  },
  "validation": "passed"
}
```

**预期结果（错误时）**:
```json
{
  "success": false,
  "error": "range_value must be between 1 and 100, got 150"
}
```

**通过条件**: 参数验证正确执行，错误信息清晰

---

### 测试 13：并发测试

**工具**: `concurrent_test`

**测试步骤**:
1. 同时发起多个 `concurrent_test` 请求：
   - `request_id: "req-1"`, `processing_time_ms: 200`
   - `request_id: "req-2"`, `processing_time_ms: 100`
   - `request_id: "req-3"`, `processing_time_ms: 150`
2. 观察响应顺序和正确性

**预期结果**（每个请求独立返回）:
```json
{
  "success": true,
  "request_id": "req-1",
  "processing_time_ms": 200,
  "actual_time_ms": 201,
  "thread_id": 12345
}
```

**通过条件**: 所有请求正确返回，处理时间准确

---

### 测试 14：长超时测试

**工具**: `long_operation`

**测试步骤**:
1. 调用 `long_operation`，参数 `delay_seconds: 10`
2. 观察阶跃是否有超时限制

**预期结果**:
```json
{
  "success": true,
  "message": "Long operation completed after 10 seconds",
  "delay": 10,
  "elapsed_ms": 10023
}
```

**通过条件**: 10秒延迟无超时

**注意**: 如果阶跃有超时限制，记录超时时间和行为

---

## Resources 测试

### 测试 R1：列出资源

**方法**: `resources/list`

**预期结果**:
```json
{
  "resources": [
    {"uri": "config://server", "name": "Server Configuration", ...},
    {"uri": "file://test.txt", "name": "Test Text File", ...},
    {"uri": "data://sample", "name": "Sample Data", ...}
  ]
}
```

**通过条件**: 返回 3 个资源

---

### 测试 R2：读取资源

**方法**: `resources/read`

**测试步骤**:
1. 读取 `config://server`
2. 读取 `file://test.txt`
3. 读取 `data://sample`

**预期结果**: 返回对应资源的文本内容

**通过条件**: 能正确读取所有资源

---

## Prompts 测试

### 测试 P1：列出提示模板

**方法**: `prompts/list`

**预期结果**:
```json
{
  "prompts": [
    {"name": "analyze_data", "description": "Analyze data with specified format", ...},
    {"name": "summarize", "description": "Summarize the content", ...}
  ]
}
```

**通过条件**: 返回 2 个提示模板

---

### 测试 P2：获取提示模板

**方法**: `prompts/get`

**测试步骤**:
1. 获取 `analyze_data` 提示，参数 `format: "json"`
2. 获取 `summarize` 提示

**预期结果**: 返回包含 messages 的提示内容

**通过条件**: 能正确获取提示模板

---

## 测试结果汇总表

| 编号 | 测试项 | 状态 | 备注 |
|------|--------|------|------|
| 1 | ping | ⬜待测 | |
| 2 | get_large_data | ⬜ 待测 | |
| 3 | list_items | ⬜ 待测 | |
| 4 | batch_execute | ⬜ 待测 | |
| 5 | slow_operation | ⬜ 待测 | |
| 6 | flaky_operation | ⬜ 待测 | |
| 7 | complex_params | ⬜ 待测 | |
| 8 | check_auth | ⬜ 待测 | |
| 9 | get_protocol_info | ⬜ 待测 | |
| 10 | unicode_test | ⬜ 待测 | 新增：Unicode/Emoji |
| 11 | error_test | ⬜ 待测 | 新增：错误码处理 |
| 12 | validate_params | ⬜ 待测 | 新增：参数验证 |
| 13 | concurrent_test | ⬜ 待测 | 新增：并发测试 |
| 14 | long_operation | ⬜ 待测 | 新增：长超时(10-60s) |
| R1 | resources/list | ⬜ 待测 | |
| R2 | resources/read | ⬜ 待测 | |
| P1 | prompts/list | ⬜ 待测 | |
| P2 | prompts/get | ⬜ 待测 | |

---

## 测试完成后

请填写测试结果汇总表，并记录：
1. 哪些功能正常工作
2. 哪些功能有问题
3. 阶跃的行为特点（如重试策略、超时处理等）
4. 对 scrcpy-py-ddlx 项目的建议
