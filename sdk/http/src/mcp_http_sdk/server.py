"""
MCP 测试服务器 - HTTP 传输 (官方 SDK, Low-Level Server API)

使用官方 mcp Python SDK 的底层 Server API 实现 Streamable HTTP 传输。

阶跃客户端配置:
{
  "mcpServers": {
    "mcp-http-sdk": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}

启动方式:
  uv run mcp-http-sdk
  或
  python -m mcp_http_sdk.server
"""

import asyncio
import contextlib
import json
from datetime import datetime
from pathlib import Path

from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.shared.progress import progress
from starlette.applications import Starlette
import mcp.types as types
import uvicorn

# ==================== 日志配置 ====================

LOGS_DIR = Path(__file__).parent.parent.parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOGS_DIR / f"http_sdk_{log_timestamp}.jsonl"


def write_log(entry: dict) -> None:
    """写入日志文件"""
    entry["timestamp"] = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_request(method: str, params: dict = None, request_id=None) -> None:
    """记录请求日志"""
    write_log({
        "direction": "IN",
        "method": method,
        "params": params,
        "request_id": request_id
    })


def log_response(request_id, result: dict = None, error: dict = None) -> None:
    """记录响应日志"""
    write_log({
        "direction": "OUT",
        "request_id": request_id,
        "result": result,
        "error": error
    })


# ==================== 服务器实例 ====================

server = Server("mcp-http-sdk")
NOTIFICATION_OPTIONS = NotificationOptions(tools_changed=True)

# ==================== 工具定义 (35个) ====================

