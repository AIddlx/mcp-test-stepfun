# 排查指南

> 按错误现象分类的排查决策树。每条指向对应的约束 ID。

---

## 一、Connection closed（MCP error -32000）

最常见的问题，有 5 种可能原因。**先看阶跃日志区分。**

日志位置：`%APPDATA%/stepfun-desktop/logs/`

### 决策树

```
MCP error -32000: Connection closed
│
├── 日志中有 "coroutine ... was never awaited"
│   └── 原因: async def main() [K001]
│       └── 修复: 改为同步函数，内部用 asyncio.run()
│       └── 注意: if __name__ == "__main__" 直接运行不会触发此问题
│           只在 uvx 启动时触发（hatch 入口点同步调用）
│
├── 日志中有 "Failed to install: xxx.whl" + "os error -2147024786"
│   └── 原因: Windows Defender/安全软件锁文件 [P005]
│       └── 修复: 将缓存目录加入排除列表，或重试
│       └── 验证: Get-WinEvent 查看 Defender 操作日志
│
├── 日志中有 "ModuleNotFoundError"
│   └── 原因: import 路径错误 [K003]
│       └── 修复: from mcp.server import FastMCP（不是 mcp.server.mcpserver）
│
├── 日志显示 "Installed N packages in Nms" 但行为是旧代码
│   └── 原因: UVX 缓存未清理，运行的是旧 .whl [P004]
│       └── 修复: 清理 5 个缓存位置 + 更新 pyproject.toml 版本号
│       └── 关键: ~/.stepfun/cache/sdists-v9 是最容易被遗漏的缓存
│
├── 日志中有 "unknown command: xxx"
│   └── 原因: 命令格式错误 [P001]
│       └── 修复: 只用裸命令名 npx/uvx，不写路径
│
└── 日志无明确错误
    ├── 进程是否存活? → ps aux | grep mcp / Get-Process
    ├── 是否超时? → 检查工具执行时间 [P002]
    └── HTTP 端口是否可达? → curl http://127.0.0.1:PORT/mcp
```

---

## 二、工具执行超时（-32001）

```
Request timed out
├── 检查工具执行时间
│   ├── > 60秒 → 超过阈值 [P002]
│   │   └── 修复: 拆分为多步调用，控制在 55 秒以内
│   └── ≤ 55秒 → 其他原因
│       └── 检查网络延迟、依赖下载、等待外部服务
```

---

## 三、工具修改后客户端看不到变化

```
新增/修改工具后，阶跃仍显示旧工具列表
└── 原因: tools/list 缓存 [P003]
    └── 修复: 阶跃客户端重新添加 MCP 配置（先删后加）
```

---

## 四、进度通知不显示

```
调用 report_progress() 但阶跃不显示进度
│
├── 阶跃客户端 → 不发送 progressToken [D003]
│   └── 这是最常见原因，目前无解（v0.2.13 限制）
│
├── HTTP stateless=True + SDK progress() → 路由 Bug [K004]
│   └── 修复: 绕过 SDK，直接调用 session.send_progress_notification()
│       并传入 related_request_id=str(ctx.request_id)
│
└── 代码未检查 progressToken 是否存在
    └── 修复: 添加 if ctx.meta and ctx.meta.progressToken 检查
```

---

## 五、outputSchema 报错

```
-32600: Tool xxx has an output schema but did not return structured content
└── 原因: 阶跃不消费 outputSchema [D002]
    └── 修复: 删除工具定义中的 outputSchema，只用 content 返回
```

---

## 六、UVX 代码更新后仍运行旧版

```
修改源码后阶跃仍运行旧代码
│
├── 1. 检查 pyproject.toml 版本号是否更新
│   └── 未更新 → 更新（如 1.0.0 → 1.1.0）
│
├── 2. 清理 5 个缓存位置 [P004]
│   ├── rm -rf ~/AppData/Local/uv/cache/archive-v0/*包名*
│   ├── uv cache clean
│   ├── rm -rf ~/.stepfun/cache/archive-v0
│   ├── rm -rf ~/.stepfun/cache/sdists-v9     ← 最关键
│   └── rm -rf 项目/build/
│
├── 3. 删除阶跃 MCP 配置 → 重新添加
│
└── 4. 验证
    └── 查看阶跃日志确认安装的是新版本
    └── 日志位置: %APPDATA%/stepfun-desktop/logs/
```

---

## 七、常见错误码

| 错误码 | 含义 | 常见原因 | 对应约束 |
|--------|------|---------|---------|
| -32000 | Connection closed | 进程崩溃 | R002, K001, K003, P004, P005 |
| -32001 | Request timed out | 工具执行 > 60 秒 | P002 |
| -32600 | Invalid Request | outputSchema 格式问题 / 请求格式错误 | D002 |
| -32601 | Method not found | 方法名错误 | — |
| -32602 | Invalid params | 参数类型/格式不匹配 | — |
| 406 | Not Acceptable | HTTP SSE 模式缺少 Accept 头 | D003 |

---

## 八、排查工具

```bash
# 查看 UVX 实际安装的包版本
uvx --verbose --from <项目路径> <入口名> --help 2>&1

# 清理系统 uv 缓存（注意：不影响阶跃缓存）
uv cache clean

# 检查 Defender 是否有相关事件
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Windows Defender/Operational'
    StartTime = (Get-Date).AddHours(-1)
} -MaxEvents 50

# 测试 HTTP 端点
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# 测试带 progressToken 的 SSE 流式响应（控制台验证）
curl -N -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"long_task","arguments":{},"_meta":{"progressToken":"test-token"}}}'

# 检查阶跃内置 uvx 版本
# StepFun/.../uvx/win32-x64/uvx.exe --version

# 检查 MCP 服务器进程是否存活
Get-Process -Name "mcp-*" -ErrorAction SilentlyContinue | Format-List Name, Id, StartTime
```
