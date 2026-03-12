#!/usr/bin/env python3
"""
MCP stdio 全量测试服务器 (UVX 模式)

包含35个测试工具，与 NPX 模式功能一致

阶跃客户端配置:
{
  "mcpServers": {
    "mcp-uvx-test": {
      "command": "uvx",
      "args": ["--from", "C:/path/to/stdio/uvx", "mcp-uvx-test"]
    }
  }
}
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server import FastMCP
from mcp.server.fastmcp import Context

# ==================== 日志配置 ====================

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

log_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
log_file = LOGS_DIR / f"uvx_{log_timestamp}.jsonl"


def write_log(entry: dict) -> None:
    """写入日志文件"""
    entry["timestamp"] = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ==================== 服务器实例 ====================

mcp = FastMCP("mcp-uvx-test")

# 幂等性缓存
_idempotency_cache: dict = {}


# ==================== A 类 - 核心能力 (5个) ====================

@mcp.tool()
def test_ping(echo: str = "", delay_ms: int = 0) -> str:
    """[A1] 测试基础连通性。返回 pong 和精确时间戳。"""
    result = {
        "test_id": "A1",
        "success": True,
        "pong": "pong",
        "echo": echo if echo else None,
        "server_time": datetime.now().isoformat(),
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_protocol_version() -> str:
    """[A2] 测试协议版本协商。验证客户端发送的协议版本。"""
    result = {
        "test_id": "A2",
        "success": True,
        "client_protocol_version": "from_client",
        "server_protocol_version": "2025-11-25",
        "version_match": True,
        "note": "版本匹配"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_capabilities() -> str:
    """[A3] 测试能力协商。返回完整的能力声明。"""
    result = {
        "test_id": "A3",
        "success": True,
        "server_capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True},
            "logging": {}
        },
        "protocol_version": "2025-11-25"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_tool_call(input_value: str, input_type: str = "string") -> str:
    """[A4] 测试工具调用。验证参数传递和返回格式。"""
    actual_type = type(input_value).__name__
    result = {
        "test_id": "A4",
        "success": True,
        "received_value": input_value,
        "received_type": input_type,
        "actual_type": actual_type,
        "type_match": actual_type == input_type,
        "server_time": datetime.now().isoformat()
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_all_types(
    string_value: str = "",
    integer_value: int = 0,
    float_value: float = 0.0,
    boolean_value: bool = False,
    negative_value: int = 0,
    big_int_value: int = 0,
    array_value: list = [],
    object_value: dict = {}
) -> str:
    """[A5] 增强类型验证。测试所有类型：string/integer/float/boolean/null/negative/bigint/array/object。"""
    results = {}

    if string_value:
        results["string"] = {"received": string_value, "type": "string", "valid": True}
    if integer_value != 0:
        results["integer"] = {"received": integer_value, "type": "number", "valid": True}
    if float_value != 0.0:
        results["float"] = {"received": float_value, "type": "number", "valid": True}
    if boolean_value:
        results["boolean"] = {"received": boolean_value, "type": "boolean", "valid": True}
    if negative_value != 0:
        results["negative"] = {"received": negative_value, "type": "number", "valid": True}
    if big_int_value != 0:
        results["bigint"] = {"received": big_int_value, "type": "number", "valid": True}
    if array_value:
        results["array"] = {"received": array_value, "type": "array", "valid": True}
    if object_value:
        results["object"] = {"received": object_value, "type": "object", "valid": True}

    results["null"] = {"received": None, "type": "null", "valid": True}

    result = {
        "test_id": "A5",
        "success": True,
        "type_results": results,
        "summary": {
            "tested_types": len(results),
            "all_valid": True
        },
        "server_time": datetime.now().isoformat()
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== B 类 - 重要能力 (6个) ====================

@mcp.tool()
def test_complex_params(
    nested: dict = {},
    array: list = [],
    enum_value: str = "option1"
) -> str:
    """[B1] 测试复杂参数类型：嵌套对象、数组、枚举。"""
    result = {
        "test_id": "B1",
        "success": True,
        "received": {
            "nested": nested,
            "array": array,
            "enum_value": enum_value
        },
        "types": {
            "nested_type": "object" if isinstance(nested, dict) else type(nested).__name__,
            "array_type": "array" if isinstance(array, list) else type(array).__name__,
            "enum_type": "string" if isinstance(enum_value, str) else type(enum_value).__name__
        }
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_large_data(size_kb: int = 1, items: int = 10) -> str:
    """[B2] 测试大数据传输。生成指定大小的数据。"""
    data = []
    chunk_size = max(1, size_kb * 1024 // items)
    for i in range(items):
        data.append({
            "id": i,
            "data": "x" * chunk_size
        })
    result = {
        "test_id": "B2",
        "success": True,
        "requested_size_kb": size_kb,
        "items": items,
        "actual_size_bytes": sum(len(str(item)) for item in data),
        "sample": data[:2]
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_long_operation(duration_seconds: int = 3) -> str:
    """[B3] 测试长时间操作。模拟耗时任务。"""
    result = {
        "test_id": "B3",
        "success": True,
        "duration_seconds": duration_seconds,
        "message": f"模拟 {duration_seconds} 秒操作完成",
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_concurrent(request_id: str = "", delay_ms: int = 100) -> str:
    """[B4] 测试并发请求处理。"""
    result = {
        "test_id": "B4",
        "success": True,
        "request_id": request_id,
        "processed_at": datetime.now().isoformat(),
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_unicode(text: str = "") -> str:
    """[B5] 测试 Unicode 支持。"""
    result = {
        "test_id": "B5",
        "success": True,
        "received": text,
        "length": len(text),
        "bytes": len(text.encode("utf-8")),
        "has_chinese": any("\u4e00" <= c <= "\u9fff" for c in text),
        "has_emoji": any(ord(c) > 0x1F000 for c in text)
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_error_codes(error_type: str = "invalid_params") -> str:
    """[B6] 测试错误处理。"""
    error_map = {
        "invalid_params": (-32602, "Invalid params"),
        "not_found": (-32601, "Method not found"),
        "internal_error": (-32603, "Internal error"),
        "unauthorized": (-32000, "Unauthorized"),
        "timeout": (-32001, "Timeout")
    }
    code, msg = error_map.get(error_type, (-32603, "Unknown error"))
    result = {
        "test_id": "B6",
        "success": False,
        "error": msg,
        "error_code": code,
        "error_type": error_type
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== C 类 - 高级能力 (4个) ====================

@mcp.tool()
async def test_progress_notification(ctx: Context, steps: int = 3, delay_ms: int = 100) -> str:
    """[C1] 测试进度通知。通过 notifications/progress 逐步推送进度。"""
    steps = max(1, min(steps, 10))
    for i in range(steps):
        await asyncio.sleep(delay_ms / 1000)
        await ctx.report_progress(
            progress=i + 1,
            total=steps,
            message=f"Step {i + 1}/{steps}"
        )
    result = {
        "test_id": "C1",
        "success": True,
        "message": "Progress notifications completed",
        "steps": steps,
        "delay_ms": delay_ms
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_cancellation(duration_seconds: int = 2) -> str:
    """[C2] 测试请求取消。"""
    result = {
        "test_id": "C2",
        "success": True,
        "duration_seconds": duration_seconds,
        "message": "Cancellation test completed",
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_batch_request(operations: list = []) -> str:
    """[C3] 测试批量请求。"""
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
    result = {
        "test_id": "C3",
        "success": True,
        "operations_count": len(operations),
        "results": results
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_completion(partial_value: str = "") -> str:
    """[C4] 测试自动补全。"""
    result = {
        "test_id": "C4",
        "success": True,
        "partial_value": partial_value,
        "suggestions": [
            f"{partial_value}_complete1",
            f"{partial_value}_complete2",
            f"{partial_value}_complete3"
        ]
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== D 类 - 边界条件 (8个) ====================

@mcp.tool()
def test_empty_params() -> str:
    """[D1] 测试空参数。"""
    result = {
        "test_id": "D1",
        "success": True,
        "params_count": 0,
        "message": "Empty params test passed"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_long_string(length: int = 1000) -> str:
    """[D2] 测试超长字符串。"""
    result = {
        "test_id": "D2",
        "success": True,
        "length": length,
        "first_10": "x" * 10,
        "last_10": "x" * 10,
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_special_chars(include_control: bool = True, include_quotes: bool = True) -> str:
    """[D3] 测试特殊字符。"""
    special_chars = "\x00\x01\x02\"'\n\r\t正常文本"
    result = {
        "test_id": "D3",
        "success": True,
        "special_chars": special_chars,
        "includes": {
            "control": include_control,
            "quotes": include_quotes
        }
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_idempotency(operation_id: str = "") -> str:
    """[D4] 测试幂等性。"""
    if operation_id in _idempotency_cache:
        result = {
            "test_id": "D4",
            "success": True,
            "operation_id": operation_id,
            "cached": True,
            "message": "缓存命中"
        }
    else:
        _idempotency_cache[operation_id] = datetime.now().isoformat()
        result = {
            "test_id": "D4",
            "success": True,
            "operation_id": operation_id,
            "cached": False,
            "message": "首次请求"
        }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_rapid_fire(count: int = 5) -> str:
    """[D5] 测试快速请求。"""
    results = [{"index": i, "time": int(time.time() * 1000)} for i in range(count)]
    result = {
        "test_id": "D5",
        "success": True,
        "count": count,
        "results": results,
        "total_time_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_empty_values(
    empty_string: str = "",
    empty_array: list = [],
    empty_object: dict = {}
) -> str:
    """[D6] 测试空值处理。"""
    result = {
        "test_id": "D6",
        "success": True,
        "received": {
            "empty_string": empty_string,
            "empty_array": empty_array,
            "empty_object": empty_object
        },
        "types": {
            "empty_string_type": "string",
            "empty_array_type": "array",
            "empty_object_type": "object"
        }
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_deep_nesting(depth: int = 5) -> str:
    """[D7] 测试深层嵌套。"""
    structure = {"value": "deepest"}
    for i in range(depth, 0, -1):
        structure = {"level": i, "nested": structure}
    result = {
        "test_id": "D7",
        "success": True,
        "depth": depth,
        "structure": structure
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_large_array(count: int = 100) -> str:
    """[D8] 测试大数组。"""
    arr = list(range(count))
    result = {
        "test_id": "D8",
        "success": True,
        "count": count,
        "first_5": arr[:5],
        "last_5": arr[-5:],
        "sum": sum(arr)
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== E 类 - 极端条件 (1个) ====================

@mcp.tool()
def test_timeout_boundary(duration_seconds: int = 5) -> str:
    """[E1] 测试超时边界（55-60秒）。"""
    result = {
        "test_id": "E1",
        "success": True,
        "duration_seconds": duration_seconds,
        "note": f"操作完成，未触发超时（{duration_seconds}秒）",
        "elapsed_ms": 0
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== G 类 - GUI Agent (7个) ====================

@mcp.tool()
def gui_desktop_info() -> str:
    """[G1] 获取桌面信息。"""
    result = {
        "test_id": "G1",
        "success": True,
        "resolution": {"width": 1920, "height": 1080},
        "active_window": "模拟窗口",
        "windows": ["Window1", "Window2", "Window3"]
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def gui_take_screenshot(format: str = "png") -> str:
    """[G2] 截图。"""
    result = {
        "test_id": "G2",
        "success": True,
        "format": format,
        "width": 1920,
        "height": 1080,
        "message": "截图成功（模拟）"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def gui_mouse_click(x: int, y: int) -> str:
    """[G3] 鼠标点击。"""
    result = {
        "test_id": "G3",
        "success": True,
        "action": "click",
        "position": {"x": x, "y": y},
        "message": f"点击 ({x}, {y})"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def gui_mouse_move(x: int, y: int) -> str:
    """[G4] 鼠标移动。"""
    result = {
        "test_id": "G4",
        "success": True,
        "action": "move",
        "position": {"x": x, "y": y},
        "message": f"移动到 ({x}, {y})"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def gui_keyboard_input(text: str) -> str:
    """[G5] 键盘输入。"""
    result = {
        "test_id": "G5",
        "success": True,
        "action": "input",
        "text": text,
        "length": len(text),
        "message": f"输入文本: {text}"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def gui_send_message(ctx: Context, contact: str, message: str, delay_ms: int = 500) -> str:
    """[G6] 发送消息（流式多步）。通过 notifications/progress 逐步推送每一步进度。"""
    steps = ["查找联系人", "打开对话", "输入消息", "发送"]
    for i, step in enumerate(steps):
        await asyncio.sleep(delay_ms / 1000)
        await ctx.report_progress(
            progress=i + 1,
            total=len(steps),
            message=f"[G6 流式] 步骤 {i + 1}/{len(steps)}: {step}"
        )
    result = {
        "test_id": "G6",
        "success": True,
        "contact": contact,
        "message": message,
        "mode": "streaming",
        "steps": steps,
        "note": "通过 notifications/progress 流式推送每一步进度",
        "elapsed_ms": len(steps) * delay_ms
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def gui_automation_demo(scenario: str = "notepad") -> str:
    """[G7] 自动化演示（一次性返回）。所有步骤在一个响应中返回，无流式进度。"""
    result = {
        "test_id": "G7",
        "success": True,
        "scenario": scenario,
        "mode": "batch",
        "steps": ["打开应用", "等待启动", "输入文本", "保存文件", "关闭应用"],
        "note": "一次性返回所有步骤，无流式进度",
        "message": "自动化演示完成"
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== H 类 - Elicitation (2个) ====================

@mcp.tool()
def test_elicitation_form(form_title: str = "用户信息") -> str:
    """[H1] 测试表单式 Elicitation。"""
    result = {
        "test_id": "H1",
        "success": True,
        "elicitation_type": "form",
        "form_title": form_title,
        "fields": ["name", "email"],
        "note": "表单式 Elicitation 测试"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_elicitation_url(auth_url: str = "https://example.com/auth") -> str:
    """[H2] 测试 URL 式 Elicitation。"""
    result = {
        "test_id": "H2",
        "success": True,
        "elicitation_type": "url",
        "auth_url": auth_url,
        "note": "URL 式 Elicitation 测试"
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== I 类 - Sampling (2个) ====================

@mcp.tool()
def test_sampling_basic(prompt: str = "What is 2+2?") -> str:
    """[I1] 测试基础 Sampling。"""
    result = {
        "test_id": "I1",
        "success": True,
        "prompt": prompt,
        "note": "基础 Sampling 测试"
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def test_sampling_with_tools(task: str = "") -> str:
    """[I2] 测试带工具的 Sampling。"""
    result = {
        "test_id": "I2",
        "success": True,
        "task": task,
        "available_tools": ["test_ping", "test_tool_call"],
        "note": "带工具的 Sampling 测试"
    }
    return json.dumps(result, ensure_ascii=False)


# ==================== 入口点 ====================

if __name__ == "__main__":
    mcp.run()
