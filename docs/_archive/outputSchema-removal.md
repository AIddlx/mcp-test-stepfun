# outputSchema 删除说明

## 背景
MCP 2025-11-05 规范引入了 `outputSchema` 特性，用于定义工具返回值的结构。

## 结论
**阶跃客户端不需要 `outputSchema`，可以安全删除。**

## 验证
- 日志文件: `logs/full_test_20260310_202744.jsonl`
- 删除后服务器运行正常，客户端无任何问题

## 删除内容
1. 工具定义中的 `outputSchema` 块（7处）
2. 工具调用结果中的 `structuredContent` 字段（5处）
3. 相关注释

## 参考
- `outputSchema` 与 `inputSchema` 对应，定义输出结构
- `structuredContent` 用于返回机器可解析的结构化数据
- 对阶跃客户端而言，`content` 字段已足够
