#!/usr/bin/env python3
"""简化版测试脚本 - 快速诊断"""

import json
import subprocess
import sys
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def call_tool(tool_name: str, args: dict = None, timeout: int = 10) -> dict:
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args or {}}
    }
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=timeout)
        data = resp.json()
        if "error" in data:
            return {"ok": False, "error": data["error"]}
        result = data.get("result", {})
        if result.get("isError"):
            return {"ok": False, "error": "Tool error"}
        return {"ok": True}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "TIMEOUT"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:50]}


def main():
    print("MCP HTTP SDK 快速测试")
    print("=" * 50)

    # 启动服务器
    script_dir = Path(__file__).parent
    server_proc = subprocess.Popen(
        [sys.executable, str(script_dir / "src" / "mcp_http_sdk" / "server.py")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # 等待启动
    for _ in range(20):
        try:
            r = requests.post(BASE_URL, headers=HEADERS,
                json={"jsonrpc": "2.0", "id": 0, "method": "initialize",
                      "params": {"protocolVersion": "2025-11-05", "capabilities": {},
                                 "clientInfo": {"name": "t", "version": "1"}}},
                timeout=1)
            if r.status_code == 200:
                break
        except:
            time.sleep(0.5)
    else:
        print("服务器启动失败")
        return 1

    print("服务器已启动\n")

    # 测试所有工具
    tools = [
        # A类
        ("test_ping", {"echo": "hi"}),
        ("test_protocol_version", {}),
        ("test_capabilities", {}),
        ("test_tool_call", {"input_value": "x"}),
        ("test_all_types", {"string_value": "s"}),
        # B类
        ("test_complex_params", {"nested": {}}),
        ("test_large_data", {"size_kb": 1}),
        ("test_long_operation", {"duration_seconds": 1}),
        ("test_concurrent", {"request_id": "1"}),
        ("test_unicode", {"text": "你好"}),
        ("test_error_codes", {"error_type": "invalid_params"}),
        # C类
        ("test_progress_notification", {"steps": 2}),
        ("test_cancellation", {"duration_seconds": 1}),
        ("test_batch_request", {"operations": [{"operation": "add", "value": 1}]}),
        ("test_completion", {"partial_value": "t"}),
        # D类
        ("test_empty_params", {}),
        ("test_long_string", {"length": 100}),
        ("test_special_chars", {}),
        ("test_idempotency", {"operation_id": "1"}),
        ("test_rapid_fire", {"count": 3}),
        ("test_empty_values", {}),
        ("test_deep_nesting", {"depth": 3}),
        ("test_large_array", {"count": 10}),
        # E类
        ("test_timeout_boundary", {"duration_seconds": 1}),
        # G类
        ("gui_desktop_info", {}),
        ("gui_take_screenshot", {"format": "png"}),
        ("gui_mouse_click", {"x": 1, "y": 1}),
        ("gui_mouse_move", {"x": 1, "y": 1}),
        ("gui_keyboard_input", {"text": "a"}),
        ("gui_send_message", {"contact": "A", "message": "B", "delay_ms": 10}),
        ("gui_automation_demo", {}),
        # H类
        ("test_elicitation_form", {}),
        ("test_elicitation_url", {}),
        # I类
        ("test_sampling_basic", {}),
        ("test_sampling_with_tools", {}),
    ]

    passed = failed = 0
    for name, args in tools:
        start = time.time()
        r = call_tool(name, args)
        elapsed = time.time() - start

        if r["ok"]:
            passed += 1
            print(f"[PASS] {name} ({elapsed:.2f}s)")
        else:
            failed += 1
            print(f"[FAIL] {name} - {r['error']} ({elapsed:.2f}s)")

    print(f"\n结果: {passed}/{len(tools)} 通过, {failed} 失败")

    server_proc.terminate()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
