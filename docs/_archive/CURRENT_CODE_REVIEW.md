# full_test_server.py 代码审查报告

**审查日期**: 2026-03-10
**文件版本**: v3.1 (MCP 2025-11-25)
**代码行数**: ~2122 行

---

## 1. 架构概述

### 1.1 技术栈

| 组件 | 技术选型 |
|------|----------|
| Web 框架 | Starlette (异步 ASGI) |
| HTTP 服务器 | Uvicorn |
| 协议版本 | MCP 2025-11-25 |
| 数据格式 | JSON-RPC 2.0 |
| 流式响应 | Server-Sent Events (SSE) |

### 1.2 模块结构

```
full_test_server.py
├── 日志系统 (FullInteractionLogger)
│   ├── 请求/响应日志
│   ├── 通知追踪
│   └── 事件记录
├── 工具定义 (6 大类)
│   ├── CORE_TOOLS (A 类 - 核心能力)
│   ├── IMPORTANT_TOOLS (B 类 - 重要能力)
│   ├── RESOURCE_TOOLS (B7-B8 - 资源/提示)
│   ├── ADVANCED_TOOLS (B9-C5 - 高级能力)
│   ├── BOUNDARY_TOOLS (D 类 - 边界条件)
│   ├── TIMEOUT_TOOLS (E 类 - 超时边界)
│   └── GUI_AGENT_TOOLS (G 类 - GUI 自动化)
├── 工具实现 (call_tool 函数)
├── HTTP 处理
│   ├── handle_mcp_request
│   ├── process_single_request
│   └── create_streaming_response
└── 应用入口 (Starlette routes)
```

---

## 2. JSON-RPC 方法支持

### 2.1 生命周期方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `initialize` | 完整 | 返回 capabilities 和 serverInfo |
| `notifications/initialized` | 完整 | 记录日志，无响应 |
| `ping` | 完整 | 返回 pong 和时间戳 |

### 2.2 工具方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `tools/list` | 完整 | 返回 36 个工具定义 |
| `tools/call` | 完整 | 执行工具并返回结果 |

### 2.3 资源方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `resources/list` | 完整 | 4 个静态资源 |
| `resources/read` | 完整 | 按 URI 读取资源 |

### 2.4 提示方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `prompts/list` | 完整 | 2 个提示模板 |
| `prompts/get` | 完整 | 按名称获取模板 |

### 2.5 日志方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `logging/setLevel` | 完整 | 设置日志级别 |

### 2.6 补全方法

| 方法 | 实现 | 说明 |
|------|------|------|
| `completion/complete` | 完整 | 返回补全建议 |

### 2.7 缺失的方法

| 方法 | 状态 | 说明 |
|------|------|------|
| `resources/subscribe` | 未实现 | capability 声明了但无实际处理 |
| `resources/unsubscribe` | 未实现 | 同上 |
| `resources/templates/list` | 未实现 | 资源模板列表 |
| `roots/list` | 未实现 | 客户端根目录 |
| `sampling/createMessage` | 未实现 | 服务器到客户端的采样请求 |

---

## 3. Capabilities 声明结构

### 3.1 initialize 响应中的 capabilities

```json
{
  "capabilities": {
    "tools": {"listChanged": true},
    "resources": {"subscribe": true, "listChanged": true},
    "prompts": {"listChanged": true},
    "logging": {},
    "streaming": true
  }
}
```

### 3.2 Capability 分析

| Capability | 声明 | 实际实现 | 一致性 |
|------------|------|----------|--------|
| `tools.listChanged` | true | 无实际通知发送 | 部分 |
| `resources.subscribe` | true | 未实现 | 不一致 |
| `resources.listChanged` | true | 无实际通知发送 | 部分 |
| `prompts.listChanged` | true | 无实际通知发送 | 部分 |
| `logging` | {} | 已实现 setLevel | 一致 |
| `streaming` | true | SSE 已实现 | 一致 |

### 3.3 问题

1. **声明了 `resources.subscribe` 但未实现**: 客户端可能会尝试订阅资源但收到错误
2. **listChanged 声明但未发送通知**: 工具/资源/提示列表变更时应发送 `notifications/tools/list_changed` 等

---

## 4. 工具定义结构

### 4.1 标准 inputSchema 格式

```json
{
  "name": "test_ping",
  "description": "[A1] 测试基础连通性...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "echo": {"type": "string", "description": "..."},
      "delay_ms": {"type": "integer", "default": 0, "description": "..."}
    }
  }
}
```

### 4.2 缺失的 outputSchema

**问题**: 所有工具都没有定义 `outputSchema`。

根据 MCP 2025-11-25 规范，工具应该包含 `outputSchema` 来描述返回结构：

```json
{
  "name": "test_ping",
  "inputSchema": {...},
  "outputSchema": {
    "type": "object",
    "properties": {
      "test_id": {"type": "string"},
      "success": {"type": "boolean"},
      "pong": {"type": "boolean"},
      "server_time": {"type": "string"}
    }
  }
}
```

