#!/usr/bin/env python3
"""
MCP 2025-11-25 全量测试服务器 v3.1

基于 2026-03-09 测试结果改进，具备：
1. 完整 JSON-RPC 请求/响应日志（含原始请求体）
2. 所有 MCP 协议能力测试
3. 边界条件和异常值测试
4. 批量请求支持
5. 通知发送和追踪
6. 超时边界探测测试（新增）
7. 增强类型验证测试（新增）
8. 并发压力测试（增强）
9. Resources 稳定性测试（增强）

配置方式:
{
  "mcpServers": {
    "full-test": {
      "url": "http://127.0.0.1:3372/mcp"
    }
  }
}
"""

import json
import logging
import asyncio
import os
import uuid
import time
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path

try:
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.requests import Request
    from starlette.responses import Response, StreamingResponse
    import uvicorn
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False
    print("请安装依赖: pip install starlette uvicorn")
    exit(1)

# ==================== 日志系统 ====================

class FullInteractionLogger:
    """完整交互日志记录器"""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"full_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.request_counter = 0
        self.session_start = datetime.now()
        self.request_timestamps: Dict[str, datetime] = {}

    def log(self, entry: Dict):
        """写入日志"""
        entry["log_id"] = str(uuid.uuid4())[:8]
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_request(self, req_id: str, method: str, params: Any, http_info: Dict, raw_body: str = None) -> int:
        """记录请求（包含原始请求体）"""
        self.request_counter += 1
        timestamp = datetime.now()
        self.request_timestamps[req_id] = timestamp

        entry = {
            "timestamp": timestamp.isoformat(),
            "type": "request",
            "request_id": self.request_counter,
            "jsonrpc_id": req_id,
            "method": method,
            "params": params,
            "http": http_info
        }

        # 记录原始请求体（用于调试）
        if raw_body:
            entry["raw_body"] = raw_body
            entry["raw_body_bytes"] = len(raw_body.encode("utf-8"))

        self.log(entry)
        return self.request_counter

    def log_raw_request(self, req_id: str, method: str, params: Any, http_info: Dict, raw_body: str = None):
        """记录原始请求（别名）"""
        return self.log_request(req_id, method, params, http_info, raw_body)

    def log_response(self, req_id: str, result: Any, error: Any = None, raw_response: str = None):
        """记录响应（包含原始响应体）"""
        timestamp = datetime.now()
        start_time = self.request_timestamps.get(req_id)
        elapsed_ms = int((timestamp - start_time).total_seconds() * 1000) if start_time else 0

        entry = {
            "timestamp": timestamp.isoformat(),
            "type": "response",
            "jsonrpc_id": req_id,
            "elapsed_ms": elapsed_ms
        }
        if error:
            entry["error"] = error
        else:
            entry["result"] = result

        # 记录原始响应体
        if raw_response:
            entry["raw_response"] = raw_response
            entry["raw_response_bytes"] = len(raw_response.encode("utf-8"))

        self.log(entry)

    def log_notification(self, method: str, params: Any, direction: str = "outbound"):
        """记录通知"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "notification",
            "direction": direction,
            "method": method,
            "params": params
        }
        self.log(entry)

    def log_event(self, event: str, data: Any):
        """记录事件"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "event",
            "event": event,
            "data": data
        }
        self.log(entry)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局日志记录器
_logger: Optional[FullInteractionLogger] = None

def get_logger() -> FullInteractionLogger:
    global _logger
    if _logger is None:
        log_dir = Path(__file__).parent / "logs"
        _logger = FullInteractionLogger(log_dir)
    return _logger

def set_log_dir(path: str):
    global _logger
    _logger = FullInteractionLogger(Path(path))


# MCP 协议版本 - 使用 SDK 提供的最新版本
try:
    from mcp import types as mcp_types
    MCP_PROTOCOL_VERSION = mcp_types.LATEST_PROTOCOL_VERSION  # "2025-11-25"
except ImportError:
    MCP_PROTOCOL_VERSION = "2025-11-25"  # fallback
SERVER_INFO = {
    "name": "mcp-full-test",
    "title": "MCP Full Test Server",
    "version": "2.0.0",
    "description": "MCP 2025-11-25 全功能测试服务器，支持工具、资源、提示词、任务系统等完整协议功能测试"
    # 注意: protocolVersion 应在 InitializeResult 根级别返回，不在 serverInfo 中
}


# ==================== P1-7: 日志级别过滤 (MCP 2025-11-25) ====================

# 当前日志级别
_current_log_level = "info"
LOG_LEVELS = ["debug", "info", "notice", "warning", "error", "critical", "alert", "emergency"]
LOG_LEVEL_PRIORITY = {level: i for i, level in enumerate(LOG_LEVELS)}

def should_log(level: str) -> bool:
    """检查是否应该记录指定级别的日志"""
    return LOG_LEVEL_PRIORITY.get(level, 0) >= LOG_LEVEL_PRIORITY.get(_current_log_level, 1)


# ==================== P1-1: Tasks 异步任务系统 ====================

from enum import Enum
from dataclasses import dataclass, field
import uuid

class TaskStatus(str, Enum):
    """任务状态枚举 (MCP 2025-11-25)"""
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskSupport(str, Enum):
    """工具的任务支持级别"""
    FORBIDDEN = "forbidden"   # 不支持任务模式 (默认)
    OPTIONAL = "optional"     # 可选任务模式
    REQUIRED = "required"     # 必须使用任务模式


@dataclass
class Task:
    """任务实体"""
    task_id: str
    status: TaskStatus
    created_at: datetime
    last_updated_at: datetime
    ttl: Optional[int] = None           # 生存时间 (毫秒)
    poll_interval: Optional[int] = 5000  # 建议轮询间隔 (毫秒)
    status_message: Optional[str] = None
    # 内部字段
    _result: Optional[Any] = field(default=None, repr=False)
    _error: Optional[Dict] = field(default=None, repr=False)
    _request_type: Optional[str] = field(default=None, repr=False)
    _request_params: Optional[Dict] = field(default=None, repr=False)

    def to_dict(self) -> Dict:
        """转换为 JSON-RPC 响应格式"""
        result = {
            "taskId": self.task_id,
            "status": self.status.value,
            "createdAt": self.created_at.isoformat() + "Z",
            "lastUpdatedAt": self.last_updated_at.isoformat() + "Z",
        }
        if self.ttl is not None:
            result["ttl"] = self.ttl
        if self.poll_interval is not None:
            result["pollInterval"] = self.poll_interval
        if self.status_message:
            result["statusMessage"] = self.status_message
        return result


class TaskManager:
    """任务管理器"""

    TERMINAL_STATES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    def __init__(self, max_ttl: int = 86400000, max_concurrent: int = 100):
        self._tasks: Dict[str, Task] = {}
        self._max_ttl = max_ttl
        self._max_concurrent = max_concurrent
        # MCP 2025-11-25: 任务状态变更通知回调
        self._status_notification_callback: Optional[callable] = None

    def set_status_notification_callback(self, callback: callable):
        """设置任务状态变更通知回调 (用于发送 notifications/tasks/status)"""
        self._status_notification_callback = callback

    async def _notify_status_change(self, task: Task):
        """发送任务状态变更通知 (MCP 2025-11-25 SHOULD)"""
        if self._status_notification_callback:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/tasks/status",
                "params": task.to_dict()
            }
            await self._status_notification_callback(notification)

    def create_task(
        self,
        request_type: str,
        request_params: Dict,
        ttl: Optional[int] = None,
    ) -> Task:
        """创建新任务"""
        if len(self._tasks) >= self._max_concurrent:
            raise ValueError("Maximum concurrent tasks exceeded")

        task_id = str(uuid.uuid4())
        actual_ttl = min(ttl or self._max_ttl, self._max_ttl)
        now = datetime.now(timezone.utc)

        task = Task(
            task_id=task_id,
            status=TaskStatus.WORKING,
            created_at=now,
            last_updated_at=now,
            ttl=actual_ttl,
            poll_interval=5000,
            _request_type=request_type,
            _request_params=request_params,
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        task = self._tasks.get(task_id)
        if task and self._is_expired(task):
            del self._tasks[task_id]
            return None
        return task

    def list_tasks(self, cursor: Optional[str] = None, page_size: int = 50) -> Dict:
        """列出任务 (支持分页)"""
        # 清理过期任务
        self._cleanup_expired()

        tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        start_idx = 0
        if cursor:
            try:
                import base64
                start_idx = int(base64.urlsafe_b64decode(cursor.encode()).decode())
            except:
                pass

        page = tasks[start_idx:start_idx + page_size]
        next_cursor = None
        if start_idx + page_size < len(tasks):
            import base64
            next_cursor = base64.urlsafe_b64encode(str(start_idx + page_size).encode()).decode()

        return {"tasks": [t.to_dict() for t in page], "nextCursor": next_cursor}

    async def cancel_task(self, task_id: str) -> Optional[Task]:
        """取消任务"""
        task = self.get_task(task_id)
        if not task:
            return None
        if task.status in self.TERMINAL_STATES:
            raise ValueError(f"Cannot cancel task in terminal status: {task.status.value}")

        task.status = TaskStatus.CANCELLED
        task.status_message = "Task cancelled by request"
        task.last_updated_at = datetime.now(timezone.utc)
        # MCP 2025-11-25: 发送状态变更通知
        await self._notify_status_change(task)
        return task

    async def complete_task(self, task_id: str, result: Any) -> Optional[Task]:
        """标记任务完成"""
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task._result = result
        task.last_updated_at = datetime.now(timezone.utc)
        # MCP 2025-11-25: 发送状态变更通知
        await self._notify_status_change(task)
        return task

    async def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """标记任务失败"""
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = TaskStatus.FAILED
        task.status_message = error
        task._error = {"code": -32603, "message": error}
        task.last_updated_at = datetime.now(timezone.utc)
        # MCP 2025-11-25: 发送状态变更通知
        await self._notify_status_change(task)
        return task

    def _is_expired(self, task: Task) -> bool:
        if task.ttl is None:
            return False
        elapsed = (datetime.now(timezone.utc) - task.created_at).total_seconds() * 1000
        return elapsed > task.ttl

    def _cleanup_expired(self) -> int:
        """清理过期任务"""
        expired = [tid for tid, t in self._tasks.items() if self._is_expired(t)]
        for tid in expired:
            del self._tasks[tid]
        return len(expired)


# 全局任务管理器
_task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

# ==================== 测试工具定义 ====================

# P2-3: 图标定义 (MCP 2025-11-25 SEP-973)
# 使用 data URI 格式的简单 SVG 图标

# 通用测试图标 (SVG data URI)
ICON_TEST = {
    "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNGE5MGUyIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik05IDEybDYgNi02IDYiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjwvc3ZnPg==",
    "mimeType": "image/svg+xml",
    "sizes": ["any"]
}

ICON_NETWORK = {
    "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMjE5NmYzIiBzdHJva2Utd2lkdGg9IjIiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIi8+PGxpbmUgeDE9IjIiIHkxPSIxMiIgeDI9IjIyIiB5Mj0iMTIiLz48bGluZSB4MT0iMTIiIHkxPSIyIiB4Mj0iMTIiIHkyPSIyMiIvPjwvc3ZnPg==",
    "mimeType": "image/svg+xml",
    "sizes": ["any"]
}

ICON_TIME = {
    "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZjk3NzE0IiBzdHJva2Utd2lkdGg9IjIiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIi8+PHBvbHlsaW5lIHBvaW50cz0iMTIgNiAxMiAxMiAxNiAxNCIvPjwvc3ZnPg==",
    "mimeType": "image/svg+xml",
    "sizes": ["any"]
}

ICON_GUI = {
    "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOWMzMjdiIiBzdHJva2Utd2lkdGg9IjIiPjxyZWN0IHg9IjMiIHk9IjMiIHdpZHRoPSIxOCIgaGVpZ2h0PSIxOCIgcng9IjIiLz48bGluZSB4MT0iMyIgeTE9IjkiIHgyPSIyMSIgeTI9IjkiLz48L3N2Zz4=",
    "mimeType": "image/svg+xml",
    "sizes": ["any"]
}

ICON_AI = {
    "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOGI1Y2Y2IiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0xMiAyYTEwIDEwIDAgMSAwIDEwIDEwQTEwIDEwIDAgMCAwIDEyIDJaIi8+PHBhdGggZD0iTTEyIDE2djQiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxIi8+PC9zdmc+",
    "mimeType": "image/svg+xml",
    "sizes": ["any"]
}

# Dark 主题变体
ICON_TEST_DARK = {**ICON_TEST, "theme": "dark", "src": ICON_TEST["src"].replace("#4a90e2", "#6bb3ff")}
ICON_NETWORK_DARK = {**ICON_NETWORK, "theme": "dark", "src": ICON_NETWORK["src"].replace("#2196f3", "#64b5f6")}

# 核心能力测试工具
CORE_TOOLS = [
    {
        "name": "test_ping",
        "title": "Ping 测试",
        "description": "[A1] 测试基础连通性。返回 pong 和精确时间戳。",
        "icons": [ICON_NETWORK, ICON_NETWORK_DARK],
        "inputSchema": {
            "type": "object",
            "properties": {
                "echo": {"type": "string", "description": "可选的回显字符串"},
                "delay_ms": {"type": "integer", "default": 0, "description": "响应延迟（毫秒）"}
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "test_protocol_version",
        "title": "协议版本测试",
        "description": "[A2] 测试协议版本协商。验证客户端发送的协议版本。",
        "icons": [ICON_TEST, ICON_TEST_DARK],
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "test_capabilities",
        "title": "能力协商测试",
        "description": "[A3] 测试能力协商。返回完整的能力声明。",
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "test_tool_call",
        "title": "工具调用测试",
        "description": "[A4] 测试工具调用。验证参数传递和返回格式。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_value": {"type": "string", "description": "输入值"},
                "input_type": {"type": "string", "enum": ["string", "number", "boolean", "array", "object", "integer", "null"], "default": "string"}
            },
            "required": ["input_value"]
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "test_all_types",
        "title": "全类型验证测试",
        "description": "[A5] 增强类型验证。一次性测试所有类型：string/integer/float/boolean/null/negative/bigint/array/object。返回每种类型的验证结果。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "string_value": {"type": "string", "description": "字符串值"},
                "integer_value": {"type": "integer", "description": "整数值"},
                "float_value": {"type": "number", "description": "浮点数值"},
                "boolean_value": {"type": "boolean", "description": "布尔值"},
                "negative_value": {"type": "integer", "description": "负整数"},
                "big_int_value": {"type": "integer", "description": "大整数（>9007199254740991）"},
                "array_value": {"type": "array", "items": {"type": "integer"}, "description": "整型数组"},
                "object_value": {"type": "object", "description": "对象值"}
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
]

# 重要能力测试工具
IMPORTANT_TOOLS = [
    {
        "name": "test_complex_params",
        "description": "[B1] 测试复杂参数类型：嵌套对象、数组、枚举。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "level1": {
                            "type": "object",
                            "properties": {
                                "level2": {"type": "string"}
                            }
                        }
                    }
                },
                "array": {"type": "array", "items": {"type": "integer"}},
                "enum_value": {"type": "string", "enum": ["option1", "option2", "option3"]},
                "optional_with_default": {"type": "integer", "default": 42}
            }
        }
    },
    {
        "name": "test_large_data",
        "description": "[B2] 测试大数据量处理。生成指定数量的数据项。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 100, "description": "数据项数量（1-10000）"},
                "item_size": {"type": "integer", "default": 100, "description": "每项大小（字节）"}
            }
        }
    },
    {
        "name": "test_long_operation",
        "title": "长时间操作测试",
        "description": "[B3] 测试长时间操作。模拟耗时任务并发送进度通知。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "default": 5, "description": "操作时长（秒）"},
                "progress_interval_ms": {"type": "integer", "default": 1000, "description": "进度通知间隔"},
                "send_progress": {"type": "boolean", "default": True, "description": "是否发送进度通知"}
            }
        },
        "execution": {
            "taskSupport": "optional"
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    },
    {
        "name": "test_concurrent",
        "description": "[B4] 测试并发请求处理。返回请求ID和处理时间。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "请求标识"},
                "delay_ms": {"type": "integer", "default": 100, "description": "模拟处理延迟"}
            }
        }
    },
    {
        "name": "test_unicode",
        "description": "[B5] 测试 Unicode 支持。验证多语言字符编码。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "测试文本"},
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["chinese", "japanese", "arabic", "emoji"],
                    "description": "测试语言列表"
                }
            }
        }
    },
    {
        "name": "test_error_codes",
        "description": "[B6] 测试错误处理。模拟各种错误场景。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_type": {
                    "type": "string",
                    "enum": ["invalid_params", "not_found", "internal_error", "unauthorized", "timeout"],
                    "description": "错误类型"
                }
            },
            "required": ["error_type"]
        }
    },
]

