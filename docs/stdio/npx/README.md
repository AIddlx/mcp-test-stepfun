# NPX 模式 - MCP 测试服务器

> **传输模式**: stdio (标准输入输出)
> **协议版本**: MCP 2025-11-25
> **适用客户端**: 阶跃 AI 桌面助手 v0.2.13
> **测试平台**: Windows 11 Pro（仅在 Windows 平台测试，其他平台未测试）

---

## 一、快速配置

### 1.1 阶跃客户端配置

```json
{
  "mcpServers": {
    "mcp-npx-test": {
      "command": "npx",
      "args": ["-y", "<服务器路径>"]
    }
  }
}
```

**示例**：
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

### 1.2 重要提示

> ⚠️ **阶跃客户端只能通过 `npx` 命令启动 Node.js MCP 服务器**
>
> 直接使用 `node` 命令（即使使用完整路径）会导致失败。

---

## 二、服务器文件

```
stdio/npx/
├── package.json           # NPX 包配置
├── stdio-full-server.js   # 服务器主程序 (35个工具)
└── bin/
    └── mcp-server.js      # 入口文件
```

---

## 三、测试工具 (35个)

### A 类 - 核心能力 (5个)

| 工具 | 说明 |
|------|------|
| `test_ping` | 基础连通性测试 |
| `test_protocol_version` | 协议版本协商 |
| `test_capabilities` | 能力声明查询 |
| `test_tool_call` | 工具调用基础验证 |
| `test_all_types` | 全类型参数验证 |

### B 类 - 复杂参数 (6个)

| 工具 | 说明 |
|------|------|
| `test_complex_params` | 嵌套对象、数组、枚举 |
| `test_large_data` | 大数据传输 |
| `test_long_operation` | 长时间操作 |
| `test_concurrent` | 并发请求处理 |
| `test_unicode` | Unicode 多语言支持 |
| `test_error_codes` | 错误码处理 |

### C 类 - 高级能力 (4个)

| 工具 | 说明 |
|------|------|
| `test_progress_notification` | 进度通知（流式） |
| `test_cancellation` | 请求取消 |
| `test_batch_request` | 批量请求 |
| `test_completion` | 自动补全 |

### D 类 - 边界条件 (8个)

| 工具 | 说明 |
|------|------|
| `test_empty_params` | 空参数处理 |
| `test_long_string` | 超长字符串 |
| `test_special_chars` | 特殊字符处理 |
| `test_idempotency` | 幂等性测试 |
| `test_rapid_fire` | 快速连续请求 |
| `test_empty_values` | 空值处理 |
| `test_deep_nesting` | 深层嵌套对象 |
| `test_large_array` | 大数组处理 |

### E 类 - 极端条件 (1个)

| 工具 | 说明 |
|------|------|
| `test_timeout_boundary` | 超时边界测试 |

### G 类 - GUI Agent (7个)

| 工具 | 说明 |
|------|------|
| `gui_desktop_info` | 获取桌面信息 |
| `gui_take_screenshot` | 屏幕截图 |
| `gui_mouse_click` | 鼠标点击 |
| `gui_mouse_move` | 鼠标移动 |
| `gui_keyboard_input` | 键盘输入 |
| `gui_send_message` | 发送消息（流式进度） |
| `gui_automation_demo` | 自动化演示（批量） |

### H 类 - Elicitation (2个)

| 工具 | 说明 |
|------|------|
| `test_elicitation_form` | 表单式 Elicitation |
| `test_elicitation_url` | URL 式 Elicitation |

### I 类 - Sampling (2个)

| 工具 | 说明 |
|------|------|
| `test_sampling_basic` | 基础 Sampling |
| `test_sampling_with_tools` | 带工具的 Sampling |

---

## 四、测试结果

详见 [TEST_REPORT.md](./TEST_REPORT.md)

**总结**: 2026-03-11 测试通过率 **100%** (35/35)

---

## 五、为阶跃编写 NPX MCP 的要点

### 5.1 package.json 配置

```json
{
  "name": "your-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "your-mcp-server": "./bin/mcp-server.js"
  },
  "files": ["bin/", "your-server.js", "package.json"]
}
```

### 5.2 入口文件示例

```javascript
#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: 'your-mcp-server',
  version: '1.0.0'
}, {
  capabilities: { tools: {} }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 5.3 阶跃客户端配置格式

```json
{
  "mcpServers": {
    "your-server": {
      "command": "npx",
      "args": ["-y", "<本地路径或包名>"]
    }
  }
}
```

---

## 六、相关文档

- [测试报告](./TEST_REPORT.md) - 2026-03-11 测试结果
- [开发指南](../../DEVELOPMENT_GUIDE.md) - MCP 服务器开发

---

*更新时间: 2026-03-11*
