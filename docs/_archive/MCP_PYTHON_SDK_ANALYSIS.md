# MCP Python SDK 2025-11-25 支持分析报告

**分析日期**: 2026-03-10
**SDK 位置**: `%USERPROFILE%\AppData\Roaming\Python\Python313\site-packages\mcp\`

---

## 1. 协议版本

```
LATEST_PROTOCOL_VERSION = "2025-11-25"
DEFAULT_NEGOTIATED_VERSION = "2025-11-25"
```

**结论**: SDK 已声明支持 2025-11-25 协议版本。

---

## 2. Tasks 支持 (2025-11-25 新特性)

### 已定义类型

| 类型 | 说明 |
|------|------|
| `Task` | 任务实体，包含 taskId, status, createdAt, lastUpdatedAt, ttl, pollInterval |
| `TaskMetadata` | 任务元数据，包含 ttl |
| `TaskStatus` | Literal['working', 'input_required', 'completed', 'failed', 'cancelled'] |
| `TaskExecutionMode` | Literal['forbidden', 'optional', 'required'] |

### 请求/响应类型

| 类型 | 方法 |
|------|------|
| `ListTasksRequest` | `tasks/list` |
| `ListTasksResult` | - |
| `GetTaskRequest` | `tasks/get` |
| `GetTaskResult` | - |
| `CancelTaskRequest` | `tasks/cancel` |
| `CancelTaskResult` | - |
| `GetTaskPayloadRequest` | `tasks/result` |
| `GetTaskPayloadResult` | - |
| `CreateTaskResult` | 创建任务响应 |

### 通知类型

| 类型 | 方法 |
|------|------|
| `TaskStatusNotification` | `notifications/tasks/status` |
| `TaskStatusNotificationParams` | - |

### 能力声明

```python
ServerTasksCapability:
  list: TasksListCapability | None
  cancel: TasksCancelCapability | None
  requests: ServerTasksRequestsCapability | None

ClientTasksCapability:
  list: TasksListCapability | None
  cancel: TasksCancelCapability | None
  requests: ClientTasksRequestsCapability | None
```

### 常量

```python
TASK_STATUS_WORKING = "working"
TASK_STATUS_INPUT_REQUIRED = "input_required"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
TASK_STATUS_CANCELLED = "cancelled"

TASK_REQUIRED = "required"
TASK_OPTIONAL = "optional"
TASK_FORBIDDEN = "forbidden"
```

**结论**: Tasks 特性已完全定义，包括所有请求、响应、通知和能力声明。

---

## 3. Elicitation 支持 (2025-11-25 新特性)

### 已定义类型

| 类型 | 说明 |
|------|------|
| `ElicitRequest` | `elicitation/create` 请求 |
| `ElicitRequestFormParams` | 表单模式参数 (mode, message, requestedSchema) |
| `ElicitRequestURLParams` | URL 模式参数 (mode, message, url, elicitationId) |
| `ElicitResult` | 响应 (action: accept/decline/cancel, content) |
| `ElicitCompleteNotification` | `notifications/elicitation/complete` |

### 能力声明

```python
ElicitationCapability:
  form: FormElicitationCapability | None
  url: UrlElicitationCapability | None
```

### 错误码

```python
URL_ELICITATION_REQUIRED = -32042
ElicitationRequiredErrorData:
  elicitations: list[ElicitRequestURLParams]
```

**结论**: Elicitation 特性已完全定义，支持 Form 和 URL 两种模式。

---

## 4. Sampling 支持

### 已定义类型

| 类型 | 说明 |
|------|------|
| `CreateMessageRequest` | `sampling/createMessage` 请求 |
| `CreateMessageRequestParams` | 包含 messages, modelPreferences, tools, toolChoice 等 |
| `CreateMessageResult` | 响应 (role, content, model, stopReason) |
| `CreateMessageResultWithTools` | 支持 ToolUseContent/ToolResultContent 的响应 |
| `SamplingMessage` | 消息结构 (role, content) |
| `SamplingCapability` | 能力声明 (context, tools) |

### 新特性支持

```python
CreateMessageRequestParams:
  tools: list[Tool] | None          # 支持传递工具定义
  toolChoice: ToolChoice | None     # 支持工具选择

SamplingCapability:
  context: SamplingContextCapability | None
  tools: SamplingToolsCapability | None
```

**结论**: Sampling 已支持工具集成特性。

---

## 5. Tool 定义更新

### Tool 结构

```python
Tool:
  name: str
  title: str | None                    # 新增: 显示标题
  description: str | None
  inputSchema: dict[str, Any]
  outputSchema: dict[str, Any] | None  # 新增: 输出 Schema
  icons: list[Icon] | None             # 新增: 图标列表
  annotations: ToolAnnotations | None  # 新增: 注解
  meta: dict[str, Any] | None
  execution: ToolExecution | None      # 新增: 执行配置