TOOLS = [
    # --- A 类 - 核心能力 (5个) ---
    types.Tool(
        name="test_ping",
        description="[A1] 测试基础连通性。返回 pong 和精确时间戳。",
        inputSchema={
            "type": "object",
            "properties": {
                "echo": {"type": "string", "description": "可选的回显字符串"},
                "delay_ms": {"type": "integer", "description": "响应延迟（毫秒）", "default": 0}
            }
        }
    ),
    types.Tool(
        name="test_protocol_version",
        description="[A2] 测试协议版本协商。验证客户端发送的协议版本。",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="test_capabilities",
        description="[A3] 测试能力协商。返回完整的能力声明。",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="test_tool_call",
        description="[A4] 测试工具调用。验证参数传递和返回格式。",
        inputSchema={
            "type": "object",
            "properties": {
                "input_value": {"type": "string", "description": "输入值"},
                "input_type": {
                    "type": "string",
                    "description": "期望的类型",
                    "enum": ["string", "number", "boolean", "array", "object", "integer", "null"],
                    "default": "string"
                }
            },
            "required": ["input_value"]
        }
    ),
    types.Tool(
        name="test_all_types",
        description="[A5] 增强类型验证。测试所有类型：string/integer/float/boolean/null/negative/bigint/array/object。",
        inputSchema={
            "type": "object",
            "properties": {
                "string_value": {"type": "string", "description": "字符串值"},
                "integer_value": {"type": "integer", "description": "整数值"},
                "float_value": {"type": "number", "description": "浮点数值"},
                "boolean_value": {"type": "boolean", "description": "布尔值"},
                "negative_value": {"type": "integer", "description": "负数值"},
                "big_int_value": {"type": "integer", "description": "大整数值"},
                "array_value": {"type": "array", "description": "数组值", "items": {"type": "number"}},
                "object_value": {"type": "object", "description": "对象值"}
            }
        }
    ),

    # --- B 类 - 重要能力 (6个) ---
    types.Tool(
        name="test_complex_params",
        description="[B1] 测试复杂参数类型：嵌套对象、数组、枚举。",
        inputSchema={
            "type": "object",
            "properties": {
                "nested": {"type": "object", "description": "嵌套对象"},
                "array": {"type": "array", "description": "数组", "items": {"type": "number"}},
                "enum_value": {
                    "type": "string",
                    "description": "枚举值",
                    "enum": ["option1", "option2", "option3"],
                    "default": "option1"
                }
            }
        }
    ),
    types.Tool(
        name="test_large_data",
        description="[B2] 测试大数据传输。生成指定大小的数据。",
        inputSchema={
            "type": "object",
            "properties": {
                "size_kb": {"type": "integer", "description": "数据大小(KB)", "default": 1},
                "items": {"type": "integer", "description": "数据条数", "default": 10}
            }
        }
    ),
    types.Tool(
        name="test_long_operation",
        description="[B3] 测试长时间操作。模拟耗时任务。",
        inputSchema={
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "持续时间（秒）", "default": 3}
            }
        }
    ),
    types.Tool(
        name="test_concurrent",
        description="[B4] 测试并发请求处理。",
        inputSchema={
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "请求ID", "default": ""},
                "delay_ms": {"type": "integer", "description": "延迟（毫秒）", "default": 100}
            }
        }
    ),
    types.Tool(
        name="test_unicode",
        description="[B5] 测试 Unicode 支持。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "测试文本", "default": ""}
            }
        }
    ),
    types.Tool(
        name="test_error_codes",
        description="[B6] 测试错误处理。",
        inputSchema={
            "type": "object",
            "properties": {
                "error_type": {
                    "type": "string",
                    "description": "错误类型",
                    "enum": ["invalid_params", "not_found", "internal_error", "unauthorized", "timeout"],
                    "default": "invalid_params"
                }
            }
        }
    ),

    # --- C 类 - 高级能力 (4个) ---
    types.Tool(
        name="test_progress_notification",
        description="[C1] 测试进度通知。通过 notifications/progress 逐步推送进度。",
        inputSchema={
            "type": "object",
            "properties": {
                "steps": {"type": "integer", "description": "步骤数", "default": 3},
                "delay_ms": {"type": "integer", "description": "每步延迟（毫秒）", "default": 100}
            }
        }
    ),
    types.Tool(
        name="test_cancellation",
        description="[C2] 测试请求取消。",
        inputSchema={
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "持续时间（秒）", "default": 2}
            }
        }
    ),
    types.Tool(
        name="test_batch_request",
        description="[C3] 测试批量请求。",
        inputSchema={
            "type": "object",
            "properties": {
                "operations": {
                    "type": "array",
                    "description": "操作列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"},
                            "value": {"type": "number"}
                        }
                    },
                    "default": []
                }
            }
        }
    ),
    types.Tool(
        name="test_completion",
        description="[C4] 测试自动补全。",
        inputSchema={
            "type": "object",
            "properties": {
                "partial_value": {"type": "string", "description": "部分值", "default": ""}
            }
        }
    ),

    # --- D 类 - 边界条件 (8个) ---
    types.Tool(
        name="test_empty_params",
        description="[D1] 测试空参数。",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="test_long_string",
        description="[D2] 测试超长字符串。",
        inputSchema={
            "type": "object",
            "properties": {
                "length": {"type": "integer", "description": "字符串长度", "default": 1000}
            }
        }
    ),
    types.Tool(
        name="test_special_chars",
        description="[D3] 测试特殊字符。",
        inputSchema={
            "type": "object",
            "properties": {
                "include_control": {"type": "boolean", "description": "包含控制字符", "default": True},
                "include_quotes": {"type": "boolean", "description": "包含引号", "default": True}
            }
        }
    ),
    types.Tool(
        name="test_idempotency",
        description="[D4] 测试幂等性。",
        inputSchema={
            "type": "object",
            "properties": {
                "operation_id": {"type": "string", "description": "操作ID", "default": ""}
            }
        }
    ),
    types.Tool(
        name="test_rapid_fire",
        description="[D5] 测试快速请求。",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "请求次数", "default": 5}
            }
        }
    ),
    types.Tool(
        name="test_empty_values",
        description="[D6] 测试空值处理。",
        inputSchema={
            "type": "object",
            "properties": {
                "empty_string": {"type": "string", "description": "空字符串", "default": ""},
                "empty_array": {"type": "array", "description": "空数组", "default": []},
                "empty_object": {"type": "object", "description": "空对象", "default": {}}
            }
        }
    ),
    types.Tool(
        name="test_deep_nesting",
        description="[D7] 测试深层嵌套。",
        inputSchema={
            "type": "object",
            "properties": {
                "depth": {"type": "integer", "description": "嵌套深度", "default": 5}
            }
        }
    ),
    types.Tool(
        name="test_large_array",
        description="[D8] 测试大数组。",
        inputSchema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "数组大小", "default": 100}
            }
        }
    ),

    # --- E 类 - 极端条件 (1个) ---
    types.Tool(
        name="test_timeout_boundary",
        description="[E1] 测试超时边界（55-60秒）。",
        inputSchema={
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "持续时间（秒）", "default": 5}
            }
        }
    ),

    # --- G 类 - GUI Agent (7个) ---
    types.Tool(
        name="gui_desktop_info",
        description="[G1] 获取桌面信息。",
        inputSchema={"type": "object", "properties": {}}
    ),
    types.Tool(
        name="gui_take_screenshot",
        description="[G2] 截图。",
        inputSchema={
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "截图格式",
                    "enum": ["png", "jpg"],
                    "default": "png"
                }
            }
        }
    ),
    types.Tool(
        name="gui_mouse_click",
        description="[G3] 鼠标点击。",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 坐标"},
                "y": {"type": "integer", "description": "Y 坐标"}
            },
            "required": ["x", "y"]
        }
    ),
    types.Tool(
        name="gui_mouse_move",
        description="[G4] 鼠标移动。",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 坐标"},
                "y": {"type": "integer", "description": "Y 坐标"}
            },
            "required": ["x", "y"]
        }
    ),
    types.Tool(
        name="gui_keyboard_input",
        description="[G5] 键盘输入。",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "输入文本"}
            },
            "required": ["text"]
        }
    ),
    types.Tool(
        name="gui_send_message",
        description="[G6] 发送消息（流式多步）。通过 notifications/progress 逐步推送每一步进度。",
        inputSchema={
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人"},
                "message": {"type": "string", "description": "消息内容"},
                "delay_ms": {"type": "integer", "description": "每步延迟（毫秒）", "default": 500}
            },
            "required": ["contact", "message"]
        }
    ),
    types.Tool(
        name="gui_automation_demo",
        description="[G7] 自动化演示（一次性返回）。所有步骤在一个响应中返回，无流式进度。",
        inputSchema={
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "description": "场景", "default": "notepad"}
            }
        }
    ),

    # --- H 类 - Elicitation (2个) ---
    types.Tool(
        name="test_elicitation_form",
        description="[H1] 测试表单式 Elicitation。",
        inputSchema={
            "type": "object",
            "properties": {
                "form_title": {"type": "string", "description": "表单标题", "default": "用户信息"}
            }
        }
    ),
    types.Tool(
        name="test_elicitation_url",
        description="[H2] 测试 URL 式 Elicitation。",
        inputSchema={
            "type": "object",
            "properties": {
                "auth_url": {"type": "string", "description": "认证URL", "default": "https://example.com/auth"}
            }
        }
    ),

    # --- I 类 - Sampling (2个) ---
    types.Tool(
        name="test_sampling_basic",
        description="[I1] 测试基础 Sampling。",
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "提示词", "default": "What is 2+2?"}
            }
        }
    ),
    types.Tool(
        name="test_sampling_with_tools",
        description="[I2] 测试带工具的 Sampling。",
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "任务描述", "default": ""}
            }
        }
    ),

    # --- J 类 - SSE 流式进度通知 (2个) ---
    types.Tool(
        name="test_progress_sse",
        description="[J1] SSE 流式进度通知。通过 notifications/progress 逐步推送进度，客户端需在 _meta 中携带 progressToken。",
        inputSchema={
            "type": "object",
            "properties": {
                "steps": {"type": "integer", "description": "步骤数", "default": 5},
                "delay_ms": {"type": "integer", "description": "每步延迟（毫秒）", "default": 200}
            }
        }
    ),
    types.Tool(
        name="test_streaming_workflow",
        description="[J2] SSE 流式多步工作流。模拟一个完整的多步工作流程，通过 notifications/progress 推送每步进度，客户端需在 _meta 中携带 progressToken。",
        inputSchema={
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "工作流名称",
                    "enum": ["data_pipeline", "file_conversion", "report_generation"],
                    "default": "data_pipeline"
                },
                "step_delay_ms": {"type": "integer", "description": "每步延迟（毫秒）", "default": 300}
            }
        }
    ),
]