# 资源和提示测试工具
RESOURCE_TOOLS = [
    {
        "name": "list_resources",
        "description": "[B7] 列出可用的 MCP 资源。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["config", "data", "status"], "description": "资源类别"}
            }
        }
    },
    {
        "name": "read_resource",
        "description": "[B7] 读取指定的 MCP 资源。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "uri": {"type": "string", "description": "资源 URI"}
            },
            "required": ["uri"]
        }
    },
    {
        "name": "list_prompts",
        "description": "[B8] 列出可用的 MCP 提示模板。",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_prompt",
        "description": "[B8] 获取指定的 MCP 提示模板。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "提示模板名称"},
                "arguments": {"type": "object", "description": "模板参数"}
            },
            "required": ["name"]
        }
    },
]

# 高级能力测试工具
ADVANCED_TOOLS = [
    {
        "name": "test_progress_notification",
        "description": "[B9] 测试进度通知。发送指定数量的进度更新。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "total_steps": {"type": "integer", "default": 5, "description": "总步数"},
                "step_delay_ms": {"type": "integer", "default": 500, "description": "步间延迟"}
            }
        }
    },
    {
        "name": "test_cancellation",
        "description": "[B10] 测试取消操作。启动可取消的长操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "default": 30, "description": "操作时长"}
            }
        }
    },
    {
        "name": "test_sampling",
        "description": "[B11] 测试采样请求。请求客户端 LLM 进行采样。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "采样提示"},
                "max_tokens": {"type": "integer", "default": 100, "description": "最大令牌数"}
            }
        }
    },
    {
        "name": "test_batch_request",
        "description": "[C2] 测试批量请求。验证 JSON-RPC 批量处理。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "op": {"type": "string"},
                            "value": {"type": "integer"}
                        }
                    },
                    "description": "操作列表"
                }
            }
        }
    },
    {
        "name": "test_completion",
        "description": "[C5] 测试自动补全。返回补全建议。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref_type": {"type": "string", "enum": ["ref/resource", "ref/prompt"]},
                "partial_value": {"type": "string", "description": "部分输入值"}
            }
        }
    },
]

# 边界条件测试工具
BOUNDARY_TOOLS = [
    {
        "name": "test_empty_params",
        "description": "[D1] 测试空参数。验证默认值处理。",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "test_long_string",
        "description": "[D2] 测试超长字符串。处理大文本输入。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "length": {"type": "integer", "default": 10000, "description": "字符串长度"}
            }
        }
    },
    {
        "name": "test_special_chars",
        "description": "[D3] 测试特殊字符。处理控制字符、引号等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_control": {"type": "boolean", "default": False},
                "include_quotes": {"type": "boolean", "default": True},
                "include_newlines": {"type": "boolean", "default": True}
            }
        }
    },
    {
        "name": "test_idempotency",
        "description": "[D4] 测试幂等性。相同请求应返回相同结果。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation_id": {"type": "string", "description": "操作标识"}
            }
        }
    },
    {
        "name": "test_rapid_fire",
        "description": "[D5] 测试快速连续请求。验证连接稳定性。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 5, "description": "请求数量"}
            }
        }
    },
    {
        "name": "test_empty_values",
        "description": "[D6] 测试空值边界。验证空数组[]、空对象{}、空字符串\"\"的传递。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "empty_array": {"type": "array", "items": {"type": "string"}, "description": "空数组"},
                "empty_object": {"type": "object", "description": "空对象"},
                "empty_string": {"type": "string", "description": "空字符串"}
            }
        }
    },
    {
        "name": "test_deep_nesting",
        "description": "[D7] 测试深层嵌套。验证深度嵌套对象（默认10层）的传递。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "depth": {"type": "integer", "default": 10, "description": "嵌套深度（1-20）"}
            }
        }
    },
    {
        "name": "test_large_array",
        "description": "[D8] 测试超大数组。验证大数组（默认10000个元素）的传递。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "default": 1000, "description": "数组元素数量（1-50000）"}
            }
        }
    },
]

# 超时边界探测测试工具 (E 类 - 新增)
TIMEOUT_TOOLS = [
    {
        "name": "test_timeout_boundary",
        "title": "超时边界探测",
        "description": "[E1] 超时边界探测。测试不同时长操作，找出客户端超时阈值。建议依次测试：5/10/15/20/25/30秒。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "default": 5, "description": "操作时长（1-60秒）"},
                "send_keepalive": {"type": "boolean", "default": False, "description": "是否每秒发送保活通知"}
            }
        },
        "execution": {
            "taskSupport": "optional"
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    },
]

# ==================== GUI Agent 原子工具 (G 类) ====================
# 模拟多步 GUI Agent 交互，每步独立调用，LLM 可以实时看到结果

GUI_AGENT_TOOLS = [
    {
        "name": "gui_screenshot",
        "description": "[G1] 获取当前屏幕截图。返回模拟的屏幕状态信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app": {"type": "string", "default": "desktop", "description": "目标应用: desktop/wechat/browser/notepad"}
            }
        }
    },
    {
        "name": "gui_click",
        "description": "[G2] 点击屏幕指定位置。返回操作结果和新截图信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X 坐标"},
                "y": {"type": "integer", "description": "Y 坐标"},
                "description": {"type": "string", "default": "", "description": "点击目标的描述（如：发送按钮）"}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "gui_type",
        "description": "[G3] 在当前位置输入文本。返回操作结果。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要输入的文本"},
                "enter": {"type": "boolean", "default": False, "description": "输入后是否按回车"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "gui_find_element",
        "description": "[G4] 在屏幕上查找指定元素。返回元素位置坐标。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element": {"type": "string", "description": "要查找的元素描述（如：发送按钮、搜索框）"},
                "app": {"type": "string", "default": "current", "description": "目标应用"}
            },
            "required": ["element"]
        }
    },
    {
        "name": "gui_open_app",
        "description": "[G5] 打开指定应用。返回应用状态和截图信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app": {"type": "string", "description": "应用名称: wechat/browser/notepad/calculator"},
                "simulate_delay_ms": {"type": "integer", "default": 500, "description": "模拟启动延迟（毫秒）"}
            },
            "required": ["app"]
        }
    },
    {
        "name": "gui_scroll",
        "description": "[G6] 滚动屏幕。返回滚动后的状态。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"], "description": "滚动方向"},
                "amount": {"type": "integer", "default": 100, "description": "滚动像素数"}
            },
            "required": ["direction"]
        }
    },
    {
        "name": "gui_wait_for_element",
        "description": "[G7] 等待指定元素出现。返回元素位置或超时。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element": {"type": "string", "description": "要等待的元素描述"},
                "timeout_ms": {"type": "integer", "default": 5000, "description": "超时时间（毫秒）"},
                "simulate_found": {"type": "boolean", "default": True, "description": "模拟是否找到元素"}
            },
            "required": ["element"]
        }
    },
    {
        "name": "gui_get_state",
        "description": "[G8] 获取当前 GUI 状态摘要。返回当前应用、窗口、可见元素等。",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "gui_send_message",
        "description": "[G6] 发送消息（流式多步）。通过 notifications/progress 逐步推送每一步进度。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "message": {"type": "string", "description": "消息内容"},
                "step_delay_ms": {"type": "integer", "default": 1000, "description": "每步之间的延迟（毫秒）"}
            },
            "required": ["contact", "message"]
        }
    },
    {
        "name": "gui_automation_demo",
        "description": "[G7] 自动化演示（一次性返回）。所有步骤在一个响应中返回，无流式进度。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {"type": "string", "default": "notepad", "description": "场景名称"}
            }
        }
    },
]

# ==================== Elicitation 测试工具 (H 类) ====================
# MCP 2025-11-25 Elicitation 机制测试

