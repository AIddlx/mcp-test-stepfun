# MCP 2024-11-05 阶跃全量测试指南

## 测试目的

验证阶跃桌面助手对 MCP 2024-11-05 协议各项能力的支持情况。

## 测试配置

```json
{
  "mcpServers": {
    "full-test": {
      "url": "http://127.0.0.1:3372/mcp"
    }
  }
}
```

**请确保服务器已启动**：
```bash
cd C:\Project\IDEA\2\new\mcp-test-stepfun
python full_test_server.py --port 3372
```

---

## A 核心能力测试（必须全部通过）

### A1: 基础连通性 (test_ping)

**步骤1** - 基础调用：
```
工具: test_ping
参数: {}
```

**步骤2** - 带回显：
```
工具: test_ping
参数: {"echo": "hello_stepfun"}
```

**步骤3** - 带延迟：
```
工具: test_ping
参数: {"echo": "delayed", "delay_ms": 500}
```

**验证点**：
- `pong: true`
- `echo` 正确返回
- `elapsed_ms` 与 `delay_ms` 接近

---

### A2: 协议版本 (test_protocol_version)

```
工具: test_protocol_version
参数: {}
```

**验证点**：
- `server_protocol_version: "2024-11-05"`
- `version_match` 状态

---

### A3: 能力协商 (test_capabilities)

```
工具: test_capabilities
参数: {}
```

**验证点**：
- 返回 `tools`, `resources`, `prompts`, `logging`, `streaming` 能力

---

### A4: 工具调用 (test_tool_call)

**步骤1** - 字符串：
```
工具: test_tool_call
参数: {"input_value": "hello", "input_type": "string"}
```

**步骤2** - 数字：
```
工具: test_tool_call
参数: {"input_value": 123, "input_type": "number"}
```

**验证点**：
- `received_value` 正确
- `type_match: true`

---

## B 重要能力测试

### B1: 复杂参数 (test_complex_params)

```
工具: test_complex_params
参数: {
  "nested": {"level1": {"level2": "deep_value"}},
  "array": [1, 2, 3, 4, 5],
  "enum_value": "option2"
}
```

**验证点**：
- 嵌套对象正确解析
- 数组长度为 5
- `enum_valid: true`

---

### B2: 大数据量 (test_large_data)

```
工具: test_large_data
参数: {"count": 500, "item_size": 200}
```

**验证点**：
- 返回 500 项数据
- 不超时

---

### B3: 长时间操作 (test_long_operation)

```
工具: test_long_operation
参数: {"duration_seconds": 10, "progress_interval_ms": 2000}
```

**验证点**：
- 10 秒后正常返回
- 不超时

---

### B4: 并发测试 (test_concurrent)

**同时调用 3 次**：
```
工具: test_concurrent
参数: {"request_id": "req_1", "delay_ms": 200}
```
```
工具: test_concurrent
参数: {"request_id": "req_2", "delay_ms": 300}
```
```
工具: test_concurrent
参数: {"request_id": "req_3", "delay_ms": 400}
```

**验证点**：
- 3 个请求全部返回
- `request_id` 正确对应

---

### B5: Unicode 支持 (test_unicode)

```
工具: test_unicode
参数: {"text": "你好世界 🎉 مرحبا こんにちは", "languages": ["chinese", "japanese", "arabic", "emoji"]}
```

**验证点**：
- `has_chinese: true`
- `has_emoji: true`
- `has_arabic: true`
- `has_japanese: true`

---

### B6: 错误处理 (test_error_codes)

**依次测试 5 种错误**：
```
1. {"error_type": "invalid_params"}
2. {"error_type": "not_found"}
3. {"error_type": "internal_error"}
4. {"error_type": "unauthorized"}
5. {"error_type": "timeout"}
```

**验证点**：
- 每种错误返回正确 `error_code`
- 系统不崩溃

---

### B7: 资源 API

**列出资源**：
```
工具: list_resources
参数: {}
```

**读取资源**：
```
工具: read_resource
参数: {"uri": "config://server"}
```

