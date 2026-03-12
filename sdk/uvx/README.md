# MCP UVX 测试服务器 (官方 SDK)

使用官方 Python MCP SDK 实现的 stdio 传输测试服务器。

## 重要说明

> **stdio 模式无需预启动** - 由客户端（阶跃）根据配置自动启动进程

## 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-uvx-sdk": {
      "command": "python",
      "args": ["C:/Project/IDEA/2/new/mcp-test-stepfun/sdk/uvx/src/mcp_uvx_sdk/server.py"]
    }
  }
}
```

## 本地测试 (可选)

```bash
cd sdk/uvx
python src/mcp_uvx_sdk/server.py
# 然后在另一个终端发送 JSON-RPC 消息测试
```

## 客户端配置

```json
{
  "mcpServers": {
    "mcp-uvx-sdk": {
      "command": "uvx",
      "args": ["--from", "C:/path/to/sdk/uvx", "mcp-uvx-sdk"]
    }
  }
}
```

## 依赖

- Python >= 3.10
- mcp[cli] >= 1.0.0

## 特性

- 使用 `FastMCP` 高级封装
- 装饰器自动生成 inputSchema
- 支持 `Context` 对象进行进度通知
- 35 个测试工具，覆盖 MCP 协议所有主要能力
