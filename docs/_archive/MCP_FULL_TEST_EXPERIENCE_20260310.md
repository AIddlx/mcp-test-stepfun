# MCP 2025-11-25 全量测试经验归档

**归档日期**: 2026-03-10  
**测试对象**: 阶跃桌面助手 (stepfun-desktop/0.2.13)  
**测试服务器**: full_test_server.py v3.1 @ 127.0.0.1:3372  
**协议版本**: MCP 2025-11-25（服务器端） / 2024-11-05（客户端实际协商）  
**测试执行方式**: 阶跃桌面助手内直接调用 MCP 工具（LLM 驱动的端到端测试）

---

## 一、测试总览

共执行 **44 项测试**，覆盖 A/B/C/D/E/G/H/I 共 8 个类别。

| 分类 | 总数 | 通过 | 失败/警告 | 通过率 |
|------|------|------|-----------|--------|
| A-核心能力 | 5 | 0 | 5 | 0% |
| B-重要能力 | 12 | 11 | 1 | 92% |
| C-高级能力 | 2 | 2 | 0 | 100% |
| D-边界条件 | 8 | 8 | 0 | 100% |
| E-极端条件 | 1 | 0 | 1 | 0% |
| G-GUI Agent | 10 | 9 | 1 | 90% |
| H-Elicitation | 3 | 1 | 2 | 33% |
| I-Sampling | 3 | 1 | 2 | 33% |
| **合计** | **44** | **32** | **12** | **73%** |

---

## 二、失败项分类与根因分析

12 项失败归结为 **3 个独立根因**：

### 根因 1：outputSchema 兼容性问题（7 项）

**影响范围**: A1-A5、B3、E1  
**错误信息**: `MCP error -32600: Tool xxx has an output schema but did not return structured content`

**原因**: 服务器在工具定义中声明了 `outputSchema`（MCP 2025-11-25 新增特性），但工具执行时返回的是传统的 `content`（文本数组）而非 `structuredContent`（JSON 对象）。阶跃客户端严格校验了这一约束：当工具声明了 outputSchema 时，必须返回 structuredContent，否则拒绝接受响应。

**关键细节**:
- 这是 **服务器端的实现缺陷**，不是客户端的问题
- 阶跃客户端的严格校验行为 **符合 MCP 2025-11-25 规范**
- 没有声明 outputSchema 的工具（B1、B2、B4-B10、C2、C5、D1-D8、G1-G10）全部正常工作

**修复方案**: 服务器端对声明了 outputSchema 的工具，将返回格式从 `content: [{"type": "text", "text": "..."}]` 改为 `structuredContent: { ... }`。

### 根因 2：工具未注册（4 项）

**影响范围**: H1、H2、I1、I2  
**错误信息**: `Unknown tool -32601`

**原因**: `test_elicitation_form`、`test_elicitation_url`、`test_sampling_basic`、`test_sampling_with_tools` 这 4 个工具在服务器的 `tools/list` 中不存在。客户端能看到这些工具定义（来自 MCP 工具列表的缓存或配置），但实际调用时服务器返回 Unknown tool。

**修复方案**: 在 full_test_server.py 中注册这 4 个工具的处理逻辑。

### 根因 3：服务器端应用限制（1 项）

**影响范围**: G5 (gui_open_app)  
**错误信息**: `不支持的应用: notepad`

**原因**: GUI 模拟服务器仅支持 wechat/browser 等预定义应用，notepad 不在列表中。属于测试服务器的功能限制，非协议问题。

---

## 三、通过项的关键验证点

### 3.1 数据传输能力（全部通过）

