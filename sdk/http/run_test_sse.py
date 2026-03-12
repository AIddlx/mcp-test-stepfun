#!/usr/bin/env python3
"""
MCP HTTP SDK SSE 模式测试脚本 (37个工具)

SSE 模式下响应为 text/event-stream，支持中间 progress notification。
progress 工具（C1、G6、J1、J2）会在请求 _meta 中携带 progressToken。
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
REQUEST_TIMEOUT = 15
SSE_HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

# 需要发送 progressToken 的工具
PROGRESS_TOOLS = {"test_progress_notification", "gui_send_message",
                  "test_progress_sse", "test_streaming_workflow"}

# ==================== 全部 37 个测试用例 ====================

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
    ("test_progress_notification", {"steps": 2, "delay_ms": 100}, "C"),
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

    # J 类 - SSE 流式进度通知 (2个)
    ("test_progress_sse", {"steps": 5, "delay_ms": 100}, "J"),
    ("test_streaming_workflow", {"workflow": "data_pipeline", "step_delay_ms": 100}, "J"),
]


def parse_sse_response(response) -> dict:
    """解析 SSE 响应，返回 {response: JSON, progress_events: list}"""
    progress_events = []
    final_response = None

    current_data = ""
    for line in response.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line.startswith("data:"):
            current_data = line[5:].strip()
        elif line == "" and current_data:
            # 空行表示一个 SSE 事件结束
            try:
                msg = json.loads(current_data)
                method = msg.get("method", "")
                if method == "notifications/progress":
                    params = msg.get("params", {})
                    progress_events.append({
                        "progress": params.get("progress"),
                        "total": params.get("total"),
                        "message": params.get("message"),
                    })
                elif "result" in msg or "error" in msg:
                    final_response = msg
            except json.JSONDecodeError:
                pass
            current_data = ""

    return {
        "response": final_response,
        "progress_events": progress_events,
    }


def call_tool(tool_name: str, args: dict) -> dict:
    """调用工具（SSE 模式），解析 SSE 响应"""
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args}
    }
    # progress 工具携带 progressToken
    if tool_name in PROGRESS_TOOLS:
        payload["params"]["_meta"] = {"progressToken": f"test-token-{tool_name}"}

    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload,
                             timeout=REQUEST_TIMEOUT, stream=True)

        # 检查是否为 SSE 响应
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            sse = parse_sse_response(resp)
            final = sse["response"]
            progress_events = sse["progress_events"]
        else:
            # 回退：按 JSON 解析
            final = resp.json()
            progress_events = []

        if final and "error" in final:
            return {"ok": False, "error": final["error"].get("message", str(final["error"])),
                    "progress_events": progress_events}
        if final and final.get("result", {}).get("isError"):
            return {"ok": False, "error": "Tool returned error",
                    "progress_events": progress_events}
        return {"ok": True, "progress_events": progress_events}

    except requests.exceptions.Timeout:
        return {"ok": False, "error": "TIMEOUT"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


def main():
    print("=" * 60)
    print("MCP HTTP SDK SSE 模式测试 (37个工具)")
    print("=" * 60)

    # 1. 启动服务器
    print("\n[1] 启动服务器...")
    script_dir = Path(__file__).parent
    server_script = script_dir / "src" / "mcp_http_sdk" / "server.py"

    server_proc = subprocess.Popen(
        [sys.executable, "-B", str(server_script)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(script_dir)
    )

    # 等待服务器启动
    for _ in range(20):
        try:
            r = requests.post(BASE_URL, headers=SSE_HEADERS,
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

    # 检查响应模式
    test_resp = requests.post(BASE_URL, headers={"Content-Type": "application/json"},
        json={"jsonrpc": "2.0", "id": 0, "method": "tools/call",
              "params": {"name": "test_ping", "arguments": {}}},
        timeout=5, stream=True)
    ct = test_resp.headers.get("Content-Type", "unknown")
    print(f"  服务器已启动 (响应模式: {ct})")

    try:
        # 2. 运行测试
        print(f"\n[2] 运行 {len(TEST_CASES)} 个测试...\n")

        passed, failed = 0, 0
        results = []
        by_category = {}

        for name, args, cat in TEST_CASES:
            if cat not in by_category:
                by_category[cat] = {"passed": 0, "failed": 0, "progress": 0}

            start = time.time()
            result = call_tool(name, args)
            elapsed = time.time() - start
            progress_events = result.get("progress_events", [])

            if result["ok"]:
                passed += 1
                by_category[cat]["passed"] += 1
                status = "\033[32mPASS\033[0m"
            else:
                failed += 1
                by_category[cat]["failed"] += 1
                status = "\033[31mFAIL\033[0m"

            # 显示 progress 事件
            progress_info = ""
            if progress_events:
                by_category[cat]["progress"] += len(progress_events)
                progress_info = f" \033[36m[{len(progress_events)} progress events]\033[0m"
            elif name in PROGRESS_TOOLS:
                progress_info = " \033[33m[0 progress events!]\033[0m"

            print(f"  [{cat}] {name}: {status} ({elapsed:.3f}s){progress_info}")

            entry = {"name": name, "cat": cat, "ok": result["ok"], "time": elapsed}
            if progress_events:
                entry["progress_count"] = len(progress_events)
                entry["progress_events"] = progress_events
            if not result["ok"]:
                entry["error"] = result.get("error", "")
            results.append(entry)

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
            line = f"  [{cat}] {s['passed']}/{total}"
            if s["progress"]:
                line += f" | {s['progress']} progress events"
            print(line)

        # 4. Progress 验证详情
        progress_tools = [(n, a) for n, a, c in TEST_CASES if n in PROGRESS_TOOLS]
        if progress_tools:
            print("\n" + "-" * 60)
            print("Progress Notification 验证")
            print("-" * 60)
            for r in results:
                if r["name"] in PROGRESS_TOOLS:
                    ok_mark = "\033[32mOK\033[0m" if r.get("progress_count", 0) > 0 else "\033[31mMISSING\033[0m"
                    print(f"  {r['name']}: {ok_mark} ({r.get('progress_count', 0)} events)")
                    if r.get("progress_events"):
                        for pe in r["progress_events"]:
                            msg = pe.get("message", "")
                            print(f"    -> progress={pe.get('progress')}/{pe.get('total')} msg={msg.encode('ascii', 'replace').decode()}")


        # 5. 保存报告
        logs_dir = script_dir.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        report_file = logs_dir / f"test_report_sse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "mode": "SSE (json_response=False)",
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