ELICITATION_TOOLS = [
    {
        "name": "test_elicitation_form",
        "title": "表单式信息请求测试",
        "description": "[H1] 测试 MCP 2025-11-25 表单式 Elicitation。服务器请求用户提供表单信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "form_type": {
                    "type": "string",
                    "enum": ["simple", "enum_select", "multi_select", "with_defaults"],
                    "default": "simple",
                    "description": "表单类型"
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "test_elicitation_url",
        "title": "URL 式信息请求测试",
        "description": "[H2] 测试 MCP 2025-11-25 URL 式 Elicitation。模拟 OAuth 授权流程。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["github", "google", "custom"],
                    "default": "github",
                    "description": "模拟授权的服务"
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
]

# ==================== Sampling 测试工具 (I 类) ====================
# MCP 2025-11-25 Sampling 工具调用支持

SAMPLING_TOOLS = [
    {
        "name": "test_sampling_basic",
        "title": "基础采样测试",
        "description": "[I1] 测试 MCP 2025-11-25 基础 Sampling 功能。请求客户端 LLM 生成响应。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "default": "What is 2+2?",
                    "description": "发送给 LLM 的提示"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 100,
                    "description": "最大生成 token 数"
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
    {
        "name": "test_sampling_with_tools",
        "title": "带工具的采样测试",
        "description": "[I2] 测试 MCP 2025-11-25 SEP-1577 Sampling 工具调用。请求 LLM 使用工具完成任务。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "default": "What is the weather in Beijing?",
                    "description": "任务描述"
                },
                "tool_choice": {
                    "type": "string",
                    "enum": ["auto", "required", "none"],
                    "default": "auto",
                    "description": "工具选择模式"
                }
            }
        },
        "execution": {
            "taskSupport": "optional"
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
    # ===== 服务器主动请求测试工具 =====
    {
        "name": "test_server_elicitation",
        "title": "服务器发起 Elicitation 测试",
        "description": "[H3] 测试服务器主动向客户端发起 Elicitation 请求。需要客户端支持 elicitation 能力。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "default": "Please provide your email address",
                    "description": "Elicitation 消息"
                },
                "requested_schema": {
                    "type": "object",
                    "description": "请求的数据 schema"
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
    {
        "name": "test_server_sampling",
        "title": "服务器发起 Sampling 测试",
        "description": "[I3] 测试服务器主动向客户端发起 Sampling 请求。需要客户端支持 sampling 能力。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "default": "Summarize the following text",
                    "description": "Sampling 提示"
                },
                "max_tokens": {
                    "type": "integer",
                    "default": 500,
                    "description": "最大生成 token 数"
                }
            }
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
]

# 所有工具
ALL_TOOLS = CORE_TOOLS + IMPORTANT_TOOLS + RESOURCE_TOOLS + ADVANCED_TOOLS + BOUNDARY_TOOLS + TIMEOUT_TOOLS + GUI_AGENT_TOOLS + ELICITATION_TOOLS + SAMPLING_TOOLS

# ==================== 工具实现 ====================

# 幂等性状态存储
_idempotency_store: Dict[str, Any] = {}

# 采样请求计数器
_sampling_counter = 0

async def call_tool(name: str, args: Dict, request: Request, req_id: str) -> Dict:
    """执行工具调用"""
    log = get_logger()
    start_time = time.time()

    # ===== A 核心能力测试 =====

    if name == "test_ping":
        echo = args.get("echo", "pong")
        delay_ms = args.get("delay_ms", 0)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
        return {
            "test_id": "A1",
            "success": True,
            "pong": "pong",  # 返回字符串 "pong" 而非布尔值
            "echo": echo,
            "server_time": datetime.now().isoformat(),
            "elapsed_ms": int((time.time() - start_time) * 1000)
        }

    if name == "test_protocol_version":
        client_version = request.headers.get("mcp-protocol-version", "unknown")
        return {
            "test_id": "A2",
            "success": True,
            "client_protocol_version": client_version,
            "server_protocol_version": MCP_PROTOCOL_VERSION,
            "version_match": client_version == MCP_PROTOCOL_VERSION,
            "note": "Protocol version negotiation test"
        }

    if name == "test_capabilities":
        return {
            "test_id": "A3",
            "success": True,
            "server_capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
                "streaming": True
            },
            "protocol_version": MCP_PROTOCOL_VERSION
        }

    if name == "test_tool_call":
        input_value = args.get("input_value")
        input_type = args.get("input_type", "string")
        return {
            "test_id": "A4",
            "success": True,
            "received_value": input_value,
            "received_type": input_type,
            "actual_type": type(input_value).__name__,
            "type_match": type(input_value).__name__ == input_type,
            "server_time": datetime.now().isoformat()
        }

    if name == "test_all_types":
        """A5: 增强类型验证 - 测试所有类型的传递情况"""
        type_results = {}

        # 测试字符串
        string_val = args.get("string_value", "default_string")
        type_results["string"] = {
            "received": string_val,
            "actual_type": type(string_val).__name__,
            "type_match": isinstance(string_val, str),
            "expected_type": "str"
        }

        # 测试整数
        int_val = args.get("integer_value")
        if int_val is not None:
            type_results["integer"] = {
                "received": int_val,
                "actual_type": type(int_val).__name__,
                "type_match": isinstance(int_val, int) and not isinstance(int_val, bool),
                "expected_type": "int"
            }

        # 测试浮点数
        float_val = args.get("float_value")
        if float_val is not None:
            type_results["float"] = {
                "received": float_val,
                "actual_type": type(float_val).__name__,
                "type_match": isinstance(float_val, (int, float)) and not isinstance(float_val, bool),
                "is_float": isinstance(float_val, float),
                "expected_type": "float"
            }

        # 测试布尔值
        bool_val = args.get("boolean_value")
        if bool_val is not None:
            type_results["boolean"] = {
                "received": bool_val,
                "actual_type": type(bool_val).__name__,
                "type_match": isinstance(bool_val, bool),
                "expected_type": "bool"
            }

        # 测试负数
        neg_val = args.get("negative_value")
        if neg_val is not None:
            type_results["negative"] = {
                "received": neg_val,
                "actual_type": type(neg_val).__name__,
                "is_negative": isinstance(neg_val, (int, float)) and neg_val < 0,
                "type_match": isinstance(neg_val, (int, float)),
                "expected_type": "int/float"
            }

        # 测试大整数
        big_val = args.get("big_int_value")
        if big_val is not None:
            type_results["bigint"] = {
                "received": big_val,
                "actual_type": type(big_val).__name__,
                "exceeds_safe_integer": isinstance(big_val, int) and abs(big_val) > 9007199254740991,
                "type_match": isinstance(big_val, int) and not isinstance(big_val, bool),
                "expected_type": "int"
            }

        # 测试数组
        arr_val = args.get("array_value")
        if arr_val is not None:
            type_results["array"] = {
                "received_type": type(arr_val).__name__,
                "length": len(arr_val) if isinstance(arr_val, list) else None,
                "type_match": isinstance(arr_val, list),
                "sample": arr_val[:3] if isinstance(arr_val, list) and len(arr_val) > 0 else arr_val
            }

        # 测试对象
        obj_val = args.get("object_value")
        if obj_val is not None:
            type_results["object"] = {
                "received_type": type(obj_val).__name__,
                "key_count": len(obj_val) if isinstance(obj_val, dict) else None,
                "type_match": isinstance(obj_val, dict),
                "keys": list(obj_val.keys()) if isinstance(obj_val, dict) else None
            }

        # 统计
        total_tests = len(type_results)
        type_matches = sum(1 for r in type_results.values() if r.get("type_match", False))

        return {
            "test_id": "A5",
            "success": True,
            "type_results": type_results,
            "summary": {
                "total_types_tested": total_tests,
                "type_matches": type_matches,
                "match_rate": f"{type_matches}/{total_tests}",
                "all_passed": type_matches == total_tests
            },
            "server_time": datetime.now().isoformat()
        }

    # ===== B 重要能力测试 =====

    if name == "test_complex_params":
        nested = args.get("nested", {})
        array = args.get("array", [])
        enum_value = args.get("enum_value")
        optional = args.get("optional_with_default", "NOT_PROVIDED")
        return {
            "test_id": "B1",
            "success": True,
            "received": {
                "nested": nested,
                "array": array,
                "enum_value": enum_value,
                "optional_with_default": optional
            },
            "analysis": {
                "nested_depth": _get_depth(nested),
                "array_length": len(array),
                "enum_valid": enum_value in ["option1", "option2", "option3"] if enum_value else False
            }
        }

    if name == "test_large_data":
        count = min(max(args.get("count", 100), 1), 10000)
        item_size = min(max(args.get("item_size", 100), 10), 1000)
        items = []
        for i in range(count):
            items.append({
                "id": i,
                "data": "x" * item_size,
                "timestamp": datetime.now().isoformat()
            })
        return {
            "test_id": "B2",
            "success": True,
            "count": count,
            "item_size": item_size,
            "total_bytes": count * (item_size + 50),
            "sample_items": items[:3],
            "generation_time_ms": int((time.time() - start_time) * 1000)
        }

    if name == "test_long_operation":
        duration = min(max(args.get("duration_seconds", 5), 1), 120)
        interval = min(max(args.get("progress_interval_ms", 1000), 100), 5000)
        send_progress = args.get("send_progress", True)

        steps = max(1, (duration * 1000) // interval)
        for i in range(steps):
            await asyncio.sleep(interval / 1000)
            if send_progress:
                # 进度通知在响应中模拟返回
                pass

        return {
            "test_id": "B3",
            "success": True,
            "duration_seconds": duration,
            "progress_interval_ms": interval,
            "steps_completed": steps,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "note": "For real progress notifications, use test_progress_notification"
        }

    if name == "test_concurrent":
        req_id_arg = args.get("request_id", str(uuid.uuid4())[:8])
        delay = args.get("delay_ms", 100)
        await asyncio.sleep(delay / 1000)
        return {
            "test_id": "B4",
            "success": True,
            "request_id": req_id_arg,
            "delay_requested_ms": delay,
            "server_time": datetime.now().isoformat(),
            "elapsed_ms": int((time.time() - start_time) * 1000)
        }

    if name == "test_unicode":
        text = args.get("text", "")
        languages = args.get("languages", ["chinese", "japanese", "arabic", "emoji"])

        analysis = {
            "length": len(text),
            "bytes_utf8": len(text.encode("utf-8")),
            "has_chinese": any("\u4e00" <= c <= "\u9fff" for c in text) if text else False,
            "has_japanese": any("\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff" for c in text) if text else False,
            "has_arabic": any("\u0600" <= c <= "\u06ff" for c in text) if text else False,
            "has_emoji": any(ord(c) > 0x1F000 for c in text) if text else False
        }

        return {
            "test_id": "B5",
            "success": True,
            "text": text,
            "analysis": analysis,
            "languages_tested": languages
        }

    if name == "test_error_codes":
        error_type = args.get("error_type")
        error_map = {
            "invalid_params": (-32602, "Invalid params: missing required field"),
            "not_found": (-32602, "Resource not found"),
            "internal_error": (-32603, "Internal server error"),
            "unauthorized": (-32600, "Unauthorized: invalid or missing token"),
            "timeout": (-32603, "Operation timed out")
        }
        code, message = error_map.get(error_type, (-32603, "Unknown error"))
        return {
            "test_id": "B6",
            "success": False,
            "error": message,
            "error_code": code,
            "error_type": error_type
        }

    # ===== B7-B8 资源和提示测试 =====

    if name == "list_resources":
        category = args.get("category")
        resources = [
            {"uri": "config://server", "name": "Server Configuration", "mimeType": "application/json"},
            {"uri": "config://database", "name": "Database Configuration", "mimeType": "application/json"},
            {"uri": "data://sample", "name": "Sample Data", "mimeType": "application/json"},
            {"uri": "status://live", "name": "Live Status", "mimeType": "application/json"}
        ]
        if category:
            resources = [r for r in resources if r["uri"].startswith(f"{category}://")]
        return {
            "test_id": "B7",
            "success": True,
            "resources": resources,
            "count": len(resources),
            "note": "MCP resources/list wrapped as tool"
        }

    if name == "read_resource":
        uri = args.get("uri", "")
        resource_data = {
            "config://server": {"host": "127.0.0.1", "port": 3372, "mode": "http"},
            "config://database": {"type": "sqlite", "path": "test.db"},
            "data://sample": {"items": [1, 2, 3], "total": 3},
            "status://live": {"uptime": 12345, "requests": get_logger().request_counter}
        }
        if uri in resource_data:
            return {
                "test_id": "B7",
                "success": True,
                "uri": uri,
                "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(resource_data[uri])}]
            }
        return {
            "test_id": "B7",
            "success": False,
            "error": f"Resource not found: {uri}",
            "error_code": -32602
        }

    if name == "list_prompts":
        return {
            "test_id": "B8",
            "success": True,
            "prompts": [
                {"name": "analyze_data", "description": "Analyze data with specified format"},
                {"name": "summarize", "description": "Summarize the content"},
                {"name": "test_sampling", "description": "Test sampling capability"}
            ],
            "note": "MCP prompts/list wrapped as tool"
        }

    if name == "get_prompt":
        prompt_name = args.get("name", "")
        prompt_args = args.get("arguments", {})
        prompts = {
            "analyze_data": {
                "description": "Analyze data",
                "messages": [{"role": "user", "content": f"Analyze this data: {prompt_args.get('data', 'N/A')}"}]
            },
            "summarize": {
                "description": "Summarize content",
                "messages": [{"role": "user", "content": "Summarize the provided content"}]
            },
            "test_sampling": {
                "description": "Test sampling",
                "messages": [{"role": "user", "content": prompt_args.get('question', 'What is 2+2?')}]
            }
        }
        if prompt_name in prompts:
            return {
                "test_id": "B8",
                "success": True,
                "name": prompt_name,
                "prompt": prompts[prompt_name]
            }
        return {
            "test_id": "B8",
            "success": False,
            "error": f"Prompt not found: {prompt_name}"
        }

    # ===== B9-B11 高级测试 =====

    if name == "test_progress_notification":
        total_steps = min(max(args.get("total_steps", 5), 1), 20)
        step_delay = min(max(args.get("step_delay_ms", 500), 100), 5000)
        progress_updates = []

        for i in range(total_steps):
            await asyncio.sleep(step_delay / 1000)
            progress = (i + 1) / total_steps
            progress_updates.append({
                "step": i + 1,
                "total": total_steps,
                "progress": progress,
                "percentage": round(progress * 100, 1),
                "timestamp": datetime.now().isoformat()
            })
            # 发送进度通知
            log.log_notification("notifications/progress", {
                "progressToken": f"test-{req_id}",
                "progress": progress,
                "total": 1.0,
                "message": f"Step {i + 1}/{total_steps}"
            })

        return {
            "test_id": "B9",
            "success": True,
            "total_steps": total_steps,
            "step_delay_ms": step_delay,
            "progress_updates": progress_updates,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "note": "Progress notifications logged to interaction log"
        }

    if name == "test_cancellation":
        duration = min(max(args.get("duration_seconds", 30), 1), 120)

        # 记录开始
        log.log_event("cancellation_test_start", {"duration": duration, "req_id": req_id})

        # 执行可取消操作
        for i in range(duration):
            await asyncio.sleep(1)
            progress = (i + 1) / duration
            log.log_notification("notifications/progress", {
                "progressToken": f"cancel-{req_id}",
                "progress": progress,
                "message": f"Progress: {round(progress * 100, 1)}%"
            })

        return {
            "test_id": "B10",
            "success": True,
            "duration_seconds": duration,
            "completed": True,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "note": "Send notifications/cancelled to interrupt this operation"
        }

    if name == "test_sampling":
        global _sampling_counter
        _sampling_counter += 1

        prompt = args.get("prompt", "What is 2+2?")
        max_tokens = args.get("max_tokens", 100)

        # 记录采样请求
        log.log_event("sampling_request", {
            "request_id": _sampling_counter,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "note": "Server sent sampling/createMessage request"
        })

        return {
            "test_id": "B11",
            "success": True,
            "sampling_requested": True,
            "request_id": _sampling_counter,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "sampling_params": {
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt}}],
                "maxTokens": max_tokens
            },
            "simulated_response": "4",
            "note": "Actual sampling requires client support for sampling/createMessage callback"
        }

    # ===== H 类 - Elicitation 测试工具 =====

    if name == "test_elicitation_form":
        message = args.get("message", "Please provide information")
        form_schema = args.get("form_schema", {
            "type": "object",
            "properties": {
                "username": {"type": "string", "title": "Username"},
                "email": {"type": "string", "title": "Email", "format": "email"}
            },
            "required": ["username"]
        })

        return {
            "test_id": "H1",
            "success": True,
            "elicitation_type": "form",
            "message": message,
            "form_schema": form_schema,
            "note": "Server requested elicitation/form from client"
        }

    if name == "test_elicitation_url":
        message = args.get("message", "Please complete authentication")
        auth_url = args.get("auth_url", "https://example.com/auth?client_id=mcp_test")
        redirect_uri = args.get("redirect_uri", "mcp://callback")

        return {
            "test_id": "H2",
            "success": True,
            "elicitation_type": "url",
            "message": message,
            "auth_url": auth_url,
            "redirect_uri": redirect_uri,
            "note": "Server requested elicitation/url from client"
        }

    # ===== I 类 - Sampling 测试工具 =====

    if name == "test_sampling_basic":
        prompt = args.get("prompt", "What is the capital of France?")
        max_tokens = args.get("max_tokens", 100)
        temperature = args.get("temperature", 0.7)

        return {
            "test_id": "I1",
            "success": True,
            "sampling_type": "basic",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "sampling_params": {
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt}}],
                "maxTokens": max_tokens,
                "temperature": temperature
            },
            "note": "Server requested basic sampling from client"
        }

    if name == "test_sampling_with_tools":
        prompt = args.get("prompt", "What is the weather in Beijing?")
        tools = args.get("tools", [{"name": "get_weather", "description": "Get weather info"}])
        tool_choice = args.get("tool_choice", {"mode": "auto"})

        return {
            "test_id": "I2",
            "success": True,
            "sampling_type": "with_tools",
            "prompt": prompt,
            "tools": tools,
            "tool_choice": tool_choice,
            "sampling_params": {
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt}}],
                "tools": tools,
                "toolChoice": tool_choice
            },
            "note": "Server requested sampling with tools from client"
        }

    # ===== C2, C5 批量和补全 =====

    if name == "test_batch_request":
        operations = args.get("operations", [])
        results = []
        for op in operations:
            op_type = op.get("op", "noop")
            value = op.get("value", 0)
            if op_type == "double":
                results.append({"op": op_type, "input": value, "output": value * 2})
            elif op_type == "square":
                results.append({"op": op_type, "input": value, "output": value * value})
            else:
                results.append({"op": op_type, "input": value, "output": value})

        return {
            "test_id": "C2",
            "success": True,
            "operations_received": len(operations),
            "results": results,
            "note": "Batch operations processed"
        }

    if name == "test_completion":
        ref_type = args.get("ref_type", "ref/resource")
        partial = args.get("partial_value", "")

        if ref_type == "ref/resource":
            completions = [
                f"config://{partial}server",
                f"config://{partial}settings",
                f"config://{partial}database"
            ]
        else:
            completions = ["analyze_data", "summarize"]

        # 过滤匹配项
        if partial:
            completions = [c for c in completions if partial.lower() in c.lower()]

        return {
            "test_id": "C5",
            "success": True,
            "ref_type": ref_type,
            "partial_value": partial,
            "completions": completions,
            "total": len(completions),
            "has_more": False
        }

    # ===== D 边界条件测试 =====

    if name == "test_empty_params":
        return {
            "test_id": "D1",
            "success": True,
            "received_params": args,
            "params_count": len(args),
            "note": "Empty params test - should use all defaults"
        }

    if name == "test_long_string":
        length = min(max(args.get("length", 10000), 1), 100000)
        test_string = "x" * length
        return {
            "test_id": "D2",
            "success": True,
            "requested_length": length,
            "actual_length": len(test_string),
            "bytes_utf8": len(test_string.encode("utf-8")),
            "sample": test_string[:100] + "..." if length > 100 else test_string,
            "elapsed_ms": int((time.time() - start_time) * 1000)
        }

    if name == "test_special_chars":
        include_control = args.get("include_control", False)
        include_quotes = args.get("include_quotes", True)
        include_newlines = args.get("include_newlines", True)

        special = ""
        if include_control:
            special += "\x00\x01\x02"  # 控制字符
        if include_quotes:
            special += "\"'`"  # 引号
        if include_newlines:
            special += "\n\r\t"  # 换行符

        return {
            "test_id": "D3",
            "success": True,
            "special_chars": special,
            "escaped": special.encode("unicode_escape").decode("ascii"),
            "length": len(special),
            "bytes_utf8": len(special.encode("utf-8")),
            "note": "Special characters test"
        }

    if name == "test_idempotency":
        op_id = args.get("operation_id", str(uuid.uuid4()))

        if op_id in _idempotency_store:
            return {
                "test_id": "D4",
                "success": True,
                "operation_id": op_id,
                "cached": True,
                "first_call_time": _idempotency_store[op_id]["time"],
                "first_call_result": _idempotency_store[op_id]["result"]
            }

        result = {"operation_id": op_id, "server_time": datetime.now().isoformat()}
        _idempotency_store[op_id] = {"time": datetime.now().isoformat(), "result": result}

        return {
            "test_id": "D4",
            "success": True,
            "operation_id": op_id,
            "cached": False,
            "result": result
        }

    if name == "test_rapid_fire":
        count = min(max(args.get("count", 5), 1), 20)
        results = []
        for i in range(count):
            results.append({
                "index": i,
                "timestamp": datetime.now().isoformat(),
                "elapsed_us": int((time.time() - start_time) * 1000000)
            })
        return {
            "test_id": "D5",
            "success": True,
            "count": count,
            "results": results,
            "total_elapsed_ms": int((time.time() - start_time) * 1000),
            "note": "Rapid fire test completed"
        }

    if name == "test_empty_values":
        """D6: 测试空值边界"""
        empty_array = args.get("empty_array", [])
        empty_object = args.get("empty_object", {})
        empty_string = args.get("empty_string", "")

        return {
            "test_id": "D6",
            "success": True,
            "received": {
                "empty_array": empty_array,
                "empty_object": empty_object,
                "empty_string": empty_string
            },
            "validation": {
                "array_is_empty_list": empty_array == [],
                "object_is_empty_dict": empty_object == {},
                "string_is_empty": empty_string == "",
                "array_actual_type": type(empty_array).__name__,
                "object_actual_type": type(empty_object).__name__,
                "string_actual_type": type(empty_string).__name__
            }
        }

    if name == "test_deep_nesting":
        """D7: 测试深层嵌套对象"""
        depth = min(max(args.get("depth", 10), 1), 20)

        # 创建指定深度的嵌套对象
        def create_nested(d):
            if d <= 0:
                return {"value": "deepest"}
            return {"level": d, "nested": create_nested(d - 1)}

        test_obj = create_nested(depth)

        # 计算实际接收到的深度
        received_depth = _get_depth(args.get("test_nested", test_obj))

        return {
            "test_id": "D7",
            "success": True,
            "requested_depth": depth,
            "generated_sample": test_obj,
            "note": f"Generated nested object with depth {depth}"
        }

    if name == "test_large_array":
        """D8: 测试超大数组"""
        count = min(max(args.get("count", 1000), 1), 50000)

        # 生成大数组
        large_array = list(range(count))

        return {
            "test_id": "D8",
            "success": True,
            "requested_count": count,
            "actual_count": len(large_array),
            "first_5": large_array[:5],
            "last_5": large_array[-5:],
            "bytes_estimate": len(json.dumps(large_array)),
            "generation_time_ms": int((time.time() - start_time) * 1000)
        }

    # ===== E 超时边界探测测试 (新增) =====

    if name == "test_timeout_boundary":
        """E1: 超时边界探测"""
        duration = min(max(args.get("duration_seconds", 5), 1), 60)
        send_keepalive = args.get("send_keepalive", False)

        log.log_event("timeout_boundary_start", {
            "duration": duration,
            "send_keepalive": send_keepalive,
            "req_id": req_id
        })

        # 执行指定时长的操作
        for i in range(duration):
            await asyncio.sleep(1)
            progress = (i + 1) / duration
            if send_keepalive:
                # 发送保活通知
                log.log_notification("notifications/progress", {
                    "progressToken": f"timeout-{req_id}",
                    "progress": progress,
                    "total": 1.0,
                    "message": f"Keepalive: {i + 1}/{duration}s"
                })

        return {
            "test_id": "E1",
            "success": True,
            "duration_seconds": duration,
            "send_keepalive": send_keepalive,
            "completed": True,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "keepalive_sent": send_keepalive * duration,
            "note": "If you see this response, the operation completed within timeout"
        }

    # ===== G GUI Agent 原子工具 =====
    # 模拟 GUI Agent 的多步交互，每个工具调用都是独立的
    # LLM 可以看到每一步的结果，从而实时调整策略

    if name == "gui_screenshot":
        """G1: 获取屏幕截图"""
        app = args.get("app", "desktop")
        await asyncio.sleep(0.3)  # 模拟截图耗时

        # 模拟不同应用的屏幕状态
        app_states = {
            "desktop": {"windows": ["微信", "浏览器", "文件管理器"], "active": "微信"},
            "wechat": {"screen": "聊天列表", "contacts": ["张三", "李四", "王五"], "unread": 3},
            "browser": {"url": "https://example.com", "title": "示例网站", "scroll_position": 0},
            "notepad": {"content": "这是一段示例文本...", "cursor_position": 15}
        }

        state = app_states.get(app, app_states["desktop"])
        return {
            "success": True,
            "app": app,
            "timestamp": datetime.now().isoformat(),
            "screen_state": state,
            "resolution": "1920x1080",
            "note": f"已获取 {app} 的屏幕状态"
        }

    if name == "gui_click":
        """G2: 点击指定位置"""
        x = args.get("x", 0)
        y = args.get("y", 0)
        description = args.get("description", "")
        await asyncio.sleep(0.2)  # 模拟点击耗时

        return {
            "success": True,
            "action": "click",
            "position": {"x": x, "y": y},
            "target": description or f"位置({x}, {y})",
            "timestamp": datetime.now().isoformat(),
            "new_state": {"screen": "点击后的屏幕状态", "active_element": description or "unknown"},
            "note": f"已点击 {description or f'位置({x}, {y})'}"
        }

    if name == "gui_type":
        """G3: 输入文本"""
        text = args.get("text", "")
        enter = args.get("enter", False)
        await asyncio.sleep(0.1 + len(text) * 0.01)  # 模拟输入耗时

        return {
            "success": True,
            "action": "type",
            "text": text,
            "enter_pressed": enter,
            "timestamp": datetime.now().isoformat(),
            "input_length": len(text),
            "note": f"已输入文本: '{text}'{' + Enter' if enter else ''}"
        }

    if name == "gui_find_element":
        """G4: 查找界面元素"""
        element = args.get("element", "")
        app = args.get("app", "current")
        await asyncio.sleep(0.15)  # 模拟查找耗时

        # 模拟查找结果
        found_elements = {
            "发送按钮": {"x": 950, "y": 800, "visible": True, "enabled": True},
            "搜索框": {"x": 500, "y": 100, "visible": True, "enabled": True},
            "输入框": {"x": 500, "y": 750, "visible": True, "enabled": True},
            "联系人": {"x": 200, "y": 300, "visible": True, "enabled": True},
        }

        # 模糊匹配
        result = None
        for key, value in found_elements.items():
            if element in key or key in element:
                result = {"name": key, **value}
                break

        if result:
            return {
                "success": True,
                "found": True,
                "element": result,
                "timestamp": datetime.now().isoformat(),
                "note": f"找到元素: {result['name']} 在位置 ({result['x']}, {result['y']})"
            }
        else:
            return {
                "success": True,
                "found": False,
                "element": None,
                "searched": element,
                "note": f"未找到元素: {element}"
            }

    if name == "gui_open_app":
        """G5: 打开应用"""
        app = args.get("app", "")
        await asyncio.sleep(0.5)  # 模拟启动耗时

        supported_apps = ["微信", "浏览器", "记事本", "文件管理器", "设置"]
        is_supported = app in supported_apps

        return {
            "success": is_supported,
            "app": app,
            "opened": is_supported,
            "timestamp": datetime.now().isoformat(),
            "window_state": "maximized" if is_supported else "error",
            "note": f"已打开应用: {app}" if is_supported else f"不支持的应用: {app}"
        }

    if name == "gui_scroll":
        """G6: 滚动屏幕"""
        direction = args.get("direction", "down")
        amount = args.get("amount", 100)
        await asyncio.sleep(0.1)

        return {
            "success": True,
            "action": "scroll",
            "direction": direction,
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
            "new_position": f"滚动{amount}px",
            "note": f"已向{direction}滚动 {amount}px"
        }

    if name == "gui_wait_for_element":
        """G7: 等待元素出现"""
        element = args.get("element", "")
        timeout_ms = args.get("timeout_ms", 5000)
        simulate_found = args.get("simulate_found", True)
        await asyncio.sleep(0.3)  # 模拟等待

        return {
            "success": True,
            "element": element,
            "found": simulate_found,
            "wait_time_ms": 300,
            "timeout_ms": timeout_ms,
            "timestamp": datetime.now().isoformat(),
            "position": {"x": 500, "y": 300} if simulate_found else None,
            "note": f"元素 '{element}' 已出现" if simulate_found else f"等待超时: {element}"
        }

    if name == "gui_get_state":
        """G8: 获取当前 GUI 状态"""
        await asyncio.sleep(0.1)

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "current_app": "微信",
            "window_title": "微信 - 张三",
            "screen": "chat",
            "focus_element": "输入框",
            "mouse_position": {"x": 500, "y": 500},
            "clipboard": "",
            "note": "当前处于微信聊天界面"
        }

    if name == "gui_send_message":
        """G9: 发送消息的综合操作（演示多步流程）"""
        contact = args.get("contact", "")
        message = args.get("message", "")
        step_delay = args.get("step_delay_ms", 1000)

        # 这是一个演示工具，展示如何拆分多步操作
        # 实际应用中应该让 LLM 自己调用多个原子工具

        steps = []
        total_steps = 4

        # Step 1: 打开微信
        await asyncio.sleep(step_delay / 1000)
        steps.append({
            "step": 1,
            "action": "打开微信",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "note": "微信已打开"
        })

        # Step 2: 搜索联系人
        await asyncio.sleep(step_delay / 1000)
        steps.append({
            "step": 2,
            "action": f"搜索联系人: {contact}",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "note": f"已找到联系人: {contact}"
        })

        # Step 3: 输入消息
        await asyncio.sleep(step_delay / 1000)
        steps.append({
            "step": 3,
            "action": f"输入消息: {message}",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "note": f"已输入消息内容"
        })

        # Step 4: 发送
        await asyncio.sleep(step_delay / 1000)
        steps.append({
            "step": 4,
            "action": "点击发送按钮",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "note": "消息已发送"
        })

        return {
            "success": True,
            "task": "发送消息",
            "contact": contact,
            "message": message,
            "total_steps": total_steps,
            "steps": steps,
            "elapsed_ms": int((time.time() - start_time) * 1000),
            "note": f"消息已成功发送给 {contact}"
        }

    # ===== 服务器主动请求测试工具 =====

    if name == "test_server_elicitation":
        # 测试服务器主动发起 Elicitation 请求
        message = args.get("message", "Please provide your email address")
        requested_schema = args.get("requested_schema", {
            "type": "object",
            "properties": {
                "email": {"type": "string", "title": "Email", "format": "email"}
            },
            "required": ["email"]
        })

        # 创建服务器发起的 Elicitation 请求
        server_request = create_server_request("elicitation/create", {
            "message": message,
            "requestedSchema": requested_schema
        })

        result = {
            "test_id": "H3",
            "success": True,
            "server_request": server_request,
            "note": "Elicitation 请求已创建。客户端需轮询 server/pendingRequests 获取请求并响应。",
            "instructions": {
                "1": "客户端调用 server/pendingRequests 获取待处理请求",
                "2": "客户端处理 elicitation/create 请求并收集用户输入",
                "3": "客户端调用 server/submitResponse 提交响应"
            }
        }
        return result

    if name == "test_server_sampling":
        # 测试服务器主动发起 Sampling 请求
        prompt = args.get("prompt", "Summarize the following text")
        max_tokens = args.get("max_tokens", 500)

        # 创建服务器发起的 Sampling 请求
        server_request = create_server_request("sampling/createMessage", {
            "messages": [
                {"role": "user", "content": {"type": "text", "text": prompt}}
            ],
            "maxTokens": max_tokens,
            "modelPreferences": {
                "hints": [{"name": "claude-3-sonnet"}]
            }
        })

        result = {
            "test_id": "I3",
            "success": True,
            "server_request": server_request,
            "note": "Sampling 请求已创建。客户端需轮询 server/pendingRequests 获取请求并响应。",
            "instructions": {
                "1": "客户端调用 server/pendingRequests 获取待处理请求",
                "2": "客户端使用其 LLM 处理 sampling/createMessage 请求",
                "3": "客户端调用 server/submitResponse 提交 LLM 响应"
            }
        }
        return result

    # 未知工具
    return {
        "success": False,
        "error": f"Unknown tool: {name}",
        "error_code": -32601
    }


