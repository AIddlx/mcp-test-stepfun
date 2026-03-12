# MCP 综合能力测试指南 V4（真正的 SSE）

## 新增测试项目（测试 18）

本文档记录真正的 Server-Sent Events (SSE) 测试。

---

## 测试 18：真正的 SSE 端点

**端点**: `GET /sse`

**测试目的**: 验证阶跃对真正的 text/event-stream 的支持能力。

### 背景说明

之前的 `sse_stream` 工具是在 MCP 工具调用中模拟流式响应（收集所有事件后一次性返回）。

本测试使用**独立的 HTTP SSE 端点**，返回真正的 `Content-Type: text/event-stream`。

### MCP 工具引导

先调用 `sse_endpoint` 工具获取 SSE 端点信息：

```json
{
  "event_count": 5,
  "interval_ms": 1000
}
```

**返回示例**:
```json
{
  "success": true,
  "sse_available": true,
  "sse_url": "http://127.0.0.1:3370/sse",
  "params": {
    "event_count": 5,
    "interval_ms": 1000
  },
  "usage": "GET /sse?event_count=5&interval_ms=1000",
  "content_type": "text/event-stream",
  "note": "Connect to SSE URL with Accept: text/event-stream for real streaming"
}
```

### 测试步骤

#### 步骤 1：获取 SSE 端点信息

调用 `sse_endpoint` 工具：
```json
{
  "event_count": 5,
  "interval_ms": 1000
}
```

#### 步骤 2：连接 SSE 端点

使用浏览器、curl 或其他 HTTP 客户端连接：

```bash
curl -N -H "Accept: text/event-stream" "http://127.0.0.1:3370/sse?event_count=5&interval_ms=1000"
```

**注意**: 阶跃是否能自动连接 SSE 端点需要测试验证。

#### 步骤 3：观察 SSE 事件流

**预期 SSE 响应格式**:
```
data: {"event_id": 1, "total_events": 5, "message": "SSE Event 1 of 5", "timestamp": "2026-03-09T...", "progress_percent": 20.0}

data: {"event_id": 2, "total_events": 5, "message": "SSE Event 2 of 5", "timestamp": "2026-03-09T...", "progress_percent": 40.0}

data: {"event_id": 3, "total_events": 5, "message": "SSE Event 3 of 5", "timestamp": "2026-03-09T...", "progress_percent": 60.0}

data: {"event_id": 4, "total_events": 5, "message": "SSE Event 4 of 5", "timestamp": "2026-03-09T...", "progress_percent": 80.0}

data: {"event_id": 5, "total_events": 5, "message": "SSE Event 5 of 5", "timestamp": "2026-03-09T...", "progress_percent": 100.0}

data: {"event_id": "complete", "total_events": 5, "message": "SSE stream completed", "timestamp": "2026-03-09T...", "all_events_count": 5}
```

### 测试变体

1. **快速测试** (5 事件，500ms 间隔):
   ```json
   {"event_count": 5, "interval_ms": 500}
   ```

2. **长时间测试** (10 事件，2 秒间隔):
   ```json
   {"event_count": 10, "interval_ms": 2000}
   ```

3. **高频测试** (20 事件，100ms 间隔):
   ```json
   {"event_count": 20, "interval_ms": 100}
   ```

---

## SSE 技术说明

### SSE 格式

```
Content-Type: text/event-stream

data: {"key": "value"}\n\n
data: {"key2": "value2"}\n\n
```

每个事件以 `data: ` 开头，以两个换行符 `\n\n` 结束。

### 与 MCP 的关系

| 特性 | MCP 工具调用 | SSE 端点 |
|------|-------------|----------|
| 传输格式 | JSON-RPC | text/event-stream |
| 连接方式 | POST /mcp | GET /sse |
| 响应模式 | 请求-响应 | 持续流 |
| 适用场景 | 控制命令 | 实时事件推送 |

### 阶跃支持情况

根据之前的测试，阶跃的 HTTP 请求包含：
```
Accept: application/json, text/event-stream
```

这表明阶跃**客户端支持接收 SSE**，但需要验证阶跃**AI 是否能主动连接 SSE 端点**。

---

## 新增测试结果汇总表

| 编号 | 测试项 | 状态 | 备注 |
|------|--------|------|------|
| 18-基础 | SSE 端点（基础） | ✅ 通过 | 5事件, 1000ms间隔, 事件完整 |
| 18-变体1 | SSE 端点（快速） | ✅ 通过 | 5事件, 500ms间隔, 事件完整 |
| 18-变体2 | SSE 端点（长时间） | ✅ 通过 | 10事件, 2000ms间隔, 长连接稳定 |
| 18-变体3 | SSE 端点（高频） | ✅ 通过 | 20事件, 100ms间隔, 无丢失 |

**通过率**: 4/4 = 100%

---

## 测试完成后

**测试日期**: 2026-03-09

1. **SSE 端点访问**：阶跃是否能获取 SSE 端点信息？
   - ✅ 能。通过 `sse_endpoint` MCP 工具成功获取端点 URL 和参数

2. **SSE 连接**：阶跃是否能主动连接 SSE 端点？
   - ⚠️ 间接实现。阶跃 AI 无法直接发起 HTTP SSE 连接，但可通过终端工具（PowerShell + .NET HttpClient）间接连接

3. **事件接收**：阶跃是否能接收并解析 SSE 事件流？
   - ✅ 能。通过终端工具流式读取，所有事件均正确接收和解析

4. **实时性**：事件是否实时到达（而非一次性返回）？
   - ✅ 是。使用 `HttpCompletionOption.ResponseHeadersRead` 实现了真正的流式读取，事件间隔与服务端配置一致

5. **断开处理**：SSE 流结束后阶跃的行为？
   - ✅ 正常。流结束后连接自动关闭，客户端捕获到流结束信号

---

## 服务器日志

服务器会输出详细日志：

```
[SSE] 客户端连接: event_count=5, interval_ms=1000, supports_sse=True
[SSE] 发送事件 1/5: 20.0%
[SSE] 发送事件 2/5: 40.0%
[SSE] 发送事件 3/5: 60.0%
[SSE] 发送事件 4/5: 80.0%
[SSE] 发送事件 5/5: 100.0%
[SSE] 流完成，共发送 6 个事件
```

如果客户端不支持 SSE（没有 Accept: text/event-stream 头），会返回错误：
```json
{
  "error": "Client does not accept text/event-stream",
  "hint": "Include 'Accept: text/event-stream' header"
}
```
