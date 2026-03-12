# MCP 2024-11-05 全量测试执行指南

**版本**: 2.0
**日期**: 2026-03-09
**服务器端口**: 3372

---

## 一、准备工作

### 1.1 启动测试服务器

```bash
cd C:\Project\IDEA\2\new\mcp-test-stepfun
python full_test_server.py --port 3372 --log-dir ./logs
```

### 1.2 配置阶跃桌面助手

```json
{
  "mcpServers": {
    "full-test": {
      "url": "http://127.0.0.1:3372/mcp"
    }
  }
}
```

### 1.3 验证服务器启动

服务器启动后会显示：
- 服务器 URL
- 日志文件路径
- 测试分类说明

---

## 二、测试清单

### A. 核心能力测试（P0 - 必须全部通过）

#### A1: 基础连通性

**工具**: `test_ping`

**测试步骤**:
1. 基础调用：`{}`
2. 带回显：`{"echo": "hello"}`
3. 带延迟：`{"echo": "delayed", "delay_ms": 1000}`

**验证点**:
- [ ] 返回 `pong: true`
- [ ] `echo` 正确返回
- [ ] `server_time` 格式正确（ISO 8601）
- [ ] `elapsed_ms` 与 `delay_ms` 接近

**预期结果**:
```json
{
  "test_id": "A1",
  "success": true,
  "pong": true,
  "echo": "hello",
  "server_time": "2026-03-09T15:00:00.000000",
  "elapsed_ms": 5
}
```

---

#### A2: 协议版本协商

**工具**: `test_protocol_version`

**测试步骤**:
1. 调用 `test_protocol_version`

**验证点**:
- [ ] `client_protocol_version` 显示客户端发送的版本
- [ ] `server_protocol_version` 为 `2024-11-05`
- [ ] `version_match` 为 true（如果客户端版本正确）

---

#### A3: 能力协商

**工具**: `test_capabilities`

**测试步骤**:
1. 调用 `test_capabilities`

**验证点**:
- [ ] 返回 `tools`, `resources`, `prompts`, `logging`, `streaming` 能力
- [ ] 每个能力格式正确

---

#### A4: 工具调用

**工具**: `test_tool_call`

**测试步骤**:
1. 字符串：`{"input_value": "test"}`
2. 数字：`{"input_value": "123", "input_type": "number"}`
3. 布尔：`{"input_value": "true", "input_type": "boolean"}`

**验证点**:
- [ ] `received_value` 正确返回
- [ ] `type_match` 为 true（类型匹配时）

---

### B. 重要能力测试（P1 - 大部分应通过）

#### B1: 复杂参数

**工具**: `test_complex_params`

**测试步骤**:
1. 嵌套对象：
   ```json
   {
     "nested": {"level1": {"level2": "deep"}},
     "array": [1, 2, 3, 4, 5],
     "enum_value": "option2"
   }
   ```

**验证点**:
- [ ] `nested_depth` 正确计算
- [ ] `array_length` 正确
- [ ] `enum_valid` 为 true

---

#### B2: 大数据量

**工具**: `test_large_data`

**测试步骤**:
1. 小数据：`{"count": 100}`
2. 中数据：`{"count": 1000}`
3. 大数据：`{"count": 5000}`

**验证点**:
- [ ] `count` 与请求数量一致
- [ ] `sample_items` 包含前 3 项
- [ ] 请求不超时

---

#### B3: 长时间操作

**工具**: `test_long_operation`

**测试步骤**:
1. 短操作：`{"duration_seconds": 3, "progress_interval_ms": 500}`
2. 中操作：`{"duration_seconds": 10, "progress_interval_ms": 1000}`
3. 长操作：`{"duration_seconds": 30, "progress_interval_ms": 2000}`

**验证点**:
- [ ] `elapsed_ms` 与 `duration_seconds` 接近
- [ ] `steps_completed` 正确计算
- [ ] 无超时错误

---

#### B4: 并发测试

**工具**: `test_concurrent`

**测试步骤**:
1. 同时调用 3 次：
   - `{"request_id": "req1", "delay_ms": 100}`
   - `{"request_id": "req2", "delay_ms": 150}`
   - `{"request_id": "req3", "delay_ms": 200}`

