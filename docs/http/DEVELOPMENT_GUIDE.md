# HTTP URL 模式 - 开发指南

> **操作系统**: Windows 11 Pro 10.0.26200
> **传输模式**: HTTP URL (Streamable HTTP)
> **协议版本**: MCP 2025-11-25
> **测试客户端**: 阶跃桌面助手 v0.2.13

## 一、模式概述

HTTP URL 模式是 MCP 的远程传输模式，客户端通过 HTTP 请求与服务器通信。

```
客户端 (阶跃) <--HTTP--> MCP 服务器
```

### 1.1 请求格式

```http
POST /mcp HTTP/1.1
Host: 127.0.0.1:3372
Content-Type: application/json
Accept: application/json, text/event-stream
Authorization: ApiKey your-api-key

{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{...}}
```

### 1.2 响应格式

**普通响应:**
```json
{"jsonrpc":"2.0","id":1,"result":{...}}
```

**SSE 流式响应:**
```
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

## 二、服务器实现

### 2.1 基本结构

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 读取请求
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        request = json.loads(body)

        # 处理请求
        response = handle_mcp_request(request)

        # 返回响应
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
```

### 2.2 认证实现

```python
def check_auth(headers):
    auth = headers.get('Authorization', '')

    if auth.startswith('ApiKey '):
        key = auth[7:]
        return validate_api_key(key)
    elif auth.startswith('Bearer '):
        token = auth[7:]
        return validate_bearer_token(token)

    return False
```

### 2.3 CORS 配置

```python
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}
```

## 三、工具定义

### 3.1 工具结构

```json
{
  "name": "tool_name",
  "description": "工具描述",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {"type": "string", "description": "参数1"}
    },
    "required": ["param1"]
  }
}
```

### 3.2 工具返回

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"success\": true, \"result\": \"...\"}"
    }
  ],
  "isError": false
}
```

## 四、阶跃客户端配置

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://127.0.0.1:3372/mcp",
      "headers": {
        "Authorization": "ApiKey your-api-key"
      }
    }
  }
}
```

## 五、常见问题

### 5.1 连接失败
- 检查服务器是否启动
- 检查端口是否被占用
- 检查防火墙设置

### 5.2 认证失败
- 检查 Authorization 头格式
- 检查 API Key / Token 是否正确

### 5.3 超时
- 检查工具执行时间是否超过 55 秒
- 考虑使用进度通知或轮询模式

## 六、调试技巧

### 6.1 查看原始请求

在服务器端记录完整请求：

```python
def log_request(request, headers):
    print(f"Request: {json.dumps(request, indent=2)}")
    print(f"Headers: {headers}")
```

### 6.2 使用 curl 测试

```bash
curl -X POST http://127.0.0.1:3372/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: ApiKey your-api-key" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```
