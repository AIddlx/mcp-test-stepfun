# MCP 2025-11-25 协议规范摘要

> 文档生成日期: 2026-03-10
> 协议版本: 2025-11-25
> 前一版本: 2025-06-18

---

## 目录

1. [概述](#概述)
2. [协议基础](#协议基础)
3. [必须实现的方法](#必须实现的方法)
4. [可选方法](#可选方法)
5. [Capabilities 结构](#capabilities-结构)
6. [工具定义结构](#工具定义结构)
7. [通知类型](#通知类型)
8. [与 2024-11-05 的主要差异](#与-2024-11-05-的主要差异)
9. [新特性详解](#新特性详解)

---

## 概述

MCP (Model Context Protocol) 是一个基于 JSON-RPC 2.0 的协议，用于在 LLM 应用和上下文提供者之间建立标准化通信。协议定义了客户端和服务端之间的能力协商、资源访问、工具调用等机制。

### 协议版本演进

- **2024-11-05**: 初始稳定版本
- **2025-06-18**: 中间版本
- **2025-11-25**: 当前版本（新增 Tasks、Icons、Sampling 工具调用等特性）

---

## 协议基础

### 消息类型

MCP 使用 JSON-RPC 2.0 消息格式，包含三种消息类型：

1. **Request** (请求)
   ```json
   {
     "jsonrpc": "2.0",
     "id": "string | number",
     "method": "string",
     "params": {}
   }
   ```

2. **Response** (响应)
   ```json
   {
     "jsonrpc": "2.0",
     "id": "string | number",
     "result": {} // 成功时
     // 或
     "error": {    // 失败时
       "code": number,
       "message": "string",
       "data": {}
     }
   }
   ```

3. **Notification** (通知)
   ```json
   {
     "jsonrpc": "2.0",
     "method": "string",
     "params": {}
   }
   ```

### 生命周期

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  初始化     │ ──► │   运行      │ ──► │   关闭      │
│  Initialize │     │  Operation  │     │  Shutdown   │
└─────────────┘     └─────────────┘     └─────────────┘
```

1. **初始化阶段**: 能力协商，建立连接参数
2. **运行阶段**: 正常的请求/响应交互
3. **关闭阶段**: 优雅关闭连接

### 传输方式

| 传输类型 | 描述 |
|---------|------|
| **stdio** | 标准输入/输出，用于本地进程通信 |
| **Streamable HTTP** | HTTP 传输，支持 SSE 和批量响应 |

---

## 必须实现的方法

### 客户端必须实现

| 方法 | 描述 | 版本 |
|------|------|------|
| `initialize` | 初始化连接，协商能力 | 核心方法 |
| `notifications/initialized` | 通知服务端初始化完成 | 核心方法 |

### 服务端必须实现

| 方法 | 描述 | 版本 |
|------|------|------|
| `initialize` | 响应客户端初始化请求，返回服务端能力 | 核心方法 |

---

## 可选方法

### 服务端功能 (Server Features)

#### Prompts (提示词)

| 方法 | 描述 |
|------|------|
| `prompts/list` | 列出可用提示词 |
| `prompts/get` | 获取特定提示词 |

#### Resources (资源)

| 方法 | 描述 |
|------|------|
| `resources/list` | 列出可用资源 |
| `resources/read` | 读取资源内容 |
| `resources/subscribe` | 订阅资源变更 |
| `resources/unsubscribe` | 取消订阅 |
| `resources/templates/list` | 列出资源模板 |

#### Tools (工具)

| 方法 | 描述 |
|------|------|
| `tools/list` | 列出可用工具 |
| `tools/call` | 调用工具 |
| `tools/cancel` | 取消工具执行 (实验性，Tasks) |

#### Completion (补全)

| 方法 | 描述 |
|------|------|
| `completion/complete` | 提供参数补全建议 |

#### Logging (日志)

| 方法 | 描述 |
|------|------|
| `logging/setLevel` | 设置日志级别 |

### 客户端功能 (Client Features)

#### Sampling (采样)

| 方法 | 描述 |
|------|------|
| `sampling/createMessage` | 请求 LLM 生成消息 |

#### Roots (根目录)

| 方法 | 描述 |
|------|------|
| `roots/list` | 列出客户端根目录 |

#### Elicitation (信息请求)

| 方法 | 描述 |
|------|------|
| `elicitation/create` | 向用户请求信息 |

---

## Capabilities 结构

### 客户端能力 (ClientCapabilities)

```typescript
interface ClientCapabilities {
  // 实验性特性
  experimental?: { [key: string]: object };

  // 根目录支持
  roots?: {
    listChanged?: boolean;  // 是否支持 roots/list_changed 通知
  };

  // 采样支持
  sampling?: {};

  // Elicitation 支持 (v2025-11-25)
  elicitation?: {};

  // Tasks 支持 (v2025-11-25, 实验性)
  tasks?: {};
}
```

### 服务端能力 (ServerCapabilities)

```typescript
interface ServerCapabilities {
  // 实验性特性
  experimental?: { [key: string]: object };

  // 提示词支持
  prompts?: {
    listChanged?: boolean;  // 是否支持 prompts/list_changed 通知
  };

  // 资源支持
  resources?: {
    subscribe?: boolean;     // 是否支持订阅
    listChanged?: boolean;   // 是否支持 resources/list_changed 通知
  };

  // 工具支持
  tools?: {
    listChanged?: boolean;   // 是否支持 tools/list_changed 通知
  };

  // 日志支持
  logging?: {};

  // 补全支持
  completion?: {};
}
```

### 初始化请求/响应示例

**请求:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {},
      "elicitation": {}
    },
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

**响应:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true },
      "prompts": {}
    },
    "serverInfo": {
      "name": "my-server",
      "version": "1.0.0"
    }
  }
}
```

---

## 工具定义结构

### 基本工具定义

```typescript
interface Tool {
  // 工具名称 (必需)
  name: string;

  // 工具描述 (必需)
  description: string;

  // 输入参数 Schema (必需)
  inputSchema: {
    type: "object";
    properties: { [key: string]: any };
    required?: string[];
  };

  // 输出 Schema (可选, v2025-11-25)
  outputSchema?: {
    type: "object";
    properties: { [key: string]: any };
  };

  // 图标 (可选, v2025-11-25)
  icons?: ToolIcons;

  // 执行选项 (可选, v2025-11-25)
  execution?: {
    taskSupport?: "forbidden" | "optional" | "required";
  };

  // 标题 (可选, v2025-11-25)
  title?: string;

  // 是否只读 (可选)
  readOnly?: boolean;

  // 是否破坏性 (可选)
  destructive?: boolean;

  // 是否幂等 (可选)
  idempotent?: boolean;

  // 是否开放世界 (可选)
  openWorld?: boolean;
}
```

### 工具图标 (ToolIcons)

```typescript
interface ToolIcons {
  // 小图标 (默认 16x16)
  small?: ImageContent;

  // 中等图标 (默认 32x32)
  medium?: ImageContent;

  // 大图标 (默认 64x64)
  large?: ImageContent;
}

interface ImageContent {
  type: "image";
  data: string;      // Base64 编码的图像数据
  mimeType: string;  // 如 "image/png", "image/svg+xml"
}
```

### 执行选项详解

| taskSupport 值 | 描述 |
|----------------|------|
| `"forbidden"` | 默认值。工具必须在单次调用中返回结果，不能使用 Tasks 机制 |
| `"optional"` | 工具可以选择使用 Tasks 机制进行异步处理 |
| `"required"` | 工具必须使用 Tasks 机制，适用于长时间运行的操作 |

### 工具调用请求

```typescript
interface CallToolRequest {
  method: "tools/call";
  params: {
    name: string;
    arguments?: { [key: string]: any };

    // v2025-11-25: Tasks 支持
    taskId?: string;      // 任务 ID（用于轮询）
    status?: string;      // 任务状态
    result?: any;         // 任务结果
  };
}
```

### 工具调用响应

**同步结果:**
```json
{
  "content": [
    { "type": "text", "text": "结果文本" },
    { "type": "image", "data": "...", "mimeType": "image/png" }
  ],
  "isError": false
}
```

**异步任务 (v2025-11-25):**
```json
{
  "taskId": "task-123",
  "status": "pending"
}
```

---

## 通知类型

### 连接生命周期通知

| 通知 | 方向 | 描述 |
|------|------|------|
| `notifications/initialized` | Client → Server | 客户端初始化完成 |
| `notifications/cancelled` | 双向 | 请求被取消 |
| `notifications/progress` | 双向 | 进度更新 |

### 列表变更通知

| 通知 | 方向 | 描述 |
|------|------|------|
| `notifications/resources/list_changed` | Server → Client | 资源列表已变更 |
| `notifications/prompts/list_changed` | Server → Client | 提示词列表已变更 |
| `notifications/tools/list_changed` | Server → Client | 工具列表已变更 |
| `notifications/roots/list_changed` | Client → Server | 根目录列表已变更 |

### 资源通知

| 通知 | 方向 | 描述 |
|------|------|------|
| `notifications/resources/updated` | Server → Client | 资源内容已更新 |

### 日志通知

| 通知 | 方向 | 描述 |
|------|------|------|
| `notifications/message` | Server → Client | 日志消息 |

### Tasks 通知 (v2025-11-25, 实验性)

| 通知 | 方向 | 描述 |
|------|------|------|
| `notifications/tasks/list_changed` | Server → Client | 任务列表已变更 |

---

## 与 2024-11-05 的主要差异

### 1. 新增特性

| 特性 | 描述 |
|------|------|
| **Tasks (实验性)** | 异步任务机制，支持长时间运行的操作通过轮询或延迟获取结果 |
| **Icons 元数据** | 工具、资源、提示词可携带图标，增强 UI 展示 |
| **execution.taskSupport** | 工具可声明其对异步任务的支持级别 |
| **Elicitation 增强** | 支持 URL 模式、带标题的枚举类型 |
| **Sampling 工具调用** | 采样请求可包含工具和 toolChoice 参数 |
| **JSON Schema 2020-12** | 新的默认 Schema 方言 |
| **HTTP 403 Origin 校验** | Streamable HTTP 传输中无效 Origin 返回 403 |
| **输入验证错误处理** | 输入验证失败作为工具执行错误而非协议错误 |

### 2. 主要变更

#### JSON Schema 版本升级

```typescript
// 2024-11-05: 使用 JSON Schema Draft 2020-12
inputSchema: {
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}

// 2025-11-25: 默认使用 JSON Schema 2020-12
// $schema 可选，默认为新版本
```

#### 工具定义扩展

```typescript
// 2024-11-05 基本定义
{
  name: "my-tool",
  description: "...",
  inputSchema: { ... }
}

// 2025-11-25 扩展定义
{
  name: "my-tool",
  title: "My Tool",           // 新增: 显示标题
  description: "...",
  inputSchema: { ... },
  outputSchema: { ... },       // 新增: 输出 Schema
  icons: { ... },              // 新增: 图标
  execution: {                 // 新增: 执行选项
    taskSupport: "optional"
  }
}
```

#### Elicitation 增强

```typescript
// 2025-11-25 新支持的类型
interface ElicitationRequest {
  message: string;
  requestedSchema: {
    type: "object";
    properties: {
      // 新增: URL 类型
      website: { type: "string", format: "uri" },

      // 新增: 带标题的枚举
      priority: {
        type: "string",
        enum: ["low", "medium", "high"],
        titles: ["低优先级", "中优先级", "高优先级"]
      }
    }
  };
}
```

#### Sampling 工具调用

```typescript
// 2025-11-25: Sampling 请求可包含工具
interface SamplingRequest {
  messages: Message[];
  tools?: Tool[];           // 新增: 可用工具列表
  toolChoice?: "auto" | "none" | "required" | { type: "tool", name: string };
  // ... 其他参数
}
```

### 3. Breaking Changes

| 变更 | 影响 |
|------|------|
| 输入验证错误处理 | 验证失败返回 `isError: true` 而非协议错误 |
| HTTP 403 校验 | 无效 Origin 请求返回 403 而非忽略 |

---

## 新特性详解

### Tasks (异步任务机制) - 实验性

Tasks 是一种用于处理长时间运行操作的机制，允许工具返回任务 ID 而非即时结果。

#### 工作流程

```
1. 客户端调用 tools/call
2. 服务端返回 taskId + status: "pending"
3. 客户端轮询 (或接收通知) 获取状态更新
4. 任务完成后返回最终结果
```

#### 状态值

| 状态 | 描述 |
|------|------|
| `pending` | 任务等待处理 |
| `running` | 任务正在执行 |
| `complete` | 任务已完成 |
| `failed` | 任务失败 |
| `cancelled` | 任务被取消 |

#### 能力声明

```json
{
  "capabilities": {
    "tasks": {}
  }
}
```

### Icons 元数据

图标支持多尺寸，适用于不同 UI 场景。

```typescript
// 工具图标
{
  "icons": {
    "small": {
      "type": "image",
      "data": "base64...",
      "mimeType": "image/png"
    },
    "medium": { ... },
    "large": { ... }
  }
}

// 服务端信息图标
{
  "serverInfo": {
    "name": "my-server",
    "version": "1.0.0",
    "icons": { ... }
  }
}
```

### execution.taskSupport 字段

```typescript
// 示例: 必须使用异步任务的工具
{
  "name": "process-large-file",
  "execution": {
    "taskSupport": "required"
  }
}

// 示例: 可选异步的工具
{
  "name": "search",
  "execution": {
    "taskSupport": "optional"
  }
}
```

### Elicitation 增强

#### URL 模式

```typescript
{
  "requestedSchema": {
    "type": "object",
    "properties": {
      "documentation": {
        "type": "string",
        "format": "uri",
        "description": "文档链接"
      }
    }
  }
}
```

#### 带标题的枚举

```typescript
{
  "requestedSchema": {
    "type": "object",
    "properties": {
      "environment": {
        "type": "string",
        "enum": ["dev", "staging", "prod"],
        "titles": ["开发环境", "测试环境", "生产环境"]
      }
    }
  }
}
```

### Sampling 工具调用支持

允许服务端在 Sampling 请求中提供工具，使 LLM 可以在生成过程中调用工具。

#### 请求格式

```typescript
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [...],
    "tools": [
      {
        "name": "get-weather",
        "description": "获取天气信息",
        "inputSchema": { ... }
      }
    ],
    "toolChoice": "auto"  // 或 "none", "required", { type: "tool", name: "get-weather" }
  }
}
```

#### 多轮工具调用循环

1. 服务端发送 `sampling/createMessage`，包含工具
2. LLM 返回工具调用请求
3. 服务端执行工具，将结果添加到消息
4. 继续调用 `sampling/createMessage` 直到 LLM 返回最终响应

### HTTP 403 Origin 校验

在 Streamable HTTP 传输中，服务端必须验证请求的 Origin 头。

```http
# 请求
POST /mcp HTTP/1.1
Origin: https://trusted-domain.com

# 有效 Origin - 正常响应
HTTP/1.1 200 OK

# 无效 Origin
HTTP/1.1 403 Forbidden
```

### 输入验证错误处理变更

#### 2024-11-05 (旧方式)
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

#### 2025-11-25 (新方式)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "输入验证失败: 参数 'path' 不能为空"
      }
    ],
    "isError": true
  }
}
```

---

## 错误处理

### 错误代码

| 代码 | 名称 | 描述 |
|------|------|------|
| -32700 | Parse error | JSON 解析失败 |
| -32600 | Invalid Request | 无效的 JSON-RPC 请求 |
| -32601 | Method not found | 方法不存在 |
| -32602 | Invalid params | 无效的参数 |
| -32603 | Internal error | 内部错误 |
| -32001 | Connection closed | 连接已关闭 |
| -32002 | Request timeout | 请求超时 |

### 工具执行错误 vs 协议错误

| 类型 | 处理方式 |
|------|---------|
| **协议错误** | 返回 JSON-RPC error 对象 |
| **工具执行错误** | 返回 `result.isError: true` + content |

---

## 参考链接

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP 2025-11-25 规范](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP 变更日志](https://modelcontextprotocol.io/specification/2025-11-25/changelog)
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core)
