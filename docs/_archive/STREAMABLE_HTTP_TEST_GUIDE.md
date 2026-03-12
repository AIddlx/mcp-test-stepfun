# MCP Streamable HTTP 测试指南

## 背景

MCP 在 **2025年3月26日** 更新了协议，使用 **Streamable HTTP** 替代了原来的 SSE transport。

### 协议对比

| 对比项 | 旧版 (SSE) | 新版 (Streamable HTTP) |
|--------|-----------|----------------------|
| 连接方式 | HTTP + SSE 双链接 | 单一 HTTP 连接 |
| 无状态调用 | ❌ 不支持 | ✅ 支持 |
| 流式响应 | ✅ SSE 长连接 | ✅ HTTP 流式 |
| 云端部署 | ⚠️ 复杂 | ✅ 简单 |
| Accept 头 | 必须包含 `text/event-stream` | 可选 |

## 测试目的

验证阶跃桌面助手是否支持 MCP 2025-03-26 的 Streamable HTTP 协议：
1. **无状态调用** - 普通 HTTP POST 请求
2. **流式响应** - Accept: text/event-stream 时返回 SSE 流
3. **进度通知** - 服务端主动发送进度更新

## 配置方法

### 启动测试服务器

```bash
cd <项目路径>
python streamable_http_test.py --port 3371
```

### 阶跃桌面助手配置

```json
{
  "mcpServers": {
    "streamable-test": {
      "url": "http://127.0.0.1:3371/mcp"
    }
  }
}
```

## 测试清单

### 测试 1：基础连通性 (ping)

**工具**: `ping`

**预期结果**:
```json
{
  "success": true,
  "pong": true,
  "mode": "streamable-http",
  "note": "Using Streamable HTTP transport (MCP 2025-03-26)"
}
```

**验证点**: `mode: "streamable-http"` 确认使用新协议

---

### 测试 2：SSE Accept 头检测

**工具**: `test_sse_accept`

**预期结果**:
```json
{
  "success": true,
  "accept_header": "...",
  "supports_sse": true/false,
  "note": "Client should include 'text/event-stream' in Accept header for streaming"
}
```

**验证点**:
- ⬜ Accept 头是否包含 `text/event-stream`？
- ⬜ `supports_sse` 是否为 true？

---

### 测试 3：请求信息检查

**工具**: `get_request_info`

**预期结果**: 返回完整的 HTTP 请求信息

**验证点**:
- ⬜ Content-Type 是什么？
- ⬜ Accept 头内容？
- ⬜ User-Agent 标识？

---

### 测试 4：流式响应测试

**工具**: `test_streaming`

**参数**:
```json
{
  "count": 5,
  "delay_ms": 500
}
```

**预期行为**:
- 服务端发送 5 个 `notifications/progress` 通知
- 每个通知包含进度百分比

**验证点**:
- ⬜ 是否收到进度通知？
- ⬜ 通知是实时到达还是批量返回？
- ⬜ 进度百分比是否正确递增？

---

### 测试 5：长时间操作

**工具**: `long_operation`

**参数**:
```json
{
  "steps": 5,
  "step_delay_ms": 500
}
```

**预期行为**:
- 服务端执行 5 步操作
- 每步发送进度通知

**验证点**:
- ⬜ 进度通知是否实时到达？
- ⬜ 最终结果是否正确返回？

---

## 关键观察点

### 1. Accept 头

阶跃应该发送类似：
```
Accept: application/json, text/event-stream
```

如果只发送 `Accept: application/json`，说明不支持流式。

### 2. 流式响应处理

如果支持 Streamable HTTP：
- 长操作应该**实时**显示进度
- 不需要等待所有操作完成

### 3. 与旧版 HTTP 模式的区别

| 功能 | 旧版 HTTP | Streamable HTTP |
|------|----------|-----------------|
| 工具调用 | ✅ 支持 | ✅ 支持 |
| 流式响应 | ❌ 不支持 | ✅ 应该支持 |
| 进度通知 | ❌ 不支持 | ✅ 应该支持 |

---

## 测试结果记录表

| 编号 | 测试项 | 工具调用 | Accept 头 | 流式响应 | 结果 |
|------|--------|----------|-----------|----------|------|
| 1 | ping | ⬜ | - | - | ⬜ |
| 2 | test_sse_accept | ⬜ | ⬜ | - | ⬜ |
| 3 | get_request_info | ⬜ | - | - | ⬜ |
| 4 | test_streaming | ⬜ | - | ⬜ | ⬜ |
| 5 | long_operation | ⬜ | - | ⬜ | ⬜ |

---

## 预期结论

| 功能 | 旧版 HTTP | Streamable HTTP |
|------|----------|-----------------|
| **Tools API** | ✅ 支持 | ✅ 应该支持 |
| **Accept 头** | 仅 application/json | 应包含 text/event-stream |
| **流式响应** | ❌ 不支持 | ⚠️ 待验证 |
| **进度通知** | ❌ 不支持 | ⚠️ 待验证 |

测试完成后，请填写结果并记录发现。
