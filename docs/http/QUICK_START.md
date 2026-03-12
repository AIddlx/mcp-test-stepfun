# HTTP URL 模式 - 快速开始

> **操作系统**: Windows 11 Pro
> **传输模式**: HTTP URL (Streamable HTTP)
> **协议版本**: MCP 2025-11-25
> **测试客户端**: 阶跃桌面助手 v0.2.13

## 启动服务器

```bash
# HTTP 模式（推荐）
python full_test_server.py --http

# 指定端口
python full_test_server.py --http --port 3372

# 无认证模式（测试用）
python full_test_server.py --http --auth none

# 完整参数
python full_test_server.py --host 127.0.0.1 --port 3372 --auth both
```

## 阶跃客户端配置

```json
{
  "mcpServers": {
    "full-test": {
      "url": "http://127.0.0.1:3372/mcp",
      "headers": {
        "Authorization": "ApiKey mcp_admin_key_prod_2025"
      }
    }
  }
}
```

## 可用凭据

| 类型 | 名称 | 值 |
|------|------|-----|
| API Key | admin | `mcp_admin_key_prod_2025` |
| API Key | developer | `mcp_dev_key_2025` |
| Bearer | prod | `mcp_prod_token_a1b2c3d4e5f6` |

## 服务器地址

- HTTP URL: `http://127.0.0.1:3372/mcp`

## 验证连接

在阶跃客户端中执行：
```
请调用 test_ping 工具测试连接
```

成功响应：
```json
{
  "test_id": "A1",
  "success": true,
  "pong": "pong"
}
```
