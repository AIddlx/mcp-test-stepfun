# MCP 2025-11-25 协议合规差距分析报告

**分析日期**: 2026-03-10
**当前版本**: full_test_server.py v3.1
**目标版本**: MCP 2025-11-25

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [功能差距矩阵](#2-功能差距矩阵)
3. [必须实现的功能 (P0)](#3-必须实现的功能-p0)
4. [应该实现的功能 (P1)](#4-应该实现的功能-p1)
5. [可选实现的功能 (P2)](#5-可选实现的功能-p2)
6. [代码修改清单](#6-代码修改清单)
7. [工作量估算](#7-工作量估算)
8. [建议方案](#8-建议方案)

---

## 1. 执行摘要

### 1.1 关键发现

| 类别 | 状态 | 说明 |
|------|------|------|
| **协议版本** | 已声明 | `protocolVersion: "2025-11-25"` |
| **核心方法** | 基本完成 | initialize, tools/list, tools/call 等已实现 |
| **Capabilities 一致性** | 不一致 | 声明了 subscribe 但未实现 |
| **新特性支持** | 缺失 | Tasks, Icons, Elicitation, Sampling 等均未实现 |
| **安全合规** | 不合规 | 缺少 Origin 校验、认证机制 |
| **工具定义** | 不完整 | 缺少 outputSchema, icons, execution 等新字段 |

### 1.2 总体评估

**当前合规率**: 约 55%

主要差距集中在:
1. 2025-11-25 新特性 (Tasks, Icons, Elicitation URL 模式)
2. HTTP 安全要求 (Origin 校验)
3. 工具定义扩展字段
4. 输入验证错误处理方式

### 1.3 建议优先级

| 优先级 | 工作项 | 预计工时 |
|--------|--------|----------|
| P0 | Origin 校验 + Capabilities 一致性 | 2-3 天 |
| P1 | Tasks 支持 + 工具定义扩展 | 5-7 天 |
| P2 | Elicitation URL + Icons + Sampling 工具 | 3-5 天 |

---

## 2. 功能差距矩阵

### 2.1 核心协议

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| `initialize` | 必须 | 已实现 | 无 |
| `notifications/initialized` | 必须 | 已实现 | 无 |
| `ping` | 可选 | 已实现 | 无 |
| `notifications/cancelled` | 可选 | 未实现 | 需实现 |
| `notifications/progress` | 可选 | 已实现 | 需优化格式 |

### 2.2 工具系统

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| `tools/list` | 必须 | 已实现 | 缺少新字段 |
| `tools/call` | 必须 | 已实现 | 需支持任务模式 |
| `tools/cancel` | 可选 | 未实现 | 需实现 |
| `Tool.outputSchema` | 可选 | 缺失 | 应添加 |
| `Tool.icons` | 可选 | 缺失 | 应添加 |
| `Tool.title` | 可选 | 缺失 | 应添加 |
| `Tool.execution.taskSupport` | 可选 | 缺失 | 需添加 |
| `Tool.annotations` | 可选 | 缺失 | 应添加 |
| 输入验证错误处理 | 必须 | 部分实现 | 需改用 `isError: true` |

### 2.3 资源系统

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| `resources/list` | 可选 | 已实现 | 无 |
| `resources/read` | 可选 | 已实现 | 无 |
| `resources/subscribe` | 可选 | 声明但未实现 | **需移除声明或实现** |
| `resources/unsubscribe` | 可选 | 未实现 | 同上 |
| `resources/templates/list` | 可选 | 未实现 | 无 |
| `notifications/resources/list_changed` | 可选 | 声明但未发送 | 需实现或移除声明 |

### 2.4 提示系统

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| `prompts/list` | 可选 | 已实现 | 无 |
| `prompts/get` | 可选 | 已实现 | 无 |
| `notifications/prompts/list_changed` | 可选 | 声明但未发送 | 需实现或移除声明 |

### 2.5 日志和补全

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| `logging/setLevel` | 可选 | 已实现 | 无 |
| `notifications/message` | 可选 | 未实现 | 应添加 |
| `completion/complete` | 可选 | 已实现 | 无 |

### 2.6 2025-11-25 新特性

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| **Tasks** | 实验性 | 完全缺失 | **需完整实现** |
| `tasks/list` | 可选 | 未实现 | - |
| `tasks/get` | 可选 | 未实现 | - |
| `tasks/cancel` | 可选 | 未实现 | - |
| `tasks/result` | 可选 | 未实现 | - |
| `notifications/tasks/status` | 可选 | 未实现 | - |
| **Elicitation** | 可选 | 缺失 | 需实现 |
| `elicitation/create` (Form) | 可选 | 未实现 | - |
| `elicitation/create` (URL) | 可选 | 未实现 | - |
| **Sampling + Tools** | 可选 | 缺失 | 需扩展 |
| `sampling/createMessage` | 可选 | 未实现 | - |
| tools/toolChoice 支持 | 可选 | 未实现 | - |
| **Icons** | 可选 | 缺失 | 应添加 |
| Tool icons | 可选 | 未实现 | - |
| Server icons | 可选 | 未实现 | - |

### 2.7 HTTP 传输层安全

| 功能 | 规范要求 | 当前状态 | 差距 |
|------|----------|----------|------|
| **Origin 校验** | 必须 | 缺失 | **必须实现** |
| 本地绑定 (127.0.0.1) | 应该 | 已实现 | 无 |
| 请求大小限制 | 应该 | 缺失 | 应添加 |
| 请求超时 | 应该 | 缺失 | 应添加 |
| SSE 轮询 (SEP-1699) | 可选 | 缺失 | 可选实现 |

### 2.8 Capabilities 一致性

| Capability | 声明值 | 实际实现 | 一致性 |
|------------|--------|----------|--------|
| `tools.listChanged` | true | 未发送通知 | **不一致** |
| `resources.subscribe` | true | 未实现 | **不一致** |
| `resources.listChanged` | true | 未发送通知 | **不一致** |
| `prompts.listChanged` | true | 未发送通知 | **不一致** |
| `logging` | {} | 已实现 | 一致 |
| `streaming` | true | 已实现 | 一致 |
| `tasks` | 未声明 | 未实现 | 一致 |

---

## 3. 必须实现的功能 (P0)

### 3.1 HTTP 403 Origin 校验

**优先级**: 最高
**原因**: 安全要求，防止 DNS 重绑定攻击

**实现要求**:
```python
# 在 handle_mcp_request 开头添加
origin = request.headers.get("origin")
if origin and not is_origin_allowed(origin):
    return JSONResponse(
        {"error": "Invalid Origin"},
        status_code=403
    )
```

**允许列表**:
```python
ALLOWED_ORIGINS = {
    "http://localhost",
    "http://127.0.0.1",
    "http://[::1]",
    "null",  # file:// 协议
}
```

### 3.2 Capabilities 一致性修复

**优先级**: 高
**原因**: 声明与实现不一致会导致客户端错误

**方案 A - 移除未实现的声明**:
```python
# 修改 initialize 响应
{
    "capabilities": {
        "tools": {"listChanged": false},  # 改为 false
        "resources": {"subscribe": false, "listChanged": false},  # 改为 false
        "prompts": {"listChanged": false},  # 改为 false
        "logging": {},
        "streaming": true
    }
}
```

**方案 B - 实现缺失功能**:
- 实现 `resources/subscribe` 和 `resources/unsubscribe`
- 发送 `notifications/tools/list_changed` 等通知

**推荐**: 方案 A (快速修复)

### 3.3 输入验证错误处理

**优先级**: 高
**原因**: SEP-1303 要求，影响 LLM 自我纠正能力

**当前行为** (不合规):
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "error": {
        "code": -32602,
        "message": "Invalid params"
    }
}
```

**要求行为**:
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {"type": "text", "text": "参数验证失败: city 不能为空"}
        ],
        "isError": true
    }
}
```

### 3.4 请求大小限制

**优先级**: 中
**原因**: 防止 DoS 攻击

```python
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

async def handle_mcp_request(request):
    content_length = int(request.headers.get("content-length", 0))
    if content_length > MAX_REQUEST_SIZE:
        return JSONResponse(
            {"error": "Request too large"},
            status_code=413
        )
```

---

## 4. 应该实现的功能 (P1)

### 4.1 Tasks 异步任务系统

**优先级**: 高
**原因**: 2025-11-25 核心新特性，支持长时间运行操作

**需要实现**:

| 方法 | 说明 |
|------|------|
| `tasks/list` | 列出任务 |
| `tasks/get` | 获取任务状态 |
| `tasks/cancel` | 取消任务 |
| `tasks/result` | 获取任务结果 |
| `notifications/tasks/status` | 任务状态通知 |

**Capability 声明**:
```json
{
    "capabilities": {
        "tasks": {
            "list": {},
            "cancel": {},
            "requests": {
                "tools": {
                    "call": {}
                }
            }
        }
    }
}
```

**工作量**: 3-5 天

### 4.2 工具定义扩展

**优先级**: 高
**原因**: 提升工具可发现性和可用性

**需要添加的字段**:

```python
{
    "name": "test_ping",
    "title": "Ping 测试",  # 新增
    "description": "[A1] 测试基础连通性...",
    "inputSchema": {...},
    "outputSchema": {     # 新增
        "type": "object",
        "properties": {
            "pong": {"type": "boolean"},
            "server_time": {"type": "string"}
        }
    },
    "icons": [            # 新增
        {"src": "data:image/png;base64,...", "mimeType": "image/png", "sizes": ["48x48"]}
    ],
    "execution": {        # 新增
        "taskSupport": "optional"
    },
    "annotations": {      # 新增
        "readOnlyHint": true,
        "destructiveHint": false
    }
}
```

**工作量**: 2-3 天

### 4.3 请求超时处理

**优先级**: 中
**原因**: 防止长时间请求阻塞

```python
import asyncio

REQUEST_TIMEOUT = 30  # 秒

async def handle_tool_call_with_timeout(params):
    try:
        result = await asyncio.wait_for(
            call_tool(params),
            timeout=REQUEST_TIMEOUT
        )
        return result
    except asyncio.TimeoutError:
        return {
            "content": [{"type": "text", "text": "请求超时"}],
            "isError": True
        }
```

**工作量**: 0.5 天

### 4.4 通知系统完善

**优先级**: 中
**原因**: 增强实时性

**需要添加**:
- `notifications/tools/list_changed`
- `notifications/resources/list_changed`
- `notifications/prompts/list_changed`
- `notifications/cancelled`
- `notifications/message`

**工作量**: 1-2 天

---

## 5. 可选实现的功能 (P2)

### 5.1 Elicitation 机制

**优先级**: 中低
**原因**: 高级交互场景

**Form 模式**:
```json
{
    "method": "elicitation/create",
    "params": {
        "mode": "form",
        "message": "请提供配置信息",
        "requestedSchema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"}
            }
        }
    }
}
```

**URL 模式** (OAuth 场景):
```json
{
    "method": "elicitation/create",
    "params": {
        "mode": "url",
        "elicitationId": "uuid",
        "url": "https://oauth.example.com/authorize",
        "message": "请授权访问"
    }
}
```

**工作量**: 2-3 天

### 5.2 Sampling 工具调用

**优先级**: 中低
**原因**: 代理循环场景

```json
{
    "method": "sampling/createMessage",
    "params": {
        "messages": [...],
        "tools": [{"name": "get_weather", ...}],
        "toolChoice": {"mode": "auto"}
    }
}
```

**工作量**: 2-3 天

### 5.3 Icons 元数据

**优先级**: 低
**原因**: UI 增强

```json
{
    "serverInfo": {
        "name": "test-server",
        "version": "1.0.0",
        "icons": [
            {"src": "https://example.com/icon.png", "sizes": ["48x48"]}
        ]
    }
}
```

**工作量**: 0.5 天

### 5.4 SSE 轮询支持 (SEP-1699)

**优先级**: 低
**原因**: 长连接优化

**工作量**: 1-2 天

### 5.5 JSON Schema 2020-12

**优先级**: 低
**原因**: 规范对齐

**工作量**: 0.5 天 (添加 `$schema` 声明)

---

## 6. 代码修改清单

### 6.1 full_test_server.py 修改

| 位置 | 修改内容 | 优先级 |
|------|----------|--------|
| `handle_mcp_request` 开头 | 添加 Origin 校验 | P0 |
| `handle_mcp_request` 开头 | 添加请求大小检查 | P0 |
| `initialize` 响应 | 修正 capabilities 声明 | P0 |
| `call_tool` 函数 | 修改验证错误返回方式 | P0 |
| 全局 | 添加请求超时处理 | P1 |
| 工具定义 (`CORE_TOOLS` 等) | 添加 outputSchema, icons, execution | P1 |
| 新增 | Tasks 相关方法处理器 | P1 |
| 新增 | 通知发送逻辑 | P1 |

### 6.2 新增文件建议

| 文件 | 内容 | 优先级 |
|------|------|--------|
| `task_manager.py` | Tasks 管理 | P1 |
| `origin_validator.py` | Origin 校验 | P0 |
| `notification_sender.py` | 通知发送 | P1 |

### 6.3 工具定义模板

```python
# 修改前
CORE_TOOLS = [
    {
        "name": "test_ping",
        "description": "[A1] 测试基础连通性...",
        "inputSchema": {...}
    }
]

# 修改后
CORE_TOOLS = [
    {
        "name": "test_ping",
        "title": "Ping 测试",
        "description": "[A1] 测试基础连通性...",
        "inputSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            ...
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "pong": {"type": "boolean"},
                "server_time": {"type": "string"}
            }
        },
        "execution": {
            "taskSupport": "forbidden"
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False
        }
    }
]
```

---

## 7. 工作量估算

### 7.1 按优先级

| 优先级 | 工作项 | 工时 | 风险 |
|--------|--------|------|------|
| P0 | Origin 校验 | 0.5 天 | 低 |
| P0 | Capabilities 修复 | 0.5 天 | 低 |
| P0 | 验证错误处理 | 1 天 | 低 |
| P0 | 请求大小限制 | 0.5 天 | 低 |
| **P0 小计** | - | **2.5 天** | - |
| P1 | Tasks 系统 | 4 天 | 中 |
| P1 | 工具定义扩展 | 2 天 | 低 |
| P1 | 超时处理 | 0.5 天 | 低 |
| P1 | 通知系统 | 1.5 天 | 低 |
| **P1 小计** | - | **8 天** | - |
| P2 | Elicitation | 2.5 天 | 中 |
| P2 | Sampling 工具 | 2 天 | 中 |
| P2 | Icons | 0.5 天 | 低 |
| P2 | SSE 轮询 | 1.5 天 | 中 |
| **P2 小计** | - | **6.5 天** | - |
| **总计** | - | **17 天** | - |

### 7.2 测试和文档

| 类型 | 工时 |
|------|------|
| 单元测试 | 3 天 |
| 集成测试 | 2 天 |
| 文档更新 | 1 天 |
| **小计** | **6 天** |

### 7.3 总工时

| 场景 | 工时 |
|------|------|
| 仅 P0 | 2.5 + 1 (测试) = 3.5 天 |
| P0 + P1 | 10.5 + 4 (测试) = 14.5 天 |
| 完整实现 | 17 + 6 = 23 天 |

---

## 8. 建议方案

### 8.1 方案对比

| 方案 | 工时 | 合规率 | 风险 | 推荐度 |
|------|------|--------|------|--------|
| **增量修复 (P0)** | 3-4 天 | 70% | 低 | 推荐 (短期) |
| **增量修复 (P0+P1)** | 14-16 天 | 90% | 中 | 推荐 (中期) |
| **完整实现** | 20-25 天 | 100% | 中 | 可选 |
| **重写 (使用 SDK)** | 15-20 天 | 95% | 高 | 可选 |

### 8.2 推荐: 增量修改 (分阶段)

**阶段 1: 安全合规 (1 周)**
- Origin 校验
- Capabilities 一致性
- 验证错误处理
- 请求限制

**阶段 2: 核心新特性 (2 周)**
- Tasks 系统
- 工具定义扩展
- 通知完善

**阶段 3: 高级特性 (1-2 周)**
- Elicitation
- Sampling 工具
- Icons

### 8.3 使用 MCP Python SDK 的考量

**优势**:
- 类型定义完整 (Tasks, Elicitation 等)
- 自动处理协议细节
- 社区维护

**劣势**:
- 需要重写现有代码
- 学习曲线
- 可能与现有架构不兼容

**建议**:
- 当前代码可以继续使用
- 逐步引入 SDK 类型定义
- 新功能优先使用 SDK

### 8.4 迁移路径

```
当前状态 (v3.1)
    |
    v
阶段 1: P0 修复 (合规 70%)
    |
    v
阶段 2: P1 实现 (合规 90%)
    |
    v
阶段 3: P2 实现 (合规 100%)
    |
    v
可选: 重构使用 SDK
```

---

## 附录 A: MCP Python SDK 支持状态

| 特性 | SDK 支持 | 当前实现 | 差距 |
|------|----------|----------|------|
| Protocol 2025-11-25 | 已支持 | 已声明 | 无 |
| Tasks | 完整类型 | 无 | 需实现逻辑 |
| Elicitation (Form) | 完整类型 | 无 | 需实现逻辑 |
| Elicitation (URL) | 完整类型 | 无 | 需实现逻辑 |
| Sampling + Tools | 完整类型 | 无 | 需实现逻辑 |
| Tool.title | 已支持 | 无 | 需添加 |
| Tool.outputSchema | 已支持 | 无 | 需添加 |
| Tool.icons | 已支持 | 无 | 需添加 |
| Tool.annotations | 已支持 | 无 | 需添加 |
| Tool.execution | 已支持 | 无 | 需添加 |

**结论**: SDK 类型定义完整，可直接使用，无需手动定义。

---

## 附录 B: 参考资料

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [SEP-973: Icons](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/973)
- [SEP-1303: Input Validation Errors](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1303)
- [SEP-1613: JSON Schema 2020-12](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1613)
- [SEP-1699: SSE Polling](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1699)

---

*报告生成时间: 2026-03-10*
