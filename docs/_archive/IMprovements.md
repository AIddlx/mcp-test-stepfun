# MCP 全量测试 v3.0 改进说明

## 改进概述

### 1. 增强类型验证测试（新增 A5)

- 新增 A5 寽合测试项，一次性验证所有类型：确保服务端根据 schema 进行类型转换

- `integer_value`: 整数类型
- `float_value`: 浮点数
- `big_int_value`: 大整数（>9007199254740991)
- `negative_value`: 负数验证
- `array_value`: 数组
- `object_value`: 对象

- **建议**: 使用 `string_value`, `integer_value`, `float_value`, `big_int_value`, `negative_value`, `array_value` 参数进行测试

 返回详细的类型验证结果

- **参数**: schema 中定义的类型 vs实际接收的类型**
  - 注意 MCP 传输层会将所有参数序列化为字符串，这是已知行为，建议服务端根据 schema 进行类型转换

- 如果需要验证类型信息，使用 `test_all_types` 工具传入对应参数

- service端会尝试根据 schema 解析预期类型
- 如果所有参数都是字符串，说明 MCP 传输层的类型转换机制工作正常
但 `received_value` 内容本身是正确的

- **建议**: 使用二分查找确定精确超时阈值
1. 逐步测试 `duration_seconds` 参数（建议从 5 秒开始，每次增加 5 秒)
2. 如果成功，记录为找到的超时边界
3. 如果所有测试都失败,则说明超时阈值小于当前测试的 `duration_seconds`
2 **参数说明**:
| duration_seconds | 操作时长（1-60秒) |
| send_keepalive | 是否每秒发送保活通知保持连接活跃 (default false) |

| **步骤**:
| 1. 逐步测试 5 秒。 15 秒、 20 秒, 25 秒来探索超时边界 |
| 2. 测试不同时长，如果成功则继续增加时长
  - `send_keepalive=true` 测试发送保活通知
- **注意**: 保活通知需要客户端支持才能生效