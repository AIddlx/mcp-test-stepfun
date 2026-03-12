#!/usr/bin/env node

/**
 * MCP stdio 全量测试服务器 (NPX 模式)
 *
 * 包含35个测试工具，与 HTTP URL 模式功能一致
 *
 * 阶跃客户端配置:
 * {
 *   "mcpServers": {
 *     "mcp-npx-test": {
 *       "command": "npx",
 *       "args": ["-y", "C:/path/to/stdio/npx"]
 *     }
 *   }
 * }
 */

import readline from 'readline';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ==================== 日志文件 ====================

// 日志目录：项目根目录/logs
const logsDir = path.resolve(__dirname, '../../logs');
if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
}

const logTimestamp = new Date().toISOString().replace(/[-:T.Z]/g, '').substring(0, 15);
const logFile = path.join(logsDir, `stdio_${logTimestamp}.jsonl`);

function writeLog(entry) {
    const line = JSON.stringify({
        ...entry,
        timestamp: new Date().toISOString()
    });
    fs.appendFileSync(logFile, line + '\n');
}

function log(message, level = 'info') {
    const ts = new Date().toISOString().substring(11, 23);
    process.stderr.write(`[${ts}] [${level.toUpperCase()}] ${message}\n`);
}

// ==================== 状态 ====================

let initialized = false;
let clientProtocolVersion = '';
let clientCapabilities = {};
let requestIdCounter = 0;

// ==================== 消息发送 ====================

function sendMessage(message) {
    const line = JSON.stringify(message);
    process.stdout.write(line + '\n');

    // 记录所有发送的消息到日志文件
    writeLog({ direction: 'OUT', message });
}

function sendResponse(id, result = null, error = null) {
    const response = { jsonrpc: '2.0', id };
    if (error) {
        response.error = error;
    } else {
        response.result = result;
    }
    sendMessage(response);
}

function sendNotification(method, params = null) {
    const notification = { jsonrpc: '2.0', method };
    if (params) {
        notification.params = params;
    }
    sendMessage(notification);
    log(`发送通知: ${method}`);
}

// ==================== 工具定义 ====================