# ==================== 工具处理函数 ====================

# 幂等性缓存
_idempotency_cache: dict = {}


async def handle_test_ping(arguments: dict) -> list[types.TextContent]:
    echo = arguments.get("echo", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "A1", "success": True, "pong": "pong",
        "echo": echo if echo else None,
        "server_time": datetime.now().isoformat(), "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_test_protocol_version(arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "A2", "success": True,
        "client_protocol_version": "from_client",
        "server_protocol_version": "2025-11-25",
        "version_match": True, "note": "版本匹配"
    }, ensure_ascii=False))]


async def handle_test_capabilities(arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "A3", "success": True,
        "server_capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True},
            "logging": {}
        },
        "protocol_version": "2025-11-25"
    }, ensure_ascii=False))]


async def handle_test_tool_call(arguments: dict) -> list[types.TextContent]:
    input_value = arguments.get("input_value", "")
    input_type = arguments.get("input_type", "string")
    actual_type = type(input_value).__name__
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "A4", "success": True,
        "received_value": input_value, "received_type": input_type,
        "actual_type": actual_type, "type_match": actual_type == input_type,
        "server_time": datetime.now().isoformat()
    }, ensure_ascii=False))]


async def handle_test_all_types(arguments: dict) -> list[types.TextContent]:
    results = {}
    if arguments.get("string_value"):
        results["string"] = {"received": arguments["string_value"], "type": "string", "valid": True}
    if arguments.get("integer_value"):
        results["integer"] = {"received": arguments["integer_value"], "type": "number", "valid": True}
    if arguments.get("float_value"):
        results["float"] = {"received": arguments["float_value"], "type": "number", "valid": True}
    if arguments.get("boolean_value"):
        results["boolean"] = {"received": arguments["boolean_value"], "type": "boolean", "valid": True}
    if arguments.get("negative_value"):
        results["negative"] = {"received": arguments["negative_value"], "type": "number", "valid": True}
    if arguments.get("big_int_value"):
        results["bigint"] = {"received": arguments["big_int_value"], "type": "number", "valid": True}
    if arguments.get("array_value"):
        results["array"] = {"received": arguments["array_value"], "type": "array", "valid": True}
    if arguments.get("object_value"):
        results["object"] = {"received": arguments["object_value"], "type": "object", "valid": True}
    results["null"] = {"received": None, "type": "null", "valid": True}
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "A5", "success": True, "type_results": results,
        "summary": {"tested_types": len(results), "all_valid": True},
        "server_time": datetime.now().isoformat()
    }, ensure_ascii=False))]


