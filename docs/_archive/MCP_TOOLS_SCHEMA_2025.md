# MCP Tools Schema 2025-11-25 规范详解

本文档详细说明 MCP 协议 2025-11-25 版本中工具定义的变更，涵盖六个核心 SEP (Specification Enhancement Proposal)。

---

## 目录

1. [Icons 元数据 (SEP-973)](#1-icons-元数据-sep-973)
2. [execution.taskSupport 字段](#2-executiontasksupport-字段)
3. [JSON Schema 2020-12 (SEP-1613)](#3-json-schema-2020-12-sep-1613)
4. [输入验证错误处理 (SEP-1303)](#4-输入验证错误处理-sep-1303)
5. [工具命名指南 (SEP-986)](#5-工具命名指南-sep-986)
6. [Implementation description 字段](#6-implementation-description-字段)
7. [完整工具定义规范](#7-完整工具定义规范)
8. [实现示例](#8-实现示例)

---

## 1. Icons 元数据 (SEP-973)

### 概述

SEP-973 允许 MCP 服务器在元数据中定义 `icons` 字段，为工具、资源、资源模板、提示词和实现提供自定义图标标识。

### Icon 数据结构

```typescript
interface Icon {
  /**
   * 图标资源的 URI。
   * 可以是标准 URL 或 base64 编码的 data URI。
   * @format uri
   */
  src: string;

  /**
   * 可选的 MIME 类型覆盖。
   * 当服务器的 MIME 类型缺失或为通用类型时使用。
   */
  mimeType?: string;

  /**
   * 图标尺寸。
   * 例如: "48x48", "96x96", "any" (SVG), "48x48 96x96"
   */
  sizes?: string[];

  /**
   * 主题适配 (2025-11-25 新增)。
   * 用于指定图标适用的主题。
   */
  theme?: "light" | "dark";
}
```

### 支持的 MIME 类型

**客户端必须支持:**
- `image/png` - PNG 图像 (安全，通用兼容)
- `image/jpeg` (和 `image/jpg`) - JPEG 图像 (安全，通用兼容)

**客户端应该支持:**
- `image/svg+xml` - SVG 图像 (可缩放，但需要安全预防措施)
- `image/webp` - WebP 图像 (现代，高效格式)

### 安全注意事项

1. **URL 来源验证**: 消费者必须确保图标 URL 来自与客户端/服务器相同的域或受信任的域
2. **SVG 安全**: SVG 可能包含可执行的 JavaScript，消费者必须采取适当的预防措施

### 应用范围

`icons` 字段可添加到以下接口:
- `Implementation` - 服务器/客户端实现
- `Tool` - 工具
- `Resource` - 资源
- `ResourceTemplate` - 资源模板
- `Prompt` - 提示词

### 示例

```json
{
  "name": "weather_tool",
  "description": "获取天气信息",
  "icons": [
    {
      "src": "https://example.com/icons/weather-48.png",
      "mimeType": "image/png",
      "sizes": ["48x48"]
    },
    {
      "src": "https://example.com/icons/weather-dark.svg",
      "mimeType": "image/svg+xml",
      "sizes": ["any"],
      "theme": "dark"
    }
  ],
  "inputSchema": {
    "type": "object",
    "properties": {
      "city": { "type": "string" }
    }
  }
}
```

---

## 2. execution.taskSupport 字段

### 概述

`execution.taskSupport` 字段用于声明工具对任务增强执行 (Task-Augmented Execution) 的支持级别。这是 MCP 任务系统的一部分，允许长时间运行的操作进行轮询和延迟结果检索。

### 字段定义

```typescript
interface ToolExecution {
  /**
   * 声明工具对任务增强执行的支持级别。
   * - "forbidden": 不支持任务执行 (默认)
   * - "optional": 可选支持任务执行
   * - "required": 必须使用任务执行
   */
  taskSupport?: "forbidden" | "optional" | "required";
}

interface Tool {
  // ... 其他字段
  execution?: ToolExecution;
}
```

### 与 capabilities.tasks 的关系

#### Server Capabilities

服务器通过 `capabilities.tasks` 声明对任务的支持:

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

#### 能力协商规则

1. **基础能力检查**:
   - 如果服务器的 `capabilities` 不包含 `tasks.requests.tools.call`，客户端**绝不能**尝试对该服务器的工具使用任务增强，无论 `execution.taskSupport` 值为何

2. **工具级别协商** (当服务器支持 tasks.requests.tools.call 时):

| taskSupport 值 | 客户端行为 | 服务器行为 |
|---------------|-----------|-----------|
| 不存在或 `"forbidden"` | **绝不能**尝试将工具作为任务调用 | 应返回 `-32601` (Method not found) 错误 |
| `"optional"` | **可以**将工具作为任务或普通请求调用 | - |
| `"required"` | **必须**将工具作为任务调用 | 必须返回 `-32601` 错误如果客户端不这样做 |

### 任务增强请求示例

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "long_running_analysis",
    "arguments": { "dataset": "large_file.csv" },
    "task": {
      "ttl": 60000
    }
  }
}

// 响应 (立即返回任务信息)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "task": {
      "taskId": "786512e2-9e0d-44bd-8f29-789f320fe840",
      "status": "working",
      "statusMessage": "操作正在进行中",
      "createdAt": "2025-11-25T10:30:00Z",
      "lastUpdatedAt": "2025-11-25T10:40:00Z",
      "ttl": 60000,
      "pollInterval": 5000
    }
  }
}
```

### 任务状态

```
TaskStatus: "working" | "input_required" | "completed" | "failed" | "cancelled"
```

---

## 3. JSON Schema 2020-12 (SEP-1613)

### 概述

SEP-1613 确立 JSON Schema 2020-12 作为 MCP 内嵌 schema 的默认方言。这解决了之前实现之间因假设不同版本而导致的兼容性问题。

### 默认方言

当没有 `$schema` 字段时，MCP 消息中的内嵌 JSON schema **必须**符合 JSON Schema 2020-12 规范。

### 显式方言声明

Schema **可以**包含显式的 `$schema` 字段来声明不同的方言:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "name": { "type": "string" }
  }
}
```

### 无参数工具的 Schema 处理

对于没有参数的工具，`inputSchema` 字段**绝不能**为 `null`。使用以下有效方式之一:

```json
// 方式 1: 最宽松 - 接受任何输入
{ "inputSchema": true }

// 方式 2: 等同于 true - 接受任何输入
{ "inputSchema": {} }

// 方式 3: 接受任何对象
{ "inputSchema": { "type": "object" } }

// 方式 4: 只接受空对象 {}
{
  "inputSchema": {
    "type": "object",
    "additionalProperties": false
  }
}
```

### 应用范围

- `tools/list` 响应中的 `inputSchema` 和 `outputSchema`
- `prompts/elicit` 请求中的 `requestedSchema`
- 任何未来嵌入 JSON Schema 定义的 MCP 功能

### JSON Schema 2020-12 vs Draft-07 主要差异

| 特性 | Draft-07 | 2020-12 |
|-----|----------|---------|
| 条件依赖 | `dependencies` | `dependentSchemas` + `dependentRequired` |
| 数组前缀验证 | `items` + `additionalItems` | `prefixItems` + `items` |
| 循环引用 | 需要特殊处理 | 原生支持 `$recursiveRef` |
| 组合验证 | `allOf`, `anyOf`, `oneOf` | 同上，行为更清晰 |

### 迁移建议

对于假设 Draft-07 的现有 schema:
1. 添加显式 `$schema: "http://json-schema.org/draft-07/schema#"` 作为过渡
2. 逐步更新到 2020-12 特性

---

## 4. 输入验证错误处理 (SEP-1303)

### 概述

SEP-1303 明确工具输入验证错误应作为 **Tool Execution Errors** 而非 **Protocol Errors** 返回。这使得语言模型能够在上下文窗口中接收验证错误反馈，从而自我纠正并成功完成任务。

### 问题背景

之前的行为:
- 验证错误作为 Protocol Error 返回 (JSON-RPC error)
- 模型无法看到错误消息
- 模型重复相同的错误
- 任务失败需要人工干预

### 新的行为

验证错误作为 Tool Execution Error 返回:

```json
// 错误的请求
{
  "method": "tools/call",
  "params": {
    "name": "book_flight",
    "arguments": {
      "departureDate": "12/12/2024"  // 过去的日期
    }
  }
}

// 返回 Tool Execution Error (模型可见)
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "日期必须是将来的日期。当前日期是 10/03/2026"
      }
    ],
    "isError": true
  }
}
```

### 错误类型对比

| 错误类型 | 返回方式 | 模型可见 | 用例 |
|---------|---------|---------|------|
| Protocol Error | JSON-RPC `error` 字段 | 否 | 未知工具、服务器错误 |
| Tool Execution Error | `result` 中 `isError: true` | 是 | API 失败、输入验证、业务逻辑错误 |

### 实现要求

**服务器应该:**
- 对所有工具参数验证失败返回 Tool Execution Error
- 在错误消息中提供清晰的反馈
- 包含足够的信息让模型能够自我纠正

**错误消息示例:**

```json
{
  "content": [
    {
      "type": "text",
      "text": "参数验证失败:\n- departureDate: 日期格式必须为 dd/mm/yyyy\n- passengers: 必须是 1-9 之间的整数"
    }
  ],
  "isError": true
}
```

---

## 5. 工具命名指南 (SEP-986)

### 概述

SEP-986 为工具名称提供了清晰的标准化格式，以最大化兼容性、清晰度和互操作性。

### 命名规范

1. **长度**: 工具名称应为 1-64 个字符 (包含)
2. **大小写**: 工具名称区分大小写
3. **允许的字符**:
   - 大写字母 A-Z
   - 小写字母 a-z
   - 数字 0-9
   - 下划线 `_`
   - 连字符 `-`
   - 点 `.`
   - 正斜杠 `/`
4. **禁止的字符**: 空格、逗号和其他特殊字符
5. **唯一性**: 工具名称应在其命名空间内唯一

### 有效示例

```
getUser                    // 驼峰命名
user-profile/update        // 层级命名 (斜杠分隔)
DATA_EXPORT_v2             // 全大写带版本
admin.tools.list           // 点分隔命名空间
search_items               // 蛇形命名
get-user-info              // 短横线命名
```

### 无效示例

```
get user info              // 包含空格
tool,name                  // 包含逗号
tool@home                  // 包含特殊字符 @
a                          // 太短 (少于1个字符是不可能的)
```

### 命名约定建议

| 风格 | 示例 | 适用场景 |
|-----|------|---------|
| camelCase | `getUser`, `calculateTotal` | 通用推荐 |
| snake_case | `get_user`, `calculate_total` | Python 生态 |
| kebab-case | `get-user`, `calculate-total` | CLI 工具 |
| 命名空间 | `user.profile/update` | 大型系统 |
| 版本化 | `api.v2.getUser` | API 版本控制 |

---

## 6. Implementation description 字段

### 概述

2025-11-25 版本为 `Implementation` 接口添加了可选的 `description` 字段，用于提供初始化期间的人类可读上下文，并与 MCP 注册表的 `server.json` 格式对齐。

### 数据结构

```typescript
interface Implementation {
  /** 实现名称 */
  name: string;

  /** 人类可读的标题 */
  title?: string;

  /** 版本号 */
  version: string;

  /**
   * 实现的描述。
   * 提供初始化期间的人类可读上下文。
   */
  description?: string;

  /** 图标列表 */
  icons?: Icon[];

  /** 网站 URL */
  websiteUrl?: string;
}
```

### 使用示例

```json
// 初始化响应
{
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": { ... },
    "serverInfo": {
      "name": "weather-mcp-server",
      "title": "Weather MCP Server",
      "version": "1.0.0",
      "description": "提供全球天气数据查询服务，支持当前天气、预报和历史数据",
      "websiteUrl": "https://github.com/example/weather-mcp",
      "icons": [
        {
          "src": "https://example.com/weather-icon.png",
          "mimeType": "image/png",
          "sizes": ["48x48"]
        }
      ]
    }
  }
}
```

---

## 7. 完整工具定义规范

### Tool 接口

```typescript
interface Tool {
  /** 工具图标列表 (SEP-973) */
  icons?: Icon[];

  /** 工具名称 (1-64 字符, SEP-986) */
  name: string;

  /** 人类可读的标题 */
  title?: string;

  /** 工具描述 */
  description?: string;

  /**
   * 输入参数的 JSON Schema。
   * 默认使用 JSON Schema 2020-12 (SEP-1613)。
   * 绝不能为 null。
   */
  inputSchema: {
    /** 可选的 schema 方言声明 */
    $schema?: string;
    type: "object";
    properties?: { [key: string]: object };
    required?: string[];
  };

  /**
   * 执行配置 (包含任务支持设置)
   */
  execution?: ToolExecution;

  /**
   * 输出的 JSON Schema (可选)
   */
  outputSchema?: {
    $schema?: string;
    type: "object";
    properties?: { [key: string]: object };
    required?: string[];
  };

  /** 工具注解 */
  annotations?: ToolAnnotations;

  /** 元数据 */
  _meta?: { [key: string]: unknown };
}

interface ToolExecution {
  /**
   * 任务支持级别 (SEP-1686)
   * - "forbidden": 不支持 (默认)
   * - "optional": 可选支持
   * - "required": 必须使用
   */
  taskSupport?: "forbidden" | "optional" | "required";
}

interface ToolAnnotations {
  /** 人类可读的标题 */
  title?: string;

  /** 是否为只读操作 */
  readOnlyHint?: boolean;

  /** 是否为破坏性操作 */
  destructiveHint?: boolean;

  /** 是否为幂等操作 */
  idempotentHint?: boolean;

  /** 是否与外部世界交互 */
  openWorldHint?: boolean;
}

interface Icon {
  src: string;
  mimeType?: string;
  sizes?: string[];
  theme?: "light" | "dark";
}
```

### CallToolRequest

```typescript
interface CallToolRequest {
  jsonrpc: "2.0";
  id: RequestId;
  method: "tools/call";
  params: CallToolRequestParams;
}

interface CallToolRequestParams {
  /** 任务元数据 (用于任务增强执行) */
  task?: TaskMetadata;

  /** 进度令牌等元数据 */
  _meta?: {
    progressToken?: ProgressToken;
    [key: string]: unknown;
  };

  /** 工具名称 */
  name: string;

  /** 工具参数 */
  arguments?: { [key: string]: unknown };
}

interface TaskMetadata {
  /** 任务存活时间 (毫秒) */
  ttl?: number;
}
```

### CallToolResult

```typescript
interface CallToolResult {
  /** 元数据 */
  _meta?: { [key: string]: unknown };

  /** 内容块数组 */
  content: ContentBlock[];

  /** 结构化内容 (可选) */
  structuredContent?: { [key: string]: unknown };

  /**
   * 是否为错误。
   * 输入验证错误应设置此字段为 true (SEP-1303)
   */
  isError?: boolean;
}
```

---

## 8. 实现示例

### 完整的 Tool 定义示例

```json
{
  "name": "weather/forecast",
  "title": "天气预报",
  "description": "获取指定城市的天气预报信息，支持未来7天的预报",
  "icons": [
    {
      "src": "https://example.com/icons/weather-light.png",
      "mimeType": "image/png",
      "sizes": ["48x48"],
      "theme": "light"
    },
    {
      "src": "https://example.com/icons/weather-dark.png",
      "mimeType": "image/png",
      "sizes": ["48x48"],
      "theme": "dark"
    }
  ],
  "inputSchema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "城市名称"
      },
      "days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 7,
        "default": 3,
        "description": "预报天数 (1-7)"
      },
      "unit": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "default": "celsius",
        "description": "温度单位"
      }
    },
    "required": ["city"]
  },
  "outputSchema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
      "city": { "type": "string" },
      "forecasts": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "date": { "type": "string", "format": "date" },
            "high": { "type": "number" },
            "low": { "type": "number" },
            "condition": { "type": "string" }
          }
        }
      }
    }
  },
  "execution": {
    "taskSupport": "optional"
  },
  "annotations": {
    "title": "天气预报",
    "readOnlyHint": true,
    "destructiveHint": false,
    "idempotentHint": true,
    "openWorldHint": true
  }
}
```

### 输入验证错误返回示例

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "参数验证失败:\n- city: 必填字段不能为空\n- days: 值 10 超出允许范围 (1-7)\n- unit: 无效值 'kelvin'，允许的值: celsius, fahrenheit"
      }
    ],
    "isError": true,
    "_meta": {}
  }
}
```

### 任务增强调用示例

```json
// 1. 初始请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "weather/forecast",
    "arguments": {
      "city": "Beijing",
      "days": 7
    },
    "task": {
      "ttl": 30000
    }
  }
}