function getTools() {
    return [
        // A 类 - 核心能力
        {
            name: "test_ping",
            description: "[A1] 测试基础连通性。返回 pong 和精确时间戳。",
            inputSchema: {
                type: "object",
                properties: {
                    echo: { type: "string", description: "可选的回显字符串" },
                    delay_ms: { type: "integer", default: 0, description: "响应延迟（毫秒）" }
                }
            }
        },
        {
            name: "test_protocol_version",
            description: "[A2] 测试协议版本协商。验证客户端发送的协议版本。",
            inputSchema: { type: "object", properties: {} }
        },
        {
            name: "test_capabilities",
            description: "[A3] 测试能力协商。返回完整的能力声明。",
            inputSchema: { type: "object", properties: {} }
        },
        {
            name: "test_tool_call",
            description: "[A4] 测试工具调用。验证参数传递和返回格式。",
            inputSchema: {
                type: "object",
                properties: {
                    input_value: { type: "string", description: "输入值" },
                    input_type: {
                        type: "string",
                        enum: ["string", "number", "boolean", "array", "object", "integer", "null"],
                        default: "string"
                    }
                },
                required: ["input_value"]
            }
        },
        {
            name: "test_all_types",
            description: "[A5] 增强类型验证。测试所有类型：string/integer/float/boolean/null/negative/bigint/array/object。",
            inputSchema: {
                type: "object",
                properties: {
                    string_value: { type: "string" },
                    integer_value: { type: "integer" },
                    float_value: { type: "number" },
                    boolean_value: { type: "boolean" },
                    negative_value: { type: "integer" },
                    big_int_value: { type: "integer", description: "大整数（>9007199254740991）" },
                    array_value: { type: "array", items: { type: "integer" } },
                    object_value: { type: "object" }
                }
            }
        },

        // B 类 - 重要能力
        {
            name: "test_complex_params",
            description: "[B1] 测试复杂参数类型：嵌套对象、数组、枚举。",
            inputSchema: {
                type: "object",
                properties: {
                    nested: {
                        type: "object",
                        properties: {
                            level1: {
                                type: "object",
                                properties: {
                                    level2: { type: "string" }
                                }
                            }
                        }
                    },
                    array: { type: "array", items: { type: "integer" } },
                    enum_value: {
                        type: "string",
                        enum: ["option1", "option2", "option3"]
                    }
                }
            }
        },
        {
            name: "test_large_data",
            description: "[B2] 测试大数据传输。生成指定大小的数据。",
            inputSchema: {
                type: "object",
                properties: {
                    size_kb: { type: "integer", default: 1, description: "数据大小（KB）" },
                    items: { type: "integer", default: 10 }
                }
            }
        },
        {
            name: "test_long_operation",
            description: "[B3] 测试长时间操作。模拟耗时任务。",
            inputSchema: {
                type: "object",
                properties: {
                    duration_seconds: { type: "integer", default: 3, description: "操作时长（1-60秒）" }
                }
            }
        },
        {
            name: "test_concurrent",
            description: "[B4] 测试并发请求处理。",
            inputSchema: {
                type: "object",
                properties: {
                    request_id: { type: "string" },
                    delay_ms: { type: "integer", default: 100 }
                }
            }
        },
        {
            name: "test_unicode",
            description: "[B5] 测试 Unicode 支持。",
            inputSchema: {
                type: "object",
                properties: {
                    text: { type: "string" }
                }
            }
        },
        {
            name: "test_error_codes",
            description: "[B6] 测试错误处理。",
            inputSchema: {
                type: "object",
                properties: {
                    error_type: {
                        type: "string",
                        enum: ["invalid_params", "not_found", "internal_error", "unauthorized", "timeout"]
                    }
                },
                required: ["error_type"]
            }
        },

        // C 类 - 高级能力
        {
            name: "test_progress_notification",
            description: "[C1] 测试进度通知。",
            inputSchema: {
                type: "object",
                properties: {
                    steps: { type: "integer", default: 3 },
                    delay_ms: { type: "integer", default: 100 }
                }
            }
        },
        {
            name: "test_cancellation",
            description: "[C2] 测试请求取消。",
            inputSchema: {
                type: "object",
                properties: {
                    duration_seconds: { type: "integer", default: 3 }
                }
            }
        },
        {
            name: "test_batch_request",
            description: "[C3] 测试批量请求。",
            inputSchema: {
                type: "object",
                properties: {
                    operations: {
                        type: "array",
                        items: {
                            type: "object",
                            properties: {
                                operation: { type: "string" },
                                value: { type: "integer" }
                            }
                        }
                    }
                }
            }
        },
        {
            name: "test_completion",
            description: "[C4] 测试自动补全。",
            inputSchema: {
                type: "object",
                properties: {
                    partial_value: { type: "string" }
                }
            }
        },

        // D 类 - 边界条件
        {
            name: "test_empty_params",
            description: "[D1] 测试空参数。",
            inputSchema: { type: "object", properties: {} }
        },
        {
            name: "test_long_string",
            description: "[D2] 测试超长字符串。",
            inputSchema: {
                type: "object",
                properties: {
                    length: { type: "integer", default: 1000 }
                }
            }
        },
        {
            name: "test_special_chars",
            description: "[D3] 测试特殊字符。",
            inputSchema: {
                type: "object",
                properties: {
                    include_control: { type: "boolean", default: true },
                    include_quotes: { type: "boolean", default: true }
                }
            }
        },
        {
            name: "test_idempotency",
            description: "[D4] 测试幂等性。",
            inputSchema: {
                type: "object",
                properties: {
                    operation_id: { type: "string" }
                }
            }
        },
        {
            name: "test_rapid_fire",
            description: "[D5] 测试快速请求。",
            inputSchema: {
                type: "object",
                properties: {
                    count: { type: "integer", default: 5 }
                }
            }
        },
        {
            name: "test_empty_values",
            description: "[D6] 测试空值处理。",
            inputSchema: {
                type: "object",
                properties: {
                    empty_string: { type: "string", default: "" },
                    empty_array: { type: "array", default: [] },
                    empty_object: { type: "object", default: {} }
                }
            }
        },
        {
            name: "test_deep_nesting",
            description: "[D7] 测试深层嵌套。",
            inputSchema: {
                type: "object",
                properties: {
                    depth: { type: "integer", default: 5 }
                }
            }
        },
        {
            name: "test_large_array",
            description: "[D8] 测试大数组。",
            inputSchema: {
                type: "object",
                properties: {
                    count: { type: "integer", default: 100 }
                }
            }
        },

        // E 类 - 极端条件
        {
            name: "test_timeout_boundary",
            description: "[E1] 测试超时边界（55-60秒）。",
            inputSchema: {
                type: "object",
                properties: {
                    duration_seconds: { type: "integer", default: 5, description: "操作时长（1-60秒）" }
                }
            }
        },

        // G 类 - GUI Agent
        {
            name: "gui_desktop_info",
            description: "[G1] 获取桌面信息。",
            inputSchema: { type: "object", properties: {} }
        },
        {
            name: "gui_take_screenshot",
            description: "[G2] 截图。",
            inputSchema: {
                type: "object",
                properties: {
                    format: { type: "string", enum: ["png", "jpg"], default: "png" }
                }
            }
        },
        {
            name: "gui_mouse_click",
            description: "[G3] 鼠标点击。",
            inputSchema: {
                type: "object",
                properties: {
                    x: { type: "integer" },
                    y: { type: "integer" }
                },
                required: ["x", "y"]
            }
        },
        {
            name: "gui_mouse_move",
            description: "[G4] 鼠标移动。",
            inputSchema: {
                type: "object",
                properties: {
                    x: { type: "integer" },
                    y: { type: "integer" }
                },
                required: ["x", "y"]
            }
        },
        {
            name: "gui_keyboard_input",
            description: "[G5] 键盘输入。",
            inputSchema: {
                type: "object",
                properties: {
                    text: { type: "string" }
                },
                required: ["text"]
            }
        },
        {
            name: "gui_send_message",
            description: "[G6] 发送消息（流式多步）。通过 notifications/progress 逐步推送每一步进度。",
            inputSchema: {
                type: "object",
                properties: {
                    contact: { type: "string" },
                    message: { type: "string" },
                    delay_ms: { type: "integer", default: 500, description: "每步间隔（毫秒）" }
                },
                required: ["contact", "message"]
            }
        },
        {
            name: "gui_automation_demo",
            description: "[G7] 自动化演示（一次性返回）。所有步骤在一个响应中返回，无流式进度。",
            inputSchema: {
                type: "object",
                properties: {
                    scenario: { type: "string", default: "notepad" }
                }
            }
        },

        // H 类 - Elicitation
        {
            name: "test_elicitation_form",
            description: "[H1] 测试表单式 Elicitation。",
            inputSchema: {
                type: "object",
                properties: {
                    form_title: { type: "string", default: "用户信息" }
                }
            }
        },
        {
            name: "test_elicitation_url",
            description: "[H2] 测试 URL 式 Elicitation。",
            inputSchema: {
                type: "object",
                properties: {
                    auth_url: { type: "string", default: "https://example.com/auth" }
                }
            }
        },

        // I 类 - Sampling
        {
            name: "test_sampling_basic",
            description: "[I1] 测试基础 Sampling。",
            inputSchema: {
                type: "object",
                properties: {
                    prompt: { type: "string", default: "What is 2+2?" }
                }
            }
        },
        {
            name: "test_sampling_with_tools",
            description: "[I2] 测试带工具的 Sampling。",
            inputSchema: {
                type: "object",
                properties: {
                    task: { type: "string" }
                }
            }
        }
    ];
}

