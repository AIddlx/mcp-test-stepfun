# 阶跃 MCP 服务器开发指南（通用）

> 本文档适用于所有传输模式（HTTP URL / NPX / UVX）

## 一、阶跃客户端特性

### 1.1 协议版本
- **支持版本**: MCP 2025-11-25
- **协商机制**: 客户端在 `initialize` 时发送协议版本

### 1.2 传输模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| HTTP URL | Streamable HTTP | 远程服务、云端部署 |
| NPX | Node.js stdio | 本地 Node.js 工具 |
| UVX | Python stdio | 本地 Python 工具 |

### 1.3 超时阈值
- **请求超时**: 55~60 秒
- **建议**: 长操作控制在 55 秒以内，或使用进度通知保持心跳

## 二、兼容性要求

### 2.1 outputSchema 问题 ⚠️

**重要**: 阶跃客户端对 `outputSchema` 严格校验

```
❌ 错误做法：
工具声明 outputSchema 但返回 content

✅ 正确做法：
不声明 outputSchema，直接返回 content
```

**建议**: 除非确定客户端支持 `structuredContent`，否则不要声明 `outputSchema`

### 2.2 流式响应限制

- SSE 中间事件**不会传递给 LLM**
- 只有最终结果可见
- 进度通知：协议层接收，UI 不展示

**建议**: 长任务使用轮询模式
```
start_task → get_status → get_result
```

### 2.3 tools/list 缓存

- 客户端会缓存工具列表
- 修改工具定义后需要**重新连接**或**刷新客户端**

## 三、数据类型支持

| 类型 | 支持 | 备注 |
|------|------|------|
| string | ✅ | UTF-8 编码 |
| integer | ✅ | |
| number (float) | ✅ | |
| boolean | ✅ | |
| null | ✅ | |
| array | ✅ | 支持嵌套 |
| object | ✅ | 支持深层嵌套 |

## 四、最佳实践

### 4.1 工具设计
1. 单个工具执行时间 < 55 秒
2. 返回结构化的 JSON（便于 LLM 解析）
3. 包含 `success` 字段表示成功/失败
4. 错误时返回 `isError: true`

### 4.2 错误处理
```json
{
  "success": false,
  "error": "错误描述",
  "error_code": "ERROR_CODE"
}
```

### 4.3 Unicode 处理
- 中文字符正常支持，无需额外处理
- 确保返回 JSON 使用 UTF-8 编码

## 五、测试方法

1. 使用本项目提供的测试服务器
2. 逐项测试核心功能
3. 记录兼容性问题

---

## 各模式特定指南

- [HTTP URL 开发指南](./http-url/DEVELOPMENT_GUIDE.md)
- [NPX 开发指南](./npx/DEVELOPMENT_GUIDE.md)（待完善）
- [UVX 开发指南](./uvx/DEVELOPMENT_GUIDE.md)（待完善）
