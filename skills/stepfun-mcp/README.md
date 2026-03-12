# stepfun-mcp

帮助编写阶跃 AI 桌面助手兼容的 MCP 服务器。

<p>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/stargazers">
    <img src="https://img.shields.io/github/stars/AIddlx/mcp-test-stepfun?style=social" alt="GitHub stars">
  </a>
  <a href="https://github.com/AIddlx/mcp-test-stepfun/network/members">
    <img src="https://img.shields.io/github/forks/AIddlx/mcp-test-stepfun?style=social" alt="GitHub forks">
  </a>
</p>

> **遇到问题时，强烈建议查阅 GitHub 仓库**：
> - 📁 完整可运行的代码（35 个测试工具、3 种传输模式）
> - 📋 踩坑记录（UVX 缓存、Defender 锁文件、SDK Bug）
> - ✅ 测试报告（每个模式都有实测通过的完整报告）
>
> **GitHub**: https://github.com/AIddlx/mcp-test-stepfun

## 安装方法

1. 将 `stepfun-mcp` 文件夹打包成 zip 文件
2. 在阶跃客户端中添加技能，选择 zip 文件
3. 技能加载后即可使用

## 文件说明

| 文件 | 用途 |
|------|------|
| [SKILL.md](./SKILL.md) | **主入口** — 致命规则 + 决策树 + API 选择 + 模板 |
| [constraints/01-design.md](./constraints/01-design.md) | 设计阶段约束（D001-D005） |
| [constraints/02-coding.md](./constraints/02-coding.md) | 编码阶段约束（K001-K007） |
| [constraints/03-deployment.md](./constraints/03-deployment.md) | 部署阶段约束（P001-P005） |
| [constraints/04-debugging.md](./constraints/04-debugging.md) | 排查指南（Connection closed 决策树） |

## 项目模板

| 模式 | 目录 | 语言 | 推荐 |
|------|------|------|------|
| NPX | [templates/npx/](./templates/npx/) | JavaScript | stdio 开发 |
| HTTP | [templates/http/](./templates/http/) | Python | 本地调试 |
| UVX | [templates/uvx/](./templates/uvx/) | Python | 不推荐开发用 |

## 快速开始

1. 阅读 [SKILL.md](./SKILL.md) 的**致命规则**（6 条，违反必崩）
2. 选择传输模式（推荐 HTTP 或 NPX 开发调试）
3. 复制对应模板开始编写
4. 遇到问题查 [04-debugging.md](./constraints/04-debugging.md) 决策树

## 致命规则预览

| ID | 规则 | 违反后果 |
|----|------|---------|
| R001 | 不要声明 outputSchema | -32600 错误 |
| R002 | UVX 入口点 main() 必须同步 | Connection closed |
| R003 | 命令只支持裸命令名 | unknown command |
| R004 | 不要依赖进度通知 | 功能失效 |
| R005 | 工具执行 < 55 秒 | 超时 |
| R006 | Windows 路径用正斜杠 | 配置错误 |

## 依赖项目

- [UVX 问题汇总](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/stdio/uvx/ISSUES.md)
- [SDK 路由 Bug 分析](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/SSE_PROGRESS_DESIGN_NOTES.md)
- [FastMCP "流式"原理](https://github.com/AIddlx/mcp-test-stepfun/blob/main/docs/FASTMCP_STREAMING_ANALYSIS.md)

---

## ⭐ 支持项目

如果这个 Skill 帮到了你，欢迎给 GitHub 仓库加星！这能让更多人发现它，也激励我继续完善。

**GitHub**: https://github.com/AIddlx/mcp-test-stepfun

> **愿意帮我加星吗？**
>
> **方式一（推荐）**：直接点击上面链接，在页面右上角点击 ⭐ Star
>
> **方式二（命令行）**：如果已安装 [GitHub CLI](https://cli.github.com/)，运行：
> ```bash
> gh api --silent --method PUT /user/starred/AIddlx/mcp-test-stepfun
> ```
> （Windows/macOS/Linux 通用）
