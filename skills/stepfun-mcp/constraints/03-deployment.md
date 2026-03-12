# 部署阶段约束

> 配置阶跃客户端、选择传输模式、管理缓存。

---

## P001: 命令格式限制

**致命规则 R003 的详细说明。**

阶跃客户端只识别**裸命令名**，不支持完整路径或非标准命令。

| 配置 | 结果 | 原因 |
|------|------|------|
| `"command": "npx"` | ✅ 正常 | 阶跃内置 |
| `"command": "uvx"` | ✅ 正常 | 阶跃内置 uvx 0.9.17 |
| `"command": "node"` | ❌ 失败 | `unknown command: node` |
| `"command": "python"` | ❌ 失败 | `unknown command: python` |
| `"command": "C:\\...\\uvx.exe"` | ❌ 失败 | 不接受带路径的命令 |

### 阶跃内置运行时

| 工具 | 版本 | 位置 |
|------|------|------|
| uvx | 0.9.17 | `StepFun/.../uvx/win32-x64/uvx.exe` |
| Python | 3.11.9 | `StepFun/.../python-3.11.9/python.exe` |
| Node.js | v22.18.0 | `~/.stepfun/runtimes/node/` (动态下载) |

### PATH 注入顺序

阶跃启动 MCP 服务器时，按以下顺序注入 PATH：

```
1. ~/.stepfun/runtimes/node/...     ← 动态安装的 Node.js
2. ~/.stepfun/bin/
3. StepFun/.../python-3.11.9      ← 内置 Python
4. StepFun/.../uvx/win32-x64      ← 内置 uvx
5. 系统 PATH                        ← 包含用户安装的 uvx
```

---

## P002: 工具执行超时

**致命规则 R005 的详细说明。**

| 时长 | 结果 |
|------|------|
| ≤ 55 秒 | 通过 |
| 55-60 秒 | 边界区域（不确定） |
| ≥ 60 秒 | `-32001: Request timed out` |

**规则**：单次工具执行控制在 55 秒以内。长任务拆分为多步调用。

---

## P003: tools/list 缓存

修改工具定义（新增/删除/修改工具的 name/description/inputSchema）后，阶跃仍使用旧的工具列表。

**解决方案**：在阶跃客户端中**重新添加 MCP 配置**（先删除再添加）。

后续版本可能自动刷新。

---

## P004: UVX 缓存问题（不推荐开发时用）

### 为什么不推荐

UVX 在本地开发场景下，每次修改源码后都需要复杂的缓存清理才能让阶跃运行新代码：

1. **五层独立缓存**：系统 uv + 阶跃 uvx，每层独立缓存旧代码
2. **版本号绑定**：`sdists-v9` 以版本号为 key 缓存 `.whl`，版本号不变永远用旧包
3. **无法传参数**：阶跃控制 uvx 调用，无法加 `--refresh`、`--no-cache`
4. **环境变量受限**：`UV_NO_CACHE=1` 会影响所有包安装
5. **安全软件干扰**：Defender/第三方杀软可能锁文件

**每次修改源码后的完整清理流程**：删除 MCP 配置 → 清理 5 个缓存位置 → 更新版本号 → 重新添加。成本过高。

### 五个缓存位置（Windows）

| # | 路径 | 用途 | 清理方式 |
|---|------|------|---------|
| 1 | `AppData\Local\uv\cache\archive-v0` | 系统 uvx 构建环境 | 手动删除 |
| 2 | `AppData\Local\uv\cache\sdists-v9` | 系统 uvx 包缓存 | `uv cache clean` |
| 3 | `~/.stepfun/cache/archive-v0` | 阶跃 uvx 构建环境 | 手动删除 |
| 4 | **`~/.stepfun/cache/sdists-v9`** | **阶跃 uvx .whl 缓存（最关键）** | 手动删除 |
| 5 | `项目/build/` | 本地构建产物 | 手动删除 |

**位置 4 是最容易遗漏的**：以版本号为 key 缓存 `.whl`，版本号不变就永远用旧包。`uv cache clean` 只清理系统 uv 缓存，**不影响**阶跃缓存。

### 完整清理流程

```bash
# 1. 阶跃客户端删除 MCP 配置（终止旧进程）
# 2. 清理全部缓存
rm -rf ~/AppData/Local/uv/cache/archive-v0/*mcp-uvx*
uv cache clean
rm -rf ~/.stepfun/cache/archive-v0
rm -rf ~/.stepfun/cache/sdists-v9
rm -rf 项目/build/

# 3. 更新 pyproject.toml 版本号（如 1.0.0 → 1.1.0）
# 4. 重新添加 MCP 配置
```

### 预防

每次修改源码后同步更新 `pyproject.toml` 版本号。确保包含 `[build-system]`：

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## P005: Defender 锁文件

Windows Defender（特别是与其他安全软件共存时）可能锁定 uvx 下载的 `.whl 文件。

**现象**：`MCP error -32000: Connection closed` + 日志中 `os error -2147024786`

**解决方案**：

```powershell
# 将缓存目录加入排除列表
Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\uv\cache"
Add-MpPreference -ExclusionPath "$env:APPDATA\uv"
Add-MpPreference -ExclusionPath "$env:USERPROFILE\.stepfun\cache"
```

或者重试——第一次失败，第二次缓存已存在，直接成功。

**注意**：单独 Defender 通常不会锁文件。两个安全软件同时开启时才触发（已卸载腾讯管家后未再出现）。

---

## 推荐开发流程

| 阶段 | 推荐方式 | 原因 |
|------|---------|------|
| **编写调试** | HTTP 模式 | `python server.py`，修改即生效 |
| **阶跃 stdio 测试** | NPX 模式 | `npx -y C:/path`，修改即生效 |
| **最终验证** | NPX 或 UVX | 确认在阶跃客户端中正常工作 |

**UVX 验证前提**：代码已确认无误 → 清理全部缓存 + 更新版本号 → 重新添加。
