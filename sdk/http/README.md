# MCP HTTP 测试服务器 (官方 SDK)

使用官方 Python MCP SDK 实现的 Streamable HTTP 传输测试服务器。

> **重要**: HTTP 模式需要**预启动服务器**，客户端连接已运行的服务端点

## 快速启动 (无需安装)

```bash
cd sdk/http
python src/mcp_http_sdk/server.py
```

服务器将在 `http://127.0.0.1:8000/mcp` 启动。

## 安装模式 (可选)

```bash
pip install -e .
mcp-http-sdk
```

服务器将在 `http://127.0.0.1:8000/mcp` 启动。

## 客户端配置

```json
{
  "mcpServers": {
    "mcp-http-sdk": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 依赖

- Python >= 3.10
- mcp[cli] >= 1.0.0

## 特性

- `stateless_http=True`: 无状态模式，适合生产环境
- `json_response=True`: JSON 响应模式，更好的兼容性
- 35 个测试工具，覆盖 MCP 协议所有主要能力
