#!/usr/bin/env node

/**
 * MCP NPX 测试服务器 - 入口
 *
 * 阶跃客户端配置:
 * {
 *   "mcpServers": {
 *     "mcp-npx-test": {
 *       "command": "npx",
 *       "args": ["-y", "mcp-npx-test"]
 *     }
 *   }
 * }
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 解析参数
const args = process.argv.slice(2);
const showHelp = args.includes('--help') || args.includes('-h');

if (showHelp) {
    console.log(`
MCP NPX 测试服务器

用法:
  npx mcp-npx-test [选项]

选项:
  --help     显示帮助信息

阶跃客户端配置:
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "mcp-npx-test"]
    }
  }
}

测试工具: 35个 (A-I类 + GUI)
协议版本: MCP 2025-11-25
传输模式: stdio
`);
    process.exit(0);
}

// 启动 stdio 服务器
const stdioPath = join(__dirname, '..', 'stdio-full-server.js');
const server = spawn('node', [stdioPath], {
    stdio: 'inherit',
    env: process.env
});

server.on('error', (err) => {
    process.stderr.write(`[Error] Failed to start server: ${err.message}\n`);
    process.exit(1);
});

server.on('exit', (code) => {
    process.exit(code || 0);
});

process.on('SIGINT', () => server.kill('SIGINT'));
process.on('SIGTERM', () => server.kill('SIGTERM'));