# ==================== P0-2: 任务增强请求辅助函数 ====================

async def execute_tool_as_task(task, tool_name: str, tool_args: Dict, request: Request, req_id: str):
    """P0-2: 后台执行工具并更新任务状态 (MCP 2025-11-25)"""
    tm = get_task_manager()
    try:
        result = await call_tool(tool_name, tool_args, request, req_id)
        await tm.complete_task(task.task_id, result)
    except Exception as e:
        await tm.fail_task(task.task_id, str(e))


def _get_depth(obj: Any, current: int = 0) -> int:
    """计算对象嵌套深度"""
    if isinstance(obj, dict) and obj:
        return max(_get_depth(v, current + 1) for v in obj.values())
    elif isinstance(obj, list) and obj:
        return max(_get_depth(v, current + 1) for v in obj)
    return current


# ==================== P2-11: 会话管理 (MCP 2025-11-25) ====================

# 活跃会话存储
_active_sessions: Dict[str, Dict] = {}

def create_session() -> str:
    """创建新会话并返回 session ID"""
    session_id = str(uuid.uuid4())
    _active_sessions[session_id] = {
        "createdAt": datetime.now().isoformat(),
        "tasks": []
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict]:
    """获取会话信息"""
    return _active_sessions.get(session_id)

def terminate_session(session_id: str) -> bool:
    """终止会话"""
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        return True
    return False


