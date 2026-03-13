# 约束详细说明

> 按阶段分类的完整约束清单。SKILL.md 只包含摘要，本文档包含详细说明和代码示例。

---

## 目录

- [设计阶段 (D001-D005)](#设计阶段)
- [编码阶段 (K001-K007)](#编码阶段)
- [部署阶段 (P001-P005)](#部署阶段)
- [排查指南](#排查指南)

---

## 设计阶段

> 阶跃 MCP 服务器设计时需要考虑的协议和架构限制。

### D001: tools/call 是原子的

**MCP 规范设计，不是客户端缺陷。**

`tools/call` 返回单个 `CallToolResult`，没有"部分结果"或"流式内容"的概念。

```json
{
  "content": [{"type": "text", "text": "完整结果"}],
  "isError": false
}
```

**影响**：GUI Agent 的多步操作（点击→输入→等待→截图）无法实时反馈给用户。

**替代方案**：
- **异步轮询**：`start_task → get_task_status → get_result`
- **分段工具调用**：拆分为多个短工具（`click → type → wait → screenshot`）

---

### D002: 不要声明 outputSchema

阶跃不消费 `outputSchema` 和 `structuredContent`，只读取 `content` 中的文本。

**影响**：
- 声明 outputSchema → `-32600: Tool xxx has an output schema but did not return structured content`
- 返回 structuredContent 但格式不匹配 → 同上错误

**规则**：工具定义中不写 `outputSchema`，返回值只用 `content` 数组。

---

### D003: 进度通知不可靠

`notifications/progress` 是 MCP 协议中唯一的服务器→客户端中间通知机制，但在阶跃中存在两层问题：

1. **阶跃不发送 `progressToken`** — 服务端无法发送进度通知
2. **SDK 有路由 Bug** — `report_progress()` 和 `progress()` 都缺少 `related_request_id`

**结论**：不要设计依赖进度通知的功能。长任务必须使用异步轮询模式。

| 模式 | progress 可见性 | 原因 |
|------|----------------|------|
| stdio | ✅ 可用（协议层） | 消息直接通过 stdout |
| HTTP `stateless=True` | ❌ 丢弃 | 无 GET 流 + 缺少 `related_request_id` |
| 任何模式（阶跃客户端） | ❌ 全部无效 | 客户端不发送 `progressToken` |

---

### D004: 服务器→客户端能力受限

阶跃 v0.2.13 对以下能力未实现客户端支持：

| 能力 | 实测观察 |
|------|---------|
| `resources/subscribe` | 客户端未发起订阅 |
| `sampling/createMessage` | 客户端未响应 |
| `elicitation/create` | 客户端未响应 |

**规则**：可以声明这些能力，但不要依赖客户端消费它们。

---

### D005: FastMCP 没有 stream=True

FastMCP **不存在** `stream=True` 参数。控制台测试中看到的"流式"效果是 `notifications/progress` 作为中间 SSE 事件逐行到达。

```
请求 ──→ notification(progress 1/5) ──→ ... ──→ 最终响应
```

视觉效果像"流式"，实际是多个独立的 SSE 事件。最终只有 `result` 中的内容被提交给 LLM。

---

## 编码阶段

> 编写 MCP 服务器代码时必须遵守的规则。

### K001: UVX 入口点 main() 必须同步

**致命规则 R002 的详细说明。**

hatch 构建的 `[project.scripts]` 入口点被同步调用。如果 `main()` 是 `async def`，coroutine 不会被 await，进程立即退出。

```python
# ❌ 崩溃：coroutine 'main' was never awaited → Connection closed
async def main():
    async with stdio_server() as (read, write):
        await server.run(...)

# ✅ 正确
def main():
    import asyncio
    async def _run():
        async with stdio_server() as (read, write):
            await server.run(...)
    asyncio.run(_run())
```

**注意**：`if __name__ == "__main__"` 直接调用时 `async def main()` 不会出问题。问题只出现在通过 `uvx --from ... server-name` 启动时。

---

### K002: Windows 路径统一正斜杠

阶跃配置文件中，路径必须使用正斜杠。反斜杠在 JSON 中需要双重转义。

```json
✅ "args": ["-y", "C:/Project/my-server"]
❌ "args": ["-y", "C:\\Project\\my-server"]  // 合法但容易出错
❌ "args": ["-y", "C:\Project\my-server"]    // 会被当作转义字符
```

---

### K003: import 路径使用正确模块

```python
# ✅ 正确
from mcp.server import FastMCP
from mcp.server.lowlevel import Server

# ❌ 错误
from mcp.server.mcpserver import FastMCP  # ModuleNotFoundError
```

---

### K004: HTTP stateless=True 下绕过 SDK progress()

在 HTTP `stateless=True` 模式下，SDK 的 `progress()` 和 `ctx.report_progress()` 都不工作。

如需发送进度通知，必须直接调用：

```python
ctx = server.request_context
request_id = str(ctx.request_id) if ctx.request_id else None

if ctx.meta and ctx.meta.progressToken and request_id:
    await ctx.session.send_progress_notification(
        progress_token=ctx.meta.progressToken,
        progress=1, total=5,
        message="步骤 1/5",
        related_request_id=request_id,  # ← 关键！
    )
```

**注意**：即使这样写，阶跃仍然不发送 `progressToken`（D003），所以这个 workaround 在阶跃中实际无用。

---

### K005: 返回值只用 content

```python
# ✅ 正确
return [types.TextContent(type="text", text=json.dumps(result))]

# ❌ 不要返回 structuredContent
return types.CallToolResult(
    content=[types.TextContent(type="text", text="...")],
    structuredContent={"key": "value"}  # 阶跃不消费
)
```

---

### K006: Python 类型名 ≠ JSON Schema 类型名

```python
type("hello").__name__  # 返回 "str"，不是 "string"
type(42).__name__        # 返回 "int"，不是 "integer"
```

做类型匹配比较时需注意。

---

### K007: 错误处理两种方式

**方式一：协议错误**（JSON-RPC error）

```python
# FastMCP — 抛异常
raise ValueError("参数错误")
# → 客户端收到: {"error": {"code": -32602, "message": "Invalid params: ..."}}
```

**方式二：业务错误**（isError: true）

```python
# 返回正常 content 但标记 isError
return [types.TextContent(type="text", text=json.dumps({
    "success": False,
    "error": "业务逻辑错误"
}))]
```

选择依据：
- 参数格式不对 → 协议错误
- 业务逻辑失败 → 业务错误（isError）

---

## 部署阶段

> 配置阶跃客户端、选择传输模式、管理缓存。

### P001: 命令格式限制

**致命规则 R003 的详细说明。**

阶跃客户端只识别**裸命令名**，不支持完整路径或非标准命令。

| 配置 | 结果 | 原因 |
|------|------|------|
| `"command": "npx"` | ✅ 正常 | 阶跃内置 |
| `"command": "uvx"` | ✅ 正常 | 阶跃内置 uvx 0.9.17 |
| `"command": "node"` | ❌ 失败 | `unknown command: node` |
| `"command": "python"` | ❌ 失败 | `unknown command: python` |
| `"command": "C:\\...\\uvx.exe"` | ❌ 失败 | 不接受带路径的命令 |

### 阶跃内置运行时

| 工具 | 版本 | 位置 |
|------|------|------|
| uvx | 0.9.17 | `StepFun/.../uvx/win32-x64/uvx.exe` |
| Python | 3.11.9 | `StepFun/.../python-3.11.9/python.exe` |
| Node.js | v22.18.0 | `~/.stepfun/runtimes/node/` |

---

### P002: 工具执行超时

**致命规则 R005 的详细说明。**

| 时长 | 结果 |
|------|------|
| ≤ 55 秒 | 通过 |
| 55-60 秒 | 边界区域（不确定） |
| ≥ 60 秒 | `-32001: Request timed out` |

**规则**：单次工具执行控制在 55 秒以内。长任务拆分为多步调用。

---

### P003: tools/list 缓存

修改工具定义后，阶跃仍使用旧的工具列表。

**解决方案**：在阶跃客户端中**重新添加 MCP 配置**（先删除再添加）。

---

### P004: UVX 缓存问题（不推荐开发时用）

### 为什么不推荐

UVX 在本地开发场景下，每次修改源码后都需要复杂的缓存清理：

1. **五层独立缓存**：系统 uv + 阶跃 uvx，每层独立缓存旧代码
2. **版本号绑定**：`sdists-v9` 以版本号为 key 缓存 `.whl`，版本号不变永远用旧包
3. **无法传参数**：阶跃控制 uvx 调用，无法加 `--refresh`、`--no-cache`

### 五个缓存位置（Windows）

| # | 路径 | 用途 |
|---|------|------|
| 1 | `AppData\Local\uv\cache\archive-v0` | 系统 uvx 构建环境 |
| 2 | `AppData\Local\uv\cache\sdists-v9` | 系统 uvx 包缓存 |
| 3 | `~/.stepfun/cache/archive-v0` | 阶跃 uvx 构建环境 |
| 4 | **`~/.stepfun/cache/sdists-v9`** | **阶跃 uvx .whl 缓存（最关键）** |
| 5 | `项目/build/` | 本地构建产物 |

**位置 4 是最容易遗漏的**：以版本号为 key 缓存 `.whl`，版本号不变就永远用旧包。`uv cache clean` 只清理系统 uv 缓存，**不影响**阶跃缓存。

### 完整清理流程

```bash
# 1. 阶跃客户端删除 MCP 配置（终止旧进程）
# 2. 清理全部缓存
rm -rf ~/AppData/Local/uv/cache/archive-v0/*mcp-uvx*
uv cache clean
rm -rf ~/.stepfun/cache/archive-v0
rm -rf ~/.stepfun/cache/sdists-v9
rm -rf 项目/build/

# 3. 更新 pyproject.toml 版本号（如 1.0.0 → 1.1.0）
# 4. 重新添加 MCP 配置
```

---

### P005: Defender 锁文件

Windows Defender（特别是与其他安全软件共存时）可能锁定 uvx 下载的 `.whl` 文件。

**现象**：`MCP error -32000: Connection closed` + 日志中 `os error -2147024786`

**解决方案**：

```powershell
# 将缓存目录加入排除列表
Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\uv\cache"
Add-MpPreference -ExclusionPath "$env:USERPROFILE\.stepfun\cache"
```

或者重试——第一次失败，第二次缓存已存在，直接成功。

---

### 推荐开发流程

| 阶段 | 推荐方式 | 原因 |
|------|---------|------|
| **编写调试** | HTTP 模式 | `python server.py`，修改即生效 |
| **阶跃 stdio 测试** | NPX 模式 | `npx -y C:/path`，修改即生效 |
| **最终验证** | NPX 或 UVX | 确认在阶跃客户端中正常工作 |

---

## 排查指南

> 按错误现象分类的排查决策树。

日志位置：`%APPDATA%/stepfun-desktop/logs/`

---

### Connection closed（MCP error -32000）

最常见的问题，有 5 种可能原因。**先看阶跃日志区分。**

```
MCP error -32000: Connection closed
│
├── 日志中有 "coroutine ... was never awaited"
│   └── R002: async def main() → 改为同步函数
│
├── 日志中有 "Failed to install: xxx.whl" + "os error -2147024786"
│   └── P005: Defender 锁文件 → 加排除列表或重试
│
├── 日志中有 "ModuleNotFoundError"
│   └── K003: import 路径错误 → from mcp.server import FastMCP
│
├── 日志显示 "Installed N packages" 但行为是旧代码
│   └── P004: UVX 缓存 → 清 5 个缓存 + 更新版本号
│
├── 日志中有 "unknown command: xxx"
│   └── P001: 命令格式错误 → 只用裸命令名 npx/uvx
│
└── 日志无明确错误
    └── 检查进程存活 + 超时 (R005)
```

---

### 工具执行超时（-32001）

```
Request timed out
├── 检查工具执行时间
│   ├── > 60秒 → 超过阈值 [P002]
│   │   └── 修复: 拆分为多步调用，控制在 55 秒以内
│   └── ≤ 55秒 → 其他原因
│       └── 检查网络延迟、依赖下载、等待外部服务
```

---

### 工具修改后客户端看不到变化

```
新增/修改工具后，阶跃仍显示旧工具列表
└── 原因: tools/list 缓存 [P003]
    └── 修复: 阶跃客户端重新添加 MCP 配置（先删后加）
```

---

### UVX 代码更新后仍运行旧版

```
修改源码后阶跃仍运行旧代码
│
├── 1. 检查 pyproject.toml 版本号是否更新
│   └── 未更新 → 更新（如 1.0.0 → 1.1.0）
│
├── 2. 清理 5 个缓存位置 [P004]
│   ├── rm -rf ~/AppData/Local/uv/cache/archive-v0/*包名*
│   ├── uv cache clean
│   ├── rm -rf ~/.stepfun/cache/archive-v0
│   ├── rm -rf ~/.stepfun/cache/sdists-v9     ← 最关键
│   └── rm -rf 项目/build/
│
├── 3. 删除阶跃 MCP 配置 → 重新添加
│
└── 4. 验证
    └── 查看阶跃日志确认安装的是新版本
```

---

### 常见错误码

| 错误码 | 含义 | 常见原因 | 对应约束 |
|--------|------|---------|---------|
| -32000 | Connection closed | 进程崩溃 | R002, K001, K003, P004, P005 |
| -32001 | Request timed out | 工具执行 > 60 秒 | P002 |
| -32600 | Invalid Request | outputSchema 格式问题 | D002 |
| -32602 | Invalid params | 参数类型/格式不匹配 | — |

---

### 排查工具

```bash
# 查看 UVX 实际安装的包版本
uvx --verbose --from <项目路径> <入口名> --help 2>&1

# 清理系统 uv 缓存（注意：不影响阶跃缓存）
uv cache clean

# 检查 Defender 是否有相关事件
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Windows Defender/Operational'
    StartTime = (Get-Date).AddHours(-1)
} -MaxEvents 50

# 测试 HTTP 端点
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# 检查 MCP 服务器进程是否存活
Get-Process -Name "mcp-*" -ErrorAction SilentlyContinue
```
