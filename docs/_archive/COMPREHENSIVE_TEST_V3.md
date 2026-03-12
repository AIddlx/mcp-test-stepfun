# MCP 综合能力测试指南 V3（流式/SSE 测试）

## 新增测试项目（测试 15-17）

本文档记录新增的 3 个流式/SSE 测试项目，请在完成 V1、V2 测试后再执行。

---

## 测试 15：SSE 流式测试

**工具**: `sse_stream`

**测试目的**: 验证阶跃对 Server-Sent Events 或类似流式响应的支持能力。

**测试步骤**:

1. **基础测试**（默认参数）:
   ```json
   {}
   ```
   预期：5 个事件，间隔 500ms

2. **多事件测试**:
   ```json
   {
     "event_count": 10,
     "interval_ms": 200
   }
   ```
   预期：10 个事件，间隔 200ms

3. **长间隔测试**:
   ```json
   {
     "event_count": 5,
     "interval_ms": 2000
   }
   ```
   预期：5 个事件，间隔 2 秒

**预期结果**:
```json
{
  "success": true,
  "stream_type": "sse_simulated",
  "event_count": 5,
  "interval_ms": 500,
  "events": [
    {"event_id": 1, "message": "Event 1 of 5", "progress": 20.0},
    {"event_id": 2, "message": "Event 2 of 5", "progress": 40.0},
    ...
  ]
}
```

**通过条件**:
- 所有事件正确返回
- 进度百分比正确计算
- 事件顺序正确

---

## 测试 16：进度报告测试

**工具**: `progress_report`

**测试目的**: 验证阶跃对长时间操作的进度更新支持。

**测试步骤**:

1. **快速测试**:
   ```json
   {
     "total_items": 10,
     "processing_delay_ms": 100
   }
   ```
   预期：10 个项目，每个 100ms，总计约 1 秒

2. **中等负载**:
   ```json
   {
     "total_items": 20,
     "processing_delay_ms": 200
   }
   ```
   预期：20 个项目，每个 200ms，总计约 4 秒

3. **长操作**:
   ```json
   {
     "total_items": 30,
     "processing_delay_ms": 500
   }
   ```
   预期：30 个项目，每个 500ms，总计约 15 秒

**预期结果**:
```json
{
  "success": true,
  "completed": true,
  "total_items": 10,
  "total_elapsed_ms": 1050,
  "progress_updates": [
    {"item": 1, "total": 10, "percent": 10.0, "elapsed_ms": 100},
    {"item": 2, "total": 10, "percent": 20.0, "elapsed_ms": 200},
    ...
  ]
}
```

**通过条件**:
- 完成状态为 true
- 进度更新数量等于 total_items
- 总耗时与预期一致

---

## 测试 17：分块响应测试

**工具**: `chunked_response`

**测试目的**: 验证阶跃对分块传输编码的支持。

**测试步骤**:

1. **小块测试**:
   ```json
   {
     "chunks": 5,
     "chunk_size": 100
   }
   ```
   预期：5 块，每块 100 字节，总计 500 字节

2. **多块测试**:
   ```json
   {
     "chunks": 10,
     "chunk_size": 500
   }
   ```
   预期：10 块，每块 500 字节，总计 5000 字节

3. **大块测试**:
   ```json
   {
     "chunks": 5,
     "chunk_size": 1000
   }
   ```
   预期：5 块，每块 1000 字节，总计 5000 字节

**预期结果**:
```json
{
  "success": true,
  "transfer_encoding": "chunked_simulated",
  "chunks_sent": 5,
  "chunk_size": 100,
  "total_bytes": 500,
  "chunk_summaries": [
    {"chunk_id": 1, "size": 100},
    {"chunk_id": 2, "size": 100},
    ...
  ]
}
```

**通过条件**:
- 所有分块正确返回
- 总字节数正确
- 分块摘要数量正确

---

## 新增测试结果汇总表

| 编号 | 测试项 | 状态 | 关键数据 |
|------|--------|------|----------|
| 15 | sse_stream | ✅ 通过 | 3个子测试全部通过，事件顺序正确，进度百分比准确 |
| 16 | progress_report | ✅ 通过 | 3个子测试全部通过，最长耗时14.5秒 |
| 17 | chunked_response | ✅ 通过 | 3个子测试全部通过，分块数据完整 |

**通过率**: 3/3 = 100%

---

## 测试完成后

**测试日期**: 2026-03-09

1. **SSE 流式**：阶跃是否能正确处理流式响应？事件顺序是否正确？
   - ✅ 是。所有事件顺序正确返回，进度百分比计算准确

2. **进度报告**：进度更新是否完整？耗时是否符合预期？
   - ✅ 是。进度更新数量与 total_items 完全一致，耗时符合预期（最长14.5秒）

3. **分块响应**：分块数据是否完整接收？总大小是否正确？
   - ✅ 是。所有分块完整接收，总字节数计算正确

4. **流式支持**：阶跃是否支持真正的 SSE（text/event-stream）？
   - ✅ 阶跃的 Accept header 包含 `text/event-stream`，表明客户端支持 SSE
   - 当前测试为模拟流式，真正的 SSE 需要服务端实现 `Content-Type: text/event-stream`

---

## 关于 MCP 与流式传输

### MCP 协议说明

MCP 协议基于 JSON-RPC，通常使用请求-响应模式。真正的 SSE 流式传输需要：

1. **HTTP SSE**: `Content-Type: text/event-stream`
2. **持续连接**: 服务端保持连接开放
3. **事件格式**: `data: {...}\n\n`

### 当前测试方案

由于 MCP 工具调用是请求-响应模式，本测试采用**模拟流式**方案：

- 工具执行期间收集所有"事件"
- 最终以单个 JSON 响应返回所有事件
- 测试阶跃对延迟响应和大数据的处理能力

### 真正的流式支持

如果需要真正的 SSE 流式支持，需要：

1. 使用 MCP 的 `notifications` 机制
2. 或使用独立的 SSE 端点（非 MCP 工具）
3. 阶跃客户端需要支持接收流式通知