# ==================== 资源订阅管理 (MCP 2025-11-25) ====================

# 资源订阅存储: {uri: set of subscriber_ids}
_resource_subscriptions: Dict[str, set] = {}
_all_subscribers: set = set()  # 通用订阅者（订阅所有资源变更）

def subscribe_resource(uri: str, subscriber_id: str = None) -> str:
    """订阅资源变更"""
    if subscriber_id is None:
        subscriber_id = str(uuid.uuid4())
    if uri not in _resource_subscriptions:
        _resource_subscriptions[uri] = set()
    _resource_subscriptions[uri].add(subscriber_id)
    logger.info(f"Resource subscribed: {uri} by {subscriber_id}")
    return subscriber_id

def unsubscribe_resource(uri: str, subscriber_id: str) -> bool:
    """取消订阅资源变更"""
    if uri in _resource_subscriptions and subscriber_id in _resource_subscriptions[uri]:
        _resource_subscriptions[uri].discard(subscriber_id)
        logger.info(f"Resource unsubscribed: {uri} by {subscriber_id}")
        return True
    return False

def get_resource_subscribers(uri: str) -> set:
    """获取资源的订阅者"""
    return _resource_subscriptions.get(uri, set())


# ==================== 服务器主动请求框架 (MCP 2025-11-25) ====================

# 客户端能力存储（从 initialize 获取）
_client_capabilities: Dict[str, Dict] = {}

# 待发送的服务器请求队列（服务器 -> 客户端）
_pending_server_requests: List[Dict] = []

# 服务器请求的响应存储
_server_request_responses: Dict[str, Dict] = {}  # {request_id: response}

def store_client_capabilities(session_id: str, capabilities: Dict):
    """存储客户端能力"""
    _client_capabilities[session_id] = capabilities
    logger.info(f"Client capabilities stored for session {session_id}: {list(capabilities.keys())}")

def get_client_capabilities(session_id: str) -> Optional[Dict]:
    """获取客户端能力"""
    return _client_capabilities.get(session_id)

def create_server_request(method: str, params: Dict) -> Dict:
    """创建服务器发起的请求"""
    request_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    _pending_server_requests.append(request)
    logger.info(f"Server request created: {method} (id={request_id})")
    return request

def get_pending_server_requests() -> List[Dict]:
    """获取待发送的服务器请求"""
    requests = _pending_server_requests.copy()
    _pending_server_requests.clear()
    return requests

def submit_server_request_response(request_id: str, response: Dict):
    """提交服务器请求的响应"""
    _server_request_responses[request_id] = response
    logger.info(f"Server request response received: {request_id}")

def get_server_request_response(request_id: str, timeout_seconds: float = 30.0) -> Optional[Dict]:
    """等待并获取服务器请求的响应"""
    import time
    start = time.time()
    while time.time() - start < timeout_seconds:
        if request_id in _server_request_responses:
            return _server_request_responses.pop(request_id)
        time.sleep(0.1)
    return None


# ==================== HTTP 安全配置 ====================

# MCP 2025-11-25: Origin 校验允许列表
ALLOWED_ORIGINS = {
    "http://localhost",
    "http://127.0.0.1",
    "http://[::1]",
    "null",  # file:// 协议
}

# 常见本地端口
for port in range(3000, 3010):
    ALLOWED_ORIGINS.add(f"http://localhost:{port}")
    ALLOWED_ORIGINS.add(f"http://127.0.0.1:{port}")
for port in [8000, 8080, 8888, 9000]:
    ALLOWED_ORIGINS.add(f"http://localhost:{port}")
    ALLOWED_ORIGINS.add(f"http://127.0.0.1:{port}")

# 请求大小限制 (10MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024

# P1-3: 请求超时设置 (秒)
DEFAULT_REQUEST_TIMEOUT = 60  # 默认 60 秒
MAX_REQUEST_TIMEOUT = 300  # 最大 5 分钟


# ==================== 安全认证配置 (MCP 2025-11-25) ====================

import secrets
import hashlib
from pathlib import Path

# 认证模式: "none" | "api_key" | "bearer_token" | "both"
AUTH_MODE = os.environ.get("MCP_AUTH_MODE", "api_key")

# 密钥文件路径
SECRETS_FILE = Path(os.environ.get("MCP_SECRETS_FILE", "mcp_secrets.json"))

# API Keys 存储
API_KEYS: Dict[str, str] = {}

# Bearer Tokens 存储
BEARER_TOKENS: Dict[str, Dict] = {}


def load_secrets_from_file() -> Dict:
    """从密钥文件加载配置"""
    secrets_data = {"api_keys": {}, "bearer_tokens": {}}

    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                secrets_data["api_keys"] = file_data.get("api_keys", {})
                # 支持 bearer_tokens 或 bearer_tokens（兼容两种拼写）
                secrets_data["bearer_tokens"] = file_data.get("bearer_tokens") or file_data.get("bearer_tokens", {})
                logger.info(f"Loaded secrets from file: {SECRETS_FILE}")
        except Exception as e:
            logger.warning(f"Failed to load secrets file: {e}")

    return secrets_data


def load_api_keys():
    """加载 API Keys（优先环境变量，其次文件）"""
    global API_KEYS

    # 1. 从环境变量加载（格式: MCP_API_KEY_1=key1,MCP_API_KEY_2=key2 或逗号分隔）
    env_api_keys = os.environ.get("MCP_API_KEYS", "")
    if env_api_keys:
        for key in env_api_keys.split(","):
            key = key.strip()
            if key:
                API_KEYS[f"env_{hashlib.md5(key.encode()).hexdigest()[:8]}"] = hashlib.sha256(key.encode()).hexdigest()

    # 2. 从文件加载
    secrets_data = load_secrets_from_file()
    for name, key in secrets_data["api_keys"].items():
        if key:
            # 支持明文或已哈希的 key
            if len(key) == 64 and all(c in '0123456789abcdef' for c in key.lower()):
                API_KEYS[name] = key.lower()  # 已是 SHA256 哈希
            else:
                API_KEYS[name] = hashlib.sha256(key.encode()).hexdigest()

    # 3. 默认测试 Key（仅当没有任何 key 时）
    if not API_KEYS:
        default_key = "mcp_test_key_2025"
        API_KEYS["default"] = hashlib.sha256(default_key.encode()).hexdigest()
        logger.info(f"No API keys configured, using default test key: {default_key}")


def load_bearer_tokens():
    """加载 Bearer Tokens（优先环境变量，其次文件）"""
    global BEARER_TOKENS

    # 1. 从环境变量加载（逗号分隔）
    env_tokens = os.environ.get("MCP_BEARER_TOKENS", "")
    if env_tokens:
        for token in env_tokens.split(","):
            token = token.strip()
            if token:
                BEARER_TOKENS[token] = {
                    "created_at": datetime.now().isoformat(),
                    "expires_at": None,
                    "scopes": ["tools:read", "tools:execute", "resources:read", "prompts:read"],
                    "source": "env"
                }

    # 2. 从文件加载
    secrets_data = load_secrets_from_file()
    for token, token_data in secrets_data["bearer_tokens"].items():
        if token:
            if isinstance(token_data, dict):
                BEARER_TOKENS[token] = token_data
            elif token_data:  # 简单字符串，使用默认配置
                BEARER_TOKENS[token] = {
                    "created_at": datetime.now().isoformat(),
                    "expires_at": None,
                    "scopes": ["tools:read", "tools:execute", "resources:read", "prompts:read"],
                    "source": "file"
                }

    # 3. 默认测试 Token（仅当没有任何 token 时）
    if not BEARER_TOKENS:
        import secrets as secrets_module  # 避免命名冲突
        default_token = f"mcp_token_{secrets_module.token_hex(16)}"
        BEARER_TOKENS[default_token] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": None,
            "scopes": ["tools:read", "tools:execute", "resources:read", "prompts:read"],
            "source": "default"
        }
        return default_token
    return None


def init_auth():
    """初始化认证系统"""
    load_api_keys()
    default_token = load_bearer_tokens()

    # 打印认证信息
    print(f"\n{'='*60}")
    print(f"MCP Authentication Configuration")
    print(f"{'='*60}")
    print(f"  Auth Mode: {AUTH_MODE}")
    print(f"  API Keys loaded: {len(API_KEYS)}")

    if API_KEYS:
        # 显示第一个可用的测试 key（仅用于开发环境）
        if AUTH_MODE in ["api_key", "both"]:
            for name, _ in list(API_KEYS.items())[:1]:
                if name == "default":
                    print(f"  Test API Key: mcp_test_key_2025")
                break

    print(f"  Bearer Tokens loaded: {len(BEARER_TOKENS)}")
    if default_token and AUTH_MODE in ["bearer_token", "both"]:
        print(f"  Test Bearer Token: {default_token}")

    print(f"  Secrets file: {SECRETS_FILE} ({'exists' if SECRETS_FILE.exists() else 'not found'})")
    print(f"{'='*60}\n")

    return default_token