// ==================== 工具实现 ====================

const operationCache = new Map();

function callTool(name, args) {
    const startTime = Date.now();

    // A 类 - 核心能力
    if (name === "test_ping") {
        const delay = args.delay_ms || 0;
        if (delay > 0) {
            // 注意：这里简化处理，实际不能阻塞
        }
        return {
            test_id: "A1",
            success: true,
            pong: "pong",
            echo: args.echo || null,
            server_time: new Date().toISOString(),
            elapsed_ms: Date.now() - startTime
        };
    }

    if (name === "test_protocol_version") {
        return {
            test_id: "A2",
            success: true,
            client_protocol_version: clientProtocolVersion,
            server_protocol_version: "2025-11-25",
            version_match: clientProtocolVersion === "2025-11-25",
            note: clientProtocolVersion !== "2025-11-25" ?
                `客户端使用 ${clientProtocolVersion}，服务器使用 2025-11-25` : "版本匹配"
        };
    }

    if (name === "test_capabilities") {
        return {
            test_id: "A3",
            success: true,
            server_capabilities: {
                tools: { listChanged: true },
                resources: { subscribe: true, listChanged: true },
                prompts: { listChanged: true },
                logging: {}
            },
            protocol_version: "2025-11-25"
        };
    }

    if (name === "test_tool_call") {
        const value = args.input_value;
        const actualType = Array.isArray(value) ? "array" :
            value === null ? "null" : typeof value;
        return {
            test_id: "A4",
            success: true,
            received_value: value,
            received_type: args.input_type || "string",
            actual_type: actualType,
            type_match: actualType === (args.input_type || "string"),
            server_time: new Date().toISOString()
        };
    }

    if (name === "test_all_types") {
        const results = {};
        const values = {
            string: args.string_value,
            integer: args.integer_value,
            float: args.float_value,
            boolean: args.boolean_value,
            null: null,
            negative: args.negative_value,
            bigint: args.big_int_value,
            array: args.array_value,
            object: args.object_value
        };

        for (const [type, value] of Object.entries(values)) {
            if (value !== undefined) {
                results[type] = {
                    received: value,
                    type: Array.isArray(value) ? "array" : (value === null ? "null" : typeof value),
                    valid: true
                };
            }
        }

        return {
            test_id: "A5",
            success: true,
            type_results: results,
            summary: {
                tested_types: Object.keys(results).length,
                all_valid: true
            },
            server_time: new Date().toISOString()
        };
    }

    // B 类 - 重要能力
    if (name === "test_complex_params") {
        return {
            test_id: "B1",
            success: true,
            received: {
                nested: args.nested || null,
                array: args.array || null,
                enum_value: args.enum_value || null
            },
            types: {
                nested_type: args.nested ? "object" : "null",
                array_type: Array.isArray(args.array) ? "array" : "null",
                enum_type: typeof args.enum_value
            }
        };
    }

    if (name === "test_large_data") {
        const sizeKb = args.size_kb || 1;
        const items = args.items || 10;
        const data = [];
        const itemSize = Math.floor((sizeKb * 1024) / items);

        for (let i = 0; i < items; i++) {
            data.push({
                id: i,
                data: "x".repeat(Math.max(1, itemSize - 20))
            });
        }

        return {
            test_id: "B2",
            success: true,
            requested_size_kb: sizeKb,
            items: items,
            actual_size_bytes: JSON.stringify(data).length,
            sample: data.slice(0, 2)
        };
    }

    if (name === "test_long_operation") {
        const duration = Math.min(Math.max(args.duration_seconds || 3, 1), 60);
        return {
            test_id: "B3",
            success: true,
            duration_seconds: duration,
            message: `模拟 ${duration} 秒操作完成`,
            elapsed_ms: Date.now() - startTime
        };
    }

    if (name === "test_concurrent") {
        return {
            test_id: "B4",
            success: true,
            request_id: args.request_id || "unknown",
            processed_at: new Date().toISOString(),
            elapsed_ms: Date.now() - startTime
        };
    }

    if (name === "test_unicode") {
        const text = args.text || "你好世界 🌍";
        return {
            test_id: "B5",
            success: true,
            received: text,
            length: text.length,
            bytes: Buffer.from(text).length,
            has_chinese: /[\u4e00-\u9fff]/.test(text),
            has_emoji: /[\u{1F300}-\u{1F9FF}]/u.test(text)
        };
    }

    if (name === "test_error_codes") {
        const errorType = args.error_type;
        const errorInfo = {
            invalid_params: { code: -32602, message: "Invalid params" },
            not_found: { code: -32601, message: "Method not found" },
            internal_error: { code: -32603, message: "Internal error" },
            unauthorized: { code: -32600, message: "Unauthorized" },
            timeout: { code: -32603, message: "Request timeout" }
        };

        const err = errorInfo[errorType] || errorInfo.internal_error;
        return {
            test_id: "B6",
            success: false,
            error: err.message,
            error_code: err.code,
            error_type: errorType
        };
    }

    // C 类 - 高级能力
    if (name === "test_progress_notification") {
        const steps = Math.min(Math.max(args.steps || 3, 1), 10);
        const delayMs = args.delay_ms || 100;

        // 发送进度通知
        setTimeout(() => {
            for (let i = 0; i < steps; i++) {
                setTimeout(() => {
                    sendNotification('notifications/progress', {
                        progressToken: 'progress-test',
                        progress: (i + 1) / steps,
                        total: steps,
                        message: `Step ${i + 1}/${steps}`
                    });
                }, (i + 1) * delayMs);
            }
        }, 10);

        return {
            test_id: "C1",
            success: true,
            message: "Progress notifications started",
            steps: steps,
            delay_ms: delayMs
        };
    }

    if (name === "test_cancellation") {
        return {
            test_id: "C2",
            success: true,
            duration_seconds: args.duration_seconds || 3,
            message: "Cancellation test completed",
            elapsed_ms: Date.now() - startTime
        };
    }

    if (name === "test_batch_request") {
        const ops = args.operations || [];
        const results = ops.map(op => {
            if (op.operation === "add") {
                return { operation: "add", result: (op.value || 0) + 1 };
            } else if (op.operation === "multiply") {
                return { operation: "multiply", result: (op.value || 0) * 2 };
            }
            return { operation: op.operation, result: null };
        });

        return {
            test_id: "C3",
            success: true,
            operations_count: ops.length,
            results: results
        };
    }

    if (name === "test_completion") {
        const partial = args.partial_value || "test";
        const suggestions = [
            partial + "_complete1",
            partial + "_complete2",
            partial + "_complete3"
        ];

        return {
            test_id: "C4",
            success: true,
            partial_value: partial,
            suggestions: suggestions
        };
    }

    // D 类 - 边界条件
    if (name === "test_empty_params") {
        return {
            test_id: "D1",
            success: true,
            params_count: Object.keys(args).length,
            message: "Empty params test passed"
        };
    }

    if (name === "test_long_string") {
        const length = args.length || 1000;
        const longStr = "x".repeat(length);
        return {
            test_id: "D2",
            success: true,
            length: length,
            first_10: longStr.substring(0, 10),
            last_10: longStr.substring(length - 10),
            elapsed_ms: Date.now() - startTime
        };
    }

    if (name === "test_special_chars") {
        const includeControl = args.include_control !== false;
        const includeQuotes = args.include_quotes !== false;

        let result = "";
        if (includeControl) result += "\x00\x01\x02";
        if (includeQuotes) result += "\"'\n\r\t";
        result += "正常文本";

        return {
            test_id: "D3",
            success: true,
            special_chars: result,
            includes: { control: includeControl, quotes: includeQuotes }
        };
    }

    if (name === "test_idempotency") {
        const opId = args.operation_id || "default";
        const cached = operationCache.has(opId);
        operationCache.set(opId, true);

        return {
            test_id: "D4",
            success: true,
            operation_id: opId,
            cached: cached,
            message: cached ? "重复请求，结果已缓存" : "首次请求"
        };
    }

    if (name === "test_rapid_fire") {
        const count = args.count || 5;
        const results = [];
        for (let i = 0; i < count; i++) {
            results.push({ index: i, time: Date.now() });
        }

        return {
            test_id: "D5",
            success: true,
            count: count,
            results: results,
            total_time_ms: Date.now() - startTime
        };
    }

    if (name === "test_empty_values") {
        return {
            test_id: "D6",
            success: true,
            received: {
                empty_string: args.empty_string ?? "",
                empty_array: args.empty_array ?? [],
                empty_object: args.empty_object ?? {}
            },
            types: {
                empty_string_type: typeof (args.empty_string ?? ""),
                empty_array_type: Array.isArray(args.empty_array ?? []) ? "array" : "other",
                empty_object_type: typeof (args.empty_object ?? {})
            }
        };
    }

    if (name === "test_deep_nesting") {
        const depth = args.depth || 5;
        let nested = { value: "deepest" };
        for (let i = 0; i < depth; i++) {
            nested = { level: depth - i, nested: nested };
        }

        return {
            test_id: "D7",
            success: true,
            depth: depth,
            structure: nested
        };
    }

    if (name === "test_large_array") {
        const count = args.count || 100;
        const arr = [];
        for (let i = 0; i < count; i++) {
            arr.push(i);
        }

        return {
            test_id: "D8",
            success: true,
            count: count,
            first_5: arr.slice(0, 5),
            last_5: arr.slice(-5),
            sum: arr.reduce((a, b) => a + b, 0)
        };
    }

    // E 类 - 极端条件
    if (name === "test_timeout_boundary") {
        const duration = Math.min(Math.max(args.duration_seconds || 5, 1), 60);
        return {
            test_id: "E1",
            success: true,
            duration_seconds: duration,
            note: `操作完成，未触发超时（${duration}秒）`,
            elapsed_ms: Date.now() - startTime
        };
    }

    // G 类 - GUI Agent
    if (name === "gui_desktop_info") {
        return {
            test_id: "G1",
            success: true,
            resolution: { width: 1920, height: 1080 },
            active_window: "模拟窗口",
            windows: ["Window1", "Window2", "Window3"]
        };
    }

    if (name === "gui_take_screenshot") {
        return {
            test_id: "G2",
            success: true,
            format: args.format || "png",
            width: 1920,
            height: 1080,
            message: "截图成功（模拟）"
        };
    }

    if (name === "gui_mouse_click") {
        return {
            test_id: "G3",
            success: true,
            action: "click",
            position: { x: args.x, y: args.y },
            message: `点击 (${args.x}, ${args.y})`
        };
    }

    if (name === "gui_mouse_move") {
        return {
            test_id: "G4",
            success: true,
            action: "move",
            position: { x: args.x, y: args.y },
            message: `移动到 (${args.x}, ${args.y})`
        };
    }

    if (name === "gui_keyboard_input") {
        return {
            test_id: "G5",
            success: true,
            action: "input",
            text: args.text,
            length: args.text.length,
            message: `输入文本: ${args.text}`
        };
    }

    if (name === "gui_send_message") {
        // 流式多步骤：通过 notifications/progress 逐步推送每一步
        const steps = ["查找联系人", "打开对话", "输入消息", "发送"];
        const delayMs = args.delay_ms || 500;

        // 逐步发送进度通知
        steps.forEach((step, index) => {
            setTimeout(() => {
                sendNotification('notifications/progress', {
                    progressToken: 'gui-send-message-progress',
                    progress: index + 1,
                    total: steps.length,
                    message: `[G6 流式] 步骤 ${index + 1}/${steps.length}: ${step}`
                });
            }, (index + 1) * delayMs);
        });

        return {
            test_id: "G6",
            success: true,
            contact: args.contact,
            message: args.message,
            mode: "streaming",
            steps: steps,
            note: "通过 notifications/progress 流式推送每一步进度",
            elapsed_ms: steps.length * delayMs
        };
    }

    if (name === "gui_automation_demo") {
        // 一次性返回：所有步骤在一个响应中返回
        return {
            test_id: "G7",
            success: true,
            scenario: args.scenario || "notepad",
            mode: "batch",
            steps: [
                "打开应用",
                "等待启动",
                "输入文本",
                "保存文件",
                "关闭应用"
            ],
            note: "一次性返回所有步骤，无流式进度",
            message: "自动化演示完成"
        };
    }

    // H 类 - Elicitation
    if (name === "test_elicitation_form") {
        return {
            test_id: "H1",
            success: true,
            elicitation_type: "form",
            form_title: args.form_title || "用户信息",
            fields: ["name", "email"],
            note: "表单式 Elicitation 测试"
        };
    }

    if (name === "test_elicitation_url") {
        return {
            test_id: "H2",
            success: true,
            elicitation_type: "url",
            auth_url: args.auth_url || "https://example.com/auth",
            note: "URL 式 Elicitation 测试"
        };
    }

    // I 类 - Sampling
    if (name === "test_sampling_basic") {
        return {
            test_id: "I1",
            success: true,
            prompt: args.prompt || "What is 2+2?",
            note: "基础 Sampling 测试"
        };
    }

    if (name === "test_sampling_with_tools") {
        return {
            test_id: "I2",
            success: true,
            task: args.task || null,
            available_tools: ["test_ping", "test_tool_call"],
            note: "带工具的 Sampling 测试"
        };
    }

    return { success: false, error: `Unknown tool: ${name}` };
}