**验证点**:
- [ ] 所有请求返回正确
- [ ] `request_id` 正确对应
- [ ] 并发执行（总时间接近最大延迟而非延迟之和）

---

#### B5: Unicode 支持

**工具**: `test_unicode`

**测试步骤**:
1. 中文：`{"text": "你好世界"}`
2. 日语：`{"text": "こんにちは"}`
3. 阿拉伯语：`{"text": "مرحبا"}`
4. Emoji：`{"text": "🎉🎊🎁"}`
5. 混合：`{"text": "你好 🎉 مرحبا こんにちは"}`

**验证点**:
- [ ] `has_chinese`, `has_japanese`, `has_arabic`, `has_emoji` 正确识别
- [ ] `bytes_utf8` 计算正确

---

#### B6: 错误处理

**工具**: `test_error_codes`

**测试步骤**:
1. `{"error_type": "invalid_params"}`
2. `{"error_type": "not_found"}`
3. `{"error_type": "internal_error"}`
4. `{"error_type": "unauthorized"}`
5. `{"error_type": "timeout"}`

**验证点**:
- [ ] 每种错误返回正确的 `error_code`
- [ ] `success: false`
- [ ] 系统不崩溃

---

#### B7: 资源 API

**工具**: `list_resources`, `read_resource`

**测试步骤**:
1. 列出资源：`list_resources` 无参数
2. 读取资源：`{"uri": "config://server"}`
3. 分类过滤：`{"category": "config"}`
4. 读取不存在的资源：`{"uri": "config://nonexistent"}`

**验证点**:
- [ ] `list_resources` 返回资源列表
- [ ] `read_resource` 返回正确内容
- [ ] 不存在资源返回错误

---

#### B8: 提示 API

**工具**: `list_prompts`, `get_prompt`

**测试步骤**:
1. 列出提示：`list_prompts` 无参数
2. 获取提示：`{"name": "analyze_data", "arguments": {"data": "test"}}`

**验证点**:
- [ ] `list_prompts` 返回提示列表
- [ ] `get_prompt` 返回正确模板

---

#### B9: 进度通知

**工具**: `test_progress_notification`

**测试步骤**:
1. 短测试：`{"total_steps": 5, "step_delay_ms": 500}`
2. 长测试：`{"total_steps": 10, "step_delay_ms": 1000}`

**验证点**:
- [ ] `progress_updates` 数量正确
- [ ] 进度百分比从 0% 到 100%
- [ ] 通知记录到日志文件

**注意**: 实时通知需要客户端支持 SSE 或 stdio 通知接收

---

#### B10: 取消操作

**工具**: `test_cancellation`

**测试步骤**:
1. 启动操作：`{"duration_seconds": 60}`
2. 在操作执行期间发送取消请求（如果客户端支持）

**验证点**:
- [ ] 操作开始执行
- [ ] 进度通知记录到日志

**注意**: 实际取消需要客户端支持 `notifications/cancelled`

---

#### B11: 采样请求

**工具**: `test_sampling`

**测试步骤**:
1. 简单采样：`{"prompt": "What is 2+2?", "max_tokens": 100}`
2. 复杂采样：`{"prompt": "Explain quantum computing", "max_tokens": 500}`

**验证点**:
- [ ] `sampling_requested: true`
- [ ] `sampling_params` 格式正确
- [ ] 采样请求记录到日志

**注意**: 实际 LLM 采样需要客户端支持 `sampling/createMessage` 回调

---

### C. 高级能力测试（P2 - 部分可能不支持）

#### C2: 批量请求

**工具**: `test_batch_request`

**测试步骤**:
```json
{
  "operations": [
    {"op": "double", "value": 10},
    {"op": "square", "value": 5},
    {"op": "double", "value": 20}
  ]
}
```

**验证点**:
- [ ] 所有操作正确执行
- [ ] 结果与输入正确对应

---

#### C5: 自动补全

**工具**: `test_completion`

**测试步骤**:
1. 资源补全：`{"ref_type": "ref/resource", "partial_value": "conf"}`
2. 提示补全：`{"ref_type": "ref/prompt", "partial_value": "ana"}`

**验证点**:
- [ ] 返回匹配的补全建议
- [ ] `total` 数量正确

---

### D. 边界条件测试（P3 - 稳定性验证）

#### D1: 空参数

**工具**: `test_empty_params`

**测试步骤**:
1. 调用 `{}`

