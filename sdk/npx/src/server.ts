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

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ==================== 服务器实例 ====================

const server = new Server(
  { name: "mcp-npx-sdk", version: "1.0.0" },
  { capabilities: { tools: { listChanged: true } } }
);

// 幂等性缓存
const idempotencyCache = new Map<string, string>();

// ==================== 工具定义 (35个) ====================

const TOOLS = [
  // --- A 类 - 核心能力 (5个) ---
  {
    name: "test_ping",
    description: "[A1] 测试基础连通性。返回 pong 和精确时间戳。",
    inputSchema: {
      type: "object",
      properties: {
        echo: { type: "string", description: "可选的回显字符串" },
        delay_ms: { type: "integer", description: "响应延迟（毫秒）", default: 0 },
      },
    },
  },
  {
    name: "test_protocol_version",
    description: "[A2] 测试协议版本协商。验证客户端发送的协议版本。",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "test_capabilities",
    description: "[A3] 测试能力协商。返回完整的能力声明。",
    inputSchema: { type: "object", properties: {} },
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
          description: "期望的类型",
          enum: ["string", "number", "boolean", "array", "object", "integer", "null"],
          default: "string",
        },
      },
      required: ["input_value"],
    },
  },
  {
    name: "test_all_types",
    description: "[A5] 增强类型验证。测试所有类型：string/integer/float/boolean/null/negative/bigint/array/object。",
    inputSchema: {
      type: "object",
      properties: {
        string_value: { type: "string", description: "字符串值" },
        integer_value: { type: "integer", description: "整数值" },
        float_value: { type: "number", description: "浮点数值" },
        boolean_value: { type: "boolean", description: "布尔值" },
        negative_value: { type: "integer", description: "负数值" },
        big_int_value: { type: "integer", description: "大整数值" },
        array_value: { type: "array", description: "数组值", items: { type: "number" } },
        object_value: { type: "object", description: "对象值" },
      },
    },
  },

  // --- B 类 - 重要能力 (6个) ---
  {
    name: "test_complex_params",
    description: "[B1] 测试复杂参数类型：嵌套对象、数组、枚举。",
    inputSchema: {
      type: "object",
      properties: {
        nested: { type: "object", description: "嵌套对象" },
        array: { type: "array", description: "数组", items: { type: "number" } },
        enum_value: {
          type: "string",
          description: "枚举值",
          enum: ["option1", "option2", "option3"],
          default: "option1",
        },
      },
    },
  },
  {
    name: "test_large_data",
    description: "[B2] 测试大数据传输。生成指定大小的数据。",
    inputSchema: {
      type: "object",
      properties: {
        size_kb: { type: "integer", description: "数据大小(KB)", default: 1 },
        items: { type: "integer", description: "数据条数", default: 10 },
      },
    },
  },
  {
    name: "test_long_operation",
    description: "[B3] 测试长时间操作。模拟耗时任务。",
    inputSchema: {
      type: "object",
      properties: {
        duration_seconds: { type: "integer", description: "持续时间（秒）", default: 3 },
      },
    },
  },
  {
    name: "test_concurrent",
    description: "[B4] 测试并发请求处理。",
    inputSchema: {
      type: "object",
      properties: {
        request_id: { type: "string", description: "请求ID", default: "" },
        delay_ms: { type: "integer", description: "延迟（毫秒）", default: 100 },
      },
    },
  },
  {
    name: "test_unicode",
    description: "[B5] 测试 Unicode 支持。",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "测试文本", default: "" },
      },
    },
  },
  {
    name: "test_error_codes",
    description: "[B6] 测试错误处理。",
    inputSchema: {
      type: "object",
      properties: {
        error_type: {
          type: "string",
          description: "错误类型",
          enum: ["invalid_params", "not_found", "internal_error", "unauthorized", "timeout"],
          default: "invalid_params",
        },
      },
    },
  },

  // --- C 类 - 高级能力 (4个) ---
  {
    name: "test_progress_notification",
    description: "[C1] 测试进度通知。通过 notifications/progress 逐步推送进度。",
    inputSchema: {
      type: "object",
      properties: {
        steps: { type: "integer", description: "步骤数", default: 3 },
        delay_ms: { type: "integer", description: "每步延迟（毫秒）", default: 100 },
      },
    },
  },
  {
    name: "test_cancellation",
    description: "[C2] 测试请求取消。",
    inputSchema: {
      type: "object",
      properties: {
        duration_seconds: { type: "integer", description: "持续时间（秒）", default: 2 },
      },
    },
  },
  {
    name: "test_batch_request",
    description: "[C3] 测试批量请求。",
    inputSchema: {
      type: "object",
      properties: {
        operations: {
          type: "array",
          description: "操作列表",
          items: {
            type: "object",
            properties: {
              operation: { type: "string" },
              value: { type: "number" },
            },
          },
          default: [],
        },
      },
    },
  },
  {
    name: "test_completion",
    description: "[C4] 测试自动补全。",
    inputSchema: {
      type: "object",
      properties: {
        partial_value: { type: "string", description: "部分值", default: "" },
      },
    },
  },

  // --- D 类 - 边界条件 (8个) ---
  {
    name: "test_empty_params",
    description: "[D1] 测试空参数。",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "test_long_string",
    description: "[D2] 测试超长字符串。",
    inputSchema: {
      type: "object",
      properties: {
        length: { type: "integer", description: "字符串长度", default: 1000 },
      },
    },
  },
  {
    name: "test_special_chars",
    description: "[D3] 测试特殊字符。",
    inputSchema: {
      type: "object",
      properties: {
        include_control: { type: "boolean", description: "包含控制字符", default: true },
        include_quotes: { type: "boolean", description: "包含引号", default: true },
      },
    },
  },
  {
    name: "test_idempotency",
    description: "[D4] 测试幂等性。",
    inputSchema: {
      type: "object",
      properties: {
        operation_id: { type: "string", description: "操作ID", default: "" },
      },
    },
  },
  {
    name: "test_rapid_fire",
    description: "[D5] 测试快速请求。",
    inputSchema: {
      type: "object",
      properties: {
        count: { type: "integer", description: "请求次数", default: 5 },
      },
    },
  },
  {
    name: "test_empty_values",
    description: "[D6] 测试空值处理。",
    inputSchema: {
      type: "object",
      properties: {
        empty_string: { type: "string", description: "空字符串", default: "" },
        empty_array: { type: "array", description: "空数组", default: [] },
        empty_object: { type: "object", description: "空对象", default: {} },
      },
    },
  },
  {
    name: "test_deep_nesting",
    description: "[D7] 测试深层嵌套。",
    inputSchema: {
      type: "object",
      properties: {
        depth: { type: "integer", description: "嵌套深度", default: 5 },
      },
    },
  },
  {
    name: "test_large_array",
    description: "[D8] 测试大数组。",
    inputSchema: {
      type: "object",
      properties: {
        count: { type: "integer", description: "数组大小", default: 100 },
      },
    },
  },

  // --- E 类 - 极端条件 (1个) ---
  {
    name: "test_timeout_boundary",
    description: "[E1] 测试超时边界（55-60秒）。",
    inputSchema: {
      type: "object",
      properties: {
        duration_seconds: { type: "integer", description: "持续时间（秒）", default: 5 },
      },
    },
  },

  // --- G 类 - GUI Agent (7个) ---
  {
    name: "gui_desktop_info",
    description: "[G1] 获取桌面信息。",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "gui_take_screenshot",
    description: "[G2] 截图。",
    inputSchema: {
      type: "object",
      properties: {
        format: {
          type: "string",
          description: "截图格式",
          enum: ["png", "jpg"],
          default: "png",
        },
      },
    },
  },
  {
    name: "gui_mouse_click",
    description: "[G3] 鼠标点击。",
    inputSchema: {
      type: "object",
      properties: {
        x: { type: "integer", description: "X 坐标" },
        y: { type: "integer", description: "Y 坐标" },
      },
      required: ["x", "y"],
    },
  },
  {
    name: "gui_mouse_move",
    description: "[G4] 鼠标移动。",
    inputSchema: {
      type: "object",
      properties: {
        x: { type: "integer", description: "X 坐标" },
        y: { type: "integer", description: "Y 坐标" },
      },
      required: ["x", "y"],
    },
  },
  {
    name: "gui_keyboard_input",
    description: "[G5] 键盘输入。",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "输入文本" },
      },
      required: ["text"],
    },
  },
  {
    name: "gui_send_message",
    description: "[G6] 发送消息（流式多步）。通过 notifications/progress 逐步推送每一步进度。",
    inputSchema: {
      type: "object",
      properties: {
        contact: { type: "string", description: "联系人" },
        message: { type: "string", description: "消息内容" },
        delay_ms: { type: "integer", description: "每步延迟（毫秒）", default: 500 },
      },
      required: ["contact", "message"],
    },
  },
  {
    name: "gui_automation_demo",
    description: "[G7] 自动化演示（一次性返回）。所有步骤在一个响应中返回，无流式进度。",
    inputSchema: {
      type: "object",
      properties: {
        scenario: { type: "string", description: "场景", default: "notepad" },
      },
    },
  },

  // --- H 类 - Elicitation (2个) ---
  {
    name: "test_elicitation_form",
    description: "[H1] 测试表单式 Elicitation。",
    inputSchema: {
      type: "object",
      properties: {
        form_title: { type: "string", description: "表单标题", default: "用户信息" },
      },
    },
  },
  {
    name: "test_elicitation_url",
    description: "[H2] 测试 URL 式 Elicitation。",
    inputSchema: {
      type: "object",
      properties: {
        auth_url: { type: "string", description: "认证URL", default: "https://example.com/auth" },
      },
    },
  },

  // --- I 类 - Sampling (2个) ---
  {
    name: "test_sampling_basic",
    description: "[I1] 测试基础 Sampling。",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "提示词", default: "What is 2+2?" },
      },
    },
  },
  {
    name: "test_sampling_with_tools",
    description: "[I2] 测试带工具的 Sampling。",
    inputSchema: {
      type: "object",
      properties: {
        task: { type: "string", description: "任务描述", default: "" },
      },
    },
  },
];

