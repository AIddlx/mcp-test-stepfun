# MCP UVX 测试服务器

> **传输模式**: stdio (标准输入输出)
> **协议版本**: MCP 2025-11-25
> **适用客户端**: 阶跃 AI 桌面助手

---

## 一、快速配置

### 1.1 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-uvx-test": {
      "command": "uvx",
      "args": ["--from", "<服务器路径>", "mcp-uvx-test"]
    }
  }
}
```

**示例**：
```json
{
  "mcpServers": {
    "mcp-uvx-test": {
      "command": "uvx",
      "args": ["--from", "C:/Project/IDEA/2/new/mcp-test-stepfun/stdio/uvx", "mcp-uvx-test"]
    }
  }
}
```

### 1.2 前置条件

- Python >= 3.10
- uv (UVX 命令)

---

## 二、测试工具 (31个)

详见 [README.md](./docs/stdio/uvx/README.md)

---

## 三、与 NPX 模式对比

| 项目 | NPX 模式 | UVX 模式 |
|------|----------|----------|
| 语言 | Node.js | Python |
| 包管理 | npm/npx | uv/uvx |
| 工具数量 | 31 | 31 |
| 功能 | 完全一致 | 完全一致 |

---

*更新时间: 2026-03-11*
