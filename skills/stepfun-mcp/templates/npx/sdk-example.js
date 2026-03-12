#!/usr/bin/env node

/**
 * MCP 服务器入口（SDK 方式）
 *
 * 使用 @modelcontextprotocol/sdk 官方 SDK。
 *
 * 注意: 此模板未经阶跃客户端实测验证。
 * 手写 JSON-RPC 模板（server.js）已通过 35 个工具的完整测试。
 * 如果 SDK 方式在阶跃中遇到问题，请切换到手写模板。
 *
 * 依赖: npm install @modelcontextprotocol/sdk
 * 测试: npx -y ./path/to/project
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
    { name: 'my-mcp-server', version: '1.0.0' },
    { capabilities: { tools: {} } }
);

// 注册工具列表
// 注意: 不需要声明 outputSchema（阶跃不消费，写了也没意义）
server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
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
    ]
}));

// 处理工具调用
// 注意: 使用 content 返回即可
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === 'hello') {
        return {
            content: [{
                type: 'text',
                text: JSON.stringify({
                    success: true,
                    message: `你好, ${args.name}!`
                })
            }]
        };
    }

    throw new Error(`Unknown tool: ${name}`);
});

// 启动
const transport = new StdioServerTransport();
await server.connect(transport);