**验证点**：
- 返回资源列表
- 读取返回正确内容

---

### B8: 提示 API

**列出提示**：
```
工具: list_prompts
参数: {}
```

**获取提示**：
```
工具: get_prompt
参数: {"name": "analyze_data", "arguments": {"data": "test"}}
```

---

### B9: 进度通知 (test_progress_notification)

```
工具: test_progress_notification
参数: {"total_steps": 5, "step_delay_ms": 500}
```

**验证点**：
- `progress_updates` 包含 5 项
- 进度从 20% 到 100%

---

### B10: 取消操作 (test_cancellation)

```
工具: test_cancellation
参数: {"duration_seconds": 30}
```

**验证点**：
- 操作正常启动
- （可选）发送取消后能中断

---

### B11: 采样请求 (test_sampling)

```
工具: test_sampling
参数: {"prompt": "What is 2+2?", "max_tokens": 100}
```

**验证点**：
- `sampling_requested: true`
- `sampling_params` 格式正确
- 注意：实际采样需要客户端回调支持

---

## C 高级能力测试

### C2: 批量请求 (test_batch_request)

```
工具: test_batch_request
参数: {
  "operations": [
    {"op": "double", "value": 10},
    {"op": "square", "value": 5},
    {"op": "double", "value": 20}
  ]
}
```

**验证点**：
- 所有操作正确执行
- `double(10)=20`, `square(5)=25`, `double(20)=40`

---

### C5: 自动补全 (test_completion)

```
工具: test_completion
参数: {"ref_type": "ref/resource", "partial_value": "config"}
```

**验证点**：
- 返回补全建议列表

---

## D 边界条件测试

### D1: 空参数 (test_empty_params)

```
工具: test_empty_params
参数: {}
```

**验证点**：
- 正常返回，不报错

---

### D2: 超长字符串 (test_long_string)

```
工具: test_long_string
参数: {"length": 50000}
```

**验证点**：
- 正确处理大文本

---

### D3: 特殊字符 (test_special_chars)

```
工具: test_special_chars
参数: {"include_quotes": true, "include_newlines": true, "include_control": false}
```

**验证点**：
- 特殊字符正确处理

---

### D4: 幂等性 (test_idempotency)

**调用 2 次相同 ID**：
```
工具: test_idempotency
参数: {"operation_id": "test_idem_123"}
```

**第一次调用**：
- `cached: false`

**第二次调用**：
- `cached: true`
- 返回与第一次相同的结果

---

### D5: 快速连续请求 (test_rapid_fire)

```
工具: test_rapid_fire
参数: {"count": 10}
```

**验证点**：
- 10 个请求全部返回
- 连接稳定

---

## 测试结果汇总

请完成测试后，填写以下表格：

| 编号 | 测试项 | 状态 | 关键发现 |
|------|--------|------|----------|
| A1 | test_ping | | |
| A2 | test_protocol_version | | |
| A3 | test_capabilities | | |
| A4 | test_tool_call | | |
| B1 | test_complex_params | | |
| B2 | test_large_data | | |
| B3 | test_long_operation | | |
| B4 | test_concurrent | | |
| B5 | test_unicode | | |
| B6 | test_error_codes | | |
| B7 | list/read_resources | | |
| B8 | list/get_prompts | | |
| B9 | test_progress_notification | | |
| B10 | test_cancellation | | |
| B11 | test_sampling | | |
| C2 | test_batch_request | | |
| C5 | test_completion | | |
| D1 | test_empty_params | | |
| D2 | test_long_string | | |
| D3 | test_special_chars | | |
| D4 | test_idempotency | | |
| D5 | test_rapid_fire | | |

**状态说明**：
- ✅ 通过：功能正常
- ⚠️ 部分通过：部分功能有问题
- ❌ 失败：功能不工作
- ⏭️ 跳过：无法测试

---

## 测试日志

所有交互日志保存在：
```
./logs/full_test_YYYYMMDD_HHMMSS.jsonl
```

测试完成后，可以将日志文件提供给我进行分析。
