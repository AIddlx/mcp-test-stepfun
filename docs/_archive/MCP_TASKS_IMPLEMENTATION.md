# MCP Tasks 实现指南 (2025-11-25)

> 基于 MCP 规范 2025-11-05 版本 - 实验性功能

## 概述

Tasks 是 MCP 协议中的异步任务机制，用于处理耗时操作、批处理请求，并与外部任务 API 集成。

### 核心概念

- **Requestor**: 发送任务请求的一方（客户端或服务端）
- **Receiver**: 接收并执行任务的一方（客户端或服务端）
- **Task ID**: 由 Receiver 生成的唯一任务标识符

### 适用场景

- 耗时计算（如大文件处理、模型训练）
- 批处理操作
- 需要轮询或延迟获取结果的操作
- 与外部任务系统集成

---

## 1. Task 数据结构

### 1.1 Task 对象

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """任务状态枚举"""
    WORKING = "working"           # 正在处理
    INPUT_REQUIRED = "input_required"  # 需要请求方输入
    COMPLETED = "completed"       # 成功完成
    FAILED = "failed"             # 执行失败
    CANCELLED = "cancelled"       # 已取消


@dataclass
class Task:
    """任务状态对象"""
    task_id: str                           # 唯一标识符
    status: TaskStatus                     # 当前状态
    created_at: datetime                   # 创建时间 (ISO 8601)
    last_updated_at: datetime              # 最后更新时间 (ISO 8601)
    ttl: Optional[int] = None              # 生存时间 (毫秒)，null 表示无限
    poll_interval: Optional[int] = None    # 建议轮询间隔 (毫秒)
    status_message: Optional[str] = None   # 状态描述信息

    # 内部字段 (不暴露给 API)
    _result: Optional[Any] = field(default=None, repr=False)
    _error: Optional[Dict] = field(default=None, repr=False)
    _request_type: Optional[str] = field(default=None, repr=False)  # 如 "tools/call"
    _request_params: Optional[Dict] = field(default=None, repr=False)
    _auth_context: Optional[Any] = field(default=None, repr=False)  # 授权上下文

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


@dataclass
class TaskParams:
    """请求中的 task 参数"""
    ttl: Optional[int] = None  # 请求的任务生存时间 (毫秒)

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskParams":
        return cls(ttl=data.get("ttl"))
```

### 1.2 Task Result 对象

```python
@dataclass
class TaskResult:
    """tasks/result 返回结果"""
    task_id: str
    result: Optional[Any] = None    # 成功结果
    error: Optional[Dict] = None    # JSON-RPC 错误

    def to_response(self) -> Dict:
        """生成 JSON-RPC 响应"""
        response = {
            "_meta": {
                "io.modelcontextprotocol/related-task": {
                    "taskId": self.task_id
                }
            }
        }
        if self.error:
            # 返回原始错误
            return {"error": self.error}
        else:
            # 合并结果到响应
            if isinstance(self.result, dict):
                response.update(self.result)
            else:
                response["result"] = self.result
            return response
```

---

## 2. Task 状态生命周期

### 2.1 状态转换规则

```
                    ┌─────────────┐
                    │   working   │◄────────────┐
                    └──────┬──────┘             │
                           │                    │
            ┌──────────────┼──────────────┬─────┴──────────┐
            │              │              │                │
            ▼              ▼              ▼                ▼
    ┌───────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐
    │input_required │ │completed │ │  failed  │ │ cancelled │
    └───────┬───────┘ └──────────┘ └──────────┘ └───────────┘
            │              ▲              ▲                ▲
            │              │              │                │
            └──────────────┴──────────────┴────────────────┘
                  (terminal states - no transitions)
```

### 2.2 状态机实现

```python
from typing import Set, Tuple


