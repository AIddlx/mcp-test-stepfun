**阶跃桌面助手 MCP 能力表格**

| 能力类别 | 阶跃支持状态 | 实测版本 | 说明 |
|---|---|---|---|
| Tools API | ✅ 完全支持 | v0.2.13 | 47+ 工具全部正常调用 |
| Token 认证 | ✅ 完全支持 | v0.2.13 | Bearer Token 通过 headers 正确传递 |
| 复杂参数 | ✅ 完全支持 | v0.2.13 | 嵌套对象、数组、枚举均正确解析 |
| 并发调用 | ✅ 完全支持 | v0.2.13 | 多工具并行调用正常 |
| 超时处理 | ✅ 完全支持 | v0.2.13 | ≥60秒，长操作无超时 |
| Unicode | ✅ 完全支持 | v0.2.13 | 中文/日语/阿拉伯语/Emoji 完美支持 |
| Ping/Logging | ✅ 完全支持 | v0.2.13 | ping/pong、logging/setLevel 正常 |
| Streamable HTTP | ✅ 完全支持 | v0.2.13 | Accept: application/json, text/event-stream |
| SSE 流式 | ✅ 完全支持 | v0.2.13 | Accept 头包含 text/event-stream |
| stdio 模式 | ✅ 完全支持 | v0.2.13 | 支持 npx 命令启动 |
| 会话初始化 | ✅ 完全支持 | v0.2.13 | initialize 正常，能力返回完整 |
| 会话持久化 | ✅ 完全支持 | v0.2.13 | 会话状态跨调用保持 |
| 能力协商 | ✅ 完全支持 | v0.2.13 | 协议版本、Accept 头、连接模式正确 |
| 服务端通知 | ⚠️ 部分支持 | v0.2.13 | 协议层支持，UI 展示待确认 |
| Sampling | ❌ 不支持 | v0.2.13 | sampling/createMessage 回调未响应 |
| Resources API | ❌ 未暴露 | v0.2.13 | 封装为工具，不主动调用 |
| Prompts API | ❌ 未暴露 | v0.2.13 | 封装为工具，不主动调用 |

补充说明：
- **服务端通知**: 服务端可发送 notifications/progress 等通知，但阶跃 UI 是否实时展示待确认
- **Sampling**: 服务端发送 sampling/createMessage 请求后，阶跃客户端未响应回调
- **Resources/Prompts API**: 阶跃将其封装为可调用工具（list_resources/list_prompts），但不会在初始化阶段自动调用
- **协议版本**: MCP 2024-11-05
- **测试日期**: 2026-03-09