# 启动时初始化认证
_DEFAULT_TOKEN = init_auth()

# 认证豁免方法 (不需要认证)
AUTH_EXEMPT_METHODS = {
    "initialize",
    "ping",
}


def verify_api_key(api_key: str) -> bool:
    """验证 API Key"""
    if not api_key:
        return False
    hashed = hashlib.sha256(api_key.encode()).hexdigest()
    return hashed in API_KEYS.values()


def verify_bearer_token(token: str) -> Optional[Dict]:
    """验证 Bearer Token"""
    if not token:
        return None
    token_data = BEARER_TOKENS.get(token)
    if not token_data:
        return None
    # 检查过期
    if token_data.get("expires_at"):
        from datetime import datetime as dt
        if dt.fromisoformat(token_data["expires_at"]) < dt.now():
            return None
    return token_data


def extract_auth_from_request(request: Request) -> Dict:
    """从请求中提取认证信息"""
    auth_info = {
        "type": None,
        "credentials": None,
        "token_data": None
    }

    # 检查 Authorization 头
    auth_header = request.headers.get("authorization", "")
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            auth_info["type"] = "bearer"
            auth_info["credentials"] = token
            auth_info["token_data"] = verify_bearer_token(token)
        elif auth_header.lower().startswith("apikey "):
            api_key = auth_header[7:].strip()
            auth_info["type"] = "api_key"
            auth_info["credentials"] = api_key
            auth_info["valid"] = verify_api_key(api_key)

    # 检查自定义头 (X-API-Key)
    api_key_header = request.headers.get("x-api-key", "")
    if api_key_header and not auth_info["type"]:
        auth_info["type"] = "api_key"
        auth_info["credentials"] = api_key_header
        auth_info["valid"] = verify_api_key(api_key_header)

    # 检查查询参数 (仅用于测试，不推荐生产使用)
    api_key_param = request.query_params.get("api_key", "")
    if api_key_param and not auth_info["type"]:
        auth_info["type"] = "api_key"
        auth_info["credentials"] = api_key_param
        auth_info["valid"] = verify_api_key(api_key_param)

    return auth_info


def check_auth(request: Request, method: str) -> Optional[Dict]:
    """检查认证，返回错误响应或 None (认证通过)"""
    if AUTH_MODE == "none":
        return None

    # 豁免方法不需要认证
    if method in AUTH_EXEMPT_METHODS:
        return None

    auth_info = extract_auth_from_request(request)

    if AUTH_MODE == "api_key":
        if auth_info["type"] != "api_key" or not auth_info.get("valid"):
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Unauthorized: Valid API key required",
                    "data": {"auth_type": "api_key"}
                },
                "id": None
            }
    elif AUTH_MODE == "bearer_token":
        if auth_info["type"] != "bearer" or not auth_info.get("token_data"):
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Unauthorized: Valid Bearer token required",
                    "data": {"auth_type": "bearer"}
                },
                "id": None
            }
    elif AUTH_MODE == "both":
        if not ((auth_info["type"] == "api_key" and auth_info.get("valid")) or
                (auth_info["type"] == "bearer" and auth_info.get("token_data"))):
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Unauthorized: Valid API key or Bearer token required",
                    "data": {"auth_type": "api_key_or_bearer"}
                },
                "id": None
            }

    return None


def is_origin_allowed(origin: str) -> bool:
    """检查 Origin 是否被允许"""
    if not origin:
        return True  # 无 Origin 头，可能是非浏览器客户端
    # 精确匹配
    if origin in ALLOWED_ORIGINS:
        return True
    # 检查是否有端口号的变体
    origin_without_port = origin.split(":")[0] + ":" + origin.split(":")[1] if ":" in origin else origin
    return origin_without_port in ALLOWED_ORIGINS


# ==================== P2-4: SSE 消息流处理 ====================

async def handle_sse_stream(request: Request) -> Response:
    """处理 SSE 消息流请求 (支持 SEP-1699 轮询)"""
    log = get_logger()

    # 获取 Last-Event-ID 用于恢复
    last_event_id = request.headers.get("last-event-id", "")
    log.log_event("sse_stream_start", {"last_event_id": last_event_id})

    async def event_generator():
        """生成 SSE 事件流"""
        stream_id = str(uuid.uuid4())
        event_counter = 0

        # 发送初始事件(带 ID 和 retry 指令)
        initial_event = {
            "id": f"{stream_id}-0",
            "retry": 5000,  # 5 秒后重连
            "event": "connected",
            "data": {"message": "SSE stream connected", "stream_id": stream_id}
        }
        yield f"id: {initial_event['id']}\n"
        yield f"retry: {initial_event['retry']}\n"
        yield f"event: {initial_event['event']}\n"
        yield f"data: {json.dumps(initial_event['data'])}\n\n"

        # 模拟定期发送通知事件
        for i in range(5):
            await asyncio.sleep(3)  # 每 3 秒发送一次通知
            event_counter += 1
            event_id = f"{stream_id}-{event_counter}"

            notification = {
                "id": event_id,
                "event": "notification",
                "data": {
                    "message": f"Heartbeat {event_counter}",
                    "timestamp": datetime.now().isoformat()
                }
            }
            yield f"id: {event_id}\n"
            yield f"event: {notification['event']}\n"
            yield f"data: {json.dumps(notification['data'])}\n\n"

            # 发送 retry 指令 (支持 SEP-1699 轮询)
            if i < 4:  # 最后一次不发送 retry
                yield f"retry: 10000\n"

        # 发送结束事件
        final_event = {
            "id": f"{stream_id}-end",
            "event": "stream_end",
            "data": {"message": "Stream completed", "total_events": event_counter}
        }
        yield f"id: {final_event['id']}\n"
        yield f"event: {final_event['event']}\n"
        yield f"data: {json.dumps(final_event['data'])}\n\n"

    # P0-4: CORS 头使用白名单而非 *
    request_origin = request.headers.get("origin", "")
    if request_origin and is_origin_allowed(request_origin):
        cors_origin = request_origin
    else:
        cors_origin = next(iter(ALLOWED_ORIGINS), "") if ALLOWED_ORIGINS else ""

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": cors_origin
        }
    )


# ==================== HTTP 处理 ====================

async def handle_mcp_request(request: Request) -> Response:
    """处理 MCP 请求"""
    log = get_logger()

    # ===== P0-1: Origin 校验 (MCP 2025-11-25 必须实现) =====
    origin = request.headers.get("origin", "")
    if origin and not is_origin_allowed(origin):
        log.log_event("origin_rejected", {"origin": origin})
        return Response(
            json.dumps({"error": "Invalid Origin", "message": "Origin not allowed"}),
            status_code=403,
            media_type="application/json"
        )

    # ===== P0-4: 请求大小限制 =====
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
            if length > MAX_REQUEST_SIZE:
                log.log_event("request_too_large", {"content_length": length, "max": MAX_REQUEST_SIZE})
                return Response(
                    json.dumps({"error": "Payload Too Large", "message": f"Request size exceeds {MAX_REQUEST_SIZE} bytes"}),
                    status_code=413,
                    media_type="application/json"
                )
        except ValueError:
            pass

    # ===== P2-4: GET 请求处理 (SSE 消息流/轮询) =====
    if request.method == "GET":
        # SSE 消息流请求
        accept_header = request.headers.get("accept", "")
        if "text/event-stream" in accept_header:
            log.log_event("sse_stream_request", {"accept": accept_header})
            return await handle_sse_stream(request)
        # 非 SSE 的 GET 请求，返回方法信息
        return Response(
            json.dumps({"message": "MCP Server Ready", "methods": ["initialize", "tools/list", "tools/call", "resources/list", "resources/read", "prompts/list", "prompts/get", "ping"]}),
            media_type="application/json"
        )

    # 读取原始请求体
    raw_body = await request.body()
    raw_body_str = raw_body.decode("utf-8")
    raw_body_bytes = len(raw_body)

    # 记录完整 HTTP 信息
    http_info = {
        "method": request.method,
        "path": str(request.url.path),
        "query": dict(request.query_params),
        "headers": {
            "content-type": request.headers.get("content-type", ""),
            "content-length": request.headers.get("content-length", ""),
            "accept": request.headers.get("accept", ""),
            "mcp-protocol-version": request.headers.get("mcp-protocol-version", ""),
            "user-agent": request.headers.get("user-agent", ""),
            "connection": request.headers.get("connection", ""),
            "host": request.headers.get("host", ""),
            "authorization": "[REDACTED]" if request.headers.get("authorization") else None
        },
        "raw_body_bytes": raw_body_bytes,
        "client": {
            "host": request.client.host if request.client else "unknown",
            "port": request.client.port if request.client else 0
        }
    }

    # 解析请求体
    try:
        body = await request.json()
    except Exception as e:
        error_response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        log.log_event("parse_error", {"error": str(e), "raw_body": raw_body_str[:500]})
        return Response(json.dumps(error_response), status_code=400, media_type="application/json")

    # 记录原始请求（包含完整的 JSON-RPC 请求体）
    log.log_raw_request(
        str(body.get("id")),
        body.get("method", ""),
        body.get("params", {}),
        http_info,
        raw_body_str
    )

    # ===== 安全认证检查 (MCP 2025-11-25) =====
    method = body.get("method", "") if isinstance(body, dict) else ""
    auth_error = check_auth(request, method)
    if auth_error:
        log.log_event("auth_failed", {"method": method, "auth_mode": AUTH_MODE})
        return Response(json.dumps(auth_error), status_code=401, media_type="application/json")

    # 处理批量请求
    if isinstance(body, list):
        log.log_event("batch_request", {"count": len(body)})
        results = []
        for req in body:
            result = await process_single_request(req, request)
            results.append(result)
        response_str = json.dumps(results)
        return Response(response_str, media_type="application/json; charset=utf-8")

    # 处理单个请求

    # ⚠️ 先检查是否请求流式响应（在执行工具之前！）
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept and body.get("method") == "tools/call":
        tool_name = body.get("params", {}).get("name", "")
        # 支持流式响应的工具列表
        streaming_tools = [
            "test_progress_notification",
            "test_long_operation",
            "gui_send_message",  # GUI Agent 多步操作
            "gui_automation_demo"  # 新增：GUI 自动化演示
        ]
        if tool_name in streaming_tools:
            log.log_event("streaming_response", {"tool": tool_name})
            return await create_streaming_response(body, request)

    # 非流式请求才执行这里
    result = await process_single_request(body, request)

    # P2-9: 通知返回 202 Accepted 而非 200 OK (MCP 2025-11-25)
    if result is None:
        return Response(status_code=202)

    response_str = json.dumps(result, ensure_ascii=False)
    # 记录响应大小
    log.log_event("response_size", {"bytes": len(response_str.encode("utf-8"))})

    # P2-11: initialize 响应添加 MCP-Session-Id 头 (MCP 2025-11-25)
    response_headers = {"Content-Type": "application/json; charset=utf-8"}
    if body.get("method") == "initialize":
        session_id = create_session()
        response_headers["Mcp-Session-Id"] = session_id
        logger.info(f"Session created: {session_id}")
        # 存储客户端能力（用于服务器主动请求）
        client_caps = body.get("params", {}).get("capabilities", {})
        store_client_capabilities(session_id, client_caps)

    return Response(response_str, media_type="application/json; charset=utf-8", headers=response_headers)


