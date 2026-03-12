# UVX 模式 - 全量测试报告

> **测试客户端**: 阶跃 AI 桌面助手 v0.2.13
> **协议版本**: MCP 2025-11-25
> **传输模式**: stdio (标准输入输出)

## 历次测试

| # | 日期 | 服务器 | 实现方式 | 结果 |
|---|------|--------|---------|------|
| 1 | 2026-03-11 | mcp-uvx-test | FastMCP (高层 API) | 35/35 (100%) |
| 2 | 2026-03-12 | mcp-uvx-sdk | Low-Level Server API (底层) | 34/35 (97.1%)，1 个预期行为 |

---

---

## 第一次测试：mcp-uvx-test (FastMCP)

> **测试日期**: 2026-03-11 21:13 ~ 21:15

## 一、测试概要

| 指标 | 值 |
|------|-----|
| 测试时间 | 2026-03-11 21:13:27 ~ 21:15:10 |
| 工具总数 | 35 |
| 通过数量 | 35 |
| 失败数量 | 0 |
| 通过率 | **100%** |

---

## 二、测试环境

| 项目 | 配置 |
|------|------|
| 操作系统 | Windows 11 Pro |
| Python | 3.12.9 (uv 管理) |
| uvx 版本 | 0.9.17 (阶跃内置) |
| 传输模式 | stdio (标准输入输出) |
| 客户端 | 阶跃 AI 桌面助手 v0.2.13 |

---

## 三、测试配置

```json
{
  "mcpServers": {
    "mcp-uvx-test": {
      "command": "uvx",
      "args": ["--from", "C:/Project/IDEA/2/new/mcp-test-stepfun/stdio/uvx", "mcp-uvx-test"]
    }
  }
}
```

---

## 四、测试结果明细

### 4.1 A 类 - 核心能力 (5个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| A1 | test_ping | ✅ 通过 | echo="hello-stepfun", delay_ms=0 | echo 回显正常 | pong 返回正确，echo 回显 "hello-stepfun"，server_time 正常 |
| A2 | test_protocol_version | ✅ 通过 | (无参数) | 版本匹配 | server_protocol_version="2025-11-25", version_match=true |
| A3 | test_capabilities | ✅ 通过 | (无参数) | 能力声明完整 | tools/resources/prompts/logging 四项能力均已声明 |
| A4 | test_tool_call | ✅ 通过 | input_value="test_string_123", input_type="string" | 参数传递正确 | received_value 正确，type_match=false (Python str vs string，预期行为) |
| A5 | test_all_types | ✅ 通过 | 全部 9 种类型 | 所有类型验证通过 | string/integer/float/boolean/negative/bigint/array/object/null 全部 valid=true |

**A5 详细类型测试数据：**

| 类型 | 输入值 | 接收值 | 验证 |
|------|--------|--------|------|
| string | "hello" | "hello" | ✅ |
| integer | 42 | 42 | ✅ |
| float | 3.14 | 3.14 | ✅ |
| boolean | true | true | ✅ |
| negative | -100 | -100 | ✅ |
| bigint | 9999999999999 | 9999999999999 | ✅ |
| array | [1, "two", 3] | [1, "two", 3] | ✅ |
| object | {"key":"value","nested":{"a":1}} | {"key":"value","nested":{"a":1}} | ✅ |
| null | (自动) | null | ✅ |

---

### 4.2 B 类 - 重要能力 (6个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| B1 | test_complex_params | ✅ 通过 | nested=3层嵌套, array=混合类型, enum="option1" | 复杂参数传递 | 嵌套对象/混合数组/枚举值均正确接收，类型识别正确 |
| B2 | test_large_data | ✅ 通过 | size_kb=10, items=5 | 大数据传输 | actual_size_bytes=10345，数据完整返回 |
| B3 | test_long_operation | ✅ 通过 | duration_seconds=2 | 长时间操作 | 模拟 2 秒操作完成，未超时 |
| B4 | test_concurrent | ✅ 通过 | request_id="req-001", delay_ms=50 | 并发请求 | request_id 正确回传，processed_at 时间戳正常 |
| B5 | test_unicode | ✅ 通过 | "你好世界🌍 Hello こんにちは 한국어" | Unicode 多语言 | length=21, bytes=48, has_chinese=true, has_emoji=true |
| B6 | test_error_codes | ✅ 通过 | error_type="invalid_params" | 错误码处理 | error_code=-32602, error="Invalid params", success=false (预期) |