| 测试项 | 验证内容 | 结果 |
|--------|----------|------|
| B1 复杂参数 | 嵌套对象 `{level1: {level2: "deep_value"}}`、数组 `[1,2,3]`、枚举 `option1` | 全部正确传递和返回 |
| B2 大数据 | 10 项 × 50 字节 = 1000 字节 | 生成耗时 0ms |
| B5 Unicode | 中文 "你好世界" → 4 字符 / 12 字节 UTF-8 | has_chinese: true |
| D2 超长字符串 | 5000 字符 | 完整传输无截断 |
| D3 特殊字符 | 控制字符 `\x00\x01\x02`、引号 `"'`、换行 `\n\r\t` | 正确转义 |
| D6 空值 | 空数组 `[]`、空对象 `{}`、空字符串 `""` | 类型和值均正确 |
| D7 深层嵌套 | 10 层嵌套对象 | 完整生成到 `{value: "deepest"}` |
| D8 大数组 | 1000 元素整型数组 | first_5: [0,1,2,3,4], last_5: [995,996,997,998,999] |

### 3.2 协议能力（全部通过）

| 测试项 | 验证内容 | 结果 |
|--------|----------|------|
| B6 错误处理 | error_type: invalid_params | 返回 isError: true, error_code: -32602 |
| B7 资源系统 | list_resources + read_resource | 列出 2 个 config 资源，读取 config://server 成功 |
| B8 提示词系统 | list_prompts + get_prompt | 列出 3 个模板，获取 analyze_data 模板成功 |
| B9 进度通知 | test_progress_notification (3 步 / 300ms) | 返回 "Streaming completed" |
| B10 请求取消 | test_cancellation (3 秒) | elapsed 3026ms，正常完成 |
| C2 批量请求 | 2 个操作 (add + multiply) | 全部正确处理 |
| C5 自动补全 | partial_value: "test", ref_type: ref/resource | 返回 3 个补全建议 |
| D1 空参数 | 无参数调用 | 使用默认值，params_count: 0 |
| D4 幂等性 | operation_id: "idem_test_001" | 正确记录，cached: false |
| D5 快速请求 | 5 次连续请求 | 全部成功，总耗时 < 1ms |

### 3.3 GUI Agent（9/10 通过）

| 测试项 | 验证内容 | 结果 |
|--------|----------|------|
| G1 截图 | 获取桌面状态 | 返回分辨率 1920×1080，活跃窗口列表 |
| G2 点击 | 点击坐标 (100, 200) | 成功，返回新状态 |
| G3 输入 | 输入 "Hello MCP" + 回车 | 成功，input_length: 9 |
| G4 查找元素 | 查找 "发送按钮" | 找到，位置 (950, 800) |
| G6 滚动 | 向下滚动 200px | 成功 |
| G7 等待元素 | 等待 "确认对话框" (超时 3000ms) | 300ms 内找到 |
| G8 获取状态 | 获取完整 GUI 状态 | 返回当前应用、窗口标题、焦点元素、鼠标位置 |
| G9 发送消息 | 给 "张三" 发送消息（5 步操作） | 全部完成，elapsed 2500ms |
| G10 自动化演示 | "打开记事本并输入文本"（7 步） | 全部完成 |

### 3.4 高级能力

| 测试项 | 验证内容 | 结果 |
|--------|----------|------|
| H3 服务器 Elicitation | 服务器主动创建 elicitation/create 请求 | 请求创建成功，返回完整 JSON-RPC 结构 |
| I3 服务器 Sampling | 服务器主动创建 sampling/createMessage 请求 | 请求创建成功，包含 modelPreferences |

---

## 四、阶跃客户端架构特性深度分析

### 4.1 "请求-响应"单向架构

阶跃桌面助手的 MCP 集成采用 **单向请求-响应模式**，这是理解所有限制的核心：

```
正常工作的方向（客户端 → 服务器）:
  LLM 决策 → 调用工具 → 服务器处理 → 返回结果 → LLM 接收

不工作的方向（服务器 → 客户端）:
  服务器推送通知 → 客户端协议层接收 → ❌ 不传递给 LLM/UI
  服务器请求回调 → 客户端协议层接收 → ❌ 不响应
```

**受此影响的能力**:

