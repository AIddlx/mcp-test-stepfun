#!/usr/bin/env node

/**
 * MCP stdio 服务器（NPX 模式）
 *
 * 手写 JSON-RPC over stdio，不依赖 MCP SDK。
 * 兼容阶跃桌面助手 v0.2.13。
 *
 * 约束检查:
 * - R001/D002: 不声明 outputSchema
 * - R006: 路径用正斜杠
 * - K005: 返回值只用 content + isError
 *
 * 测试: npx -y ./path/to/project
 */

import readline from 'readline';

// ==================== 状态 ====================

let initialized = false;
let clientProtocolVersion = '';

// ==================== 消息发送 ====================

function sendMessage(message) {
    process.stdout.write(JSON.stringify(message) + '\n');
}

function sendResponse(id, result, error) {
    const response = { jsonrpc: '2.0', id };
    if (error) response.error = error;
    else response.result = result;
    sendMessage(response);
}

function sendNotification(method, params) {
    const notification = { jsonrpc: '2.0', method };
    if (params) notification.params = params;
    sendMessage(notification);
}

// ==================== 工具定义 ====================

function getTools() {
    return [
        {
            name: 'hello',
            description: '打招呼工具。输入名字，返回问候语。',
            inputSchema: {
                type: 'object',
                properties: {
                    name: { type: 'string', description: '名字' }
                },
                required: ['name']
            }
        }
    ];
}

// ==================== 工具实现 ====================

function callTool(name, args) {
    if (name === 'hello') {
        return {
            success: true,
            message: `你好, ${args.name}!`
        };
    }

    return { success: false, error: `Unknown tool: ${name}` };
}

// ==================== 请求处理 ====================

function handleRequest(request) {
    const { method, params = {}, id } = request;

    if (method === 'initialize') {
        clientProtocolVersion = params.protocolVersion || '';
        initialized = true;

        return {
            protocolVersion: '2025-11-25',
            capabilities: {
                tools: { listChanged: true }
            },
            serverInfo: {
                name: 'my-mcp-server',
                version: '1.0.0'
            },
            instructions: 'MCP 服务器'
        };
    }

    if (method === 'notifications/initialized') {
        return null;
    }

    if (method === 'tools/list') {
        return { tools: getTools() };
    }

    if (method === 'tools/call') {
        const result = callTool(params.name, params.arguments || {});
        return {
            content: [{ type: 'text', text: JSON.stringify(result) }],
            isError: result.success === false
        };
    }

    if (method === 'ping') {
        return {};
    }

    return null;
}

// ==================== 主循环 ====================

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

rl.on('line', (line) => {
    if (!line.trim()) return;

    try {
        const request = JSON.parse(line);
        const result = handleRequest(request);

        // 通知不需要响应
        if (request.method?.startsWith('notifications/')) {
            return;
        }

        if (result === null && request.id !== undefined) {
            sendResponse(request.id, null, { code: -32601, message: `Method not found: ${request.method}` });
        } else if (request.id !== undefined) {
            sendResponse(request.id, result);
        }
    } catch (e) {
        process.stderr.write(`[Error] ${e.message}\n`);
    }
});

rl.on('close', () => {
    process.exit(0);
});