### 4.3 工具分类统计

| 分类 | 数量 | 前缀 |
|------|------|------|
| 核心能力 (A) | 5 | A1-A5 |
| 重要能力 (B) | 11 | B1-B11 |
| 高级能力 (C) | 2 | C2, C5 |
| 边界条件 (D) | 8 | D1-D8 |
| 超时边界 (E) | 1 | E1 |
| GUI Agent (G) | 10 | G1-G10 |
| **总计** | **37** | - |

---

## 5. 流式响应 (SSE) 实现

### 5.1 触发条件

```python
accept = request.headers.get("accept", "")
if "text/event-stream" in accept and body.get("method") == "tools/call":
    # 检查工具名称
    streaming_tools = [
        "test_progress_notification",
        "test_long_operation",
        "gui_send_message",
        "gui_automation_demo"
    ]
```

### 5.2 支持流式响应的工具

| 工具 | 流式内容 |
|------|----------|
| `test_progress_notification` | 进度通知 + 最终结果 |
| `test_long_operation` | 进度通知 + 最终结果 |
| `gui_send_message` | 多步骤进度 + 详细信息 |
| `gui_automation_demo` | 通用 GUI 自动化演示 |

### 5.3 SSE 格式

```
data: {"jsonrpc": "2.0", "method": "notifications/progress", "params": {...}}

data: {"jsonrpc": "2.0", "id": "...", "result": {...}}
```

### 5.4 问题

1. **缺少错误处理**: 流式生成过程中的异常未处理
2. **缺少心跳机制**: 长时间操作可能导致连接超时
3. **SSE 格式简化**: 未实现 `id`、`event`、`retry` 等 SSE 标准字段

---

## 6. 进度通知实现

### 6.1 标准 MCP 进度通知格式

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "client-token-or-server-generated",
    "progress": 0.5,
    "total": 1.0,
    "message": "Step 1/5"
  }
}
```

### 6.2 progressToken 处理

```python
_meta = params.get("_meta", {})
progress_token = _meta.get("progressToken") or f"server-{req_id}"
```

**优点**: 支持客户端提供的 token，fallback 到服务器生成的 token

### 6.3 问题

1. **非流式请求也记录进度**: `test_progress_notification` 在非流式模式下只记录日志，不实际发送通知
2. **total 字段总是 1.0**: 应该使用实际总数，便于客户端计算百分比

---

## 7. 错误处理和错误码

### 7.1 使用的标准 JSON-RPC 错误码

| 错误码 | 含义 | 使用场景 |
|--------|------|----------|
| -32700 | Parse error | JSON 解析失败 |
| -32600 | Invalid Request | 未使用 |
| -32601 | Method not found | 未知方法 |
| -32602 | Invalid params | 参数错误、资源未找到 |
| -32603 | Internal error | 工具执行异常 |

### 7.2 错误响应格式

```json
{
  "jsonrpc": "2.0",
  "id": "...",
  "error": {
    "code": -32601,
    "message": "Method not found: unknown_method"
  }
}
```

### 7.3 问题

1. **缺少 MCP 扩展错误码**: 未使用 MCP 特定的错误码 (如 -32001 RequestTimeout)
2. **错误信息缺少 data 字段**: 标准 JSON-RPC 错误可包含 `data` 字段提供更多细节
3. **-32600 未使用**: 应用于无效的 JSON-RPC 请求结构

---

## 8. HTTP 传输层实现

### 8.1 路由配置

```python
app = Starlette(
    routes=[
        Route("/mcp", handle_mcp_request, methods=["POST", "GET"]),
    ]
)
```

### 8.2 请求处理流程

```
HTTP Request
    ↓
读取原始请求体
    ↓
解析 JSON
    ↓
记录日志 (包含原始请求体)
    ↓
判断是否批量请求
    ↓
处理单个/批量请求
    ↓
检查是否需要流式响应
    ↓
返回响应 (JSON 或 SSE)
```

### 8.3 HTTP 头部记录

```python
http_info = {
    "method": request.method,
    "path": str(request.url.path),
    "query": dict(request.query_params),
    "headers": {
        "content-type": ...,
        "content-length": ...,
        "accept": ...,
        "mcp-protocol-version": ...,
        "user-agent": ...,
        "connection": ...,
        "host": ...,
        "authorization": ...  # 截断保护
    },
    ...
}
```

### 8.4 问题

1. **GET 方法支持但无实际处理**: 路由声明了 GET 但只处理 POST 请求体
2. **缺少 CORS 支持**: 跨域请求会被拒绝
3. **缺少请求大小限制**: 超大请求可能导致内存问题
4. **缺少超时处理**: 长时间请求无超时限制

---

## 9. JSON-RPC 批量请求支持

### 9.1 实现

```python
if isinstance(body, list):
    log.log_event("batch_request", {"count": len(body)})
    results = []
    for req in body:
        result = await process_single_request(req, request)
        results.append(result)
    response_str = json.dumps(results)
    return Response(response_str, media_type="application/json; charset=utf-8")
