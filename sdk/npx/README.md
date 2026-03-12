# MCP NPX 测试服务器 (官方 SDK)

使用官方 TypeScript MCP SDK 实现的 stdio 传输测试服务器。

## 重要说明

> **stdio 模式无需预启动** - 由客户端（阶跃）根据配置自动启动进程

## 编译 (首次)

```bash
cd sdk/npx
npm install && npm run build
```

## 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-npx-sdk": {
      "command": "node",
      "args": ["C:/Project/IDEA/2/new/mcp-test-stepfun/sdk/npx/dist/server.js"]
    }
  }
}
```

## 本地测试 (可选)

```bash
node dist/server.js
# 然后在另一个终端发送 JSON-RPC 消息测试
```

## 客户端配置

```json
{
  "mcpServers": {
    "mcp-npx-sdk": {
      "command": "npx",
      "args": ["-y", "mcp-npx-sdk"]
    }
  }
}
```

本地测试:
```json
{
  "mcpServers": {
    "mcp-npx-sdk": {
      "command": "node",
      "args": ["C:/path/to/sdk/npx/dist/server.js"]
    }
  }
}
```

## 依赖

- Node.js >= 18
- @modelcontextprotocol/sdk >= 1.0.0

## 特性

- 使用 `McpServer` 高级 API
- Zod schema 自动生成 inputSchema
- 35 个测试工具，覆盖 MCP 协议所有主要能力