| 能力 | MCP 方法 | 方向 | 阶跃支持 |
|------|----------|------|----------|
| 工具调用 | tools/call | 客户端→服务器 | ✅ 完全支持 |
| 资源读取 | resources/read | 客户端→服务器 | ✅ 封装为工具可用 |
| 提示词获取 | prompts/get | 客户端→服务器 | ✅ 封装为工具可用 |
| 进度通知 | notifications/progress | 服务器→客户端 | ⚠️ 协议层接收，UI 不展示中间状态 |
| 资源变更订阅 | resources/subscribe | 双向 | ❌ 客户端从不发起订阅 |
| 资源变更通知 | notifications/resources/updated | 服务器→客户端 | ❌ 不处理 |
| Sampling 回调 | sampling/createMessage | 服务器→客户端 | ❌ 不响应 |
| Elicitation 请求 | elicitation/create | 服务器→客户端 | ❌ 不响应 |
| 任务状态通知 | notifications/tasks/status | 服务器→客户端 | ❌ 不处理 |

### 4.2 流式响应的实际行为

阶跃客户端在 HTTP 层面 **确实支持 SSE**：
- 请求头包含 `Accept: application/json, text/event-stream`
- 服务器的 SSE 流在协议层被完整接收

但在集成层，**所有中间事件被静默丢弃，只有最终结果被提交给 LLM**。

实测证据：
- `test_progress_notification`（3 步 / 300ms 间隔）→ 返回 `"Streaming completed"`，无中间步骤
- `test_long_operation`（3 秒 / 1000ms 进度间隔）→ 触发 outputSchema 错误（但即使没有该错误，进度也不会实时展示）
- `gui_automation_demo`（7 步 / 500ms 间隔）→ 只返回最终完成状态

### 4.3 Resources/Prompts 的暴露方式

阶跃不会在初始化阶段主动调用 `resources/list` 或 `prompts/list`，也没有专门的 UI 入口浏览资源和提示词模板。但服务器可以将这些 API 封装为工具（如 `list_resources`、`read_resource`、`list_prompts`、`get_prompt`），LLM 就能通过工具调用间接使用。

### 4.4 outputSchema 严格校验

阶跃客户端对 MCP 2025-11-25 的 `outputSchema` 特性实施了 **严格校验**：
- 如果工具声明了 `outputSchema`，返回 **必须** 使用 `structuredContent`
- 使用传统 `content`（文本数组）会被拒绝，错误码 -32600
- 这一行为 **符合规范要求**，说明阶跃已经部分实现了 2025-11-25 的新特性

---

## 五、与历史测试结果的对比

### 5.1 2026-03-09 测试（MCP 2024-11-05 服务器）vs 2026-03-10 测试（MCP 2025-11-25 服务器）

| 维度 | 03-09 (2024-11-05) | 03-10 (2025-11-25) | 变化 |
|------|---------------------|---------------------|------|
| A 类核心 | 5/5 (100%) | 0/5 (0%) | ⬇️ outputSchema 导致 |
| B 类重要 | 11/11 (100%) | 11/12 (92%) | ⬇️ test_long_operation 受 outputSchema 影响 |
| C 类高级 | 未测 | 2/2 (100%) | 新增 |
| D 类边界 | 未测 | 8/8 (100%) | 新增 |
| G 类 GUI | 未测 | 9/10 (90%) | 新增 |
| 总体 | 26/26 (100%) | 32/44 (73%) | 覆盖面扩大，发现新问题 |

**核心差异**: 03-09 的服务器没有声明 outputSchema，所有工具都用传统 content 返回，因此全部通过。03-10 的服务器升级到 2025-11-25 规范后，部分工具声明了 outputSchema 但返回格式未同步更新，触发了客户端的严格校验。

### 5.2 关键认知修正

| 之前的认知 | 修正后的认知 |
|------------|-------------|
| "A 类核心能力不通过" | 不是客户端不支持核心能力，而是服务器 outputSchema 返回格式不匹配 |
| "流式不工作" | 协议层工作正常，是集成层不传递中间状态给 LLM |
| "Resources/Prompts 不支持" | 封装为工具后可用，只是没有原生 UI 入口 |

---

## 六、针对不同场景的开发建议

### 6.1 开发 MCP 服务器（供阶跃调用）

