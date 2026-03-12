# MCP 传输模式说明

## 一、MCP 两种基本传输模式

| 模式 | 传输方式 | 启动方式 | 适用场景 |
|------|----------|----------|----------|
| **stdio** | 标准输入输出 | 客户端启动进程 | 本地工具、快速开发 |
| **HTTP/SSE** | HTTP 请求 + SSE 流 | 独立服务器 | 远程服务、多客户端 |

### 1.1 stdio 模式

```
客户端 <--stdin/stdout--> MCP 服务器进程
```

**特点：**
- 客户端负责启动和管理进程生命周期
- 通过标准输入发送请求，标准输出接收响应
- 不需要网络端口
- 适合本地工具（npx、uvx）

**配置示例：**
```json
{
  "mcpServers": {
    "my-tool": {
      "command": "npx",
      "args": ["-y", "my-mcp-tool"]
    }
  }
}
```

### 1.2 HTTP/SSE 模式

```
客户端 <--HTTP/SSE--> MCP HTTP 服务器 (http://host:port/mcp)
```

**特点：**
- 服务器独立运行，客户端通过 URL 连接
- 支持 SSE（Server-Sent Events）流式响应
- 可以服务多个客户端
- 支持远程访问

**配置示例：**
```json
{
  "mcpServers": {
    "my-service": {
      "url": "http://127.0.0.1:3372/mcp",
      "headers": {
        "Authorization": "ApiKey your-key"
      }
    }
  }
}
```

---

## 二、NPX 配置方式

### 2.1 本地开发

```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "node",
      "args": ["C:/path/to/bin/mcp-server.js"]
    }
  }
}
```

**特点：**
- 直接运行 Node.js 脚本
- 需要知道具体入口文件路径
- 适合本地开发测试（非阶跃客户端）

### 2.2 阶跃客户端（必须使用 npx）

```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "C:/path/to/stdio/npx"]
    }
  }
}
```

**特点：**
- npx 查找 package.json 中的 `bin` 字段
- `-y` 自动确认，无需手动确认
- **阶跃客户端只能用此方式**

### 2.3 对比

| 方式 | 命令 | 适用场景 | 依赖 |
|------|------|----------|------|
| node | `node path/to/bin.js` | 本地开发 | 无 |
| npx 本地 | `npx -y C:/path/to/pkg` | **阶跃客户端** | package.json |
| npx 发布 | `npx -y package-name` | 正式使用 | npm 发布 |

### 2.4 阶跃客户端配置实践

**问题**: 阶跃客户端无法识别 `node` 命令或完整路径
- `unknown command: node`
- `unknown command: C:/Program Files/nodejs/node.exe`

**唯一可行方案**：使用 npx 本地路径
```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "C:/Project/IDEA/2/new/mcp-test-stepfun/stdio/npx"]
    }
  }
}
```

**说明**: 阶跃客户端只能通过 `npx` 命令启动 Node.js MCP 服务器，直接使用 `node` 命令（即使完整路径）也会失败。

---

## 三、本项目目录结构

```
mcp-test-stepfun/
├── stdio/                        # stdio 传输
│   ├── npx/                       # Node.js 实现
│   │   ├── package.json           # npx 配置
│   │   ├── bin/mcp-server.js      # npx 入口
│   │   └── stdio-full-server.js   # 完整服务器
│   └── uvx/                       # Python 实现
│
├── http/                          # HTTP/SSE 传输
│   └── full_test_server.py        # Python HTTP 服务器
│
└── docs/
    ├── http/                       # HTTP 文档
    └── stdio/                      # stdio 文档
```

---

## 四、选择建议

| 场景 | 推荐模式 | 说明 |
|------|----------|------|
| 本地开发测试 | stdio + node | 最简单直接 |
| 发布给他人使用 | stdio + npx | 标准化，易安装 |
| 远程服务 | HTTP/SSE | 支持多客户端 |
| 需要认证 | HTTP/SSE | 支持 headers 配置 |
