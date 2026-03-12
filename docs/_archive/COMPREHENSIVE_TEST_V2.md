# MCP 综合能力测试指南 V2（新增测试）

## 新增测试项目（测试10-14）

本文档记录新增的 5 个测试项目，请在完成 V1 测试（1-9）后再执行。

---

## 测试 10：Unicode/特殊字符

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
  "has_arabic": true,
  "has_japanese": true
}
```

**通过条件**: Unicode 字符正确返回，Emoji/中文/阿拉伯语/日语正确识别

---

## 测试 11：错误码处理

**工具**: `error_test`

**测试步骤**:
依次调用以下参数：

1. `error_type: "invalid_params"` - 无效参数错误
2. `error_type: "not_found"` - 资源未找到错误
3. `error_type: "internal_error"` - 内部错误
4. `error_type: "unauthorized"` - 未授权错误

**预期结果**（每种类型返回对应错误）:
```json
{
  "success": false,
  "error": "Invalid parameters provided",
  "error_code": "invalid_params",
  "mcp_error_code": -32602,
  "hint": "Check parameter types and required fields"
}
```

**通过条件**:
- 阶跃能正确识别不同错误类型
- 错误信息清晰易懂
- 不因错误而崩溃或异常

---

## 测试 12：参数验证

**工具**: `validate_params`

**测试步骤**:

1. **正常调用**:
   ```json
   {
     "required_string": "hello",
     "optional_number": 100,
     "range_value": 50
   }
   ```

2. **缺少必需参数**（应报错）:
   ```json
   {
     "optional_number": 100
   }
   ```

3. **超出范围**（应报错）:
   ```json
   {
     "required_string": "test",
     "range_value": 150
   }
   ```

4. **类型错误**（应报错）:
   ```json
   {
     "required_string": 12345
   }
   ```

**预期结果（正常时）**:
```json
{
  "success": true,
  "received": {
    "required_string": "hello",
    "optional_number": 100,
    "range_value": 50
  },
  "validation": "passed"
}
```

**预期结果（错误时）**:
```json
{
  "success": false,
  "error": "range_value must be between 1 and 100, got 150",
  "validation": "failed"
}
```

**通过条件**: 参数验证正确执行，错误信息准确

---

## 测试 13：并发测试

**工具**: `concurrent_test`

**测试步骤**:
同时发起 3 个请求（如果阶跃支持并行调用）：

- 请求 1: `request_id: "req-1"`, `processing_time_ms: 200`
- 请求 2: `request_id: "req-2"`, `processing_time_ms: 100`
- 请求 3: `request_id: "req-3"`, `processing_time_ms: 150`

**预期结果**（每个请求独立返回）:
```json
{
  "success": true,
  "request_id": "req-2",
  "processing_time_ms": 100,
  "actual_time_ms": 102,
  "server_time": "2026-03-09T12:00:00"
}
```

**通过条件**:
- 所有请求正确返回
- 处理时间准确
- 请求顺序可能按完成时间排序（req-2, req-3, req-1）

---

## 测试 14：长超时测试

**工具**: `long_operation`

**测试步骤**:
1. 调用 `long_operation`，参数 `delay_seconds: 10`
2. 等待响应，记录是否有超时
3. 如果 10秒成功，4. 可选：尝试 `delay_seconds: 30` 或 `delay_seconds: 60`

**预期结果**:
```json
{
  "success": true,
  "message": "Long operation completed after 10 seconds",
  "delay": 10,
  "elapsed_ms": 10023,
  "started_at": "2026-03-09T12:00:00",
  "completed_at": "2026-03-09T12:00:10"
}
```

**通过条件**:
- 10秒延迟无超时：✅ 通过
- 30秒延迟无超时：✅ 优秀
- 60秒延迟无超时：✅ 非常优秀

**如果超时**:
- 讁录超时时间
- 记录阶跃的错误信息

---

## 新增测试结果汇总表

| 编号 | 测试项 | 状态 | 备注 |
|------|--------|------|------|
| 10 | unicode_test | ✅ 通过 | Emoji/中文/阿拉伯语/日语均正确识别 |
| 11 | error_test | ✅ 通过 | 4种错误码正确返回，系统未崩溃 |
| 12 | validate_params | ✅ 通过 | 正常/超范围/缺参数均正确处理 |
| 13 | concurrent_test | ✅ 通过 | 3个并发请求全部正确返回 |
| 14 | long_operation | ✅ 非常优秀 | 10s/30s/60s 全部无超时 |

**通过率**: 5/5 = 100%

---

## 测试完成后

**测试日期**: 2026-03-09

1. **Unicode 处理是否有问题？**
   - ✅ 无问题。中文/日文/阿拉伯文/Emoji 完美支持，正确识别字符类型

2. **错误码是否被正确识别？**
   - ✅ 是。4种错误码（invalid_params, not_found, internal_error, unauthorized）均正确返回

3. **参数验证的边界情况是否被正确处理？**
   - ✅ 是。超出范围正确报错，缺少必需参数被 schema 拦截

4. **并发请求是否能正确处理？**
   - ✅ 是。3个并发请求全部正确返回，处理时间精确

5. **阶跃的超时限制是多少秒？**
   - ✅ **≥60秒**。10s/30s/60s 全部正常完成，评级：非常优秀

