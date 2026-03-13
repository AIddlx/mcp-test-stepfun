# MCP Test Server

MCP 协议测试服务器 + 阶跃 AI 桌面助手开发 Skill。

<p>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/stargazers">
    <img src="https://img.shields.io/github/stars/AIddlx/mcp-test-stepfun?style=social" alt="GitHub stars">
  </a>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/network/members">
    <img src="https://img.shields.io/github/forks/AIddlx/mcp-test-stepfun?style=social" alt="GitHub forks">
  </a>
</p>

---

## 项目价值

本项目提供两份核心资产：

| 资产 | 价值 |
|------|------|
| **兼容性测试** | 35 个测试工具 + 3 种传输模式，验证阶跃客户端 MCP 兼容性 |
| **开发 Skill** | 6 条致命规则 + 17 条约束 + 3 套模板，让 AI 帮你写 MCP 服务器 |

---

## 一、兼容性测试

### 测试覆盖

| 类别 | 数量 | 说明 |
|------|------|------|
| A - 核心能力 | 5 | 协议版本、能力声明、工具调用、全类型参数 |
| B - 复杂参数 | 6 | 嵌套对象、大数据、长操作、并发、Unicode |
| C - 高级能力 | 4 | 进度通知、取消、批量请求、自动补全 |
| D - 边界条件 | 8 | 空参数、超长字符串、特殊字符、幂等性 |
| E - 极端条件 | 1 | 超时边界 |
| G - GUI Agent | 7 | 截图、鼠标、键盘、自动化演示 |
| H - Elicitation | 2 | 表单式、URL 式 |
| I - Sampling | 2 | 基础、带工具 |

### 传输模式

| 模式 | 目录 | 状态 |
|------|------|------|
| NPX (stdio) | `stdio/npx/` | 35/35 通过 |
| UVX (stdio) | `stdio/uvx/` | 35/35 通过 |
| HTTP/SSE | `http/` | 35/35 通过 |

### 快速开始

**HTTP 模式**（推荐开发调试）：
```bash
cd http
python full_test_server.py
```

阶跃客户端配置：
```json
{
  "mcpServers": {
    "mcp-http-test": {
      "url": "http://127.0.0.1:3372/mcp"
    }
  }
}
```

**NPX 模式**（推荐 stdio 测试）：
```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "<项目路径>/stdio/npx"]
    }
  }
}
```

**UVX 模式**（不推荐开发时用）：
```json
{
  "mcpServers": {
    "mcp-uvx-test": {
      "command": "uvx",
      "args": ["--from", "<项目路径>/stdio/uvx", "mcp-uvx-test"]
    }
  }
}
```

> ⚠️ UVX 模式有严重的缓存问题，每次修改源码都需要清理缓存 + 更新版本号。详见 [docs/stdio/uvx/ISSUES.md](docs/stdio/uvx/ISSUES.md)。

---

## 二、开发 Skill

### 什么是 Skill

Skill 是阶跃 AI 桌面助手的扩展能力包。加载后，AI 获得"编写阶跃兼容 MCP 服务器"的专业知识。

### Skill 内容

| 内容 | 说明 |
|------|------|
| **致命规则 TOP 6** | 违反必崩（outputSchema、async main、命令格式...） |
| **17 条约束** | 设计/编码/部署/排查全覆盖 |
| **决策树** | Connection closed 5 种原因排查 |
| **3 套模板** | NPX / UVX / HTTP 完整项目模板 |

### 使用方法

1. 打包 `skills/stepfun-mcp/` 文件夹为 zip
2. 在阶跃客户端中添加技能（导入 zip）
3. 告诉阶跃你想实现的功能

示例对话：
> "帮我写一个阶跃兼容的 MCP 服务器，提供文件读写功能"

---

## 项目结构

```
mcp-test-stepfun/
├── stdio/                     # stdio 传输模式
│   ├── npx/                   # Node.js (NPX)
│   └── uvx/                   # Python (UVX)
├── http/                      # HTTP/SSE 传输模式
├── sdk/                       # SDK 测试服务器
│   ├── npx/                   # TypeScript SDK
│   ├── http/                  # Python SDK (HTTP)
│   └── uvx/                   # Python SDK (stdio)
├── skills/stepfun-mcp/        # 开发 Skill
│   ├── SKILL.md               # 主文件
│   ├── references/            # 参考文档
│   └── assets/                # 项目模板
└── docs/                      # 技术文档
```

---

## 文档索引

### 必读

| 文档 | 说明 |
|------|------|
| [docs/stdio/uvx/ISSUES.md](docs/stdio/uvx/ISSUES.md) | **UVX 问题汇总**（五层缓存） |

### 技术分析

| 文档 | 说明 |
|------|------|
| [docs/FASTMCP_STREAMING_ANALYSIS.md](docs/FASTMCP_STREAMING_ANALYSIS.md) | FastMCP "流式"原理 |
| [docs/SSE_PROGRESS_DESIGN_NOTES.md](docs/SSE_PROGRESS_DESIGN_NOTES.md) | SDK 路由 Bug 分析 |
| [docs/STEPFUN_STREAMING_LIMITATION.md](docs/STEPFUN_STREAMING_LIMITATION.md) | 阶跃流式限制 |

### 测试报告

| 文档 | 说明 |
|------|------|
| [docs/stdio/npx/TEST_REPORT.md](docs/stdio/npx/TEST_REPORT.md) | NPX 模式测试报告 |
| [docs/stdio/uvx/TEST_REPORT.md](docs/stdio/uvx/TEST_REPORT.md) | UVX 模式测试报告 |

---

## 测试环境

- **平台**: Windows 11 Pro
- **客户端**: 阶跃 AI 桌面助手 v0.2.13
- **协议版本**: MCP 2025-11-25

> 其他平台未测试。