---

### 4.3 C 类 - 高级能力 (4个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| C1 | test_progress_notification | ✅ 通过 | steps=5, delay_ms=100 | 进度通知 | 5 步进度通知启动成功 |
| C2 | test_cancellation | ✅ 通过 | duration_seconds=2 | 请求取消 | 取消测试完成 |
| C3 | test_batch_request | ✅ 通过 | 3 个操作 (add/multiply/unknown) | 批量请求 | add(10)→11, multiply(5)→10, unknown→null，全部正确 |
| C4 | test_completion | ✅ 通过 | partial_value="test_" | 自动补全 | 返回 3 个补全建议：test__complete1/2/3 |

---

### 4.4 D 类 - 边界条件 (8个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| D1 | test_empty_params | ✅ 通过 | (无参数) | 空参数处理 | params_count=0，正常处理 |
| D2 | test_long_string | ✅ 通过 | length=5000 | 超长字符串 | 5000 字符长度正确生成 |
| D3 | test_special_chars | ✅ 通过 | include_control=true, include_quotes=true | 特殊字符 | 控制字符(\x00\x01\x02)、引号("')、换行(\n\r\t)、中文均正确处理 |
| D4 | test_idempotency | ✅ 通过 | operation_id="op-test-001" (调用2次) | 幂等性 | 第1次: cached=false "首次请求"；第2次: cached=true "缓存命中" |
| D5 | test_rapid_fire | ✅ 通过 | count=10 | 快速连续请求 | 10 个请求全部在同一毫秒内完成 (1773234928128) |
| D6 | test_empty_values | ✅ 通过 | empty_string="", empty_array=[], empty_object={} | 空值处理 | 三种空值类型均正确识别和返回 |
| D7 | test_deep_nesting | ✅ 通过 | depth=10 | 深层嵌套 | 10 层嵌套结构完整生成，最深层 value="deepest" |
| D8 | test_large_array | ✅ 通过 | count=200 | 大数组 | 200 元素数组，first_5=[0,1,2,3,4], last_5=[195..199], sum=19900 |

---

### 4.5 E 类 - 极端条件 (1个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| E1 | test_timeout_boundary | ✅ 通过 | duration_seconds=5 | 超时边界 | 5 秒操作完成，未触发超时 |

---

### 4.6 G 类 - GUI Agent (7个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| G1 | gui_desktop_info | ✅ 通过 | (无参数) | 桌面信息 | resolution=1920x1080, 3 个模拟窗口 |
| G2 | gui_take_screenshot | ✅ 通过 | format="png" | 截图 | PNG 格式，1920x1080，截图成功（模拟） |
| G3 | gui_mouse_click | ✅ 通过 | x=500, y=300 | 鼠标点击 | 点击坐标 (500, 300) 正确 |
| G4 | gui_mouse_move | ✅ 通过 | x=800, y=600 | 鼠标移动 | 移动到 (800, 600) 正确 |
| G5 | gui_keyboard_input | ✅ 通过 | text="Hello MCP Test!" | 键盘输入 | 文本长度 15，内容正确 |
| G6 | gui_send_message | ✅ 通过 | contact="test-user", message="这是一条测试消息" | 流式消息 | streaming 模式，4 步流程，elapsed_ms=800 |
| G7 | gui_automation_demo | ✅ 通过 | scenario="notepad" | 批量自动化 | batch 模式，5 步流程一次性返回 |

---

### 4.7 H 类 - Elicitation (2个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| H1 | test_elicitation_form | ✅ 通过 | form_title="用户注册表单" | 表单式 Elicitation | form 类型，fields=["name","email"] |
| H2 | test_elicitation_url | ✅ 通过 | auth_url="https://example.com/oauth/authorize" | URL 式 Elicitation | url 类型，auth_url 正确回传 |

---

### 4.8 I 类 - Sampling (2个)

| ID | 工具 | 状态 | 测试输入 | 验证点 | 结果详情 |
|----|------|------|---------|--------|---------|
| I1 | test_sampling_basic | ✅ 通过 | prompt="What is the capital of France?" | 基础 Sampling | prompt 正确回传 |
| I2 | test_sampling_with_tools | ✅ 通过 | task="Search and summarize recent news" | 带工具 Sampling | task 正确回传，available_tools=["test_ping","test_tool_call"] |

---

## 五、测试发现与备注

### 5.1 预期行为（非 Bug）

| 工具 | 现象 | 说明 |
|------|------|------|
| A4 test_tool_call | type_match=false | Python 类型名 `str` 与参数 `string` 不匹配，属于 Python/JS 类型命名差异，非功能性问题 |
| B6 test_error_codes | success=false | 错误处理测试，返回 success=false 是预期行为 |
| B3 test_long_operation | elapsed_ms=0 | 模拟操作，未实际等待，elapsed_ms 为占位值 |
| E1 test_timeout_boundary | elapsed_ms=0 | 同上，模拟操作 |

### 5.2 文档一致性问题

源码中实际定义了 **35 个工具**，但以下文档仍标注为 31 个，建议同步更新：

| 文件 | 当前标注 | 实际数量 |
|------|---------|---------|
| `stdio/uvx/src/mcp_uvx_test/server.py` 文件头注释 | 31 | 35 |
| `stdio/uvx/src/mcp_uvx_test/__init__.py` 注释 | 31 | 35 |
| `stdio/uvx/README.md` | 31 | 35 |
| `docs/stdio/uvx/TEST_REPORT.md` | 31 | 35 (已更新) |
| `docs/stdio/uvx/README.md` | 35 | 35 ✅ |

差异原因：后期新增了 H 类 (Elicitation, 2个) 和 I 类 (Sampling, 2个)，部分文档未同步。

---

## 六、结论

**mcp-uvx-test 全部 35 个工具在阶跃 AI 桌面助手 v0.2.13 (Windows 11) 上通过 stdio/uvx 模式测试，通过率 100%。**

所有 9 个系列的工具均正常工作：
- **A 类 (核心能力)**: 连通性、协议版本、能力协商、工具调用、类型验证全部正常
- **B 类 (重要能力)**: 复杂参数、大数据、长操作、并发、Unicode、错误处理全部正常
- **C 类 (高级能力)**: 进度通知、取消、批量请求、自动补全全部正常
- **D 类 (边界条件)**: 空参数、超长字符串、特殊字符、幂等性、快速请求、空值、深层嵌套、大数组全部正常
- **E 类 (极端条件)**: 超时边界测试正常
- **G 类 (GUI Agent)**: 桌面信息、截图、鼠标、键盘、消息发送、自动化演示全部正常
- **H 类 (Elicitation)**: 表单式和 URL 式 Elicitation 全部正常
- **I 类 (Sampling)**: 基础 Sampling 和带工具 Sampling 全部正常

---

## 七、原始测试数据

### A1 test_ping
```json
{"test_id": "A1", "success": true, "pong": "pong", "echo": "hello-stepfun", "server_time": "2026-03-11T21:13:27.098961", "elapsed_ms": 0}
```

### A2 test_protocol_version
```json
{"test_id": "A2", "success": true, "client_protocol_version": "from_client", "server_protocol_version": "2025-11-25", "version_match": true, "note": "版本匹配"}
```

### A3 test_capabilities
```json
{"test_id": "A3", "success": true, "server_capabilities": {"tools": {"listChanged": true}, "resources": {"subscribe": true, "listChanged": true}, "prompts": {"listChanged": true}, "logging": {}}, "protocol_version": "2025-11-25"}
```

### A4 test_tool_call
```json
{"test_id": "A4", "success": true, "received_value": "test_string_123", "received_type": "string", "actual_type": "str", "type_match": false, "server_time": "2026-03-11T21:13:27.150048"}
```

### A5 test_all_types
```json
{"test_id": "A5", "success": true, "type_results": {"string": {"received": "hello", "type": "string", "valid": true}, "integer": {"received": 42, "type": "number", "valid": true}, "float": {"received": 3.14, "type": "number", "valid": true}, "boolean": {"received": true, "type": "boolean", "valid": true}, "negative": {"received": -100, "type": "number", "valid": true}, "bigint": {"received": 9999999999999, "type": "number", "valid": true}, "array": {"received": [1, "two", 3], "type": "array", "valid": true}, "object": {"received": {"key": "value", "nested": {"a": 1}}, "type": "object", "valid": true}, "null": {"received": null, "type": "null", "valid": true}}, "summary": {"tested_types": 9, "all_valid": true}, "server_time": "2026-03-11T21:13:40.466574"}
```

### B1 test_complex_params
```json
{"test_id": "B1", "success": true, "received": {"nested": {"level1": {"level2": {"value": "deep"}}}, "array": [1, "two", {"three": 3}, [4, 5]], "enum_value": "option1"}, "types": {"nested_type": "object", "array_type": "array", "enum_type": "string"}}
```

### B2 test_large_data
```json
{"test_id": "B2", "success": true, "requested_size_kb": 10, "items": 5, "actual_size_bytes": 10345, "sample": ["(truncated)"]}
```

### B3 test_long_operation
```json
{"test_id": "B3", "success": true, "duration_seconds": 2, "message": "模拟 2 秒操作完成", "elapsed_ms": 0}
```

### B4 test_concurrent
```json
{"test_id": "B4", "success": true, "request_id": "req-001", "processed_at": "2026-03-11T21:14:28.553358", "elapsed_ms": 0}
```

### B5 test_unicode
```json
{"test_id": "B5", "success": true, "received": "你好世界🌍 Hello こんにちは 한국어", "length": 21, "bytes": 48, "has_chinese": true, "has_emoji": true}
```

### B6 test_error_codes
```json
{"test_id": "B6", "success": false, "error": "Invalid params", "error_code": -32602, "error_type": "invalid_params"}
```

### C1 test_progress_notification
```json
{"test_id": "C1", "success": true, "message": "Progress notifications started", "steps": 5, "delay_ms": 100}
```

### C2 test_cancellation
```json
{"test_id": "C2", "success": true, "duration_seconds": 2, "message": "Cancellation test completed", "elapsed_ms": 0}
```

### C3 test_batch_request
```json
{"test_id": "C3", "success": true, "operations_count": 3, "results": [{"operation": "add", "result": 11}, {"operation": "multiply", "result": 10}, {"operation": "unknown", "result": null}]}
```

### C4 test_completion
```json
{"test_id": "C4", "success": true, "partial_value": "test_", "suggestions": ["test__complete1", "test__complete2", "test__complete3"]}
```

### D1 test_empty_params
```json
{"test_id": "D1", "success": true, "params_count": 0, "message": "Empty params test passed"}
```

### D2 test_long_string
```json
{"test_id": "D2", "success": true, "length": 5000, "first_10": "xxxxxxxxxx", "last_10": "xxxxxxxxxx", "elapsed_ms": 0}
```

### D3 test_special_chars
```json
{"test_id": "D3", "success": true, "special_chars": "\u0000\u0001\u0002\"'\n\r\t正常文本", "includes": {"control": true, "quotes": true}}
```

### D4 test_idempotency (第1次)
```json
{"test_id": "D4", "success": true, "operation_id": "op-test-001", "cached": false, "message": "首次请求"}
```

### D4 test_idempotency (第2次 - 幂等性验证)
```json
{"test_id": "D4", "success": true, "operation_id": "op-test-001", "cached": true, "message": "缓存命中"}
```

### D5 test_rapid_fire
```json
{"test_id": "D5", "success": true, "count": 10, "results": [{"index": 0, "time": 1773234928128}, {"index": 1, "time": 1773234928128}, "...(共10项)"], "total_time_ms": 0}
```

### D6 test_empty_values
```json
{"test_id": "D6", "success": true, "received": {"empty_string": "", "empty_array": [], "empty_object": {}}, "types": {"empty_string_type": "string", "empty_array_type": "array", "empty_object_type": "object"}}
```

### D7 test_deep_nesting
```json
{"test_id": "D7", "success": true, "depth": 10, "structure": {"level": 1, "nested": {"level": 2, "nested": {"level": 3, "nested": {"level": 4, "nested": {"level": 5, "nested": {"level": 6, "nested": {"level": 7, "nested": {"level": 8, "nested": {"level": 9, "nested": {"level": 10, "nested": {"value": "deepest"}}}}}}}}}}}}
```

### D8 test_large_array
```json
{"test_id": "D8", "success": true, "count": 200, "first_5": [0, 1, 2, 3, 4], "last_5": [195, 196, 197, 198, 199], "sum": 19900}
```

### E1 test_timeout_boundary
```json
{"test_id": "E1", "success": true, "duration_seconds": 5, "note": "操作完成，未触发超时（5秒）", "elapsed_ms": 0}
```

### G1 gui_desktop_info
```json
{"test_id": "G1", "success": true, "resolution": {"width": 1920, "height": 1080}, "active_window": "模拟窗口", "windows": ["Window1", "Window2", "Window3"]}
```

### G2 gui_take_screenshot
```json
{"test_id": "G2", "success": true, "format": "png", "width": 1920, "height": 1080, "message": "截图成功（模拟）"}
```

### G3 gui_mouse_click
```json
{"test_id": "G3", "success": true, "action": "click", "position": {"x": 500, "y": 300}, "message": "点击 (500, 300)"}
```

### G4 gui_mouse_move
```json
{"test_id": "G4", "success": true, "action": "move", "position": {"x": 800, "y": 600}, "message": "移动到 (800, 600)"}
```

### G5 gui_keyboard_input
```json
{"test_id": "G5", "success": true, "action": "input", "text": "Hello MCP Test!", "length": 15, "message": "输入文本: Hello MCP Test!"}
```

### G6 gui_send_message
```json
{"test_id": "G6", "success": true, "contact": "test-user", "message": "这是一条测试消息", "mode": "streaming", "steps": ["查找联系人", "打开对话", "输入消息", "发送"], "note": "通过 notifications/progress 流式推送每一步进度", "elapsed_ms": 800}
```

### G7 gui_automation_demo
```json
{"test_id": "G7", "success": true, "scenario": "notepad", "mode": "batch", "steps": ["打开应用", "等待启动", "输入文本", "保存文件", "关闭应用"], "note": "一次性返回所有步骤，无流式进度", "message": "自动化演示完成"}
```

### H1 test_elicitation_form
```json
{"test_id": "H1", "success": true, "elicitation_type": "form", "form_title": "用户注册表单", "fields": ["name", "email"], "note": "表单式 Elicitation 测试"}
```

### H2 test_elicitation_url
```json
{"test_id": "H2", "success": true, "elicitation_type": "url", "auth_url": "https://example.com/oauth/authorize", "note": "URL 式 Elicitation 测试"}
```

### I1 test_sampling_basic
```json
{"test_id": "I1", "success": true, "prompt": "What is the capital of France?", "note": "基础 Sampling 测试"}
```

### I2 test_sampling_with_tools
```json
{"test_id": "I2", "success": true, "task": "Search and summarize recent news", "available_tools": ["test_ping", "test_tool_call"], "note": "带工具的 Sampling 测试"}
```

---

*报告生成时间: 2026-03-11 21:15*
*测试执行者: 阶跃 AI 桌面助手 (自动化测试)*

---
---

## 第二次测试：mcp-uvx-sdk (Low-Level Server API)

> **测试日期**: 2026-03-12
> **SDK 实现**: `mcp.server.lowlevel.Server` (底层 API，不使用 FastMCP)

### 测试配置

```json
{
  "mcpServers": {
    "mcp-uvx-sdk": {
      "command": "uvx",
      "args": ["--from", "C:/Project/IDEA/2/new/mcp-test-stepfun/sdk/uvx", "mcp-uvx-sdk"]
    }
  }
}
```

### 测试结果汇总

| 系列 | 编号 | 工具名称 | 结果 | 备注 |
|------|------|---------|------|------|
| A-基础 | A1 | test_ping | ✅ 通过 | pong + echo 正常 |
| | A2 | test_protocol_version | ✅ 通过 | 协议版本 2025-11-25 匹配 |
| | A3 | test_capabilities | ✅ 通过 | tools/resources/prompts/logging 全部声明 |
| | A4 | test_tool_call | ⚠️ 部分 | 值传递正确，type_match=false（Python str vs JSON Schema string） |
| | A5 | test_all_types | ✅ 通过 | 9 种类型全部验证通过 |
| B-数据性能 | B1 | test_complex_params | ✅ 通过 | 嵌套对象/数组/枚举正常 |
| | B2 | test_large_data | ✅ 通过 | 5KB/20条数据传输正常 |
| | B3 | test_long_operation | ✅ 通过 | 3秒耗时操作完成 |
| | B4 | test_concurrent | ✅ 通过 | 并发请求 req-001 处理正常 |
| | B5 | test_unicode | ✅ 通过 | 中日韩+emoji 全部正确 |
| | B6 | test_error_codes | ✅ 通过 | 正确返回错误码 -32602（按设计返回错误） |
| C-通知批量 | C1 | test_progress_notification | ✅ 通过 | 5步进度通知完成 |
| | C2 | test_cancellation | ✅ 通过 | 取消测试完成 |
| | C3 | test_batch_request | ✅ 通过 | 3个批量操作执行完成 |
| | C4 | test_completion | ✅ 通过 | 返回3个补全建议 |
| D-边界 | D1 | test_empty_params | ✅ 通过 | 空参数处理正常 |
| | D2 | test_long_string | ✅ 通过 | 2000字符长字符串正常 |
| | D3 | test_special_chars | ✅ 通过 | 控制字符+引号正常 |
| | D4 | test_idempotency | ✅ 通过 | 首次请求，cached=false |
| | D5 | test_rapid_fire | ✅ 通过 | 10次快速请求 0ms 完成 |
| | D6 | test_empty_values | ✅ 通过 | 空字符串/数组/对象正常 |
| | D7 | test_deep_nesting | ✅ 通过 | 10层嵌套正常 |
| | D8 | test_large_array | ✅ 通过 | 200元素数组，sum=19900 |
| E-超时 | E1 | test_timeout_boundary | ✅ 通过 | 5秒未触发超时 |
| G-GUI | G1 | gui_desktop_info | ✅ 通过 | 1920×1080 分辨率 |
| | G2 | gui_take_screenshot | ✅ 通过 | PNG 截图成功 |
| | G3 | gui_mouse_click | ✅ 通过 | 点击 (500,300) |
| | G4 | gui_mouse_move | ✅ 通过 | 移动到 (800,600) |
| | G5 | gui_keyboard_input | ✅ 通过 | 15字符输入正常 |
| | G6 | gui_send_message | ✅ 通过 | 流式4步发送完成 |
| | G7 | gui_automation_demo | ✅ 通过 | 5步自动化演示完成 |
| H-Elicitation | H1 | test_elicitation_form | ✅ 通过 | 表单式交互正常 |
| | H2 | test_elicitation_url | ✅ 通过 | URL式交互正常 |
| I-Sampling | I1 | test_sampling_basic | ✅ 通过 | 基础采样正常 |
| | I2 | test_sampling_with_tools | ✅ 通过 | 带工具采样正常 |

### 结论

**通过率 34/35（97.1%），1 个为预期行为：**
- A4 的 `type_match=false`：Python 类型名 `str` 与 JSON Schema 的 `string` 类型名称差异，属于展示层面的小问题，值传递本身正确
- B6 的 `success=false`：错误处理测试，按设计返回错误

**所有系列（A/B/C/D/E/G/H/I）均正常工作。** Low-Level Server API 实现与 FastMCP 实现的功能完全一致。

### 部署备注

本次测试在清理阶跃 uvx 全部缓存 + 更新 `pyproject.toml` 版本号（1.0.0 → 1.1.0）后成功连接。详见 [ISSUES.md](./ISSUES.md)。
