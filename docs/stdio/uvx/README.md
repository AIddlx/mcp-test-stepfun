# UVX 模式 - MCP 测试服务器

> **传输模式**: stdio (标准输入输出)
> **协议版本**: MCP 2025-11-25
> **适用客户端**: 阶跃 AI 桌面助手

---

## 当前状态：可用

UVX 模式在阶跃 AI 桌面助手 v0.2.13（Windows）上**当前可以正常工作**。

**注意事项**：
1. 阶跃客户端只能识别裸命令名（如 `uvx`），不支持完整路径
2. 曾遇到连接失败问题，已确认为 Windows Defender IOAV 扫描锁定 .whl 文件导致（详见 [ISSUES.md](./ISSUES.md)）
3. 阶跃内置了 uvx 0.9.17，使用 uv 管理的 Python 3.12.9

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

### 1.2 重要提示

> ⚠️ **uvx 命令需要 Python 环境**
>
> 确保已安装 Python >= 3.10 和 uv 工具

---

## 二、服务器文件

```
stdio/uvx/
├── pyproject.toml           # UVX 包配置
├── README.md                # 说明文档
└── src/
    └── mcp_uvx_test/
        ├── __init__.py      # 包入口
        └── server.py        # 服务器主程序 (35个工具)
```

---

## 三、测试工具 (35个)

与 NPX 模式完全一致，详见 [../npx/README.md](../npx/README.md)

### 工具分类

| 类别 | 数量 | 说明 |
|------|------|------|
| A 类 | 5 | 核心能力 |
| B 类 | 6 | 重要能力 |
| C 类 | 4 | 高级能力 |
| D 类 | 8 | 边界条件 |
| E 类 | 1 | 极端条件 |
| G 类 | 7 | GUI Agent |
| H 类 | 2 | Elicitation |
| I 类 | 2 | Sampling |

---

## 四、与 NPX 模式对比

| 项目 | NPX 模式 | UVX 模式 |
|------|----------|----------|
| 语言 | Node.js | Python |
| 包管理 | npm/npx | uv/uvx |
| 工具数量 | 35 | 35 |
| 功能 | 完全一致 | 完全一致 |
| 日志位置 | `logs/stdio_*.jsonl` | `logs/uvx_*.jsonl` |

---

## 五、相关文档

- [问题汇总](./ISSUES.md) - UVX 模式问题分析
- [测试报告](./TEST_REPORT.md) - 测试结果
- [开发指南](./DEVELOPMENT_GUIDE.md) - 开发指南

---

*更新时间: 2026-03-11*
