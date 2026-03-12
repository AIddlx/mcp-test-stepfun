# HTTP 模式 - MCP 测试服务器

> **传输模式**: HTTP URL (Streamable HTTP)
> **协议版本**: MCP 2025-11-25
> **适用客户端**: 阶跃 AI 桌面助手 v0.2.13
> **测试平台**: Windows 11 Pro（仅在 Windows 平台测试，其他平台未测试）

---

## 一、快速配置

### 1.1 启动服务器

```bash
# 进入项目目录
cd http/

# 启动 HTTP 服务器（默认端口 3372）
python full_test_server.py --http

# 指定端口
python full_test_server.py --http --port 3372

# 无认证模式（测试用）
python full_test_server.py --http --auth none

# 完整参数
python full_test_server.py --host 127.0.0.1 --port 3372 --auth both
```

### 1.2 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-http-test": {
      "url": "http://127.0.0.1:3372/mcp",
      "headers": {
        "Authorization": "ApiKey mcp_admin_key_prod_2025"
      }
    }
  }
}
```

### 1.3 可用凭据

| 类型 | 名称 | 值 |
|------|------|-----|
| API Key | admin | `mcp_admin_key_prod_2025` |
| API Key | developer | `mcp_dev_key_2025` |
| Bearer | prod | `mcp_prod_token_a1b2c3d4e5f6` |

---

## 二、服务器文件

```
http/
└── full_test_server.py    # HTTP 服务器主程序 (30+ 个工具)
```

### 2.1 依赖安装

```bash
pip install starlette uvicorn
```

---

## 三、测试工具 (30+ 个)

### A 类 - 核心能力 (5个)

| 工具 | 说明 |
|------|------|
| `test_ping` | 基础连通性测试 |
| `test_protocol_version` | 协议版本协商 |
| `test_capabilities` | 能力声明查询 |
| `test_tool_call` | 工具调用基础验证 |
| `test_all_types` | 全类型参数验证 |

### B 类 - 复杂参数 (11个)

| 工具 | 说明 |
|------|------|
| `test_complex_params` | 嵌套对象、数组、枚举 |
| `test_large_data` | 大数据传输 |
| `test_long_operation` | 长时间操作 |
| `test_concurrent` | 并发请求处理 |
| `test_unicode` | Unicode 多语言支持 |
| `test_error_codes` | 错误码处理 |
| `test_progress_notification` | 进度通知 |
| `test_cancellation` | 请求取消 |
| `test_sampling` | Sampling 能力 |
| `test_batch_request` | 批量请求 |
| `test_completion` | 自动补全 |

### C 类 - 高级能力 (2个)

| 工具 | 说明 |
|------|------|
| `test_sampling_basic` | 基础 Sampling |
| `test_sampling_with_tools` | 带工具的 Sampling |

### D 类 - 边界条件 (8个)

| 工具 | 说明 |
|------|------|
| `test_empty_params` | 空参数处理 |
| `test_long_string` | 超长字符串 |
| `test_special_chars` | 特殊字符处理 |
| `test_idempotency` | 幂等性测试 |
| `test_rapid_fire` | 快速连续请求 |
| `test_empty_values` | 空值处理 |
| `test_deep_nesting` | 深层嵌套对象 |
| `test_large_array` | 大数组处理 |

### E 类 - 极端条件 (1个)

| 工具 | 说明 |
|------|------|
| `test_timeout_boundary` | 超时边界测试 |

### H 类 - Elicitation (3个)

| 工具 | 说明 |
|------|------|
| `test_elicitation_form` | 表单式 Elicitation |
| `test_elicitation_url` | URL 式 Elicitation |
| `test_server_elicitation` | 服务端发起 Elicitation |

### I 类 - Sampling (4个)

| 工具 | 说明 |
|------|------|
| `test_sampling` | 基础 Sampling |
| `test_sampling_basic` | 基础 Sampling 验证 |
| `test_sampling_with_tools` | 带工具的 Sampling |
| `test_server_sampling` | 服务端发起 Sampling |

---

## 四、与 stdio 模式对比

| 项目 | stdio (NPX) | HTTP |
|------|-------------|------|
| 传输方式 | 标准输入输出 | HTTP 请求 |
| 部署位置 | 本地进程 | 可本地/远程 |
| 认证 | 无 | API Key / Bearer |
| 阶跃配置 | `command` + `args` | `url` + `headers` |
| 适用场景 | 本地工具 | 远程服务、多客户端共享 |

---

## 五、为阶跃编写 HTTP MCP 的要点

### 5.1 基本结构

```python
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn

async def handle_mcp(request):
    # 读取 JSON-RPC 请求
    body = await request.json()

    # 处理 MCP 协议
    result = handle_mcp_request(body)

    # 返回 JSON 响应
    return Response(
        json.dumps(result),
        media_type="application/json"
    )

app = Starlette(routes=[Route("/mcp", handle_mcp, methods=["POST"])])
uvicorn.run(app, host="127.0.0.1", port=3372)
```

### 5.2 认证处理

```python
def check_auth(headers):
    auth = headers.get('authorization', '')

    if auth.startswith('ApiKey '):
        return validate_api_key(auth[7:])
    elif auth.startswith('Bearer '):
        return validate_bearer_token(auth[7:])

    return False
```

### 5.3 阶跃客户端配置格式

```json
{
  "mcpServers": {
    "your-server": {
      "url": "http://your-host:port/mcp",
      "headers": {
        "Authorization": "ApiKey your-api-key"
      }
    }
  }
}
```

---

## 六、调试技巧

### 6.1 使用 curl 测试

```bash
curl -X POST http://127.0.0.1:3372/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: ApiKey mcp_admin_key_prod_2025" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### 6.2 查看日志

服务器运行时会生成日志文件：
```
logs/full_test_YYYYMMDD_HHMMSS.jsonl
```

---

## 七、相关文档

- [快速开始](./QUICK_START.md) - 启动和配置
- [开发指南](./DEVELOPMENT_GUIDE.md) - 详细开发说明
- [测试指南](./TEST_GUIDE.md) - 测试方法
- [兼容性](./COMPATIBILITY.md) - 兼容性说明

---

*更新时间: 2026-03-11*
