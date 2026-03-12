# MCP Session Management 测试指南

## 测试目的

验证阶跃桌面助手对 MCP 2024-11-05 Session Management 能力的支持。

## 新增测试工具

| 工具 | 说明 |
|------|------|
| `test_session_init` | 测试会话初始化，返回协议能力和版本信息 |
| `test_session_persistence` | 测试会话持久化，先存储后读取验证状态保持 |
| `test_session_capabilities` | 测试能力协商，返回客户端和服务器能力信息 |

## 测试配置

```json
{
  "mcpServers": {
    "streamable-test": {
      "url": "http://127.0.0.1:3371/mcp"
    }
  }
}
```

## 测试清单

### 测试 1：会话初始化

**工具**: `test_session_init`

**预期结果**:
```json
{
  "success": true,
  "test": "session_init",
  "protocol_version": "2024-11-05",
  "session_supported": true,
  "capabilities": {
    "tools": {"listChanged": true},
    "resources": {"subscribe": true, "listChanged": true},
    "prompts": {"listChanged": true},
    "streaming": true
  }
}
```

**验证点**:
- ⬜ protocol_version 是否正确？
- ⬜ capabilities 是否包含预期能力？

---

### 测试 2：会话持久化

**步骤 1 - 存储值**:
```
工具: test_session_persistence
参数: {
  "action": "set",
  "key": "my_test_key",
  "value": "test_value_123"
}
```

**预期结果**:
```json
{
  "success": true,
  "action": "set",
  "key": "my_test_key",
  "stored_value": "test_value_123",
  "note": "Value stored in session. Call with action='get' to retrieve."
}
```

**步骤 2 - 读取值**:
```
工具: test_session_persistence
参数: {
  "action": "get",
  "key": "my_test_key"
}
```

**预期结果**:
```json
{
  "success": true,
  "action": "get",
  "key": "my_test_key",
  "value": "test_value_123",
  "stored_at": "2026-03-09T...",
}
```

**验证点**:
- ⬜ 存储操作是否成功？
- ⬜ 读取操作是否返回之前存储的值？
- ⬜ 会话状态是否跨调用保持？

---

### 测试 3：能力协商

**工具**: `test_session_capabilities`

**预期结果**:
```json
{
  "success": true,
  "test": "session_capabilities",
  "client_capabilities": {
    "protocol_version": "2024-11-05",
    "accept": "application/json, text/event-stream",
    "user_agent": "stepfun-desktop/...",
    "connection": "keep-alive"
  },
  "server_capabilities": {
    "tools": {"listChanged": true},
    "resources": {"subscribe": true, "listChanged": true},
    "prompts": {"listChanged": true},
    "streaming": true
  }
}
```

**验证点**:
- ⬜ 客户端协议版本是否正确？
- ⬜ Accept 头是否包含 text/event-stream？
- ⬜ 连接是否为 keep-alive？

---

## 测试结果记录表

| 编号 | 测试项 | 工具调用 | 状态保持 | 能力协商 | 结果 |
|------|--------|----------|----------|----------|------|
| 1 | test_session_init | ⬜ | - | - | ⬜ |
| 2 | test_session_persistence (set) | ⬜ | - | - | ⬜ |
| 3 | test_session_persistence (get) | ⬜ | ⬜ | - | ⬜ |
| 4 | test_session_capabilities | ⬜ | - | ⬜ | ⬜ |

---

## 预期结论

| 功能 | 阶跃支持状态 |
|------|--------------|
| **会话初始化** | ⚠️ 待验证 |
| **会话持久化** | ⚠️ 待验证 |
| **能力协商** | ⚠️ 待验证 |

测试完成后，请填写结果并记录发现。
