#!/usr/bin/env node
/**
 * MCP 测试服务器 - NPX 传输 (官方 TypeScript SDK, Low-Level Server API)
 *
 * 使用底层 Server API，手动定义 JSON Schema，替代 McpServer + zod。
 *
 * 阶跃客户端配置:
 * {
 *   "mcpServers": {
 *     "mcp-npx-sdk": {
 *       "command": "npx",
 *       "args": ["-y", "mcp-npx-sdk"]
 *     }
 *   }
 * }
 *
 * 本地测试:
 *   npm run build && node dist/server.js
 */
export {};
