# MCP 测试服务器 - 官方 SDK 版本

本目录包含使用官方 MCP SDK 实现的测试服务器，代码更简洁、更可靠。

## 目录结构

```
sdk/
├── http/          # Python SDK + Streamable HTTP 传输
├── npx/           # TypeScript SDK + stdio 传输
└── uvx/           # Python SDK + stdio 传输
```

## 对比手动实现版本

| 特性 | 手动实现 (../http, ../stdio) | 官方 SDK (sdk/) |
|------|------------------------------|-----------------|
| 代码量 | ~1000 行 | ~200 行 |
| 协议解析 | 手动实现 JSON-RPC | SDK 自动处理 |
| inputSchema | 手动定义 | 从类型注解自动生成 |
| 进度通知 | 手动构造 JSON | `ctx.report_progress()` |
| 依赖 | 无 SDK 依赖 | `mcp[cli]` / `@modelcontextprotocol/sdk` |

## 快速开始

### HTTP 模式 (Python SDK) - 无需安装

```bash
cd sdk/http
python src/mcp_http_sdk/server.py
```

> 依赖已在环境中安装，可直接启动

客户端配置:
```json
{
  "mcpServers": {
    "mcp-http-sdk": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### NPX 模式 (TypeScript SDK) - stdio 传输

> **无需预启动** - 由客户端根据配置自动启动进程

```bash
cd sdk/npx
npm install && npm run build  # 只需编译一次
```

阶跃客户端配置:
```json
{
  "mcpServers": {
    "mcp-npx-sdk": {
      "command": "node",
      "args": ["C:/Project/IDEA/2/new/mcp-test-stepfun/sdk/npx/dist/server.js"]
    }
  }
}
```

### UVX 模式 (Python SDK) - stdio 传输

> **无需预启动** - 由客户端根据配置自动启动进程

阶跃客户端配置:
```json
{
  "mcpServers": {
    "mcp-uvx-sdk": {
      "command": "python",
      "args": ["C:/Project/IDEA/2/new/mcp-test-stepfun/sdk/uvx/src/mcp_uvx_sdk/server.py"]
    }
  }
}
```

## 测试工具 (35个)

所有版本都包含相同的 35 个测试工具:

- **A 类 (5个)**: 核心能力 - ping, 版本, 能力, 工具调用, 类型测试
- **B 类 (6个)**: 重要能力 - 复杂参数, 大数据, 长操作, 并发, Unicode, 错误
- **C 类 (4个)**: 高级能力 - 进度通知, 取消, 批量, 补全
- **D 类 (8个)**: 边界条件 - 空参数, 长字符串, 特殊字符, 幂等性等
- **E 类 (1个)**: 极端条件 - 超时边界
- **G 类 (7个)**: GUI Agent - 桌面信息, 截图, 鼠标, 键盘, 消息, 自动化
- **H 类 (2个)**: Elicitation - 表单, URL
- **I 类 (2个)**: Sampling - 基础, 带工具

## 技术细节

### 依赖

- **Python**: `mcp[cli]>=1.0.0` (官方 Python SDK)
- **TypeScript**: `@modelcontextprotocol/sdk>=1.0.0` (官方 TypeScript SDK)

### SDK 特性利用

- `FastMCP` 高级封装
- `@mcp.tool()` 装饰器自动生成 inputSchema
- `Context` 对象提供进度通知、日志等功能
- `stateless_http=True` 无状态 HTTP 模式
- `json_response=True` JSON 响应模式
