# MCP Elicitation 与 Sampling 机制 (2025-11-25)

本文档总结 MCP 2025-11-25 规范中 Elicitation 和 Sampling 机制的主要变更。

---

## 目录

1. [Elicitation 变更概览](#elicitation-变更概览)
2. [URL Mode Elicitation (SEP-1036)](#url-mode-elicitation-sep-1036)
3. [Enum Schema 改进 (SEP-1330)](#enum-schema-改进-sep-1330)
4. [默认值支持 (SEP-1034)](#默认值支持-sep-1034)
5. [Sampling 工具调用支持 (SEP-1577)](#sampling-工具调用支持-sep-1577)
6. [Python 实现示例](#python-实现示例)

---

## Elicitation 变更概览

MCP 2025-11-25 版本对 Elicitation 机制进行了重大增强：

| 特性 | SEP | 状态 |
|------|-----|------|
| URL Mode Elicitation | SEP-1036 | Proposal |
| Enum Schema 改进 | SEP-1330 | Final |
| 默认值支持 | SEP-1034 | Accepted |

### 客户端能力声明

```json
{
  "capabilities": {
    "elicitation": {
      "form": {},
      "url": {}
    }
  }
}
```

---

## URL Mode Elicitation (SEP-1036)

### 概述

URL Mode Elicitation 引入了一种新的带外交互模式，用于处理敏感数据收集、第三方 OAuth 授权和支付流程等场景，这些操作**不经过 MCP 客户端**。

### 核心差异

| 模式 | 交互方式 | 适用场景 |
|------|----------|----------|
| **Form Mode** | 带内 (in-band) | 普通信息收集，如表单输入 |
| **URL Mode** | 带外 (out-of-band) | 敏感凭据、OAuth 授权、支付 |

### 请求结构

#### Form Mode 请求

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "elicitation/create",
  "params": {
    "mode": "form",
    "message": "Please provide your GitHub username",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "username": {
          "type": "string",
          "title": "Username"
        }
      },
      "required": ["username"]
    }
  }
}
```

#### URL Mode 请求

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "elicitation/create",
  "params": {
    "mode": "url",
    "elicitationId": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://github.com/login/oauth/authorize?client_id=abc123&state=xyz789",
    "message": "Please authorize access to your GitHub repositories."
  }
}
```

### 响应结构

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "action": "accept"  // 或 "decline" 或 "cancel"
  }
}
```

### 完成通知

服务器应发送完成通知：

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/elicitation/complete",
  "params": {
    "elicitationId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### URL Elicitation Required 错误

当请求需要先完成 URL 授权时：

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32042,
    "message": "This request requires more information.",
    "data": {
      "elicitations": [
        {
          "mode": "url",
          "elicitationId": "550e8400-e29b-41d4-a716-446655440000",
          "url": "https://oauth.example.com/authorize?...",
          "message": "Authorization is required."
        }
      ]
    }
  }
}
```

### 安全考虑

1. **SSRF 防护**: 客户端必须验证 URL
2. **协议限制**: 仅允许 HTTPS URL
3. **域名校验**: 客户端必须清晰显示目标域名
4. **身份验证**: 服务器必须验证完成交互的用户与发起请求的用户一致

---

## Enum Schema 改进 (SEP-1330)

### 概述

SEP-1330 弃用了非标准的 `enumNames` 属性，采用 JSON Schema 兼容的模式，并引入多选枚举支持。

### Schema 类型

```
EnumSchema
├── SingleSelectEnumSchema
│   ├── UntitledSingleSelectEnumSchema  (无标题单选)
│   └── TitledSingleSelectEnumSchema    (有标题单选)
├── MultiSelectEnumSchema
│   ├── UntitledMultiSelectEnumSchema   (无标题多选)
│   └── TitledMultiSelectEnumSchema     (有标题多选)
└── LegacyTitledEnumSchema              (旧版，使用 enumNames)
```

### 类型定义

#### UntitledSingleSelectEnumSchema

```typescript
interface UntitledSingleSelectEnumSchema {
  type: "string";
  title?: string;
  description?: string;
  enum: string[];           // 枚举值即显示值
  default?: string;
}
```

#### TitledSingleSelectEnumSchema

```typescript
interface TitledSingleSelectEnumSchema {
  type: "string";
  title?: string;
  description?: string;
  oneOf: {
    const: string;          // 枚举值
    title: string;          // 显示名称
  }[];
  default?: string;
}
```

#### UntitledMultiSelectEnumSchema

```typescript
interface UntitledMultiSelectEnumSchema {
  type: "array";
  title?: string;
  description?: string;
  minItems?: number;
  maxItems?: number;
  items: {
    type: "string";
    enum: string[];
  };
  default?: string[];
}
```

#### TitledMultiSelectEnumSchema

```typescript
interface TitledMultiSelectEnumSchema {
  type: "array";
  title?: string;
  description?: string;
  minItems?: number;
  maxItems?: number;
  items: {
    anyOf: {
      const: string;
      title: string;
    }[];
  };
  default?: string[];
}
```

### 示例

#### 单选无标题

```json
{
  "type": "string",
  "title": "Color Selection",
  "description": "Choose your favorite color",
  "enum": ["Red", "Green", "Blue"],
  "default": "Green"
}
```

#### 单选有标题

```json
{
  "type": "string",
  "title": "Color Selection",
  "description": "Choose your favorite color",
  "oneOf": [
    { "const": "#FF0000", "title": "Red" },
    { "const": "#00FF00", "title": "Green" },
    { "const": "#0000FF", "title": "Blue" }
  ],
  "default": "#00FF00"
}
```

#### 多选有标题

```json
{
  "type": "array",
  "title": "Features",
  "description": "Select features to enable",
  "minItems": 1,
  "maxItems": 3,
  "items": {
    "anyOf": [
      { "const": "dark_mode", "title": "Dark Mode" },
      { "const": "notifications", "title": "Push Notifications" },
      { "const": "analytics", "title": "Usage Analytics" }
    ]
  },
  "default": ["dark_mode"]
}
```

### ElicitResult 扩展

支持返回数组类型：

```typescript
interface ElicitResult {
  action: "accept" | "decline" | "cancel";
  content?: { [key: string]: string | number | boolean | string[] };
}
```

---

## 默认值支持 (SEP-1034)

### 概述

SEP-1034 为所有原始类型（string, number, enum）添加了 `default` 字段支持，之前只有 `BooleanSchema` 支持。

### Schema 定义

#### StringSchema

```typescript
interface StringSchema {
  type: "string";
  title?: string;
  description?: string;
  minLength?: number;
  maxLength?: number;
  format?: "uri" | "email" | "date" | "date-time";
  default?: string;          // NEW
}
```

#### NumberSchema

```typescript
interface NumberSchema {
  type: "number" | "integer";
  title?: string;
  description?: string;
  minimum?: number;
  maximum?: number;
  default?: number;          // NEW
}
```

#### BooleanSchema (已有)

```typescript
interface BooleanSchema {
  type: "boolean";
  title?: string;
  description?: string;
  default?: boolean;
}
```

### 示例：预填充表单

```json
{
  "method": "elicitation/create",
  "params": {
    "mode": "form",
    "message": "Configure email reply",
    "requestedSchema": {
      "type": "object",
      "properties": {
        "recipients": {
          "type": "string",
          "title": "Recipients",
          "default": "alice@company.com, bob@company.com"
        },
        "cc": {
          "type": "string",
          "title": "CC",
          "default": "john@company.com"
        },
        "priority": {
          "type": "integer",
          "title": "Priority",
          "minimum": 1,
          "maximum": 5,
          "default": 3
        }
      }
    }
  }
}
```

---

## Sampling 工具调用支持 (SEP-1577)

### 概述

SEP-1577 为 `sampling/createMessage` 添加了 `tools` 和 `toolChoice` 参数，使 MCP 服务器能够实现代理循环 (agentic loops)。

### 客户端能力声明

```typescript
interface ClientCapabilities {
  sampling?: {
    context?: object;    // 允许 includeContext != "none"
    tools?: object;      // NEW: 允许 tools 和 toolChoice 参数
  };
}
```

### 请求结构

```typescript
interface CreateMessageRequestParams {
  messages: SamplingMessage[];
  modelPreferences?: ModelPreferences;
  systemPrompt?: string;
  includeContext?: "none" | "thisServer" | "allServers";
  temperature?: number;
  maxTokens: number;
  stopSequences?: string[];
  metadata?: object;
  tools?: Tool[];           // NEW
  toolChoice?: ToolChoice;  // NEW
}

interface ToolChoice {
  mode?: "auto" | "required" | "none";
}
```

### 消息内容类型

```typescript
// 消息可以是用户或助手角色
type SamplingMessage = UserMessage | AssistantMessage;

// 助手消息内容
type AssistantMessageContent =
  | TextContent
  | ImageContent
  | AudioContent
  | ToolUseContent;  // NEW

// 用户消息内容
type UserMessageContent =
  | TextContent
  | ImageContent
  | AudioContent
  | ToolResultContent;  // NEW

// 工具调用内容
interface ToolUseContent {
  type: "tool_use";
  id: string;
  name: string;
  input: { [key: string]: unknown };
}

// 工具结果内容
interface ToolResultContent {
  type: "tool_result";
  toolUseId: string;
  content: ContentBlock[];
  structuredContent?: { [key: string]: unknown };
  isError?: boolean;
}
```

### 响应结构

```typescript
interface CreateMessageResult {
  model: string;
  role: "assistant";
  content: AssistantMessageContent | AssistantMessageContent[];
  stopReason?: "endTurn" | "stopSequence" | "toolUse" | "maxTokens" | string;
}
```

### 工具循环示例

```
[用户] "What's the weather in London?"
   |
   v
[sampling/createMessage]
   |
   v
[助手] tool_use: get_weather(location="London")
   |
   v
[服务器执行工具]
   |
   v
[sampling/createMessage]
   messages: [
     {role: "user", content: "What's the weather?"},
     {role: "assistant", content: [tool_use]},
     {role: "user", content: [tool_result]}
   ]
   |
   v
[助手] "The weather in London is sunny, 20°C"
```

### API 风格对比

| API | 工具调用位置 | 工具结果角色 |
|-----|------------|------------|
| **MCP (Claude 风格)** | 嵌入 assistant 消息 | user 消息中的 `tool_result` |
| **OpenAI** | `tool_calls` 数组 | `role: "tool"` |
| **Gemini** | `function` 内容 | `function` 角色 |

---

## Python 实现示例

### 1. Elicitation 请求处理

```python
from typing import TypedDict, Literal, Union
from pydantic import BaseModel

# === Schema 定义 ===

class StringSchema(BaseModel):
    type: Literal["string"] = "string"
    title: str | None = None
    description: str | None = None
    minLength: int | None = None
    maxLength: int | None = None
    format: Literal["uri", "email", "date", "date-time"] | None = None
    default: str | None = None


class NumberSchema(BaseModel):
    type: Literal["number", "integer"]
    title: str | None = None
    description: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    default: float | None = None


class BooleanSchema(BaseModel):
    type: Literal["boolean"] = "boolean"
    title: str | None = None
    description: str | None = None
    default: bool | None = None


class TitledSingleSelectEnumSchema(BaseModel):
    type: Literal["string"] = "string"
    title: str | None = None
    description: str | None = None
    oneOf: list[dict[Literal["const", "title"], str]]
    default: str | None = None


class TitledMultiSelectEnumSchema(BaseModel):
    type: Literal["array"] = "array"
    title: str | None = None
    description: str | None = None
    minItems: int | None = None
    maxItems: int | None = None
    items: dict[Literal["anyOf"], list[dict[Literal["const", "title"], str]]]
    default: list[str] | None = None


# === Elicitation 请求 ===

class ElicitRequestFormParams(BaseModel):
    mode: Literal["form"] = "form"
    message: str
    requestedSchema: dict


class ElicitRequestURLParams(BaseModel):
    mode: Literal["url"] = "url"
    message: str
    elicitationId: str
    url: str


ElicitRequestParams = Union[ElicitRequestFormParams, ElicitRequestURLParams]


class ElicitResult(BaseModel):
    action: Literal["accept", "decline", "cancel"]
    content: dict[str, str | int | bool | list[str]] | None = None


# === 使用示例 ===

async def create_form_elicitation():
    """创建表单式 Elicitation 请求"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "elicitation/create",
        "params": {
            "mode": "form",
            "message": "Please configure your settings",
            "requestedSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "title": "Username",
                        "default": "guest"
                    },
                    "role": {
                        "type": "string",
                        "title": "Role",
                        "oneOf": [
                            {"const": "admin", "title": "Administrator"},
                            {"const": "user", "title": "Regular User"},
                            {"const": "guest", "title": "Guest"}
                        ],
                        "default": "user"
                    },
                    "features": {
                        "type": "array",
                        "title": "Features",
                        "items": {
                            "anyOf": [
                                {"const": "notifications", "title": "Notifications"},
                                {"const": "analytics", "title": "Analytics"}
                            ]
                        },
                        "default": ["notifications"]
                    }
                },
                "required": ["username", "role"]
            }
        }
    }
    return request


async def create_url_elicitation():
    """创建 URL 式 Elicitation 请求"""
    import uuid

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "elicitation/create",
        "params": {
            "mode": "url",
            "elicitationId": str(uuid.uuid4()),
            "url": "https://oauth.example.com/authorize?client_id=xxx",
            "message": "Please authorize access to your account"
        }
    }
    return request
```

### 2. Sampling 工具调用

```python
from typing import Literal, Union
from pydantic import BaseModel

# === 工具定义 ===

class Tool(BaseModel):
    name: str
    title: str | None = None
    description: str | None = None
    inputSchema: dict


class ToolChoice(BaseModel):
    mode: Literal["auto", "required", "none"] = "auto"


# === 消息内容类型 ===

class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ToolUseContent(BaseModel):
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    toolUseId: str
    content: list[dict]
    isError: bool = False


class SamplingMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[TextContent, ToolUseContent, ToolResultContent, list]


# === Sampling 请求 ===

class CreateMessageRequestParams(BaseModel):
    messages: list[SamplingMessage]
    maxTokens: int
    modelPreferences: dict | None = None
    systemPrompt: str | None = None
    temperature: float | None = None
    tools: list[Tool] | None = None
    toolChoice: ToolChoice | None = None


class CreateMessageResult(BaseModel):
    model: str
    role: Literal["assistant"] = "assistant"
    content: Union[dict, list[dict]]
    stopReason: str | None = None


# === 使用示例 ===

async def create_sampling_with_tools():
    """创建带工具的 Sampling 请求"""

    # 定义工具
    weather_tool = Tool(
        name="get_weather",
        description="Get current weather for a location",
        inputSchema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    )

    # 创建请求
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sampling/createMessage",
        "params": {
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "What's the weather in London?"}
                }
            ],
            "maxTokens": 1024,
            "tools": [weather_tool.model_dump()],
            "toolChoice": {"mode": "auto"}
        }
    }
    return request


async def handle_tool_use_result(tool_call_id: str, result: dict):
    """创建包含工具结果的 Sampling 请求"""

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "sampling/createMessage",
        "params": {
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "What's the weather in London?"}
                },
                {
                    "role": "assistant",
                    "content": {
                        "type": "tool_use",
                        "id": tool_call_id,
                        "name": "get_weather",
                        "input": {"location": "London"}
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "tool_result",
                        "toolUseId": tool_call_id,
                        "content": [
                            {"type": "text", "text": f"Weather result: {result}"}
                        ]
                    }
                }
            ],
            "maxTokens": 1024
        }
    }
    return request
```

### 3. 完整的 Elicitation 处理器

```python
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable

@dataclass
class ElicitationHandler:
    """Elicitation 请求处理器"""

    # 注册的完成回调
    completion_callbacks: dict[str, Callable[[], Awaitable[None]]] = None

    def __post_init__(self):
        self.completion_callbacks = {}

    async def handle_elicitation(
        self,
        params: dict,
        user_approve: Callable[[dict], Awaitable[bool]]
    ) -> dict:
        """处理 Elicitation 请求"""

        mode = params.get("mode", "form")

        if mode == "url":
            # URL 模式：请求用户打开 URL
            elicitation_id = params["elicitationId"]
            url = params["url"]
            message = params["message"]

            # 显示 URL 给用户，等待确认
            approved = await user_approve({
                "type": "url",
                "url": url,
                "message": message
            })

            return {
                "action": "accept" if approved else "decline"
            }

        else:
            # Form 模式：显示表单
            schema = params["requestedSchema"]
            message = params.get("message", "")

            # 使用 schema 渲染表单，收集用户输入
            user_input = await user_approve({
                "type": "form",
                "schema": schema,
                "message": message
            })

            if user_input is None:
                return {"action": "cancel"}

            return {
                "action": "accept",
                "content": user_input
            }

    def register_completion_callback(
        self,
        elicitation_id: str,
        callback: Callable[[], Awaitable[None]]
    ):
        """注册 URL Elicitation 完成回调"""
        self.completion_callbacks[elicitation_id] = callback

    async def handle_completion_notification(self, params: dict):
        """处理完成通知"""
        elicitation_id = params["elicitationId"]

        if elicitation_id in self.completion_callbacks:
            callback = self.completion_callbacks.pop(elicitation_id)
            await callback()
```

---

## 参考资料

- [SEP-1036: URL Mode Elicitation](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1036)
- [SEP-1330: Elicitation Enum Schema Improvements](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1330)
- [SEP-1034: Default Values for Primitive Types](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1034)
- [SEP-1577: Sampling With Tools](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1577)
- [MCP 2025-11-25 Schema Reference](https://modelcontextprotocol.io/specification/2025-11-25/schema)

---

*文档版本: 2025-03-10*
*协议版本: MCP 2025-11-25*