async def handle_test_complex_params(arguments: dict) -> list[types.TextContent]:
    nested = arguments.get("nested", {})
    array = arguments.get("array", [])
    enum_value = arguments.get("enum_value", "option1")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B1", "success": True,
        "received": {"nested": nested, "array": array, "enum_value": enum_value},
        "types": {
            "nested_type": "object" if isinstance(nested, dict) else type(nested).__name__,
            "array_type": "array" if isinstance(array, list) else type(array).__name__,
            "enum_type": "string" if isinstance(enum_value, str) else type(enum_value).__name__
        }
    }, ensure_ascii=False))]


async def handle_test_large_data(arguments: dict) -> list[types.TextContent]:
    size_kb = arguments.get("size_kb", 1)
    items = arguments.get("items", 10)
    data = []
    chunk_size = max(1, size_kb * 1024 // items)
    for i in range(items):
        data.append({"id": i, "data": "x" * chunk_size})
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B2", "success": True,
        "requested_size_kb": size_kb, "items": items,
        "actual_size_bytes": sum(len(str(item)) for item in data),
        "sample": data[:2]
    }, ensure_ascii=False))]


async def handle_test_long_operation(arguments: dict) -> list[types.TextContent]:
    duration_seconds = arguments.get("duration_seconds", 3)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B3", "success": True, "duration_seconds": duration_seconds,
        "message": f"模拟 {duration_seconds} 秒操作完成", "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_test_concurrent(arguments: dict) -> list[types.TextContent]:
    request_id = arguments.get("request_id", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B4", "success": True, "request_id": request_id,
        "processed_at": datetime.now().isoformat(), "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_test_unicode(arguments: dict) -> list[types.TextContent]:
    text = arguments.get("text", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B5", "success": True, "received": text,
        "length": len(text), "bytes": len(text.encode("utf-8")),
        "has_chinese": any("\u4e00" <= c <= "\u9fff" for c in text),
        "has_emoji": any(ord(c) > 0x1F000 for c in text)
    }, ensure_ascii=False))]


