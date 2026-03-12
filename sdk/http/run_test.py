#!/usr/bin/env python3
"""
MCP HTTP SDK 完整测试脚本 (35个工具)

自动启动服务器并运行所有测试。
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ==================== 配置 ====================

BASE_URL = "http://127.0.0.1:8000/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
REQUEST_TIMEOUT = 10  # 缩短超时时间

# ==================== 全部 35 个测试用例 ====================

TEST_CASES = [
    # A 类 - 核心能力 (5个)
    ("test_ping", {"echo": "hello"}, "A"),
    ("test_protocol_version", {}, "A"),
    ("test_capabilities", {}, "A"),
    ("test_tool_call", {"input_value": "test123"}, "A"),
    ("test_all_types", {"string_value": "hello", "integer_value": 42}, "A"),

    # B 类 - 重要能力 (6个)
    ("test_complex_params", {"nested": {"a": 1}, "array": [1, 2, 3]}, "B"),
    ("test_large_data", {"size_kb": 1, "items": 5}, "B"),
    ("test_long_operation", {"duration_seconds": 1}, "B"),
    ("test_concurrent", {"request_id": "test-001"}, "B"),
    ("test_unicode", {"text": "你好世界"}, "B"),
    ("test_error_codes", {"error_type": "invalid_params"}, "B"),

    # C 类 - 高级能力 (4个)
    ("test_progress_notification", {"steps": 2}, "C"),
    ("test_cancellation", {"duration_seconds": 1}, "C"),
    ("test_batch_request", {"operations": [{"operation": "add", "value": 5}]}, "C"),
    ("test_completion", {"partial_value": "test"}, "C"),

    # D 类 - 边界条件 (8个)
    ("test_empty_params", {}, "D"),
    ("test_long_string", {"length": 1000}, "D"),
    ("test_special_chars", {"include_control": True}, "D"),
    ("test_idempotency", {"operation_id": "op-001"}, "D"),
    ("test_rapid_fire", {"count": 3}, "D"),
    ("test_empty_values", {}, "D"),
    ("test_deep_nesting", {"depth": 5}, "D"),
    ("test_large_array", {"count": 50}, "D"),

    # E 类 - 极端条件 (1个)
    ("test_timeout_boundary", {"duration_seconds": 1}, "E"),

    # G 类 - GUI Agent (7个)
    ("gui_desktop_info", {}, "G"),
    ("gui_take_screenshot", {"format": "png"}, "G"),
    ("gui_mouse_click", {"x": 100, "y": 200}, "G"),
    ("gui_mouse_move", {"x": 500, "y": 300}, "G"),
    ("gui_keyboard_input", {"text": "Hello"}, "G"),
    ("gui_send_message", {"contact": "Test", "message": "Hi", "delay_ms": 10}, "G"),
    ("gui_automation_demo", {"scenario": "notepad"}, "G"),

    # H 类 - Elicitation (2个)
    ("test_elicitation_form", {"form_title": "用户信息"}, "H"),
    ("test_elicitation_url", {"auth_url": "https://example.com"}, "H"),

    # I 类 - Sampling (2个)
    ("test_sampling_basic", {"prompt": "What is 2+2?"}, "I"),
    ("test_sampling_with_tools", {"task": "test"}, "I"),
]


def call_tool(tool_name: str, args: dict) -> dict:
    """调用工具"""
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args}
    }
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if "error" in data:
            return {"ok": False, "error": data["error"].get("message", str(data["error"]))}
        result = data.get("result", {})
        if result.get("isError"):
            return {"ok": False, "error": "Tool returned error"}
        return {"ok": True}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "TIMEOUT"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:50]}


def main():
    print("=" * 60)
    print("MCP HTTP SDK 完整测试 (35个工具)")
    print("=" * 60)

    # 1. 启动服务器
    print("\n[1] 启动服务器...")
    script_dir = Path(__file__).parent
    server_script = script_dir / "src" / "mcp_http_sdk" / "server.py"

    server_proc = subprocess.Popen(
        [sys.executable, str(server_script)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(script_dir)
    )

    # 等待服务器启动
    for _ in range(20):
        try:
            r = requests.post(BASE_URL, headers=HEADERS,
                json={"jsonrpc": "2.0", "id": 0, "method": "initialize",
                      "params": {"protocolVersion": "2025-11-05", "capabilities": {},
                                 "clientInfo": {"name": "test", "version": "1"}}},
                timeout=1)
            if r.status_code == 200:
                break
        except:
            time.sleep(0.5)
    else:
        print("  服务器启动失败!")
        server_proc.kill()
        return 1

    print("  服务器已启动")

    try:
        # 2. 运行测试
        print(f"\n[2] 运行 {len(TEST_CASES)} 个测试...\n")

        passed, failed = 0, 0
        results = []
        by_category = {}

        for name, args, cat in TEST_CASES:
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0}

            start = time.time()
            result = call_tool(name, args)
            elapsed = time.time() - start

            if result["ok"]:
                passed += 1
                by_category[cat]["passed"] += 1
                status = "\033[32mPASS\033[0m"
                results.append({"name": name, "cat": cat, "ok": True, "time": elapsed})
            else:
                failed += 1
                by_category[cat]["failed"] += 1
                status = "\033[31mFAIL\033[0m"
                results.append({"name": name, "cat": cat, "ok": False, "error": result["error"], "time": elapsed})

            print(f"  [{cat}] {name}: {status} ({elapsed:.2f}s)")

        # 3. 打印摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"总计: {len(TEST_CASES)} | 通过: {passed} | 失败: {failed}")
        print()
        print("按类别:")
        for cat in sorted(by_category.keys()):
            s = by_category[cat]
            total = s["passed"] + s["failed"]
            print(f"  [{cat}] {s['passed']}/{total}")

        # 4. 保存报告
        logs_dir = script_dir.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_file = logs_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {"total": len(TEST_CASES), "passed": passed, "failed": failed},
                "by_category": by_category,
                "results": results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n报告: {report_file}")
        return 0 if failed == 0 else 1

    finally:
        print("\n[3] 关闭服务器...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except:
            server_proc.kill()
        print("  完成")


if __name__ == "__main__":
    sys.exit(main())
