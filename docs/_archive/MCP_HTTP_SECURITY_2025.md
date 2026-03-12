# MCP 2025-11-25 HTTP 传输层安全实现指南

> 基于 MCP 规范版本 2025-11-25

## 目录

1. [HTTP 403 Origin 校验](#1-http-403-origin-校验)
2. [OAuth 2.0/2.1 增强](#2-oauth-2021-增强)
3. [SSE 轮询支持 (SEP-1699)](#3-sse-轮询支持-sep-1699)
4. [安全最佳实践](#4-安全最佳实践)
5. [Python/Starlette 实现示例](#5-pythonstarlette-实现示例)

---

## 1. HTTP 403 Origin 校验

### 1.1 规范要求

根据 MCP 2025-11-25 规范，Streamable HTTP 传输层 **必须** 校验 `Origin` 头：

> Servers **MUST** validate the `Origin` header on all incoming connections to prevent DNS rebinding attacks.
> - If the `Origin` header is present and invalid, servers **MUST** respond with HTTP 403 Forbidden.

### 1.2 DNS 重绑定攻击原理

```
攻击流程:
1. 攻击者注册域名 evil.com
2. 配置 DNS 服务器，初始解析到合法 IP (如 93.184.216.34)
3. 诱导用户访问 evil.com 上的恶意页面
4. 页面加载后，攻击者快速将 DNS 解析到本地 IP (如 127.0.0.1)
5. 浏览器发起请求到本地 MCP 服务器，携带恶意 Origin
6. 如果服务器不校验 Origin，攻击者可访问本地资源
```

### 1.3 Origin 校验逻辑

```
Origin 校验决策树:

请求到达
    |
    v
Origin 头是否存在?
    |
    +-- 否 --> 允许请求 (可能是非浏览器客户端)
    |
    +-- 是 --> Origin 是否在允许列表?
                    |
                    +-- 是 --> 允许请求
                    |
                    +-- 否 --> 返回 HTTP 403 Forbidden
```

### 1.4 允许的 Origin 列表

对于本地 MCP 服务器，推荐的允许列表：

```python
ALLOWED_ORIGINS = {
    # 本地开发
    "http://localhost",
    "http://127.0.0.1",
    "http://[::1]",

    # 常见本地端口
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",

    # null origin (file:// 协议)
    "null",
}
```

---

## 2. OAuth 2.0/2.1 增强

### 2.1 OpenID Connect Discovery 1.0 支持 (PR #797)

MCP 2025-11-25 新增 OIDC Discovery 作为授权服务器元数据发现机制。

#### 发现顺序

对于带路径的 issuer URL (如 `https://auth.example.com/tenant1`)：

```
优先级:
1. OAuth 2.0 Authorization Server Metadata (path insertion):
   https://auth.example.com/.well-known/oauth-authorization-server/tenant1

2. OpenID Connect Discovery 1.0 (path insertion):
   https://auth.example.com/.well-known/openid-configuration/tenant1

3. OpenID Connect Discovery 1.0 (path appending):
   https://auth.example.com/tenant1/.well-known/openid-configuration
```

对于不带路径的 issuer URL (如 `https://auth.example.com`)：

```
优先级:
1. https://auth.example.com/.well-known/oauth-authorization-server
2. https://auth.example.com/.well-known/openid-configuration
```

### 2.2 OAuth Client ID Metadata Documents (SEP-991, PR #1296)

CIMD 是 MCP 2025-11-25 中最重要的变更，解决了客户端与服务器无预存关系的场景。

#### 工作原理

```
1. 客户端在 HTTPS URL 托管元数据文档
   例如: https://app.example.com/oauth/client-metadata.json

2. 授权请求中使用 URL 作为 client_id
   client_id=https://app.example.com/oauth/client-metadata.json

3. 授权服务器获取并验证元数据文档

4. 验证成功后继续授权流程
```

#### 元数据文档示例

```json
{
  "client_id": "https://app.example.com/oauth/client-metadata.json",
  "client_name": "Example MCP Client",
  "client_uri": "https://app.example.com",
  "logo_uri": "https://app.example.com/logo.png",
  "redirect_uris": [
    "http://127.0.0.1:3000/callback",
    "http://localhost:3000/callback"
  ],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

#### 客户端注册优先级

```
1. 使用预注册的客户端信息（如果可用）
2. 使用 CIMD（如果 AS 支持 client_id_metadata_document_supported: true）
3. 使用 DCR（如果 AS 支持 registration_endpoint）
4. 提示用户输入客户端信息
```

### 2.3 WWW-Authenticate 增量授权 (SEP-835)

支持在运行时请求额外权限，避免一次性请求过多权限。

#### 403 响应示例

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope",
                         scope="files:read files:write user:profile",
                         resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource",
                         error_description="Additional file write permission required"
```

#### Step-Up Authorization Flow

```
客户端发起请求 (token with scope: files:read)
    |
    v
服务器检测权限不足
    |
    v
返回 403 + WWW-Authenticate (scope=files:read files:write)
    |
    v
客户端解析错误信息
    |
    v
客户端重新发起授权请求 (scope=files:read files:write)
    |
    v
用户授权新权限
    |
    v
客户端获取新 token
    |
    v
使用新 token 重试原请求
```

---

## 3. SSE 轮询支持 (SEP-1699)

### 3.1 问题背景

原规范要求服务器在发送响应前保持连接，导致：
- 长时间运行的请求占用连接资源
- 代理/负载均衡器超时问题
- 扩展性受限

### 3.2 SEP-1699 解决方案

服务器可以主动断开连接，客户端使用 `Last-Event-ID` 重连。

#### 服务器行为

```
1. 开始 SSE 流时，立即发送带 id 的空事件:
   id: event-123
   data:

2. 服务器可在任意时刻断开连接

3. 断开前应发送 retry 字段:
   id: event-124
   retry: 5000
   data: {"status": "processing"}
```

#### 客户端行为

```
1. 收到断开后，等待 retry 毫秒

2. 发起重连请求 (GET):
   GET /mcp HTTP/1.1
   Last-Event-ID: event-124
   Accept: text/event-stream

3. 服务器根据 Last-Event-ID 恢复流
```

### 3.3 GET Streams 支持轮询

独立的 GET 通知流同样支持轮询：

```
GET /mcp HTTP/1.1
Accept: text/event-stream

<-- 服务器响应 -->
HTTP/1.1 200 OK
Content-Type: text/event-stream

id: notify-1
retry: 10000
data: {"method": "notifications/progress", ...}

<-- 服务器断开 -->
<-- 客户端等待 10 秒后重连 -->
GET /mcp HTTP/1.1
Last-Event-ID: notify-1
Accept: text/event-stream
```

---

## 4. 安全最佳实践

### 4.1 传输层安全清单

| 要求 | 优先级 | 说明 |
|------|--------|------|
| Origin 头校验 | MUST | 防止 DNS 重绑定攻击 |
| 本地绑定 127.0.0.1 | SHOULD | 本地服务器不监听 0.0.0.0 |
| HTTPS 强制 | MUST | 所有端点必须 HTTPS |
| Token 验证 | MUST | 验证 token audience |
| PKCE 使用 | MUST | 公共客户端必须使用 PKCE |

### 4.2 CIMD 安全注意事项

#### SSRF 防护

```python
# 验证 URL 格式
def validate_metadata_url(url: str) -> bool:
    parsed = urlparse(url)

    # 必须是 HTTPS
    if parsed.scheme != "https":
        return False

    # 必须包含路径
    if not parsed.path or parsed.path == "/":
        return False

    # 禁止私有 IP 地址
    hostname = parsed.hostname
    if is_private_ip(hostname):
        return False

    return True
```

#### Localhost 重定向风险

CIMD 无法完全防止 localhost 重定向攻击。建议：
- 对 localhost-only 客户端显示额外警告
- 清晰显示重定向 URI 主机名
- 考虑额外认证机制

### 4.3 Token 安全

```
MUST:
- 使用 Authorization: Bearer <token> 头
- 不在 URI 查询字符串中传递 token
- 验证 token audience 与当前服务器匹配
- 不转发 token 到下游服务

SHOULD:
- 使用短期 token
- 实现 token 刷新轮换
- 安全存储 token
```

---

## 5. Python/Starlette 实现示例

### 5.1 Origin 校验中间件

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Set
import logging

logger = logging.getLogger(__name__)


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """
    MCP Origin 校验中间件

    根据 MCP 2025-11-25 规范：
    - 必须校验所有传入连接的 Origin 头
    - 如果 Origin 头存在且无效，必须返回 HTTP 403
    """

    def __init__(self, app, allowed_origins: Set[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or self._default_origins()

    def _default_origins(self) -> Set[str]:
        """默认允许的 Origin 列表"""
        return {
            # 本地开发
            "http://localhost",
            "http://127.0.0.1",
            "http://[::1]",
            # 常见本地端口
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:5000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            # file:// 协议
            "null",
        }

    def _normalize_origin(self, origin: str) -> str:
        """标准化 Origin（移除尾部斜杠）"""
        return origin.rstrip("/")

    def _is_origin_allowed(self, origin: str) -> bool:
        """检查 Origin 是否在允许列表"""
        normalized = self._normalize_origin(origin)

        # 精确匹配
        if normalized in self.allowed_origins:
            return True

        # 检查是否匹配任何允许的 Origin 的端口变体
        for allowed in self.allowed_origins:
            if normalized.startswith(allowed):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # 如果没有 Origin 头，允许请求（非浏览器客户端）
        if origin is None:
            return await call_next(request)

        # 校验 Origin
        if not self._is_origin_allowed(origin):
            logger.warning(
                f"Origin validation failed: {origin} not in allowed list"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Origin header"
                    }
                },
                headers={
                    "Content-Type": "application/json"
                }
            )

        return await call_next(request)


# 使用示例
from starlette.applications import Starlette
from starlette.routing import Route

app = Starlette(
    routes=[...],
    middleware=[
        (OriginValidationMiddleware, {"allowed_origins": {
            "http://localhost:3000",
            "https://myapp.example.com",
        }})
    ]
)
```

### 5.2 SSE 轮询支持实现

```python
from starlette.responses import StreamingResponse
from starlette.requests import Request
from typing import AsyncGenerator, Optional
import asyncio
import uuid

class SSEStreamWriter:
    """SSE 流写入器，支持 SEP-1699 轮询"""

    def __init__(
        self,
        retry_interval: int = 5000,
        session_store: dict = None
    ):
        self.retry_interval = retry_interval
        self.session_store = session_store or {}
        self._event_id_counter = 0

    def _generate_event_id(self, stream_id: str) -> str:
        """生成唯一事件 ID"""
        self._event_id_counter += 1
        return f"{stream_id}-{self._event_id_counter}"

    async def _send_event(
        self,
        event_id: str,
        data: str,
        retry: Optional[int] = None
    ) -> str:
        """格式化 SSE 事件"""
        lines = [f"id: {event_id}"]
        if retry is not None:
            lines.append(f"retry: {retry}")
        lines.append(f"data: {data}")
        lines.append("")  # 空行结束事件
        lines.append("")  # SSE 需要两个换行
        return "\n".join(lines)

    async def stream_with_polling(
        self,
        request: Request,
        stream_id: str,
        generator: AsyncGenerator
    ) -> AsyncGenerator[str, None]:
        """
        支持 SEP-1699 轮询的 SSE 流

        1. 立即发送带 id 的空事件
        2. 定期发送 retry 指令
        3. 支持通过 Last-Event-ID 恢复
        """
        # 检查是否为恢复请求
        last_event_id = request.headers.get("last-event-id")

        # 发送初始空事件（primer）
        initial_id = self._generate_event_id(stream_id)
        yield await self._send_event(initial_id, "")

        # 如果是恢复请求，从存储中获取状态
        start_index = 0
        if last_event_id:
            stored_state = self.session_store.get(stream_id, {})
            start_index = stored_state.get("event_index", 0)

        event_index = start_index

        async for data in generator:
            event_index += 1
            event_id = self._generate_event_id(stream_id)

            # 存储进度
            self.session_store[stream_id] = {
                "event_index": event_index,
                "last_event_id": event_id
            }

            # 发送带 retry 的事件
            yield await self._send_event(
                event_id,
                data,
                retry=self.retry_interval
            )

        # 流结束，清理存储
        if stream_id in self.session_store:
            del self.session_store[stream_id]


# 使用示例
async def mcp_endpoint(request: Request):
    """MCP 端点，支持 SSE 轮询"""

    if request.method == "POST":
        body = await request.json()

        async def process_request():
            # 处理请求并产生事件
            yield '{"jsonrpc": "2.0", "result": {"status": "processing"}}'
            await asyncio.sleep(1)
            yield '{"jsonrpc": "2.0", "result": {"status": "complete"}}'

        stream_id = str(uuid.uuid4())
        writer = SSEStreamWriter()

        return StreamingResponse(
            writer.stream_with_polling(request, stream_id, process_request()),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
```

### 5.3 WWW-Authenticate 增量授权

```python
from starlette.responses import JSONResponse
from typing import List, Optional


def create_insufficient_scope_response(
    required_scopes: List[str],
    resource_metadata_url: str,
    error_description: Optional[str] = None
) -> JSONResponse:
    """
    创建 insufficient_scope 403 响应

    用于 Step-Up Authorization Flow
    """
    scope_str = " ".join(required_scopes)

    www_authenticate = (
        f'Bearer error="insufficient_scope", '
        f'scope="{scope_str}", '
        f'resource_metadata="{resource_metadata_url}"'
    )

    if error_description:
        www_authenticate += f', error_description="{error_description}"'

    return JSONResponse(
        status_code=403,
        content={
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Insufficient scope"
            }
        },
        headers={
            "WWW-Authenticate": www_authenticate,
            "Content-Type": "application/json"
        }
    )


# 使用示例
async def protected_resource(request: Request):
    """受保护资源端点"""

    token = extract_token(request)
    token_scopes = validate_token(token)

    required_scopes = ["files:read", "files:write"]

    # 检查权限
    if not all(scope in token_scopes for scope in required_scopes):
        return create_insufficient_scope_response(
            required_scopes=required_scopes,
            resource_metadata_url="https://mcp.example.com/.well-known/oauth-protected-resource",
            error_description="Additional file write permission required"
        )

    # 处理请求
    return JSONResponse({"result": "success"})
```

### 5.4 完整 MCP 服务器示例

```python
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP 2025-11-25 兼容服务器"""

    def __init__(self, allowed_origins: set = None):
        self.allowed_origins = allowed_origins or {
            "http://localhost",
            "http://127.0.0.1",
        }
        self.sessions = {}  # 会话存储

    async def handle_mcp(self, request):
        """MCP 端点处理器"""

        # 1. Origin 校验
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in self.allowed_origins:
            logger.warning(f"Rejected Origin: {origin}")
            return JSONResponse(
                {"error": "Invalid Origin"},
                status_code=403
            )

        # 2. 协议版本检查
        protocol_version = request.headers.get("mcp-protocol-version", "2025-03-26")
        if protocol_version not in ["2025-03-26", "2025-11-25"]:
            return JSONResponse(
                {"error": "Unsupported protocol version"},
                status_code=400
            )

        # 3. 会话管理
        session_id = request.headers.get("mcp-session-id")

        # 4. 根据方法处理
        if request.method == "POST":
            return await self._handle_post(request, session_id)
        elif request.method == "GET":
            return await self._handle_get(request, session_id)
        elif request.method == "DELETE":
            return await self._handle_delete(session_id)

        return JSONResponse(
            {"error": "Method not allowed"},
            status_code=405
        )

    async def _handle_post(self, request, session_id):
        """处理 POST 请求"""
        body = await request.json()

        # JSON-RPC 请求处理
        if "method" in body:
            return await self._handle_request(body, session_id)
        # JSON-RPC 通知/响应
        else:
            return JSONResponse(status_code=202)

    async def _handle_get(self, request, session_id):
        """处理 GET 请求 (SSE 流)"""
        # 支持 Last-Event-ID 恢复
        last_event_id = request.headers.get("last-event-id")

        # 返回 SSE 流
        # ... SSE 流实现

    async def _handle_delete(self, session_id):
        """处理 DELETE 请求 (终止会话)"""
        if session_id and session_id in self.sessions:
            del self.sessions[session_id]
            return JSONResponse({"status": "session terminated"})
        return JSONResponse(status_code=404)


# 创建应用
mcp_server = MCPServer()

app = Starlette(
    routes=[
        Route("/mcp", mcp_server.handle_mcp, methods=["GET", "POST", "DELETE"])
    ],
    middleware=[
        Middleware(OriginValidationMiddleware, allowed_origins={
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        })
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",  # 仅绑定本地
        port=3000
    )
```

---

## 参考资料

- [MCP Transports Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP Authorization Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [SEP-991: OAuth Client ID Metadata Documents](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/991)
- [SEP-1699: SSE Polling Support](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1699)
- [RFC 9728: OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728)
- [RFC 8414: OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)
- [OAuth 2.1 Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13)