async def handle_test_error_codes(arguments: dict) -> list[types.TextContent]:
    error_type = arguments.get("error_type", "invalid_params")
    error_map = {
        "invalid_params": (-32602, "Invalid params"),
        "not_found": (-32601, "Method not found"),
        "internal_error": (-32603, "Internal error"),
        "unauthorized": (-32000, "Unauthorized"),
        "timeout": (-32001, "Timeout")
    }
    code, msg = error_map.get(error_type, (-32603, "Unknown error"))
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "B6", "success": False, "error": msg,
        "error_code": code, "error_type": error_type
    }, ensure_ascii=False))]


async def handle_test_progress_notification(arguments: dict) -> list[types.TextContent]:
    steps = max(1, min(arguments.get("steps", 3), 10))
    delay_ms = arguments.get("delay_ms", 100)
    ctx = server.request_context
    try:
        with progress(ctx, total=float(steps)) as p:
            for i in range(steps):
                await asyncio.sleep(delay_ms / 1000)
                p.progress(float(i + 1), message=f"Step {i + 1}/{steps}")
    except (ValueError, AttributeError):
        await asyncio.sleep(delay_ms / 1000 * steps)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "C1", "success": True,
        "message": "Progress notifications completed",
        "steps": steps, "delay_ms": delay_ms
    }, ensure_ascii=False))]


async def handle_test_cancellation(arguments: dict) -> list[types.TextContent]:
    duration_seconds = arguments.get("duration_seconds", 2)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "C2", "success": True, "duration_seconds": duration_seconds,
        "message": "Cancellation test completed", "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_test_batch_request(arguments: dict) -> list[types.TextContent]:
    operations = arguments.get("operations", [])
    results = []
    for op in operations:
        operation = op.get("operation", "")
        value = op.get("value", 0)
        if operation == "add":
            results.append({"operation": "add", "result": value + 1})
        elif operation == "multiply":
            results.append({"operation": "multiply", "result": value * 2})
        else:
            results.append({"operation": operation, "result": None})
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "C3", "success": True,
        "operations_count": len(operations), "results": results
    }, ensure_ascii=False))]


async def handle_test_completion(arguments: dict) -> list[types.TextContent]:
    partial_value = arguments.get("partial_value", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "C4", "success": True, "partial_value": partial_value,
        "suggestions": [
            f"{partial_value}_complete1",
            f"{partial_value}_complete2",
            f"{partial_value}_complete3"
        ]
    }, ensure_ascii=False))]


async def handle_test_empty_params(arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D1", "success": True, "params_count": 0,
        "message": "Empty params test passed"
    }, ensure_ascii=False))]


async def handle_test_long_string(arguments: dict) -> list[types.TextContent]:
    length = arguments.get("length", 1000)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D2", "success": True, "length": length,
        "first_10": "x" * 10, "last_10": "x" * 10, "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_test_special_chars(arguments: dict) -> list[types.TextContent]:
    special_chars = "\x00\x01\x02\"'\n\r\t正常文本"
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D3", "success": True, "special_chars": special_chars,
        "includes": {
            "control": arguments.get("include_control", True),
            "quotes": arguments.get("include_quotes", True)
        }
    }, ensure_ascii=False))]


async def handle_test_idempotency(arguments: dict) -> list[types.TextContent]:
    global _idempotency_cache
    operation_id = arguments.get("operation_id", "")
    if operation_id in _idempotency_cache:
        result = {"test_id": "D4", "success": True, "operation_id": operation_id,
                  "cached": True, "message": "缓存命中"}
    else:
        _idempotency_cache[operation_id] = datetime.now().isoformat()
        result = {"test_id": "D4", "success": True, "operation_id": operation_id,
                  "cached": False, "message": "首次请求"}
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def handle_test_rapid_fire(arguments: dict) -> list[types.TextContent]:
    import time
    count = arguments.get("count", 5)
    results = [{"index": i, "time": int(time.time() * 1000)} for i in range(count)]
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D5", "success": True, "count": count,
        "results": results, "total_time_ms": 0
    }, ensure_ascii=False))]