class TaskStateMachine:
    """任务状态机"""

    # 有效状态转换: {from_status: {to_status_set}}
    VALID_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        TaskStatus.WORKING: {
            TaskStatus.INPUT_REQUIRED,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.INPUT_REQUIRED: {
            TaskStatus.WORKING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        # 终态不能转换
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: set(),
        TaskStatus.CANCELLED: set(),
    }

    TERMINAL_STATES = {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查状态转换是否有效"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, set())

    @classmethod
    def is_terminal(cls, status: TaskStatus) -> bool:
        """检查是否为终态"""
        return status in cls.TERMINAL_STATES

    @classmethod
    def validate_transition(cls, task: Task, new_status: TaskStatus) -> None:
        """验证状态转换，无效时抛出异常"""
        if not cls.can_transition(task.status, new_status):
            raise ValueError(
                f"Invalid transition from '{task.status.value}' to '{new_status.value}'"
            )
```

---

## 3. Capability 声明

### 3.1 服务端 Capability

```python
# 服务端声明支持 tasks
SERVER_TASKS_CAPABILITY = {
    "capabilities": {
        "tasks": {
            "list": {},       # 支持 tasks/list
            "cancel": {},     # 支持 tasks/cancel
            "requests": {
                "tools": {
                    "call": {}  # tools/call 支持任务模式
                }
            }
        }
    }
}
```

### 3.2 客户端 Capability

```python
# 客户端声明支持 tasks
CLIENT_TASKS_CAPABILITY = {
    "capabilities": {
        "tasks": {
            "list": {},
            "cancel": {},
            "requests": {
                "sampling": {
                    "createMessage": {}
                },
                "elicitation": {
                    "create": {}
                }
            }
        }
    }
}
```

### 3.3 Tool 级别配置

```python
from enum import Enum


class TaskSupport(str, Enum):
    """工具的任务支持级别"""
    REQUIRED = "required"    # 必须使用任务模式
    OPTIONAL = "optional"    # 可选任务模式
    FORBIDDEN = "forbidden"  # 禁止任务模式


# 在 tools/list 响应中
def get_tool_definition():
    return {
        "name": "long_running_analysis",
        "description": "执行长时间分析",
        "inputSchema": {...},
        "execution": {
            "taskSupport": "optional"  # 或 "required" / "forbidden"
        }
    }
```

---

## 4. 协议消息实现

### 4.1 创建任务 (Create Task)

```python
import asyncio
from datetime import datetime, timezone


class TaskManager:
    """任务管理器"""

    def __init__(self, max_ttl: int = 86400000, max_concurrent: int = 100):
        self._tasks: Dict[str, Task] = {}
        self._max_ttl = max_ttl  # 最大 TTL (毫秒)
        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        request_type: str,
        request_params: Dict,
        task_params: Optional[TaskParams] = None,
        auth_context: Any = None,
    ) -> Task:
        """创建新任务"""
        async with self._lock:
            # 检查并发限制
            if len(self._tasks) >= self._max_concurrent:
                raise ValueError("Maximum concurrent tasks exceeded")

            # 生成安全的 Task ID
            task_id = self._generate_task_id()

            # 确定 TTL
            requested_ttl = task_params.ttl if task_params else None
            ttl = min(requested_ttl or self._max_ttl, self._max_ttl)

            now = datetime.now(timezone.utc)

            task = Task(
                task_id=task_id,
                status=TaskStatus.WORKING,
                created_at=now,
                last_updated_at=now,
                ttl=ttl,
                poll_interval=5000,  # 默认 5 秒
                _request_type=request_type,
                _request_params=request_params,
                _auth_context=auth_context,
            )

            self._tasks[task_id] = task
            return task

    def _generate_task_id(self) -> str:
        """生成加密安全的 Task ID"""
        return str(uuid.uuid4())
```

### 4.2 获取任务 (tasks/get)

```python
    async def get_task(self, task_id: str, auth_context: Any = None) -> Task:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        # 检查授权上下文
        if auth_context and task._auth_context != auth_context:
            raise TaskAccessDeniedError("Access denied")

        # 检查 TTL 是否过期
        if self._is_expired(task):
            del self._tasks[task_id]
            raise TaskExpiredError(f"Task has expired: {task_id}")

        return task

    def _is_expired(self, task: Task) -> bool:
        """检查任务是否过期"""
        if task.ttl is None:
            return False
        elapsed = (datetime.now(timezone.utc) - task.created_at).total_seconds() * 1000
        return elapsed > task.ttl
```

### 4.3 获取任务结果 (tasks/result)

```python
    async def get_task_result(
        self,
        task_id: str,
        auth_context: Any = None,
        timeout: float = 300.0,  # 阻塞超时
    ) -> TaskResult:
        """获取任务结果（可能阻塞）"""
        task = await self.get_task(task_id, auth_context)

        # 如果任务未完成，阻塞等待
        if not TaskStateMachine.is_terminal(task.status):
            await self._wait_for_completion(task, timeout)

        return TaskResult(
            task_id=task.task_id,
            result=task._result,
            error=task._error,
        )

    async def _wait_for_completion(self, task: Task, timeout: float) -> None:
        """等待任务完成"""
        start_time = asyncio.get_event_loop().time()

        while not TaskStateMachine.is_terminal(task.status):
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise asyncio.TimeoutError("Timeout waiting for task completion")
            await asyncio.sleep(0.5)  # 轮询间隔
```

### 4.4 列出任务 (tasks/list)

```python
@dataclass
class TaskListResult:
    """任务列表结果"""
    tasks: List[Task]
    next_cursor: Optional[str] = None


    async def list_tasks(
        self,
        auth_context: Any = None,
        cursor: Optional[str] = None,
        page_size: int = 50,
    ) -> TaskListResult:
        """列出任务（支持分页）"""
        # 过滤授权上下文匹配的任务
        filtered_tasks = [
            task for task in self._tasks.values()
            if not auth_context or task._auth_context == auth_context
        ]

        # 按 created_at 排序
        filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 游标分页
        start_idx = 0
        if cursor:
            start_idx = self._decode_cursor(cursor)

        end_idx = start_idx + page_size
        page = filtered_tasks[start_idx:end_idx]

        next_cursor = None
        if end_idx < len(filtered_tasks):
            next_cursor = self._encode_cursor(end_idx)

        return TaskListResult(tasks=page, next_cursor=next_cursor)

    def _encode_cursor(self, index: int) -> str:
        """编码游标"""
        import base64
        return base64.urlsafe_b64encode(str(index).encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """解码游标"""
        import base64
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
```

### 4.5 取消任务 (tasks/cancel)

```python
    async def cancel_task(self, task_id: str, auth_context: Any = None) -> Task:
        """取消任务"""
        task = await self.get_task(task_id, auth_context)

        # 检查是否为终态
        if TaskStateMachine.is_terminal(task.status):
            raise ValueError(
                f"Cannot cancel task: already in terminal status '{task.status.value}'"
            )

        # 更新状态
        task.status = TaskStatus.CANCELLED
        task.status_message = "The task was cancelled by request."
        task.last_updated_at = datetime.now(timezone.utc)

        return task
```

---

## 5. 状态通知

### 5.1 发送通知

```python
class TaskNotificationSender:
    """任务状态通知发送器"""

    def __init__(self, send_notification_callback):
        self._send_notification = send_notification_callback

    async def send_status_notification(self, task: Task) -> None:
        """发送任务状态变更通知"""
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tasks/status",
            "params": task.to_dict(),
        }
        await self._send_notification(notification)
```

### 5.2 在任务状态变更时触发

```python
    async def _update_task_status(
        self,
        task: Task,
        new_status: TaskStatus,
        status_message: Optional[str] = None,
        send_notification: bool = True,
    ) -> None:
        """更新任务状态"""
        TaskStateMachine.validate_transition(task, new_status)

        task.status = new_status
        task.status_message = status_message
        task.last_updated_at = datetime.now(timezone.utc)

        if send_notification and self._notification_sender:
            await self._notification_sender.send_status_notification(task)
```

---

## 6. 存储和 TTL 管理

### 6.1 内存存储实现

```python
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class InMemoryTaskStore:
    """内存任务存储"""

    def __init__(self, cleanup_interval: int = 60000):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = cleanup_interval

    async def start(self) -> None:
        """启动清理任务"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """停止清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """定期清理过期任务"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval / 1000)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired(self) -> int:
        """清理过期任务"""
        async with self._lock:
            expired = [
                task_id for task_id, task in self._tasks.items()
                if self._is_expired(task)
            ]
            for task_id in expired:
                del self._tasks[task_id]
                logger.debug(f"Cleaned up expired task: {task_id}")
            return len(expired)

    def _is_expired(self, task: Task) -> bool:
        if task.ttl is None:
            return False
        elapsed = (datetime.now(timezone.utc) - task.created_at).total_seconds() * 1000
        return elapsed > task.ttl

    async def save(self, task: Task) -> None:
        async with self._lock:
            self._tasks[task.task_id] = task

    async def load(self, task_id: str) -> Optional[Task]:
        async with self._lock:
            return self._tasks.get(task_id)

    async def delete(self, task_id: str) -> bool:
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    async def list_all(self) -> List[Task]:
        async with self._lock:
            return list(self._tasks.values())
```

### 6.2 Redis 存储实现（生产环境推荐）

```python
import json
import redis.asyncio as redis
from typing import Optional, List


class RedisTaskStore:
    """Redis 任务存储"""

    def __init__(self, redis_url: str, key_prefix: str = "mcp:task:"):
        self._redis = redis.from_url(redis_url)
        self._key_prefix = key_prefix

    def _task_key(self, task_id: str) -> str:
        return f"{self._key_prefix}{task_id}"

    def _task_list_key(self, auth_context: str) -> str:
        return f"{self._key_prefix}list:{auth_context}"

    async def save(self, task: Task) -> None:
        """保存任务，自动设置 TTL"""
        key = self._task_key(task.task_id)
        data = {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "last_updated_at": task.last_updated_at.isoformat(),
            "ttl": task.ttl,
            "poll_interval": task.poll_interval,
            "status_message": task.status_message,
            "result": task._result,
            "error": task._error,
            "request_type": task._request_type,
            "request_params": task._request_params,
            "auth_context": str(task._auth_context) if task._auth_context else None,
        }

        # Redis TTL 使用秒为单位
        redis_ttl = (task.ttl or 86400000) // 1000

        async with self._redis.pipeline() as pipe:
            pipe.setex(key, redis_ttl, json.dumps(data))
            # 如果有授权上下文，也添加到列表
            if task._auth_context:
                list_key = self._task_list_key(str(task._auth_context))
                pipe.sadd(list_key, task.task_id)
                pipe.expire(list_key, redis_ttl)
            await pipe.execute()

    async def load(self, task_id: str) -> Optional[Task]:
        """加载任务"""
        key = self._task_key(task_id)
        data = await self._redis.get(key)
        if not data:
            return None

        parsed = json.loads(data)
        return self._deserialize_task(parsed)

    async def delete(self, task_id: str) -> bool:
        """删除任务"""
        key = self._task_key(task_id)
        result = await self._redis.delete(key)
        return result > 0

    async def list_by_auth(self, auth_context: str) -> List[Task]:
        """列出特定授权上下文的所有任务"""
        list_key = self._task_list_key(auth_context)
        task_ids = await self._redis.smembers(list_key)

        tasks = []
        for task_id in task_ids:
            task = await self.load(task_id.decode())
            if task:
                tasks.append(task)
        return tasks

    def _deserialize_task(self, data: Dict) -> Task:
        """反序列化任务"""
        task = Task(
            task_id=data["task_id"],
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated_at=datetime.fromisoformat(data["last_updated_at"]),
            ttl=data.get("ttl"),
            poll_interval=data.get("poll_interval"),
            status_message=data.get("status_message"),
        )
        task._result = data.get("result")
        task._error = data.get("error")
        task._request_type = data.get("request_type")
        task._request_params = data.get("request_params")
        return task
```

---

## 7. 完整服务端实现示例

```python
import asyncio
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# 错误类型
class TaskError(Exception):
    pass


class TaskNotFoundError(TaskError):
    pass


class TaskExpiredError(TaskError):
    pass


class TaskAccessDeniedError(TaskError):
    pass


@dataclass
class JSONRPCError:
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict:
        result = {"code": self.code, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result


class MCPTaskServer:
    """MCP 任务服务端"""

    def __init__(self):
        self.task_manager = TaskManager()
        self.task_store = InMemoryTaskStore()
        self._running_executors: Dict[str, asyncio.Task] = {}

    async def handle_request(
        self,
        method: str,
        params: Dict,
        auth_context: Any = None,
    ) -> Dict:
        """处理 JSON-RPC 请求"""
        try:
            if method == "tasks/get":
                return await self._handle_tasks_get(params, auth_context)
            elif method == "tasks/list":
                return await self._handle_tasks_list(params, auth_context)
            elif method == "tasks/result":
                return await self._handle_tasks_result(params, auth_context)
            elif method == "tasks/cancel":
                return await self._handle_tasks_cancel(params, auth_context)
            elif method == "tools/call":
                return await self._handle_tools_call(params, auth_context)
            else:
                raise JSONRPCError(-32601, f"Method not found: {method}")

        except TaskNotFoundError as e:
            raise JSONRPCError(-32602, f"Failed to retrieve task: {str(e)}")
        except TaskExpiredError as e:
            raise JSONRPCError(-32602, f"Failed to retrieve task: {str(e)}")
        except TaskAccessDeniedError:
            raise JSONRPCError(-32602, "Access denied")
        except JSONRPCError:
            raise
        except Exception as e:
            logger.exception("Internal error")
            raise JSONRPCError(-32603, f"Internal error: {str(e)}")

    async def _handle_tasks_get(self, params: Dict, auth_context: Any) -> Dict:
        """处理 tasks/get"""
        task_id = params.get("taskId")
        if not task_id:
            raise JSONRPCError(-32602, "Missing taskId")

        task = await self.task_manager.get_task(task_id, auth_context)
        return task.to_dict()

    async def _handle_tasks_list(self, params: Dict, auth_context: Any) -> Dict:
        """处理 tasks/list"""
        cursor = params.get("cursor")
        result = await self.task_manager.list_tasks(auth_context, cursor)
        return {
            "tasks": [t.to_dict() for t in result.tasks],
            "nextCursor": result.next_cursor,
        }

    async def _handle_tasks_result(self, params: Dict, auth_context: Any) -> Dict:
        """处理 tasks/result"""
        task_id = params.get("taskId")
        if not task_id:
            raise JSONRPCError(-32602, "Missing taskId")

        result = await self.task_manager.get_task_result(task_id, auth_context)
        return result.to_response()

    async def _handle_tasks_cancel(self, params: Dict, auth_context: Any) -> Dict:
        """处理 tasks/cancel"""
        task_id = params.get("taskId")
        if not task_id:
            raise JSONRPCError(-32602, "Missing taskId")

        task = await self.task_manager.cancel_task(task_id, auth_context)

        # 取消执行中的协程
        if task_id in self._running_executors:
            self._running_executors[task_id].cancel()

        return task.to_dict()

    async def _handle_tools_call(self, params: Dict, auth_context: Any) -> Dict:
        """处理 tools/call（支持任务模式）"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # 检查是否请求任务模式
        task_params_data = params.get("task")
        if task_params_data:
            # 任务模式
            task_params = TaskParams.from_dict(task_params_data)
            task = await self.task_manager.create_task(
                request_type="tools/call",
                request_params={"name": tool_name, "arguments": arguments},
                task_params=task_params,
                auth_context=auth_context,
            )

            # 启动异步执行
            executor = asyncio.create_task(
                self._execute_tool(task, tool_name, arguments)
            )
            self._running_executors[task.task_id] = executor

            return {"task": task.to_dict()}
        else:
            # 同步模式
            return await self._execute_tool_sync(tool_name, arguments)

    async def _execute_tool(self, task: Task, tool_name: str, arguments: Dict) -> None:
        """异步执行工具"""
        try:
            result = await self._execute_tool_sync(tool_name, arguments)

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task._result = result
            task.last_updated_at = datetime.now(timezone.utc)

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.status_message = "Task was cancelled"
            task.last_updated_at = datetime.now(timezone.utc)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.status_message = str(e)
            task._error = {"code": -32603, "message": str(e)}
            task.last_updated_at = datetime.now(timezone.utc)

        finally:
            self._running_executors.pop(task.task_id, None)

    async def _execute_tool_sync(self, tool_name: str, arguments: Dict) -> Dict:
        """同步执行工具（子类实现）"""
        # 示例：模拟长时间运行
        if tool_name == "long_analysis":
            await asyncio.sleep(10)  # 模拟耗时操作
            return {
                "content": [{"type": "text", "text": "Analysis complete"}],
                "isError": False,
            }

        raise JSONRPCError(-32601, f"Unknown tool: {tool_name}")

    async def start(self) -> None:
        """启动服务"""
        await self.task_store.start()

    async def stop(self) -> None:
        """停止服务"""
        await self.task_store.stop()
        # 取消所有执行中的任务
        for executor in self._running_executors.values():
            executor.cancel()


# 使用示例
async def main():
    server = MCPTaskServer()
    await server.start()

    try:
        # 模拟创建任务
        result = await server.handle_request(
            "tools/call",
            {
                "name": "long_analysis",
                "arguments": {"data": "sample"},
                "task": {"ttl": 60000},
            },
            auth_context="user123",
        )
        print(f"Created task: {result}")

        task_id = result["task"]["taskId"]

        # 轮询任务状态
        while True:
            status = await server.handle_request(
                "tasks/get",
                {"taskId": task_id},
                auth_context="user123",
            )
            print(f"Task status: {status['status']}")

            if status["status"] in ["completed", "failed", "cancelled"]:
                break

            await asyncio.sleep(5)

        # 获取结果
        final_result = await server.handle_request(
            "tasks/result",
            {"taskId": task_id},
            auth_context="user123",
        )
        print(f"Final result: {final_result}")

    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. 与 Progress Notifications 的关系

任务模式完全兼容进度通知。`progressToken` 在整个任务生命周期内保持有效。

```python
@dataclass
class ProgressToken:
    """进度令牌"""
    token: str
    task_id: str


async def send_progress(
    task: Task,
    progress: float,
    total: Optional[float] = None,
    message: Optional[str] = None,
) -> None:
    """发送进度通知"""
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/progress",
        "params": {
            "progressToken": task.task_id,  # 或单独的 token
            "progress": progress,
            "_meta": {
                "io.modelcontextprotocol/related-task": {
                    "taskId": task.task_id
                }
            }
        }
    }
    if total is not None:
        notification["params"]["total"] = total
    if message:
        notification["params"]["message"] = message

    # 发送通知...
```

---

## 9. 安全注意事项

### 9.1 Task ID 生成

```python
import secrets
import uuid


def generate_secure_task_id() -> str:
    """生成加密安全的 Task ID"""
    # 方案 1: UUID v4 (推荐)
    return str(uuid.uuid4())

    # 方案 2: 更高熵 (无授权场景)
    # return secrets.token_urlsafe(32)
```

### 9.2 授权上下文绑定

```python
async def validate_task_access(
    task: Task,
    auth_context: Any,
) -> None:
    """验证任务访问权限"""
    if task._auth_context is None:
        # 无授权上下文的任务，允许访问但记录警告
        logger.warning(f"Accessing task without auth context: {task.task_id}")
        return

    if task._auth_context != auth_context:
        raise TaskAccessDeniedError("Task does not belong to this authorization context")
```

### 9.3 速率限制

```python
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimiter:
    """任务操作速率限制器"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window = timedelta(seconds=window_seconds)
        self._requests: Dict[str, list] = defaultdict(list)

    async def check_rate_limit(self, auth_context: str) -> bool:
        """检查是否超过速率限制"""
        now = datetime.now()
        requests = self._requests[auth_context]

        # 清理过期请求
        requests[:] = [r for r in requests if now - r < self._window]

        if len(requests) >= self._max_requests:
            return False

        requests.append(now)
        return True
```

---

## 10. 最佳实践

### 10.1 Requestor (客户端) 最佳实践

1. **始终检查 Capability**: 在创建任务前检查服务端是否支持
2. **尊重 pollInterval**: 使用服务端建议的轮询间隔
3. **处理 input_required**: 当状态为 input_required 时调用 tasks/result
4. **不要依赖通知**: 通知是可选的，应该继续轮询
5. **设置合理的 TTL**: 根据任务预期时长设置

### 10.2 Receiver (服务端) 最佳实践

1. **快速响应**: 立即返回 CreateTaskResult
2. **实现 TTL 清理**: 定期清理过期任务
3. **限制并发**: 防止资源耗尽
4. **生成安全 ID**: 使用加密安全的随机数
5. **记录审计日志**: 记录任务生命周期事件

### 10.3 错误处理

```python
# 客户端轮询示例
async def poll_task_until_complete(
    server: MCPTaskServer,
    task_id: str,
    auth_context: str,
    max_attempts: int = 100,
) -> Dict:
    """轮询任务直到完成"""
    attempts = 0

    while attempts < max_attempts:
        try:
            status = await server.handle_request(
                "tasks/get",
                {"taskId": task_id},
                auth_context=auth_context,
            )

            if status["status"] == "input_required":
                # 需要处理输入请求
                result = await server.handle_request(
                    "tasks/result",
                    {"taskId": task_id},
                    auth_context=auth_context,
                )
                # 处理 elicitation/sampling 请求...
                continue

            if status["status"] in ["completed", "failed", "cancelled"]:
                return await server.handle_request(
                    "tasks/result",
                    {"taskId": task_id},
                    auth_context=auth_context,
                )

            # 使用建议的轮询间隔
            poll_interval = status.get("pollInterval", 5000)
            await asyncio.sleep(poll_interval / 1000)
            attempts += 1

        except TaskExpiredError:
            raise TimeoutError("Task expired before completion")
        except TaskNotFoundError:
            raise ValueError("Task not found")

    raise TimeoutError("Max polling attempts exceeded")
```

---

## 附录: JSON-RPC 错误码

| 错误码 | 名称 | 使用场景 |
|--------|------|----------|
| -32600 | Invalid Request | 非 task-augmented 请求但 receiver 要求任务模式 |
| -32601 | Method not found | 不支持的 task 方法或工具 |
| -32602 | Invalid params | 无效/不存在的 taskId、游标，或尝试取消终态任务 |
| -32603 | Internal error | 服务器内部错误 |

---

## 参考资料

- [MCP Specification 2025-11-25 - Tasks](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks)
- [MCP Specification - Progress](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress)