async def process_single_request(req: Dict, request: Request) -> Dict:
    """处理单个 JSON-RPC 请求"""
    log = get_logger()
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    # 记录请求
    http_info = {
        "method": request.method,
        "path": str(request.url.path),
        "accept": request.headers.get("accept", ""),
        "mcp-protocol-version": request.headers.get("mcp-protocol-version", "")
    }
    log.log_request(str(req_id), method, params, http_info)

    logger.info(f"Processing: {method} (id={req_id})")

    # ===== Lifecycle =====

    if method == "initialize":
        result = {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                # 变更通知支持 (MCP 2025-11-25)
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
                "completions": {},  # P1-5: 添加 completions 能力声明 (MCP 2025-11-25)
                # P1-1: Tasks 支持 (MCP 2025-11-25 实验性特性)
                "tasks": {
                    "list": {},
                    "cancel": {},
                    "requests": {
                        "tools": {
                            "call": {}  # tools/call 支持任务模式
                        }
                    }
                }
                # P1-5: 移除 elicitation 和 sampling（它们是客户端能力，不应在服务器能力声明中）
            },
            "serverInfo": SERVER_INFO,
            "instructions": "MCP 2025-11-25 Full Test Server. Test IDs: A1-A5 (Core), B1-B6 (Important), C2/C5 (Advanced), D1-D5 (Boundary), E1-E7 (Timeout/Edge), G1-G10 (GUI Agent), H1-H3 (Elicitation), I1-I3 (Sampling). Methods: tools/list(paged), tools/call(task-mode), resources/subscribe, server/pendingRequests."
        }
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "notifications/initialized":
        log.log_notification("notifications/initialized", {}, "inbound")
        logger.info("Client initialized")
        return None  # 通知无响应

    # P0-3: 通知请求取消 (MCP 2025-11-25)
    if method == "notifications/cancelled":
        request_id_to_cancel = params.get("requestId")
        reason = params.get("reason", "No reason provided")
        log.log_notification("notifications/cancelled", {"requestId": request_id_to_cancel, "reason": reason})
        logger.info(f"Request {request_id_to_cancel} cancelled: {reason}")
        # 尝试取消相关任务（如果存在）
        tm = get_task_manager()
        # 注意：这里可以扩展为实际取消正在执行的任务
        return None  # 通知无响应

    if method == "ping":
        result = {"pong": True, "timestamp": datetime.now().isoformat()}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # ===== Tools =====

    if method == "tools/list":
        # P0-1: 支持分页 (cursor/nextCursor) - MCP 2025-11-25
        import base64
        cursor = params.get("cursor")

        page_size = 50  # 每页工具数
        start_idx = 0
        if cursor:
            try:
                start_idx = int(base64.urlsafe_b64decode(cursor.encode()).decode())
            except:
                start_idx = 0

        page = ALL_TOOLS[start_idx:start_idx + page_size]
        result = {"tools": page}

        if start_idx + page_size < len(ALL_TOOLS):
            next_cursor = base64.urlsafe_b64encode(str(start_idx + page_size).encode()).decode()
            result["nextCursor"] = next_cursor

        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        # P0-2: 任务增强请求模式检测 (MCP 2025-11-25)
        task_request = params.get("task")
        if task_request:
            tm = get_task_manager()
            ttl = task_request.get("ttl", 86400000)  # 默认 24 小时 (毫秒)
            task = tm.create_task("tools/call", {"name": tool_name, "arguments": tool_args}, ttl=ttl)

            # 后台执行任务
            asyncio.create_task(execute_tool_as_task(task, tool_name, tool_args, request, str(req_id)))

            result = {"task": task.to_dict()}
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        # P1-3: 获取超时设置 (MCP 2025-11-25)
        meta = params.get("_meta", {})
        timeout_seconds = meta.get("timeout", DEFAULT_REQUEST_TIMEOUT)
        timeout_seconds = min(timeout_seconds, MAX_REQUEST_TIMEOUT)  # 限制最大超时

        # P0-3: 参数验证错误作为 Tool Execution Error 返回 (MCP 2025-11-25)
        if not tool_name:
            result = {
                "content": [{"type": "text", "text": "参数验证失败: 缺少工具名称 (name)"}],
                "isError": True
            }
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        try:
            # P1-3: 使用超时包装工具调用
            tool_result = await asyncio.wait_for(
                call_tool(tool_name, tool_args, request, str(req_id)),
                timeout=timeout_seconds
            )
            result = {
                "content": [{"type": "text", "text": json.dumps(tool_result, ensure_ascii=False, indent=2)}],
                "isError": tool_result.get("success") is False
            }
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except asyncio.TimeoutError:
            # P1-3: 超时错误 - 作为 Tool Execution Error 返回
            result = {
                "content": [{"type": "text", "text": f"操作超时: 工具执行超过 {timeout_seconds} 秒限制"}],
                "isError": True
            }
            log.log_event("tool_timeout", {"tool": tool_name, "timeout": timeout_seconds})
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except ValueError as e:
            # 输入验证错误 - 作为 Tool Execution Error 返回
            result = {
                "content": [{"type": "text", "text": f"输入验证失败: {str(e)}"}],
                "isError": True
            }
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            # 其他内部错误 - 仍然作为协议错误返回
            error = {"code": -32603, "message": str(e)}
            log.log_response(str(req_id), None, error)
            return {"jsonrpc": "2.0", "id": req_id, "error": error}

    # ===== Resources =====

    if method == "resources/list":
        # MCP 2025-11-25: 支持分页 (cursor/nextCursor)
        cursor = params.get("cursor")
        import base64

        all_resources = [
            {"uri": "config://server", "name": "server", "title": "Server Configuration", "description": "Main server settings", "mimeType": "application/json"},
            {"uri": "config://database", "name": "database", "title": "Database Configuration", "description": "Database connection settings", "mimeType": "application/json"},
            {"uri": "data://sample", "name": "sample", "title": "Sample Data", "description": "Sample data for testing", "mimeType": "application/json"},
            {"uri": "status://live", "name": "live", "title": "Live Status", "description": "Real-time server status", "mimeType": "application/json"}
        ]

        # 分页实现：每页10个
        page_size = 10
        start_idx = 0
        if cursor:
            try:
                start_idx = int(base64.urlsafe_b64decode(cursor.encode()).decode())
            except:
                start_idx = 0

        page = all_resources[start_idx:start_idx + page_size]
        result = {"resources": page}

        if start_idx + page_size < len(all_resources):
            next_cursor = base64.urlsafe_b64encode(str(start_idx + page_size).encode()).decode()
            result["nextCursor"] = next_cursor

        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "resources/read":
        uri = params.get("uri", "")
        resource_data = {
            "config://server": {"host": "127.0.0.1", "port": 3372, "mode": "http"},
            "config://database": {"type": "sqlite", "path": "test.db"},
            "data://sample": {"items": [1, 2, 3], "total": 3},
            "status://live": {"uptime": 12345, "requests": log.request_counter}
        }
        if uri in resource_data:
            result = {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(resource_data[uri])}]}
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        error = {"code": -32602, "message": f"Resource not found: {uri}"}
        log.log_response(str(req_id), None, error)
        return {"jsonrpc": "2.0", "id": req_id, "error": error}

    # ===== Resource Subscriptions (MCP 2025-11-25) =====

    if method == "resources/subscribe":
        uri = params.get("uri", "")
        if not uri:
            error = {"code": -32602, "message": "URI is required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        subscriber_id = subscribe_resource(uri)
        result = {"subscribed": True, "uri": uri, "subscriptionId": subscriber_id}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "resources/unsubscribe":
        uri = params.get("uri", "")
        subscriber_id = params.get("subscriptionId", "")
        if not uri or not subscriber_id:
            error = {"code": -32602, "message": "URI and subscriptionId are required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        success = unsubscribe_resource(uri, subscriber_id)
        result = {"unsubscribed": success, "uri": uri, "subscriptionId": subscriber_id}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "resources/templates/list":
        # MCP 2025-11-25: resources/templates/list 方法 - 返回资源模板列表
        cursor = params.get("cursor")
        # 支持分页
        all_templates = [
            {
                "uriTemplate": "file:///{path}",
                "name": "file",
                "title": "File Resource",
                "description": "Access files by path",
                "mimeType": "application/octet-stream"
            },
            {
                "uriTemplate": "config://{module}",
                "name": "config_module",
                "title": "Module Configuration",
                "description": "Access module-specific configuration",
                "mimeType": "application/json"
            },
            {
                "uriTemplate": "user://{userId}/settings",
                "name": "user_settings",
                "title": "User Settings",
                "description": "Access user-specific settings",
                "mimeType": "application/json"
            }
        ]
        # 简单分页实现：每页10个
        page_size = 10
        start_idx = 0
        if cursor:
            try:
                import base64
                start_idx = int(base64.urlsafe_b64decode(cursor.encode()).decode())
            except:
                start_idx = 0

        page = all_templates[start_idx:start_idx + page_size]
        result = {"resourceTemplates": page}

        if start_idx + page_size < len(all_templates):
            import base64
            next_cursor = base64.urlsafe_b64encode(str(start_idx + page_size).encode()).decode()
            result["nextCursor"] = next_cursor

        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # ===== Prompts =====

    if method == "prompts/list":
        # MCP 2025-11-25: 支持分页 (cursor/nextCursor)
        cursor = params.get("cursor")
        import base64

        all_prompts = [
            {
                "name": "analyze_data",
                "title": "Analyze Data",
                "description": "Analyze provided data and return insights",
                "arguments": [
                    {"name": "data", "description": "Data to analyze", "required": True}
                ]
            },
            {
                "name": "summarize",
                "title": "Summarize Content",
                "description": "Summarize the provided content",
                "arguments": [
                    {"name": "content", "description": "Content to summarize", "required": True}
                ]
            }
        ]

        # 分页实现：每页10个
        page_size = 10
        start_idx = 0
        if cursor:
            try:
                start_idx = int(base64.urlsafe_b64decode(cursor.encode()).decode())
            except:
                start_idx = 0

        page = all_prompts[start_idx:start_idx + page_size]
        result = {"prompts": page}

        if start_idx + page_size < len(all_prompts):
            next_cursor = base64.urlsafe_b64encode(str(start_idx + page_size).encode()).decode()
            result["nextCursor"] = next_cursor

        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "prompts/get":
        name = params.get("name", "")
        arguments = params.get("arguments", {})  # 支持参数化模板
        # MCP 2025-11-25: content 必须是对象格式 {type: "text", text: "..."}
        prompts = {
            "analyze_data": {
                "description": "Analyze data",
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": f"Analyze this data: {arguments.get('data', 'N/A')}"}
                    }
                ]
            },
            "summarize": {
                "description": "Summarize content",
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": f"Summarize the content: {arguments.get('content', 'N/A')}"}
                    }
                ]
            }
        }
        if name in prompts:
            result = prompts[name]
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        error = {"code": -32602, "message": f"Prompt not found: {name}"}
        log.log_response(str(req_id), None, error)
        return {"jsonrpc": "2.0", "id": req_id, "error": error}

    # ===== Logging =====

    if method == "logging/setLevel":
        global _current_log_level
        level = params.get("level", "info")
        # P1-7: 验证日志级别
        if level not in LOG_LEVELS:
            error = {"code": -32602, "message": f"Invalid log level: {level}. Valid levels: {LOG_LEVELS}"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        previous = _current_log_level
        _current_log_level = level
        logger.info(f"Log level changed: {previous} -> {level}")
        result = {"level": level, "previousLevel": previous}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # ===== Completion =====

    if method == "completion/complete":
        ref = params.get("ref", {})
        argument = params.get("argument", {})
        result = {
            "completion": {
                "values": ["config://server", "config://database", "config://settings"],
                "total": 3,
                "hasMore": False
            }
        }
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}


    # ===== P1-1: Tasks 方法 (MCP 2025-11-25) =====

    tm = get_task_manager()

    if method == "tasks/list":
        cursor = params.get("cursor")
        result = await tm.list_tasks(cursor=cursor)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "tasks/get":
        task_id = params.get("taskId")
        if not task_id:
            error = {"code": -32602, "message": "Task ID is required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        task = tm.get_task(task_id)  # P1-6: 同步方法，不需要 await
        if not task:
            error = {"code": -32602, "message": f"Task not found: {task_id}"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        # P1-6: 直接返回 Task 字段，而非 {"task": {...}}
        return {"jsonrpc": "2.0", "id": req_id, "result": task.to_dict()}

    if method == "tasks/cancel":
        task_id = params.get("taskId")
        if not task_id:
            error = {"code": -32602, "message": "Task ID is required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        try:
            task = await tm.cancel_task(task_id)
            if not task:
                error = {"code": -32602, "message": f"Task not found: {task_id}"}
                return {"jsonrpc": "2.0", "id": req_id, "error": error}
            # P1-6: 直接返回 Task 字段，而非 {"task": {...}}
            return {"jsonrpc": "2.0", "id": req_id, "result": task.to_dict()}
        except ValueError as e:
            error = {"code": -32602, "message": str(e)}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        except Exception as e:
            error = {"code": -32603, "message": f"Task cancellation failed: {str(e)}"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}

    if method == "tasks/result":
        # MCP 2025-11-25: tasks/result 方法 - 获取已完成任务的结果
        # 规范要求：非终端状态时 MUST block 直到任务完成
        task_id = params.get("taskId")
        if not task_id:
            error = {"code": -32602, "message": "Task ID is required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        try:
            task = await tm.get_task(task_id)
            if not task:
                error = {"code": -32602, "message": f"Failed to retrieve task: Task not found"}
                return {"jsonrpc": "2.0", "id": req_id, "error": error}

            # 检查任务是否已完成（终端状态）
            # MCP 2025-11-25 规范要求：非终端状态 MUST block
            terminal_statuses = ("completed", "failed", "cancelled")
            if task.status not in terminal_statuses:
                # 实现阻塞等待：轮询直到任务完成或超时
                max_wait_seconds = 300  # 最大等待5分钟
                poll_interval = 1.0    # 1秒轮询间隔
                elapsed = 0
                while elapsed < max_wait_seconds:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval
                    task = await tm.get_task(task_id)
                    if not task:
                        error = {"code": -32602, "message": "Failed to retrieve task: Task has expired"}
                        return {"jsonrpc": "2.0", "id": req_id, "error": error}
                    if task.status in terminal_statuses:
                        break

                # 超时检查
                if task.status not in terminal_statuses:
                    error = {"code": -32603, "message": f"Task result retrieval timed out after {max_wait_seconds}s. Current status: {task.status}"}
                    return {"jsonrpc": "2.0", "id": req_id, "error": error}

            # 返回底层请求的结果
            result_data = task._result if hasattr(task, '_result') and task._result else {"status": task.status}
            result = {
                **result_data,
                "_meta": {
                    "io.modelcontextprotocol/related-task": {"taskId": task_id}
                }
            }
            log.log_response(str(req_id), result)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except ValueError as e:
            error = {"code": -32602, "message": f"Failed to retrieve task: {str(e)}"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        except Exception as e:
            error = {"code": -32603, "message": f"Failed to retrieve task result: {str(e)}"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}

    # ===== Elicitation (P2-1: MCP 2025-11-25) =====

    if method == "elicitation/create":
        # 模拟 Elicitation 请求 - 实际场景中这是服务器发给客户端的请求
        # 这里作为测试端点，返回模拟的 Elicitation 配置
        mode = params.get("mode", "form")
        message = params.get("message", "Please provide information")
        requested_schema = params.get("requestedSchema", {
            "type": "object",
            "properties": {
                "name": {"type": "string", "title": "Name"},
                "email": {"type": "string", "title": "Email", "format": "email"}
            },
            "required": ["name"]
        })

        elicitation_id = str(uuid.uuid4())

        result = {
            "elicitation": {
                "mode": mode,
                "elicitationId": elicitation_id,
                "message": message,
                "requestedSchema": requested_schema
            },
            "note": "Elicitation request created. In real MCP flow, this would be sent TO the client."
        }
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    # ===== Sampling (P2-2: MCP 2025-11-25 SEP-1577) =====

    if method == "sampling/createMessage":
        # 模拟 Sampling 请求 - 服务器请求客户端 LLM 生成响应
        messages = params.get("messages", [])
        model_preferences = params.get("modelPreferences", {})
        system_prompt = params.get("systemPrompt", "")
        max_tokens = params.get("maxTokens", 100)
        temperature = params.get("temperature", 0.7)
        tools = params.get("tools", [])
        tool_choice = params.get("toolChoice", {"mode": "auto"})

        # 模拟 LLM 响应
        mock_response = {
            "model": model_preferences.get("hints", [{}])[0].get("name", "claude-3-sonnet") if model_preferences else "mock-model",
            "role": "assistant",
            "content": {
                "type": "text",
                "text": f"Mock LLM response to: {messages[-1].get('content', {}).get('text', 'unknown') if messages else 'no message'}"
            },
            "stopReason": "endTurn"
        }

        # 如果有工具，模拟工具调用
        if tools and tool_choice.get("mode") != "none":
            mock_response["content"] = {
                "type": "tool_use",
                "id": f"tool-{uuid.uuid4()}",
                "name": tools[0].get("name", "mock_tool") if tools else "mock_tool",
                "input": {"query": "mock query"}
            }
            mock_response["stopReason"] = "toolUse"

        result = {
            "sampling": mock_response,
            "request_info": {
                "message_count": len(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tools_count": len(tools),
                "tool_choice": tool_choice
            },
            "note": "Sampling request simulated. In real MCP flow, this invokes client's LLM."
        }
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}


    # ===== 服务器主动请求支持 (MCP 2025-11-25) =====

    if method == "server/pendingRequests":
        """客户端轮询获取服务器发起的待处理请求"""
        pending = get_pending_server_requests()
        result = {"requests": pending, "count": len(pending)}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "server/submitResponse":
        """客户端提交对服务器请求的响应"""
        server_request_id = params.get("requestId")
        response = params.get("response", {})
        if not server_request_id:
            error = {"code": -32602, "message": "requestId is required"}
            return {"jsonrpc": "2.0", "id": req_id, "error": error}
        submit_server_request_response(server_request_id, response)
        result = {"received": True, "requestId": server_request_id}
        log.log_response(str(req_id), result)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}


    # ===== Unknown =====
    error = {"code": -32601, "message": f"Method not found: {method}"}
    log.log_response(str(req_id), None, error)
    return {"jsonrpc": "2.0", "id": req_id, "error": error}


async def create_streaming_response(req: Dict, request: Request) -> StreamingResponse:
    """创建流式响应 - 支持 GUI Agent 多步操作实时推送"""

    async def generate_stream():
        params = req.get("params", {})
        args = params.get("arguments", {})
        req_id = req.get("id")
        tool_name = params.get("name", "")

        # ⚠️ MCP 规范：使用客户端提供的 progressToken（如果有）
        _meta = params.get("_meta", {})
        progress_token = _meta.get("progressToken") or f"server-{req_id}"

        # ===== test_progress_notification =====
        if tool_name == "test_progress_notification":
            total_steps = args.get("total_steps", 5)
            step_delay = args.get("step_delay_ms", 500)

            for i in range(total_steps):
                await asyncio.sleep(step_delay / 1000)
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/progress",
                    "params": {
                        "progressToken": progress_token,
                        "progress": (i + 1) / total_steps,
                        "total": 1.0,
                        "message": f"Step {i + 1}/{total_steps}"
                    }
                }
                yield f"data: {json.dumps(notification)}\n\n"

            final_result = {"success": True, "message": "Streaming completed", "steps": total_steps}
            final = {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": "Streaming completed"}]
            }}
            yield f"data: {json.dumps(final)}\n\n"

        # ===== test_long_operation =====
        elif tool_name == "test_long_operation":
            duration = args.get("duration_seconds", 5)
            interval = args.get("progress_interval_ms", 1000)
            steps = max(1, (duration * 1000) // interval)

            for i in range(steps):
                await asyncio.sleep(interval / 1000)
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/progress",
                    "params": {
                        "progressToken": progress_token,
                        "progress": (i + 1) / steps,
                        "total": 1.0
                    }
                }
                yield f"data: {json.dumps(notification)}\n\n"

            final_result = {"success": True, "message": f"Long operation completed ({steps} steps)", "steps": steps, "duration_seconds": duration}
            final = {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"Long operation completed ({steps} steps)"}]
            }}
            yield f"data: {json.dumps(final)}\n\n"

        # ===== gui_send_message - GUI Agent 多步操作演示 =====
        elif tool_name == "gui_send_message":
            contact = args.get("contact", "张三")
            message = args.get("message", "你好")
            step_delay = args.get("step_delay_ms", 1500)  # 每步延迟

            # 定义 GUI Agent 执行步骤
            gui_steps = [
                {
                    "step": 1,
                    "action": "打开微信",
                    "detail": "点击桌面微信图标，等待应用启动",
                    "screenshot_hint": "微信主界面"
                },
                {
                    "step": 2,
                    "action": f"搜索联系人: {contact}",
                    "detail": "在搜索框输入联系人名称",
                    "screenshot_hint": f"搜索结果: {contact}"
                },
                {
                    "step": 3,
                    "action": f"点击联系人: {contact}",
                    "detail": "从搜索结果中点击目标联系人",
                    "screenshot_hint": f"与 {contact} 的聊天窗口"
                },
                {
                    "step": 4,
                    "action": "输入消息内容",
                    "detail": f"在输入框输入: {message}",
                    "screenshot_hint": "输入框中显示消息"
                },
                {
                    "step": 5,
                    "action": "点击发送按钮",
                    "detail": "点击发送，消息发出",
                    "screenshot_hint": "消息已发送状态"
                }
            ]

            total_steps = len(gui_steps)

            # 逐步执行并推送进度
            for i, step_info in enumerate(gui_steps):
                await asyncio.sleep(step_delay / 1000)

                # 发送进度通知（MCP 标准）
                progress_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/progress",
                    "params": {
                        "progressToken": progress_token,
                        "progress": (i + 1) / total_steps,
                        "total": 1.0,
                        "message": f"[{i + 1}/{total_steps}] {step_info['action']}"
                    }
                }
                yield f"data: {json.dumps(progress_notification)}\n\n"

                # 发送详细步骤通知（自定义，便于调试）
                step_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/message",
                    "params": {
                        "level": "info",
                        "data": {
                            "step": step_info["step"],
                            "action": step_info["action"],
                            "detail": step_info["detail"],
                            "screenshot": step_info["screenshot_hint"],
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                }
                yield f"data: {json.dumps(step_notification)}\n\n"

            # 最终结果
            final_result = {
                "success": True,
                "task": "发送消息",
                "contact": contact,
                "message": message,
                "total_steps": total_steps,
                "elapsed_ms": total_steps * step_delay,
                "note": f"消息已成功发送给 {contact}"
            }
            final = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(final_result, ensure_ascii=False, indent=2)}]
                }
            }
            yield f"data: {json.dumps(final)}\n\n"

        # ===== gui_automation_demo - 一次性返回所有步骤（无流式进度）=====
        elif tool_name == "gui_automation_demo":
            scenario = args.get("scenario", "notepad")

            # 一次性返回所有步骤，无流式进度
            final_result = {
                "test_id": "G7",
                "success": True,
                "scenario": scenario,
                "mode": "batch",
                "steps": [
                    "打开应用",
                    "等待启动",
                    "输入文本",
                    "保存文件",
                    "关闭应用"
                ],
                "note": "一次性返回所有步骤，无流式进度",
                "message": "自动化演示完成"
            }
            final = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(final_result, ensure_ascii=False, indent=2)}]
                }
            }
            yield f"data: {json.dumps(final)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== P2-10: DELETE 方法支持 (会话终止) ====================

