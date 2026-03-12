# NPX 模式 - 快速开始

> **操作系统**: Windows 11 Pro 10.0.26200
> **传输模式**: stdio (标准输入输出)
> **协议版本**: MCP 2025-11-25
> **测试客户端**: 阶跃桌面助手

## 一、配置方法

### 1.1 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "node",
      "args": ["C:/Project/IDEA/2/new/mcp-test-stepfun/npx/bin/mcp-server.js"]
    }
  }
}
```

### 1.2 发布后配置（npx）

```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "mcp-npx-test"]
    }
  }
}
```

## 二、启动方式

### 方式1：阶跃客户端自动启动
配置完成后，阶跃客户端会自动启动 MCP 服务器。

### 方式2：手动测试

```bash
# 进入 npx 目录
cd npx

# 直接运行
node bin/mcp-server.js

# 或使用 npm
npm start
```

## 三、验证连接

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

## 四、注意事项

1. **无需认证**: stdio 模式是本地运行，不需要 API Key
2. **路径问题**: Windows 路径使用正斜杠 `/` 或双反斜杠 `\\`
3. **Node.js 版本**: 需要 Node.js >= 18.0.0

## 五、与 HTTP URL 模式的区别

| 特性 | NPX (stdio) | HTTP URL |
|------|-------------|----------|
| 传输方式 | 标准输入输出 | HTTP 请求 |
| 认证 | 不需要 | 需要 API Key |
| 部署 | 本地 | 可远程 |
| 启动 | 客户端自动启动 | 需手动启动服务器 |

## 六、常见问题

### Q1: 找不到命令
确保 Node.js 已安装并添加到 PATH

### Q2: 权限问题
Windows 上可能需要赋予脚本执行权限

### Q3: 端口冲突
stdio 模式不使用端口，不存在端口冲突