```

### ToolAnnotations

```python
ToolAnnotations:
  title: str | None
  readOnlyHint: bool | None
  destructiveHint: bool | None
  idempotentHint: bool | None
  openWorldHint: bool | None
```

### ToolExecution

```python
ToolExecution:
  taskSupport: Literal['forbidden', 'optional', 'required'] | None
```

### ToolChoice

```python
ToolChoice:
  mode: Literal['auto', 'required', 'none'] | None
```

**结论**: Tool 定义已完整支持 2025-11-25 的新字段。

---

## 6. Capabilities 结构

### ServerCapabilities

```python
ServerCapabilities:
  experimental: dict[str, dict[str, Any]] | None
  logging: LoggingCapability | None
  prompts: PromptsCapability | None
  resources: ResourcesCapability | None
  tools: ToolsCapability | None
  completions: CompletionsCapability | None
  tasks: ServerTasksCapability | None    # 新增
```

### ClientCapabilities

```python
ClientCapabilities:
  experimental: dict[str, dict[str, Any]] | None
  sampling: SamplingCapability | None
  elicitation: ElicitationCapability | None  # 新增
  roots: RootsCapability | None
  tasks: ClientTasksCapability | None        # 新增
```

---

## 7. 其他新增类型

### Icon

```python
Icon:
  src: str
  mimeType: str | None
  sizes: list[str] | None
```

### RelatedTaskMetadata

```python
RelatedTaskMetadata:
  taskId: str
```

### Content 类型扩展

| 类型 | 说明 |
|------|------|
| `TextContent` | 文本内容 |
| `ImageContent` | 图像内容 |
| `AudioContent` | 音频内容 (新增) |
| `ToolUseContent` | 工具使用内容 |
| `ToolResultContent` | 工具结果内容 |
| `EmbeddedResource` | 嵌入资源 |
| `ResourceLink` | 资源链接 |

---

## 8. 支持状态汇总

| 特性 | 状态 | 说明 |
|------|------|------|
| **Protocol Version** | ✅ 完全支持 | `LATEST_PROTOCOL_VERSION = "2025-11-25"` |
| **Tasks** | ✅ 完全支持 | 所有请求、响应、通知、能力已定义 |
| **Elicitation (Form)** | ✅ 完全支持 | 表单模式完整支持 |
| **Elicitation (URL)** | ✅ 完全支持 | URL 模式完整支持 |
| **Sampling + Tools** | ✅ 完全支持 | 支持 tools 和 toolChoice 参数 |
| **Tool.title** | ✅ 完全支持 | 已添加 |
| **Tool.outputSchema** | ✅ 完全支持 | 已添加 |
| **Tool.icons** | ✅ 完全支持 | 已添加 |
| **Tool.annotations** | ✅ 完全支持 | 已添加 |
| **Tool.execution** | ✅ 完全支持 | 已添加 taskSupport |
| **Audio Content** | ✅ 完全支持 | AudioContent 类型已定义 |

---

## 9. fastmcp 兼容性

**注意**: fastmcp 是基于 mcp Python SDK 的高级封装库。

### 建议

1. **直接使用 mcp SDK**: 当前 mcp SDK 已完整支持 2025-11-25，可直接使用
2. **fastmcp 版本**: 确保 fastmcp 版本 >= 2.14.4 以兼容最新协议
3. **手动实现**: 如需使用 Tasks 特性，可能需要手动实现服务器端处理逻辑

---

## 10. 实现建议

### 服务端 Tasks 实现

SDK 已定义所有类型，但服务端需要:

1. 实现 `tasks/list` 处理器
2. 实现 `tasks/get` 处理器
3. 实现 `tasks/cancel` 处理器
4. 实现 `tasks/result` 处理器
5. 发送 `notifications/tasks/status` 通知

### 示例代码结构

```python
from mcp import types

# 声明能力
capabilities = types.ServerCapabilities(
    tasks=types.ServerTasksCapability(
        list=types.TasksListCapability(),
        cancel=types.TasksCancelCapability(),
    ),
    tools=types.ToolsCapability(),
)

# Tool 中声明任务需求
tool = types.Tool(
    name="long_running_task",
    title="Long Running Task",
    description="A task that takes time",
    inputSchema={"type": "object", "properties": {}},
    execution=types.ToolExecution(taskSupport="required"),
)
```

---

## 11. 结论

**MCP Python SDK 已完全支持 2025-11-25 协议版本**，包括:

- ✅ Tasks 完整类型系统
- ✅ Elicitation (Form + URL) 完整支持
- ✅ Sampling 与 Tools 集成
- ✅ Tool 新字段 (title, outputSchema, icons, annotations, execution)
- ✅ Audio Content 支持
- ✅ 更新的 Capabilities 结构

**无需手动实现类型定义**，可直接使用 SDK 提供的类型进行开发。

---

*报告生成时间: 2026-03-10*
