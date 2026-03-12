# MCP Test Server

MCP 协议测试服务器，用于验证阶跃 AI 桌面助手的 MCP 兼容性。

<p>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/stargazers">
    <img src="https://img.shields.io/github/stars/AIddlx/mcp-test-stepfun?style=social" alt="GitHub stars">
  </a>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/network/members">
    <img src="https://img.shields.io/github/forks/AIddlx/mcp-test-stepfun?style=social" alt="GitHub forks">
  </a>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/issues">
    <img src="https://img.shields.io/github/issues/AIddlx/mcp-test-stepfun" alt="GitHub issues">
  </a>
</p>

## 项目结构

```
mcp-test-stepfun/
├── README.md                   # 本文件
├── stdio/                     # stdio 传输模式
│   ├── npx/                   # Node.js (NPX)
│   └── uvx/                   # Python (UVX)
├── http/                      # HTTP/SSE 传输模式
├── sdk/                       # SDK 测试服务器
│   ├── npx/                   # Node.js SDK
│   └── uvx/                   # Python SDK
├── skills/stepfun-mcp/        # AI 辅助开发 Skill
│   ├── SKILL.md               # 主 Skill 文件
│   ├── constraints/           # 开发约束清单
│   └── templates/             # 项目模板
└── docs/                      # 详细文档
    ├── stdio/                 # stdio 模式文档
    ├── http/                  # HTTP 模式文档
    └── *.md                   # 通用文档
```

## 快速开始

### 方式一：HTTP 模式（推荐开发调试）

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

### 方式二：NPX 模式（推荐 stdio 测试）

阶跃客户端配置：
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

### 方式三：UVX 模式（不推荐开发时用）

阶跃客户端配置：
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

## 测试工具

35 个测试工具，覆盖：

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

## 让 AI 帮你写 MCP 服务器

本项目提供了一个 Skill，让阶跃帮你编写阶跃兼容的 MCP 服务器。

**使用方法**：
1. 将 `skills/stepfun-mcp/` 文件夹打包成 zip
2. 在阶跃客户端中添加技能（导入 zip 文件）
3. 告诉阶跃你想实现的功能

**Skill 特性**：
- 致命规则 TOP 6（违反必崩）
- Connection closed 决策树（5 种原因排查）
- 17 条约束（设计/编码/部署/排查）
- 3 套项目模板（NPX/HTTP/UVX）

详见 [skills/stepfun-mcp/README.md](skills/stepfun-mcp/README.md)。

## 文档索引

### 传输模式

| 文档 | 说明 |
|------|------|
| [docs/MCP_TRANSPORT_MODES.md](docs/MCP_TRANSPORT_MODES.md) | stdio vs HTTP/SSE 对比 |
| [docs/stdio/npx/README.md](docs/stdio/npx/README.md) | NPX 模式说明 |
| [docs/stdio/uvx/README.md](docs/stdio/uvx/README.md) | UVX 模式说明 |
| [docs/stdio/uvx/ISSUES.md](docs/stdio/uvx/ISSUES.md) | **UVX 问题汇总**（必读） |

### 技术分析

| 文档 | 说明 |
|------|------|
| [docs/FASTMCP_STREAMING_ANALYSIS.md](docs/FASTMCP_STREAMING_ANALYSIS.md) | FastMCP "流式"原理分析 |
| [docs/SSE_PROGRESS_DESIGN_NOTES.md](docs/SSE_PROGRESS_DESIGN_NOTES.md) | SDK 路由 Bug 分析 |
| [docs/STEPFUN_STREAMING_LIMITATION.md](docs/STEPFUN_STREAMING_LIMITATION.md) | 阶跃流式限制 |

### 测试报告

| 文档 | 说明 |
|------|------|
| [docs/stdio/npx/TEST_REPORT.md](docs/stdio/npx/TEST_REPORT.md) | NPX 模式测试报告 |
| [docs/stdio/uvx/TEST_REPORT.md](docs/stdio/uvx/TEST_REPORT.md) | UVX 模式测试报告 |

## 协议版本

MCP 2025-11-25

## 测试环境

- **平台**: Windows 11 Pro
- **客户端**: 阶跃 AI 桌面助手 v0.2.13
- **测试结果**: 35/35 工具通过（NPX 模式）

> 其他平台未测试。