// 2. 立即返回任务信息
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "task": {
      "taskId": "abc-123-def",
      "status": "working",
      "statusMessage": "正在获取天气数据...",
      "createdAt": "2025-11-25T10:30:00Z",
      "lastUpdatedAt": "2025-11-25T10:30:00Z",
      "ttl": 30000,
      "pollInterval": 2000
    }
  }
}

// 3. 轮询任务状态 (tasks/get)
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tasks/get",
  "params": {
    "taskId": "abc-123-def"
  }
}

// 4. 任务完成通知 (可选)
{
  "jsonrpc": "2.0",
  "method": "notifications/tasks/status",
  "params": {
    "taskId": "abc-123-def",
    "status": "completed",
    "createdAt": "2025-11-25T10:30:00Z",
    "lastUpdatedAt": "2025-11-25T10:30:05Z",
    "ttl": 30000
  }
}

// 5. 获取任务结果 (tasks/result)
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tasks/result",
  "params": {
    "taskId": "abc-123-def"
  }
}

// 6. 最终结果
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "北京未来7天天气预报:\n..."
      }
    ],
    "isError": false,
    "_meta": {
      "io.modelcontextprotocol/related-task": {
        "taskId": "abc-123-def"
      }
    }
  }
}
```

### Python SDK 实现示例

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

# 创建服务器
server = Server("weather-server")

# 定义工具
@server.tool(
    name="weather/forecast",
    title="天气预报",
    description="获取指定城市的天气预报",
    icons=[
        {
            "src": "https://example.com/weather.png",
            "mimeType": "image/png",
            "sizes": ["48x48"]
        }
    ],
    execution={"taskSupport": "optional"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_weather_forecast(
    city: str,
    days: int = 3,
    unit: str = "celsius"
) -> list[TextContent]:
    """
    获取天气预报

    Args:
        city: 城市名称
        days: 预报天数 (1-7)
        unit: 温度单位 (celsius/fahrenheit)

    Returns:
        天气预报文本
    """
    # 输入验证 (验证错误作为 Tool Execution Error 返回)
    if days < 1 or days > 7:
        return [
            TextContent(
                type="text",
                text=f"参数验证失败: days 值 {days} 超出允许范围 (1-7)"
            )
        ], True  # isError=True

    if unit not in ["celsius", "fahrenheit"]:
        return [
            TextContent(
                type="text",
                text=f"参数验证失败: unit 无效值 '{unit}'，允许的值: celsius, fahrenheit"
            )
        ], True

    # 执行实际逻辑
    forecast_data = await fetch_weather(city, days, unit)

    return [
        TextContent(
            type="text",
            text=format_forecast(forecast_data)
        )
    ], False  # isError=False
```

---

## 参考资料

- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Schema Reference](https://modelcontextprotocol.io/specification/2025-11-25/schema)
- [SEP-973: Icons and Additional Metadata](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/973)
- [SEP-986: Tool Name Format](https://modelcontextprotocol.io/community/seps/986-specify-format-for-tool-names)
- [SEP-1303: Input Validation Errors](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1303)
- [SEP-1613: JSON Schema 2020-12](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1613)
- [MCP Tasks Specification](https://modelcontextprotocol.io/specification/draft/basic/utilities/tasks)