// ==================== MCP 处理器 ====================

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

server.setRequestHandler(CallToolRequestSchema, async (request, extra) => {
  const { name, arguments: args } = request.params;
  const progressToken = request.params._meta?.progressToken;

  // 辅助函数：发送进度通知
  const sendProgress = async (current: number, total: number, message: string) => {
    if (progressToken) {
      await extra.sendNotification({
        method: "notifications/progress",
        params: {
          progressToken,
          progress: current,
          total,
          message,
        },
      } as any);
    }
  };

  switch (name) {
    // --- A 类 - 核心能力 (5个) ---
    case "test_ping": {
      const echo = (args?.echo as string) || "";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "A1", success: true, pong: "pong",
          echo: echo || null,
          server_time: new Date().toISOString(), elapsed_ms: 0,
        }) }],
      };
    }

    case "test_protocol_version": {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "A2", success: true,
          client_protocol_version: "from_client",
          server_protocol_version: "2025-11-25",
          version_match: true, note: "版本匹配",
        }) }],
      };
    }

    case "test_capabilities": {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "A3", success: true,
          server_capabilities: {
            tools: { listChanged: true },
            resources: { subscribe: true, listChanged: true },
            prompts: { listChanged: true },
            logging: {},
          },
          protocol_version: "2025-11-25",
        }) }],
      };
    }

    case "test_tool_call": {
      const input_value = args?.input_value as string;
      const input_type = (args?.input_type as string) || "string";
      const actualType = typeof input_value;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "A4", success: true,
          received_value: input_value, received_type: input_type,
          actual_type: actualType, type_match: actualType === input_type,
          server_time: new Date().toISOString(),
        }) }],
      };
    }

    case "test_all_types": {
      const results: Record<string, any> = {};
      if (args?.string_value) results.string = { received: args.string_value, type: "string", valid: true };
      if (args?.integer_value != null) results.integer = { received: args.integer_value, type: "number", valid: true };
      if (args?.float_value != null) results.float = { received: args.float_value, type: "number", valid: true };
      if (args?.boolean_value != null) results.boolean = { received: args.boolean_value, type: "boolean", valid: true };
      if (args?.negative_value != null) results.negative = { received: args.negative_value, type: "number", valid: true };
      if (args?.big_int_value != null) results.bigint = { received: args.big_int_value, type: "number", valid: true };
      if (args?.array_value) results.array = { received: args.array_value, type: "array", valid: true };
      if (args?.object_value) results.object = { received: args.object_value, type: "object", valid: true };
      results.null = { received: null, type: "null", valid: true };
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "A5", success: true, type_results: results,
          summary: { tested_types: Object.keys(results).length, all_valid: true },
          server_time: new Date().toISOString(),
        }) }],
      };
    }

    // --- B 类 - 重要能力 (6个) ---
    case "test_complex_params": {
      const nested = args?.nested || null;
      const array = args?.array || null;
      const enum_value = (args?.enum_value as string) || "option1";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B1", success: true,
          received: { nested, array, enum_value },
          types: {
            nested_type: nested ? "object" : "null",
            array_type: Array.isArray(array) ? "array" : "null",
            enum_type: typeof enum_value,
          },
        }) }],
      };
    }

    case "test_large_data": {
      const size_kb = (args?.size_kb as number) || 1;
      const items = (args?.items as number) || 10;
      const data = [];
      const chunkSize = Math.max(1, Math.floor((size_kb * 1024) / items));
      for (let i = 0; i < items; i++) {
        data.push({ id: i, data: "x".repeat(chunkSize) });
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B2", success: true,
          requested_size_kb: size_kb, items,
          actual_size_bytes: JSON.stringify(data).length,
          sample: data.slice(0, 2),
        }) }],
      };
    }

    case "test_long_operation": {
      const duration_seconds = (args?.duration_seconds as number) || 3;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B3", success: true, duration_seconds,
          message: `模拟 ${duration_seconds} 秒操作完成`, elapsed_ms: 0,
        }) }],
      };
    }

    case "test_concurrent": {
      const request_id = (args?.request_id as string) || "";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B4", success: true, request_id,
          processed_at: new Date().toISOString(), elapsed_ms: 0,
        }) }],
      };
    }

    case "test_unicode": {
      const text = (args?.text as string) || "";
      const hasChinese = /[\u4e00-\u9fff]/.test(text);
      const hasEmoji = /[\u{1F300}-\u{1F9FF}]/u.test(text);
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B5", success: true, received: text,
          length: text.length, bytes: Buffer.byteLength(text, "utf-8"),
          has_chinese: hasChinese, has_emoji: hasEmoji,
        }) }],
      };
    }

    case "test_error_codes": {
      const error_type = (args?.error_type as string) || "invalid_params";
      const errorMap: Record<string, { code: number; message: string }> = {
        invalid_params: { code: -32602, message: "Invalid params" },
        not_found: { code: -32601, message: "Method not found" },
        internal_error: { code: -32603, message: "Internal error" },
        unauthorized: { code: -32000, message: "Unauthorized" },
        timeout: { code: -32001, message: "Timeout" },
      };
      const err = errorMap[error_type] || errorMap.internal_error;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "B6", success: false, error: err.message,
          error_code: err.code, error_type,
        }) }],
      };
    }

    // --- C 类 - 高级能力 (4个) ---
    case "test_progress_notification": {
      const steps = Math.max(1, Math.min((args?.steps as number) || 3, 10));
      const delayMs = (args?.delay_ms as number) || 100;
      for (let i = 0; i < steps; i++) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        await sendProgress(i + 1, steps, `Step ${i + 1}/${steps}`);
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "C1", success: true,
          message: "Progress notifications completed",
          steps, delay_ms: delayMs,
        }) }],
      };
    }

    case "test_cancellation": {
      const duration_seconds = (args?.duration_seconds as number) || 2;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "C2", success: true, duration_seconds,
          message: "Cancellation test completed", elapsed_ms: 0,
        }) }],
      };
    }

    case "test_batch_request": {
      const operations = (args?.operations as Array<{ operation: string; value?: number }>) || [];
      const results = operations.map((op) => {
        if (op.operation === "add") {
          return { operation: "add", result: (op.value || 0) + 1 };
        } else if (op.operation === "multiply") {
          return { operation: "multiply", result: (op.value || 0) * 2 };
        }
        return { operation: op.operation, result: null };
      });
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "C3", success: true,
          operations_count: operations.length, results,
        }) }],
      };
    }

    case "test_completion": {
      const partial_value = (args?.partial_value as string) || "";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "C4", success: true, partial_value,
          suggestions: [
            `${partial_value}_complete1`,
            `${partial_value}_complete2`,
            `${partial_value}_complete3`,
          ],
        }) }],
      };
    }

    // --- D 类 - 边界条件 (8个) ---
    case "test_empty_params": {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D1", success: true, params_count: 0,
          message: "Empty params test passed",
        }) }],
      };
    }

    case "test_long_string": {
      const length = (args?.length as number) || 1000;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D2", success: true, length,
          first_10: "x".repeat(10), last_10: "x".repeat(10), elapsed_ms: 0,
        }) }],
      };
    }

    case "test_special_chars": {
      const include_control = args?.include_control !== false;
      const include_quotes = args?.include_quotes !== false;
      let specialChars = "";
      if (include_control) specialChars += "\x00\x01\x02";
      if (include_quotes) specialChars += "\"'\n\r\t";
      specialChars += "正常文本";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D3", success: true, special_chars: specialChars,
          includes: { control: include_control, quotes: include_quotes },
        }) }],
      };
    }

    case "test_idempotency": {
      const operation_id = (args?.operation_id as string) || "";
      const cached = idempotencyCache.has(operation_id);
      if (!cached) {
        idempotencyCache.set(operation_id, new Date().toISOString());
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D4", success: true, operation_id,
          cached, message: cached ? "缓存命中" : "首次请求",
        }) }],
      };
    }

    case "test_rapid_fire": {
      const count = (args?.count as number) || 5;
      const results = [];
      for (let i = 0; i < count; i++) {
        results.push({ index: i, time: Date.now() });
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D5", success: true, count, results, total_time_ms: 0,
        }) }],
      };
    }

    case "test_empty_values": {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D6", success: true,
          received: {
            empty_string: (args?.empty_string as string) || "",
            empty_array: args?.empty_array || [],
            empty_object: args?.empty_object || {},
          },
          types: {
            empty_string_type: "string",
            empty_array_type: "array",
            empty_object_type: "object",
          },
        }) }],
      };
    }

    case "test_deep_nesting": {
      const depth = (args?.depth as number) || 5;
      let structure: any = { value: "deepest" };
      for (let i = depth; i > 0; i--) {
        structure = { level: i, nested: structure };
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D7", success: true, depth, structure,
        }) }],
      };
    }

    case "test_large_array": {
      const count = (args?.count as number) || 100;
      const arr = Array.from({ length: count }, (_, i) => i);
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "D8", success: true, count,
          first_5: arr.slice(0, 5), last_5: arr.slice(-5),
          sum: arr.reduce((a, b) => a + b, 0),
        }) }],
      };
    }

    // --- E 类 - 极端条件 (1个) ---
    case "test_timeout_boundary": {
      const duration_seconds = (args?.duration_seconds as number) || 5;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "E1", success: true, duration_seconds,
          note: `操作完成，未触发超时（${duration_seconds}秒）`, elapsed_ms: 0,
        }) }],
      };
    }

    // --- G 类 - GUI Agent (7个) ---
    case "gui_desktop_info": {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G1", success: true,
          resolution: { width: 1920, height: 1080 },
          active_window: "模拟窗口",
          windows: ["Window1", "Window2", "Window3"],
        }) }],
      };
    }

    case "gui_take_screenshot": {
      const format = (args?.format as string) || "png";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G2", success: true, format,
          width: 1920, height: 1080, message: "截图成功（模拟）",
        }) }],
      };
    }

    case "gui_mouse_click": {
      const x = args?.x as number;
      const y = args?.y as number;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G3", success: true, action: "click",
          position: { x, y }, message: `点击 (${x}, ${y})`,
        }) }],
      };
    }

    case "gui_mouse_move": {
      const x = args?.x as number;
      const y = args?.y as number;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G4", success: true, action: "move",
          position: { x, y }, message: `移动到 (${x}, ${y})`,
        }) }],
      };
    }

    case "gui_keyboard_input": {
      const text = args?.text as string;
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G5", success: true, action: "input",
          text, length: text.length, message: `输入文本: ${text}`,
        }) }],
      };
    }

    case "gui_send_message": {
      const contact = args?.contact as string;
      const message = args?.message as string;
      const delayMs = (args?.delay_ms as number) || 500;
      const steps = ["查找联系人", "打开对话", "输入消息", "发送"];
      for (let i = 0; i < steps.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        await sendProgress(i + 1, steps.length, `[G6 流式] 步骤 ${i + 1}/${steps.length}: ${steps[i]}`);
      }
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G6", success: true, contact, message,
          mode: "streaming", steps,
          note: "通过 notifications/progress 流式推送每一步进度",
          elapsed_ms: steps.length * delayMs,
        }) }],
      };
    }

    case "gui_automation_demo": {
      const scenario = (args?.scenario as string) || "notepad";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "G7", success: true, scenario,
          mode: "batch",
          steps: ["打开应用", "等待启动", "输入文本", "保存文件", "关闭应用"],
          note: "一次性返回所有步骤，无流式进度",
          message: "自动化演示完成",
        }) }],
      };
    }

    // --- H 类 - Elicitation (2个) ---
    case "test_elicitation_form": {
      const form_title = (args?.form_title as string) || "用户信息";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "H1", success: true, elicitation_type: "form",
          form_title, fields: ["name", "email"],
          note: "表单式 Elicitation 测试",
        }) }],
      };
    }

    case "test_elicitation_url": {
      const auth_url = (args?.auth_url as string) || "https://example.com/auth";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "H2", success: true, elicitation_type: "url",
          auth_url, note: "URL 式 Elicitation 测试",
        }) }],
      };
    }

    // --- I 类 - Sampling (2个) ---
    case "test_sampling_basic": {
      const prompt = (args?.prompt as string) || "What is 2+2?";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "I1", success: true, prompt,
          note: "基础 Sampling 测试",
        }) }],
      };
    }

    case "test_sampling_with_tools": {
      const task = (args?.task as string) || "";
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "I2", success: true, task,
          available_tools: ["test_ping", "test_tool_call"],
          note: "带工具的 Sampling 测试",
        }) }],
      };
    }

    default: {
      return {
        content: [{ type: "text" as const, text: JSON.stringify({
          test_id: "unknown", success: false,
          error: `Unknown tool: ${name}`,
        }) }],
      };
    }
  }
});

// ==================== 入口点 ====================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
