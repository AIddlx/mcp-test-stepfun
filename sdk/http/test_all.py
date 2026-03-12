#!/usr/bin/env python3
"""
MCP HTTP SDK 批量测试脚本

测试所有 35 个工具的连通性和基本功能。
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================

BASE_URL = "http://127.0.0.1:8000/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ==================== 测试用例 ====================

TEST_CASES = [
    # A 类 - 核心能力 (5个)
    {
        "name": "test_ping",
        "category": "A",
        "description": "基础连通性",
        "args": {"echo": "hello", "delay_ms": 0}
    },
    {
        "name": "test_protocol_version",
        "category": "A",
        "description": "协议版本协商"
    },
    {
        "name": "test_capabilities",
        "category": "A",
        "description": "能力协商"
    },
    {
        "name": "test_tool_call",
        "category": "A",
        "description": "工具调用",
        "args": {"input_value": "test123", "input_type": "string"}
    },
    {
        "name": "test_all_types",
        "category": "A",
        "description": "类型验证",
        "args": {
            "string_value": "hello",
            "integer_value": 42,
            "float_value": 3.14,
            "boolean_value": True,
            "negative_value": -10,
            "big_int_value": 9007199254740993
        }
    },

    # B 类 - 重要能力 (6个)
    {
        "name": "test_complex_params",
        "category": "B",
        "description": "复杂参数",
        "args": {
            "nested": {"level1": {"level2": "value"}},
            "array": [1, 2, 3],
            "enum_value": "option2"
        }
    },
    {
        "name": "test_large_data",
        "category": "B",
        "description": "大数据传输",
        "args": {"size_kb": 1, "items": 5}
    },
    {
        "name": "test_long_operation",
        "category": "B",
        "description": "长时间操作",
        "args": {"duration_seconds": 1}
    },
    {
        "name": "test_concurrent",
        "category": "B",
        "description": "并发请求",
        "args": {"request_id": "test-001", "delay_ms": 50}
    },
    {
        "name": "test_unicode",
        "category": "B",
        "description": "Unicode 支持",
        "args": {"text": "你好世界 🌍 Hello"}
    },
    {
        "name": "test_error_codes",
        "category": "B",
        "description": "错误处理",
        "args": {"error_type": "invalid_params"}
    },

    # C 类 - 高级能力 (4个)
    {
        "name": "test_progress_notification",
        "category": "C",
        "description": "进度通知",
        "args": {"steps": 2, "delay_ms": 50}
    },
    {
        "name": "test_cancellation",
        "category": "C",
        "description": "请求取消",
        "args": {"duration_seconds": 1}
    },
    {
        "name": "test_batch_request",
        "category": "C",
        "description": "批量请求",
        "args": {
            "operations": [
                {"operation": "add", "value": 5},
                {"operation": "multiply", "value": 3}
            ]
        }
    },
    {
        "name": "test_completion",
        "category": "C",
        "description": "自动补全",
        "args": {"partial_value": "test"}
    },

    # D 类 - 边界条件 (8个)
    {
        "name": "test_empty_params",
        "category": "D",
        "description": "空参数"
    },
    {
        "name": "test_long_string",
        "category": "D",
        "description": "超长字符串",
        "args": {"length": 1000}
    },
    {
        "name": "test_special_chars",
        "category": "D",
        "description": "特殊字符",
        "args": {"include_control": True, "include_quotes": True}
    },
    {
        "name": "test_idempotency",
        "category": "D",
        "description": "幂等性",
        "args": {"operation_id": "test-op-001"}
    },
    {
        "name": "test_rapid_fire",
        "category": "D",
        "description": "快速请求",
        "args": {"count": 3}
    },
    {
        "name": "test_empty_values",
        "category": "D",
        "description": "空值处理",
        "args": {"empty_string": "", "empty_array": [], "empty_object": {}}
    },
    {
        "name": "test_deep_nesting",
        "category": "D",
        "description": "深层嵌套",
        "args": {"depth": 5}
    },
    {
        "name": "test_large_array",
        "category": "D",
        "description": "大数组",
        "args": {"count": 50}
    },

    # E 类 - 极端条件 (1个)
    {
        "name": "test_timeout_boundary",
        "category": "E",
        "description": "超时边界",
        "args": {"duration_seconds": 1}
    },

    # G 类 - GUI Agent (7个)
    {
        "name": "gui_desktop_info",
        "category": "G",
        "description": "桌面信息"
    },
    {
        "name": "gui_take_screenshot",
        "category": "G",
        "description": "截图",
        "args": {"format": "png"}
    },
    {
        "name": "gui_mouse_click",
        "category": "G",
        "description": "鼠标点击",
        "args": {"x": 100, "y": 200}
    },
    {
        "name": "gui_mouse_move",
        "category": "G",
        "description": "鼠标移动",
        "args": {"x": 500, "y": 300}
    },
    {
        "name": "gui_keyboard_input",
        "category": "G",
        "description": "键盘输入",
        "args": {"text": "Hello World"}
    },
    {
        "name": "gui_send_message",
        "category": "G",
        "description": "发送消息",
        "args": {"contact": "Test", "message": "Hi", "delay_ms": 50}
    },
    {
        "name": "gui_automation_demo",
        "category": "G",
        "description": "自动化演示",
        "args": {"scenario": "notepad"}
    },

    # H 类 - Elicitation (2个)
    {
        "name": "test_elicitation_form",
        "category": "H",
        "description": "表单式 Elicitation",
        "args": {"form_title": "用户信息"}
    },
    {
        "name": "test_elicitation_url",
        "category": "H",
        "description": "URL 式 Elicitation",
        "args": {"auth_url": "https://example.com/auth"}
    },

    # I 类 - Sampling (2个)
    {
        "name": "test_sampling_basic",
        "category": "I",
        "description": "基础 Sampling",
        "args": {"prompt": "What is 2+2?"}
    },
    {
        "name": "test_sampling_with_tools",
        "category": "I",
        "description": "带工具的 Sampling",
        "args": {"task": "calculate something"}
    }
]


def call_tool(tool_name: str, args: dict = None) -> dict:
    """调用 MCP 工具"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args or {}
        }
    }

    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
        data = resp.json()

        if "error" in data:
            return {"success": False, "error": data["error"]}

        result = data.get("result", {})
        if result.get("isError"):
            return {"success": False, "error": "Tool returned error"}

        # 解析内容
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return {"success": True, "data": json.loads(content[0]["text"])}
            except json.JSONDecodeError:
                return {"success": True, "text": content[0]["text"]}

        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "error": str(e)}


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("MCP HTTP SDK 批量测试")
    print(f"服务器: {BASE_URL}")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)

    results = {
        "passed": 0,
        "failed": 0,
        "total": len(TEST_CASES),
        "by_category": {},
        "failures": []
    }

    start_time = time.time()

    for i, test in enumerate(TEST_CASES, 1):
        category = test["category"]
        name = test["name"]
        desc = test["description"]

        # 按类别统计
        if category not in results["by_category"]:
            results["by_category"][category] = {"passed": 0, "failed": 0}

        # 调用工具
        result = call_tool(name, test.get("args", {}))

        if result["success"]:
            results["passed"] += 1
            results["by_category"][category]["passed"] += 1
            status = "[32mPASS[0m"  # 绿色
        else:
            results["failed"] += 1
            results["by_category"][category]["failed"] += 1
            status = "[31mFAIL[0m"  # 红色
            results["failures"].append({
                "name": name,
                "error": result.get("error", "Unknown error")
            })

        # 打印结果
        print(f"[{i:02d}/{len(TEST_CASES)}] [{category}] {name}: \033{status}")

    elapsed = time.time() - start_time

    # 打印摘要
    print()
    print("=" * 60)
    print("测试摘要")
    print("=" * 60)
    print(f"总计: {results['total']} | 通过: {results['passed']} | 失败: {results['failed']}")
    print(f"耗时: {elapsed:.2f}秒")
    print()

    # 按类别打印
    print("按类别统计:")
    for cat in sorted(results["by_category"].keys()):
        stats = results["by_category"][cat]
        total = stats["passed"] + stats["failed"]
        print(f"  [{cat}] 通过: {stats['passed']}/{total}")

    # 打印失败详情
    if results["failures"]:
        print()
        print("失败详情:")
        for f in results["failures"]:
            print(f"  - {f['name']}: {f['error']}")

    # 保存结果到文件
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    report_file = logs_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "server": BASE_URL,
            "elapsed_seconds": elapsed,
            "summary": {
                "total": results["total"],
                "passed": results["passed"],
                "failed": results["failed"]
            },
            "by_category": results["by_category"],
            "failures": results["failures"]
        }, f, indent=2, ensure_ascii=False)

    print()
    print(f"报告已保存: {report_file}")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