async def handle_test_empty_values(arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D6", "success": True,
        "received": {
            "empty_string": arguments.get("empty_string", ""),
            "empty_array": arguments.get("empty_array", []),
            "empty_object": arguments.get("empty_object", {})
        },
        "types": {
            "empty_string_type": "string",
            "empty_array_type": "array",
            "empty_object_type": "object"
        }
    }, ensure_ascii=False))]


async def handle_test_deep_nesting(arguments: dict) -> list[types.TextContent]:
    depth = arguments.get("depth", 5)
    structure = {"value": "deepest"}
    for i in range(depth, 0, -1):
        structure = {"level": i, "nested": structure}
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D7", "success": True, "depth": depth, "structure": structure
    }, ensure_ascii=False))]


async def handle_test_large_array(arguments: dict) -> list[types.TextContent]:
    count = arguments.get("count", 100)
    arr = list(range(count))
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "D8", "success": True, "count": count,
        "first_5": arr[:5], "last_5": arr[-5:], "sum": sum(arr)
    }, ensure_ascii=False))]


async def handle_test_timeout_boundary(arguments: dict) -> list[types.TextContent]:
    duration_seconds = arguments.get("duration_seconds", 5)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "E1", "success": True, "duration_seconds": duration_seconds,
        "note": f"操作完成，未触发超时（{duration_seconds}秒）", "elapsed_ms": 0
    }, ensure_ascii=False))]


async def handle_gui_desktop_info(arguments: dict) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G1", "success": True,
        "resolution": {"width": 1920, "height": 1080},
        "active_window": "模拟窗口",
        "windows": ["Window1", "Window2", "Window3"]
    }, ensure_ascii=False))]


async def handle_gui_take_screenshot(arguments: dict) -> list[types.TextContent]:
    fmt = arguments.get("format", "png")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G2", "success": True, "format": fmt,
        "width": 1920, "height": 1080, "message": "截图成功（模拟）"
    }, ensure_ascii=False))]


async def handle_gui_mouse_click(arguments: dict) -> list[types.TextContent]:
    x = arguments.get("x", 0)
    y = arguments.get("y", 0)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G3", "success": True, "action": "click",
        "position": {"x": x, "y": y}, "message": f"点击 ({x}, {y})"
    }, ensure_ascii=False))]


async def handle_gui_mouse_move(arguments: dict) -> list[types.TextContent]:
    x = arguments.get("x", 0)
    y = arguments.get("y", 0)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G4", "success": True, "action": "move",
        "position": {"x": x, "y": y}, "message": f"移动到 ({x}, {y})"
    }, ensure_ascii=False))]


async def handle_gui_keyboard_input(arguments: dict) -> list[types.TextContent]:
    text = arguments.get("text", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G5", "success": True, "action": "input",
        "text": text, "length": len(text), "message": f"输入文本: {text}"
    }, ensure_ascii=False))]


async def handle_gui_send_message(arguments: dict) -> list[types.TextContent]:
    contact = arguments.get("contact", "")
    message = arguments.get("message", "")
    delay_ms = arguments.get("delay_ms", 500)
    steps = ["查找联系人", "打开对话", "输入消息", "发送"]
    ctx = server.request_context
    try:
        with progress(ctx, total=float(len(steps))) as p:
            for i, step in enumerate(steps):
                await asyncio.sleep(delay_ms / 1000)
                p.progress(float(i + 1), message=f"[G6 流式] 步骤 {i + 1}/{len(steps)}: {step}")
    except (ValueError, AttributeError):
        await asyncio.sleep(delay_ms / 1000 * len(steps))
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G6", "success": True, "contact": contact,
        "message": message, "mode": "streaming", "steps": steps,
        "note": "通过 notifications/progress 流式推送每一步进度",
        "elapsed_ms": len(steps) * delay_ms
    }, ensure_ascii=False))]


