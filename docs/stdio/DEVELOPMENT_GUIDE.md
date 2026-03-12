# NPX 模式 - 开发指南

> **状态**: 🚧 待实现
> **传输模式**: stdio (通过 Node.js)
> **适用场景**: 本地 Node.js 工具

## 一、模式概述

NPX 模式通过 Node.js 的 stdio 进行通信，客户端直接启动 Node.js 进程。

```
客户端 (阶跃) <--stdio--> npx package-name
```

## 二、项目结构

```
my-mcp-server/
├── package.json
├── bin/
│   └── index.js
├── src/
│   └── server.js
└── README.md
```

## 三、package.json

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "bin": {
    "my-mcp-server": "./bin/index.js"
  },
  "type": "module",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  }
}
```

## 四、阶跃客户端配置

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "my-mcp-server"]
    }
  }
}
```

## 五、实现示例

（待实现后补充）

---

> 注：本文档将在 NPX 模式实现后完善