async def handle_session_delete(request: Request) -> Response:
    """P2-10: 处理会话终止请求 (MCP 2025-11-25)"""
    log = get_logger()
    session_id = request.headers.get("mcp-session-id")
    log.log_event("session_terminate", {"sessionId": session_id})
    logger.info(f"Session terminated: {session_id}")
    # 清理相关任务和资源（如果有活跃会话管理）
    # 目前返回 204 No Content
    return Response(status_code=204)


# ==================== 应用 ====================

app = Starlette(
    routes=[
        Route("/mcp", handle_mcp_request, methods=["POST", "GET"]),
        Route("/mcp", handle_session_delete, methods=["DELETE"]),  # P2-10: DELETE 方法
    ]
)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP 2025-11-25 Full Test Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认启动 (API Key 认证)
  python full_test_server.py

  # 无认证模式
  python full_test_server.py --auth none

  # Bearer Token 认证
  python full_test_server.py --auth bearer

  # 自定义密钥文件
  python full_test_server.py --secrets my_keys.json

  # 环境变量 + 命令行混合
  set MCP_API_KEYS=key1,key2
  python full_test_server.py --auth api_key
        """
    )

    # 服务器配置
    parser.add_argument("--port", type=int, default=3372, help="Server port (default: 3372)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--log-dir", type=str, default=None, help="Log directory (default: ./logs)")

    # 认证配置
    parser.add_argument("--auth", "--auth-mode",
                        dest="auth_mode",
                        choices=["none", "api_key", "bearer", "both"],
                        default=None,
                        help="Authentication mode: none, api_key, bearer, both (default: api_key)")

    parser.add_argument("--secrets", "--secrets-file",
                        dest="secrets_file",
                        type=str,
                        default=None,
                        help="Path to secrets JSON file (default: mcp_secrets.json)")

    parser.add_argument("--api-keys",
                        type=str,
                        default=None,
                        help="Comma-separated API keys (overrides file)")

    parser.add_argument("--bearer-tokens",
                        type=str,
                        default=None,
                        help="Comma-separated bearer tokens (overrides file)")

    args = parser.parse_args()

    # 应用认证配置（命令行优先于环境变量）
    if args.auth_mode:
        os.environ["MCP_AUTH_MODE"] = args.auth_mode

    if args.secrets_file:
        os.environ["MCP_SECRETS_FILE"] = args.secrets_file

    if args.api_keys:
        os.environ["MCP_API_KEYS"] = args.api_keys

    if args.bearer_tokens:
        os.environ["MCP_BEARER_TOKENS"] = args.bearer_tokens

    # 设置日志目录
    if args.log_dir:
        set_log_dir(args.log_dir)

    log = get_logger()

    # 根据认证模式构建配置示例
    auth_mode = os.environ.get("MCP_AUTH_MODE", "api_key")

    # 获取一个示例凭据
    sample_api_key = None
    sample_bearer_token = None

    if API_KEYS:
        # 从文件获取明文 key（如果是默认的）
        secrets_data = load_secrets_from_file()
        for name, key in secrets_data.get("api_keys", {}).items():
            sample_api_key = key
            break
        if not sample_api_key:
            sample_api_key = "mcp_test_key_2025"  # 默认测试 key

    if BEARER_TOKENS:
        sample_bearer_token = list(BEARER_TOKENS.keys())[0]

    # 构建带认证的配置
    if auth_mode == "none":
        config_example = f'''{{
  "mcpServers": {{
    "full-test": {{
      "url": "http://{args.host}:{args.port}/mcp"
    }}
  }}
}}'''
        auth_header_info = "  认证: 无需认证"
    elif auth_mode == "api_key":
        config_example = f'''{{
  "mcpServers": {{
    "full-test": {{
      "url": "http://{args.host}:{args.port}/mcp",
      "headers": {{
        "Authorization": "ApiKey {sample_api_key}"
      }}
    }}
  }}
}}'''
        auth_header_info = f"  认证: API Key\n  示例: {sample_api_key}"
    elif auth_mode == "bearer":
        config_example = f'''{{
  "mcpServers": {{
    "full-test": {{
      "url": "http://{args.host}:{args.port}/mcp",
      "headers": {{
        "Authorization": "Bearer {sample_bearer_token}"
      }}
    }}
  }}
}}'''
        auth_header_info = f"  认证: Bearer Token\n  示例: {sample_bearer_token}"
    else:  # both
        config_example = f'''{{
  "mcpServers": {{
    "full-test": {{
      "url": "http://{args.host}:{args.port}/mcp",
      "headers": {{
        "Authorization": "ApiKey {sample_api_key}"
      }}
    }}
  }}
}}
# 或使用 Bearer Token:
# "Authorization": "Bearer {sample_bearer_token}"'''
        auth_header_info = f"  认证: API Key 或 Bearer Token\n  API Key: {sample_api_key}\n  Bearer: {sample_bearer_token}"

    print(f"""
============================================================
  MCP 2025-11-25 Full Test Server v3.1
============================================================
  URL: http://{args.host}:{args.port}/mcp
  Protocol: MCP 2025-11-25
  Log: {str(log.log_file)}
============================================================
  认证配置:
{auth_header_info}
============================================================
  测试分类:
  A1-A4: 核心能力（必测）
  B1-B11: 重要能力
  C2, C5: 高级能力
  D1-D5: 边界条件
============================================================
  阶跃配置:
{config_example}
============================================================
    """)

    logger.info(f"Starting Full Test server on {args.host}:{args.port}")
    logger.info(f"Log file: {log.log_file}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