```

### 9.2 问题

1. **顺序处理**: 批量请求是顺序而非并行处理，可能影响性能
2. **通知混合**: 批量请求中包含通知时，返回数组长度不一致
3. **缺少原子性**: 部分失败不影响其他请求执行，符合规范但需注意

---

## 10. 代码质量评估

### 10.1 优点

1. **完整的日志系统**: 记录所有请求/响应/通知，便于调试
2. **清晰的工具分类**: A/B/C/D/E/G 分类便于测试定位
3. **SSE 流式响应**: 支持 GUI Agent 场景的实时进度推送
4. **幂等性测试**: `_idempotency_store` 支持幂等性验证
5. **边界条件覆盖**: 包含空值、深嵌套、大数组等边界测试

### 10.2 缺点

1. **单文件过大**: 2000+ 行代码应拆分为多个模块
2. **全局状态**: `_logger`、`_idempotency_store`、`_sampling_counter` 是全局变量
3. **缺少类型注解**: 大部分函数缺少完整的类型注解
4. **硬编码配置**: 端口、主机等配置散落在代码中
5. **缺少单元测试**: 无测试代码

### 10.3 代码风格

- 使用中文注释和文档字符串
- 一致的命名约定 (snake_case)
- 良好的函数拆分

---

## 11. 潜在问题列表

### 11.1 协议一致性问题

| ID | 问题 | 严重程度 | 说明 |
|----|------|----------|------|
| P1 | capabilities 与实现不一致 | 高 | 声明了 subscribe 但未实现 |
| P2 | 缺少 outputSchema | 中 | 工具缺少输出结构定义 |
| P3 | listChanged 通知未发送 | 低 | 声明了但未实际使用 |

### 11.2 安全问题

| ID | 问题 | 严重程度 | 说明 |
|----|------|----------|------|
| S1 | 缺少认证机制 | 高 | 任何人都可以调用 |
| S2 | 无请求大小限制 | 中 | 可能导致 DoS |
| S3 | 授权信息记录 | 低 | authorization 头部被记录到日志 |

### 11.3 性能问题

| ID | 问题 | 严重程度 | 说明 |
|----|------|----------|------|
| F1 | 批量请求顺序处理 | 中 | 应考虑并行处理 |
| F2 | 同步日志写入 | 低 | 每次请求都同步写文件 |
| F3 | 大数据生成无流式 | 低 | `test_large_data` 全部加载到内存 |

### 11.4 可靠性问题

| ID | 问题 | 严重程度 | 说明 |
|----|------|----------|------|
| R1 | 流式响应无错误处理 | 高 | SSE 中断无恢复机制 |
| R2 | 无请求超时 | 中 | 长操作可能无限期挂起 |
| R3 | 全局状态无锁 | 低 | 并发访问可能有竞态条件 |

### 11.5 可维护性问题

| ID | 问题 | 严重程度 | 说明 |
|----|------|----------|------|
| M1 | 单文件过大 | 中 | 应拆分模块 |
| M2 | 缺少配置文件 | 低 | 配置硬编码 |
| M3 | 缺少测试代码 | 中 | 无单元测试 |

---

## 12. 改进建议

### 12.1 短期改进 (1-2 天)

1. **修正 capabilities 声明**: 移除未实现的 `subscribe` 能力
2. **添加 outputSchema**: 为常用工具添加输出结构定义
3. **添加请求大小限制**: 限制请求体大小 (如 10MB)

### 12.2 中期改进 (1 周)

1. **模块拆分**:
   ```
   full_test_server/
   ├── __init__.py
   ├── server.py          # 主服务器
   ├── handlers/          # 请求处理器
   │   ├── tools.py
   │   ├── resources.py
   │   └── prompts.py
   ├── tools/             # 工具定义和实现
   │   ├── core.py
   │   ├── boundary.py
   │   └── gui_agent.py
   ├── logging/           # 日志系统
   └── config.py          # 配置管理
   ```

2. **添加认证支持**: API Key 或 Bearer Token

3. **并行处理批量请求**: 使用 `asyncio.gather()`

### 12.3 长期改进 (2-4 周)

1. **完整的 MCP SDK 集成**: 使用官方 MCP Python SDK
2. **添加单元测试**: pytest + 测试覆盖率
3. **WebSocket 支持**: 双向实时通信
4. **监控和指标**: Prometheus metrics

---

## 13. 总结

`full_test_server.py` 是一个功能较完整的 MCP 测试服务器，覆盖了 MCP 2025-11-25 协议的大部分核心功能。主要优点是日志详细、测试场景丰富、支持 SSE 流式响应。主要问题在于代码结构需要重构、capabilities 声明与实现不一致、缺少安全机制。

建议优先解决 P1 (capabilities 一致性) 和 R1 (SSE 错误处理) 问题，然后逐步进行模块化重构。