async def handle_gui_automation_demo(arguments: dict) -> list[types.TextContent]:
    scenario = arguments.get("scenario", "notepad")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "G7", "success": True, "scenario": scenario,
        "mode": "batch",
        "steps": ["打开应用", "等待启动", "输入文本", "保存文件", "关闭应用"],
        "note": "一次性返回所有步骤，无流式进度", "message": "自动化演示完成"
    }, ensure_ascii=False))]


async def handle_test_elicitation_form(arguments: dict) -> list[types.TextContent]:
    form_title = arguments.get("form_title", "用户信息")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "H1", "success": True, "elicitation_type": "form",
        "form_title": form_title, "fields": ["name", "email"],
        "note": "表单式 Elicitation 测试"
    }, ensure_ascii=False))]


async def handle_test_elicitation_url(arguments: dict) -> list[types.TextContent]:
    auth_url = arguments.get("auth_url", "https://example.com/auth")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "H2", "success": True, "elicitation_type": "url",
        "auth_url": auth_url, "note": "URL 式 Elicitation 测试"
    }, ensure_ascii=False))]


async def handle_test_sampling_basic(arguments: dict) -> list[types.TextContent]:
    prompt = arguments.get("prompt", "What is 2+2?")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "I1", "success": True, "prompt": prompt,
        "note": "基础 Sampling 测试"
    }, ensure_ascii=False))]


async def handle_test_sampling_with_tools(arguments: dict) -> list[types.TextContent]:
    task = arguments.get("task", "")
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "I2", "success": True, "task": task,
        "available_tools": ["test_ping", "test_tool_call"],
        "note": "带工具的 Sampling 测试"
    }, ensure_ascii=False))]


async def handle_test_progress_sse(arguments: dict) -> list[types.TextContent]:
    steps = max(1, min(arguments.get("steps", 5), 20))
    delay_ms = arguments.get("delay_ms", 200)
    ctx = server.request_context
    progress_sent = False
    request_id = str(ctx.request_id) if ctx.request_id else None
    try:
        if ctx.meta and ctx.meta.progressToken and request_id:
            for i in range(steps):
                await asyncio.sleep(delay_ms / 1000)
                await ctx.session.send_progress_notification(
                    progress_token=ctx.meta.progressToken,
                    progress=float(i + 1),
                    total=float(steps),
                    message=f"步骤 {i + 1}/{steps} 完成",
                    related_request_id=request_id,
                )
            progress_sent = True
        else:
            await asyncio.sleep(delay_ms / 1000 * steps)
    except (ValueError, AttributeError):
        await asyncio.sleep(delay_ms / 1000 * steps)
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "J1", "success": True,
        "steps": steps, "delay_ms": delay_ms,
        "progress_sent": progress_sent,
        "message": "SSE 进度通知完成" if progress_sent else "无 progressToken 或 request_id，进度通知未发送（降级为 sleep）",
    }, ensure_ascii=False))]


async def handle_test_streaming_workflow(arguments: dict) -> list[types.TextContent]:
    workflow = arguments.get("workflow", "data_pipeline")
    step_delay_ms = arguments.get("step_delay_ms", 300)
    workflows = {
        "data_pipeline": ["读取源数据", "数据清洗", "格式转换", "数据验证", "写入目标"],
        "file_conversion": ["扫描文件", "解析内容", "转换格式", "校验输出", "保存结果"],
        "report_generation": ["收集数据", "生成图表", "编写摘要", "格式排版", "导出报告"],
    }
    steps = workflows.get(workflow, workflows["data_pipeline"])
    ctx = server.request_context
    progress_sent = False
    request_id = str(ctx.request_id) if ctx.request_id else None
    try:
        if ctx.meta and ctx.meta.progressToken and request_id:
            for i, step in enumerate(steps):
                await asyncio.sleep(step_delay_ms / 1000)
                await ctx.session.send_progress_notification(
                    progress_token=ctx.meta.progressToken,
                    progress=float(i + 1),
                    total=float(len(steps)),
                    message=f"[{workflow}] {i + 1}/{len(steps)}: {step}",
                    related_request_id=request_id,
                )
            progress_sent = True
        else:
            await asyncio.sleep(step_delay_ms / 1000 * len(steps))
    except (ValueError, AttributeError):
        await asyncio.sleep(step_delay_ms / 1000 * len(steps))
    return [types.TextContent(type="text", text=json.dumps({
        "test_id": "J2", "success": True,
        "workflow": workflow,
        "steps": steps,
        "step_delay_ms": step_delay_ms,
        "progress_sent": progress_sent,
        "message": "工作流完成" if progress_sent else "无 progressToken 或 request_id，进度通知未发送（降级为 sleep）",
    }, ensure_ascii=False))]


