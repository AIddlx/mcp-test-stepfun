#!/usr/bin/env node

/**
 * MCP 服务器入口
 *
 * 阶跃客户端通过 npx 启动此入口文件。
 * 入口文件负责加载并启动主服务器。
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 启动主服务器
const serverPath = join(__dirname, '..', 'server.js');
const server = spawn('node', [serverPath], {
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
