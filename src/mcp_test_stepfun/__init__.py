"""
MCP 工具测试服务器
用于测试阶跃桌面助手对 MCP 工具的理解能力
"""

import json
import sys

# ==================== 测试工具定义 ====================

TOOLS = [
    # ---------- 测试1: 工具选择歧义 ----------
    {
        "name": "capture_screen",
        "description": "Capture the screen of the device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["jpg", "png"], "default": "jpg"}
            }
        }
    },
    {
        "name": "take_screenshot",
        "description": "Take a screenshot from the device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["jpg", "png"], "default": "jpg"}
            }
        }
    },
    {
        "name": "get_screen_image",
        "description": "Get the current screen image from the device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["jpg", "png"], "default": "jpg"}
            }
        }
    },

    # ---------- 测试2: outputSchema ----------
    {
        "name": "get_device_info",
        "description": "Get device information including name, battery, and screen size.",
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "device_name": {"type": "string"},
                "battery_level": {"type": "integer"},
                "screen_width": {"type": "integer"},
                "screen_height": {"type": "integer"}
            },
            "required": ["success"]
        }
    },

    # ---------- 测试3: 参数默认值 ----------
    {
        "name": "connect_device",
        "description": "Connect to a device. Auto-detects if no device_id provided.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "Device ID (optional, auto-detect if not provided)",
                    "default": "auto"
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "usb", "wireless"],
                    "default": "auto"
                }
            }
        }
    },

    # ---------- 测试4: 错误自修正 ----------
    {
        "name": "validate_date",
        "description": "Validate a date string. Must be in YYYY-MM-DD format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date string in YYYY-MM-DD format"
                }
            },
            "required": ["date"]
        }
    },

    # ---------- 测试5: 推送类工具 ----------
    {
        "name": "push_server",
        "description": "Deploy scrcpy server for wireless control. Requires USB first. Auto-connects by default.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video": {"type": "boolean", "default": False, "description": "Enable video"},
                "audio": {"type": "boolean", "default": False, "description": "Enable audio"},
                "persistent": {"type": "boolean", "default": True, "description": "Keep server running"},
                "auto_connect": {"type": "boolean", "default": True, "description": "Connect immediately"}
            }
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "device_ip": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["success"]
        }
    },
    {
        "name": "push_server_onetime",
        "description": "[DEPRECATED] Use push_server instead.",
        "inputSchema": {"type": "object", "properties": {"video": {"type": "boolean", "default": False}}}
    },
    {
        "name": "push_server_persistent",
        "description": "[DEPRECATED] Use push_server instead.",
        "inputSchema": {"type": "object", "properties": {"video": {"type": "boolean", "default": False}}}
    },
]


# ==================== 工具实现 ====================

def call_tool(tool_name: str, arguments: dict) -> dict:
    """执行工具调用"""

    # 截图类
    if tool_name in ["capture_screen", "take_screenshot", "get_screen_image"]:
        return {
            "success": True,
            "tool_used": tool_name,
            "message": f"Screenshot captured in {arguments.get('format', 'jpg')} format"
        }

    # 设备信息
    if tool_name == "get_device_info":
        return {
            "success": True,
            "device_name": "Test Device",
            "battery_level": 85,
            "screen_width": 1080,
            "screen_height": 2400
        }

    # 连接设备
    if tool_name == "connect_device":
        device_id = arguments.get("device_id", "auto")
        if device_id == "auto":
            device_id = "ABC12345"
        return {
            "success": True,
            "device_id": device_id,
            "mode": arguments.get("mode", "auto"),
            "message": f"Connected to {device_id}"
        }

    # 日期验证
    if tool_name == "validate_date":
        import re
        date_str = arguments.get("date", "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return {
                "success": False,
                "error": f"Invalid date format: '{date_str}'",
                "hint": "Date must be in YYYY-MM-DD format, e.g., 2026-03-08"
            }
        return {"success": True, "date": date_str, "message": f"Date {date_str} is valid"}

    # 推送服务器
    if tool_name == "push_server":
        return {
            "success": True,
            "device_ip": "192.168.1.100",
            "message": "Server deployed and connected" if arguments.get("auto_connect", True) else "Server deployed",
            "video_enabled": arguments.get("video", False),
            "audio_enabled": arguments.get("audio", False)
        }

    if tool_name in ["push_server_onetime", "push_server_persistent"]:
        return {
            "success": True,
            "tool_used": tool_name,
            "message": "[DEPRECATED] Consider using push_server instead"
        }

    return {"success": False, "error": f"Unknown tool: {tool_name}"}


# ==================== MCP 协议处理 ====================

def send_response(response: dict):
    print(json.dumps(response), flush=True)


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    # 初始化
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "mcp-test-stepfun", "version": "0.1.0"}
            }
        }

    # 列出工具
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}

    # 调用工具
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = call_tool(tool_name, arguments)
        is_error = not result.get("success", True)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                "isError": is_error
            }
        }

    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main():
    """主循环"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = handle_request(request)
            send_response(response)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    main()