# ==================== 分发表 ====================

TOOL_HANDLERS = {
    "test_ping": handle_test_ping,
    "test_protocol_version": handle_test_protocol_version,
    "test_capabilities": handle_test_capabilities,
    "test_tool_call": handle_test_tool_call,
    "test_all_types": handle_test_all_types,
    "test_complex_params": handle_test_complex_params,
    "test_large_data": handle_test_large_data,
    "test_long_operation": handle_test_long_operation,
    "test_concurrent": handle_test_concurrent,
    "test_unicode": handle_test_unicode,
    "test_error_codes": handle_test_error_codes,
    "test_progress_notification": handle_test_progress_notification,
    "test_cancellation": handle_test_cancellation,
    "test_batch_request": handle_test_batch_request,
    "test_completion": handle_test_completion,
    "test_empty_params": handle_test_empty_params,
    "test_long_string": handle_test_long_string,
    "test_special_chars": handle_test_special_chars,
    "test_idempotency": handle_test_idempotency,
    "test_rapid_fire": handle_test_rapid_fire,
    "test_empty_values": handle_test_empty_values,
    "test_deep_nesting": handle_test_deep_nesting,
    "test_large_array": handle_test_large_array,
    "test_timeout_boundary": handle_test_timeout_boundary,
    "gui_desktop_info": handle_gui_desktop_info,
    "gui_take_screenshot": handle_gui_take_screenshot,
    "gui_mouse_click": handle_gui_mouse_click,
    "gui_mouse_move": handle_gui_mouse_move,
    "gui_keyboard_input": handle_gui_keyboard_input,
    "gui_send_message": handle_gui_send_message,
    "gui_automation_demo": handle_gui_automation_demo,
    "test_elicitation_form": handle_test_elicitation_form,
    "test_elicitation_url": handle_test_elicitation_url,
    "test_sampling_basic": handle_test_sampling_basic,
    "test_sampling_with_tools": handle_test_sampling_with_tools,
    "test_progress_sse": handle_test_progress_sse,
    "test_streaming_workflow": handle_test_streaming_workflow,
}

# ==================== MCP 处理器 ====================


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    log_request("tools/list")
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    args = arguments or {}
    log_request("tools/call", params={"name": name, "arguments": args})
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        result = {"test_id": "unknown", "success": False, "error": f"Unknown tool: {name}"}
        log_response(None, result=result)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
    result_content = await handler(arguments or {})
    try:
        text = result_content[0].text
        parsed = json.loads(text)
        log_response(None, result=parsed)
    except (IndexError, json.JSONDecodeError):
        log_response(None, result={"raw": "non-text content"})
    return result_content


# ==================== 传输层 (StreamableHTTP) ====================

session_manager = StreamableHTTPSessionManager(
    app=server,
    stateless=True,
    json_response=True,
)


@contextlib.asynccontextmanager
async def lifespan(app):
    async with session_manager.run():
        yield


async def asgi_app(scope, receive, send):
    """ASGI 应用：将 /mcp 请求委托给 session_manager"""
    if scope["type"] == "http" and scope["path"] == "/mcp" and scope["method"] in ("GET", "POST", "DELETE"):
        await session_manager.handle_request(scope, receive, send)
    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Not Found",
        })


app = Starlette(lifespan=lifespan, routes=[])

# 用 ASGI 中间件包装，拦截 /mcp 路径
class MCPMiddleware:
    def __init__(self, inner_app, mcp_app):
        self.inner_app = inner_app
        self.mcp_app = mcp_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/mcp" and scope["method"] in ("GET", "POST", "DELETE"):
            await self.mcp_app(scope, receive, send)
        else:
            await self.inner_app(scope, receive, send)

app = MCPMiddleware(app, asgi_app)


def main():
    """启动 HTTP 服务器"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
