# MCP Test Server 文档

详细文档索引。完整项目说明见 [根目录 README.md](../README.md)。

## 传输模式

| 模式 | 文档 | 说明 |
|------|------|------|
| NPX | [stdio/npx/README.md](./stdio/npx/README.md) | Node.js stdio（推荐开发） |
| UVX | [stdio/uvx/README.md](./stdio/uvx/README.md) | Python stdio |
| HTTP | [http/README.md](./http/README.md) | HTTP/SSE 传输 |

## 必读文档

| 文档 | 说明 |
|------|------|
| [stdio/uvx/ISSUES.md](./stdio/uvx/ISSUES.md) | **UVX 问题汇总** — 五层缓存、Defender 锁文件 |
| [FASTMCP_STREAMING_ANALYSIS.md](./FASTMCP_STREAMING_ANALYSIS.md) | FastMCP "流式"原理 — report_progress 机制 |
| [SSE_PROGRESS_DESIGN_NOTES.md](./SSE_PROGRESS_DESIGN_NOTES.md) | SDK 路由 Bug — HTTP stateless 下 progress 丢失 |
| [STEPFUN_STREAMING_LIMITATION.md](./STEPFUN_STREAMING_LIMITATION.md) | 阶跃流式限制 — 不发送 progressToken |

## 测试报告

| 模式 | 文档 | 结果 |
|------|------|------|
| NPX | [stdio/npx/TEST_REPORT.md](./stdio/npx/TEST_REPORT.md) | 35/35 通过 |
| UVX | [stdio/uvx/TEST_REPORT.md](./stdio/uvx/TEST_REPORT.md) | 35/35 通过 |

## 开发指南

| 文档 | 说明 |
|------|------|
| [MCP_TRANSPORT_MODES.md](./MCP_TRANSPORT_MODES.md) | 传输模式选择指南 |
| [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) | 跨模式开发指南 |

## Skill

让 AI 帮你写 MCP 服务器：[skills/stepfun-mcp/](../skills/stepfun-mcp/)
