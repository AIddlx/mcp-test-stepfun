# 编码阶段约束

> 编写 MCP 服务器代码时必须遵守的规则。

---

## K001: UVX 入口点 main() 必须同步

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

**注意**：`if __name__ == "__main__"` 直接调用时 `async def main()` 不会出问题（因为没有 hatch 入口点介入）。问题只出现在通过 `uvx --from ... server-name` 启动时。

---

## K002: Windows 路径统一正斜杠

阶跃配置文件中，路径必须使用正斜杠。反斜杠在 JSON 中需要双重转义。

```json
✅ "args": ["-y", "C:/Project/my-server"]
❌ "args": ["-y", "C:\\Project\\my-server"]  // 合法但容易出错
❌ "args": ["-y", "C:\Project\my-server"]    // 会被当作转义字符
```

---

## K003: import 路径使用正确模块

```python
# ✅ 正确
from mcp.server import FastMCP
from mcp.server.lowlevel import Server

# ❌ 错误
from mcp.server.mcpserver import FastMCP  # ModuleNotFoundError
```

---

## K004: HTTP stateless=True 下绕过 SDK progress()

**致命规则 R004 的编码层面说明。**

在 HTTP `stateless=True` 模式下，SDK 的 `progress()` 上下文管理器和 `ctx.report_progress()` 都不工作（缺少 `related_request_id`）。

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

**注意**：即使这样写，阶跃仍然不发送 `progressToken`（D003），所以这个 workaround 在阶跃中实际无用。仅在控制台测试或其他客户端场景下有意义。

---

## K005: 返回值只用 content

```python
# ✅ 正确
return [types.TextContent(type="text", text=json.dumps(result))]

# ❌ 不要返回 structuredContent
return types.CallToolResult(
    content=[types.TextContent(type="text", text="...")],
    structuredContent={"key": "value"}  # 阶跃不消费
)
```

JSON 格式：

```json
{
  "content": [{"type": "text", "text": "JSON 字符串或纯文本"}],
  "isError": false
}
```

---

## K006: Python 类型名 ≠ JSON Schema 类型名

```python
type("hello").__name__  # 返回 "str"，不是 "string"
type(42).__name__        # 返回 "int"，不是 "integer"
```

做类型匹配比较时需注意。阶跃测试中 `type_match=false` 即因此差异（功能无影响）。

---

## K007: 错误处理两种方式

阶跃能正确区分两种错误：

**方式一：协议错误**（JSON-RPC error）

```python
# FastMCP — 抛异常
raise ValueError("参数错误")
# → 客户端收到: {"error": {"code": -32602, "message": "Invalid params: ..."}}

# Low-Level — 返回 ErrorData
return types.ErrorData(code=-32602, message="参数错误")
```

**方式二：业务错误**（isError: true）

```python
# 返回正常 content 但标记 isError
return [types.TextContent(type="text", text=json.dumps({
    "success": False,
    "error": "业务逻辑错误"
}))]
# 在 CallToolResult 中: isError=True
```

两种方式阶跃都能正确展示。选择依据：
- 参数格式不对 → 协议错误
- 业务逻辑失败 → 业务错误（isError）