**验证点**:
- [ ] 使用默认值正确处理
- [ ] 无错误

---

#### D2: 超长字符串

**工具**: `test_long_string`

**测试步骤**:
1. 10KB：`{"length": 10000}`
2. 50KB：`{"length": 50000}`
3. 100KB：`{"length": 100000}`

**验证点**:
- [ ] 字符串长度正确
- [ ] 不超时、不崩溃

---

#### D3: 特殊字符

**工具**: `test_special_chars`

**测试步骤**:
1. 默认：`{}`
2. 含控制字符：`{"include_control": true}`
3. 全部：`{"include_control": true, "include_quotes": true, "include_newlines": true}`

**验证点**:
- [ ] 字符正确处理
- [ ] 转义正确

---

#### D4: 幂等性

**工具**: `test_idempotency`

**测试步骤**:
1. 第一次调用：`{"operation_id": "test-123"}`
2. 第二次调用（相同 ID）：`{"operation_id": "test-123"}`
3. 第三次调用（不同 ID）：`{"operation_id": "test-456"}`

**验证点**:
- [ ] 第一次 `cached: false`
- [ ] 第二次 `cached: true`
- [ ] 第三次 `cached: false`

---

#### D5: 快速连续请求

**工具**: `test_rapid_fire`

**测试步骤**:
1. 5 次：`{"count": 5}`
2. 10 次：`{"count": 10}`
3. 20 次：`{"count": 20}`

**验证点**:
- [ ] 所有请求返回正确
- [ ] 连接稳定

---

## 三、测试结果记录表

| 编号 | 测试项 | 状态 | 关键数据 | 备注 |
|------|--------|------|----------|------|
| A1 | test_ping | ⬜ | | |
| A2 | test_protocol_version | ⬜ | | |
| A3 | test_capabilities | ⬜ | | |
| A4 | test_tool_call | ⬜ | | |
| B1 | test_complex_params | ⬜ | | |
| B2 | test_large_data | ⬜ | | |
| B3 | test_long_operation | ⬜ | | |
| B4 | test_concurrent | ⬜ | | |
| B5 | test_unicode | ⬜ | | |
| B6 | test_error_codes | ⬜ | | |
| B7 | list_resources | ⬜ | | |
| B7 | read_resource | ⬜ | | |
| B8 | list_prompts | ⬜ | | |
| B8 | get_prompt | ⬜ | | |
| B9 | test_progress_notification | ⬜ | | |
| B10 | test_cancellation | ⬜ | | |
| B11 | test_sampling | ⬜ | | |
| C2 | test_batch_request | ⬜ | | |
| C5 | test_completion | ⬜ | | |
| D1 | test_empty_params | ⬜ | | |
| D2 | test_long_string | ⬜ | | |
| D3 | test_special_chars | ⬜ | | |
| D4 | test_idempotency | ⬜ | | |
| D5 | test_rapid_fire | ⬜ | | |

---

## 四、日志分析

### 4.1 日志文件位置

```
./logs/full_test_YYYYMMDD_HHMMSS.jsonl
```

### 4.2 日志格式

每行一个 JSON 对象，包含：
- `timestamp`: 时间戳
- `type`: request/response/notification/event
- `jsonrpc_id`: 请求 ID
- `method`: 方法名
- `params`/`result`/`error`: 数据

### 4.3 分析命令

```bash
# 统计请求数
cat logs/*.jsonl | grep '"type": "request"' | wc -l

# 统计响应数
cat logs/*.jsonl | grep '"type": "response"' | wc -l

# 查看所有错误
cat logs/*.jsonl | grep '"error"'
```

---

## 五、预期测试结果

| 类别 | 预期通过 | 预期不通过/待确认 |
|------|---------|-----------------|
| A 核心 | A1, A2, A3, A4 | - |
| B 重要 | B1-B8 | B9(通知接收待确认), B10(取消待确认), B11(采样需回调) |
| C 高级 | C2, C5 | - |
| D 边界 | D1, D4, D5 | D2(大文本可能超时), D3(特殊字符可能转义问题) |

---

## 六、测试完成后

1. 停止服务器
2. 检查日志文件
3. 填写测试结果记录表
4. 生成测试报告
5. 更新能力清单文档

---

*本指南与 full_test_server.py 配合使用*