1. **不要声明 outputSchema**（除非你确定返回 structuredContent）。去掉 outputSchema 后，传统的 content 返回方式在阶跃上完全正常。
2. **不要依赖服务器→客户端的推送**。进度通知、资源变更通知、Sampling 回调在阶跃上都不会被处理。
3. **长任务用轮询模式**。将长任务拆分为 `start_task` → `get_status` → `get_result` 三个工具，让 LLM 主动轮询。
4. **Resources/Prompts 封装为工具**。如果希望 LLM 能使用资源和提示词，将它们包装成普通工具。

### 6.2 开发 GUI Agent 服务器

1. **采用分步工具调用模式**。每个 GUI 操作（点击、输入、截图）作为独立工具，LLM 逐步调用并观察结果后决定下一步。
2. **不要用流式进度反馈**。LLM 看不到中间进度，只能看到最终结果。
3. **每步返回足够的上下文**。包括当前屏幕状态、可见元素列表等，帮助 LLM 做出下一步决策。

### 6.3 测试服务器修复清单

| 优先级 | 修复项 | 具体操作 |
|--------|--------|----------|
| 高 | outputSchema 兼容 | 对 A1-A5、B3、E1 的工具处理函数，将返回格式改为 `structuredContent: {...}` |
| 中 | 注册缺失工具 | 在 tools/list 和 tools/call 中添加 test_elicitation_form、test_elicitation_url、test_sampling_basic、test_sampling_with_tools |
| 低 | GUI 应用列表 | gui_open_app 添加 notepad、calculator 等常见应用支持 |

---

## 七、测试方法论总结

### 7.1 测试执行方式

本次测试采用 **LLM 驱动的端到端测试**：在阶跃桌面助手对话中直接调用 MCP 工具，观察返回结果。这种方式的优势是完全模拟真实使用场景，劣势是无法观察协议层的中间行为（如 SSE 事件流的逐条接收）。

### 7.2 并行测试策略

将互相独立的测试并行发起，显著提高效率：
- 第一批：A1-A5（5 个核心测试并行）
- 第二批：B1-B6（6 个重要测试并行）
- 第三批：B7-B10 + C2 + C5 + D1-D3（资源/提示词 + 边界条件并行）
- 第四批：D4-D8 + E1（边界 + 极端条件并行）
- 第五批：G1-G8（GUI 测试并行）
- 第六批：G9-G10 + H1-H3 + I1-I3（多步操作 + 高级能力并行）

### 7.3 结果判定标准

| 结果 | 判定条件 |
|------|----------|
| PASS | 返回 JSON 中 `success: true`，关键字段值符合预期 |
| FAIL | 返回 MCP 错误码，或 `success: false` 且原因为协议/实现问题 |
| WARN | 功能受限但非协议问题（如服务器不支持特定应用名） |

---

## 八、附录

### 8.1 测试环境配置

```json
{
  "mcpServers": {
    "full-test": {
      "url": "http://127.0.0.1:3372/mcp",
      "headers": {
        "Authorization": "ApiKey mcp_admin_key_prod_2025"
      }
    }
  }
}
```

### 8.2 服务器启动命令

```bash
python full_test_server.py --host 127.0.0.1 --port 3372 --auth both
```

### 8.3 相关文件索引

| 文件 | 说明 |
|------|------|
| `full_test_server.py` | 全量测试服务器源码 |
| `README.md` | 服务器配置和工具分类说明 |
| `FULL_TEST_GUIDE.md` | 逐项测试操作指南 |
| `TEST_PROMPTS.md` | 阶跃 AI 测试指令模板 |
| `MCP全量测试报告_20260310.xlsx` | 本次测试的 Excel 报告（Documents 目录） |
| `docs/STEPFUN_MCP_CAPABILITIES.md` | 阶跃 MCP 能力详细清单 |
| `docs/STEPFUN_STREAMING_LIMITATION.md` | 流式进度通知限制分析 |
| `docs/STREAMABLE_HTTP_TEST_REPORT.md` | Streamable HTTP 测试报告 |
| `docs/TEST_RESULTS_20260310.md` | 03-10 早期测试结果（2024-11-05 服务器） |
| `logs/full_test_20260310_*.jsonl` | 服务器端完整交互日志 |
