# UVX 模式 - 开发指南

> **状态**: 📋 计划中
> **传输模式**: stdio (通过 Python)
> **适用场景**: 本地 Python 工具

## 一、模式概述

UVX 模式通过 Python 的 stdio 进行通信，客户端使用 uvx 启动 Python 包。

```
客户端 (阶跃) <--stdio--> uvx package-name
```

## 二、项目结构

```
my-mcp-server/
├── pyproject.toml
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       └── server.py
└── README.md
```

## 三、pyproject.toml

```toml
[project]
name = "my-mcp-server"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
]

[project.scripts]
my-mcp-server = "my_mcp_server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 四、阶跃客户端配置

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"]
    }
  }
}
```

## 五、实现示例

（待实现后补充）

---

> 注：本文档将在 UVX 模式实现后完善