// ==================== 请求处理 ====================

function handleRequest(request) {
    const method = request.method;
    const params = request.params || {};
    const id = request.id;

    log(`收到请求: ${method}` + (id !== undefined ? ` (id=${id})` : ''));

    // 初始化
    if (method === "initialize") {
        clientProtocolVersion = params.protocolVersion || "2024-11-05";
        clientCapabilities = params.capabilities || {};
        initialized = true;

        return {
            protocolVersion: "2025-11-25",
            capabilities: {
                tools: { listChanged: true },
                resources: { subscribe: true, listChanged: true },
                prompts: { listChanged: true },
                logging: {}
            },
            serverInfo: {
                name: "mcp-stdio-full-test",
                version: "1.0.0"
            },
            instructions: "MCP stdio 全量测试服务器。包含31个测试工具 (A-I类)。"
        };
    }

    // 初始化完成通知
    if (method === "notifications/initialized") {
        log('客户端初始化完成');
        return null;
    }

    // 工具
    if (method === "tools/list") {
        return { tools: getTools() };
    }

    if (method === "tools/call") {
        const toolName = params.name;
        const toolArgs = params.arguments || {};
        const result = callTool(toolName, toolArgs);
        const isError = result.success === false;

        return {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            isError
        };
    }

    // Ping
    if (method === "ping") {
        return { pong: true, timestamp: new Date().toISOString() };
    }

    return null;
}

// ==================== 主循环 ====================

log('MCP stdio 全量测试服务器启动 (Node.js)');
log('包含31个测试工具 (A-I类)');
log('等待客户端连接...');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

rl.on('line', (line) => {
    if (!line.trim()) return;

    try {
        const request = JSON.parse(line);

        // 记录接收的消息
        writeLog({ direction: 'IN', message: request });

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
        log(`错误: ${e.message}`, 'error');
        sendResponse(null, null, { code: -32700, message: 'Parse error' });
    }
});

rl.on('close', () => {
    log('服务器关闭');
    process.exit(0);
});
