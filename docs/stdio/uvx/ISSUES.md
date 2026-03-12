# UVX 模式问题汇总

> 阶跃 AI 桌面助手 v0.2.13 | Windows 11 | 最后更新: 2026-03-12

## 结论

**UVX 模式在阶跃桌面客户端可以正常工作，但不建议在本地编写调试时使用。**

### 不推荐用于本地开发的原因

UVX 在本地开发调试场景下面临严重的缓存问题，修改源码后很难让阶跃客户端运行到最新代码：

| 问题 | 说明 |
|------|------|
| **五层独立缓存** | 系统 uv 缓存（archive-v0 / sdists-v9）+ 阶跃 uvx 缓存（archive-v0 / sdists-v9 / builds-v0），每层都独立缓存旧代码 |
| **版本号绑定缓存** | `sdists-v9` 中以版本号为 key 缓存 .whl，版本号不变则永远使用旧包 |
| **无法传递 uvx 参数** | 阶跃客户端控制 uvx 调用，无法添加 `--refresh`、`--no-cache` 等标志 |
| **环境变量受限** | `UV_NO_CACHE=1` 会影响该次调用的所有包安装，不适合常规使用 |
| **Windows 安全软件干扰** | Defender / 第三方杀软可能锁定 .whl 文件导致安装失败（腾讯管家已卸载，Defender 仍存在） |

**每次修改源码后的完整清理流程**：删除 MCP 配置 → 清理 5 个缓存位置 → 更新版本号 → 重新添加配置。成本过高。

### 推荐的开发调试方式

| 场景 | 推荐方式 |
|------|---------|
| **本地编写调试** | 使用 HTTP 模式（`python -m mcp_http_sdk.server`），无需 uvx，修改即生效 |
| **阶跃客户端测试** | 使用 NPX 模式（`npx -y C:/path/to/npx`），修改即生效，无需缓存管理 |
| **UVX 验证** | 确认代码无误后，再清理全部缓存 + 更新版本号，通过 UVX 模式最终验证 |

---

## 历史问题记录

之前（2026-03-11）遇到的连接失败问题，经过排查后恢复正常。

---

## 阶跃内置运行时

经调查确认，阶跃客户端内置了以下运行时：

| 工具 | 版本 | 位置 |
|-----|------|------|
| uvx | 0.9.17 | `...\tools\uvx\win32-x64\uvx.exe` |
| Python | 3.11.9 | `...\tools\win\python-3.11.9\python.exe` |
| Node.js | v22.18.0 (动态下载) | `~\.stepfun\runtimes\node\` |

### PATH 注入顺序

阶跃启动 MCP 服务器时，按以下顺序注入 PATH：

```
1. ~/.stepfun/runtimes/node/...     ← 动态安装的 Node.js
2. ~/.stepfun/bin/
3. StepFun/.../python-3.11.9      ← 内置 Python
4. StepFun/.../uvx/win32-x64      ← 内置 uvx
5. 系统 PATH                        ← 包含用户安装的 uvx
```

### uvx 的 Python 来源

内置 uvx 0.9.17 使用 `%USERPROFILE%\AppData\Roaming\uv\python\` 中的 Python：

```
%USERPROFILE%\AppData\Roaming\uv\python\
├── cpython-3.12.9-windows-x86_64-none\   ← uvx 当前使用
└── cpython-3.11.14-windows-x86_64-none\  ← 2026-03-08 安装
```

---

## 问题分类

### 1. 命令识别限制（阶跃客户端限制）

| 错误信息 | 配置示例 | 原因 |
|---------|---------|------|
| `unknown command: python` | `python C:\...\run_mcp_server.py` | 阶跃不识别 `python` 命令 |
| `unknown command: <path>/uvx.exe` | `C:\Users\...\.local\bin\uvx.exe mcp-uvx-test` | 阶跃不接受带路径的命令 |

**结论**: 阶跃客户端只能识别**裸命令名**（如 `uvx`、`npx`），不支持完整路径。

---

### 2. UVX 连接失败（已解决：Windows Defender 导致）

| 错误信息 | 时间范围 | 出现次数 |
|---------|---------|---------|
| `os error -2147024786` (系统无法打开指定的设备或文件) | 01-28 ~ 03-11 | 7 次 |
| `MCP error -32000: Connection closed` | 01-28 ~ 03-11 | 7 次 |

**根因：Windows Defender 实时保护锁定了 uvx 下载的 .whl 文件。**

#### 确凿证据（Windows 事件日志）

阶跃客户端日志和 Windows Defender 操作日志的交叉对比：

```
16:04:34  阶跃启动 uvx 0.9.17
16:04:35  uvx 失败: Failed to install: mcp-1.26.0-py3-none-any.whl
16:04:35  uvx 失败: Caused by: 系统无法打开指定的设备或文件。 (os error -2147024786)
16:04:35  阶跃: MCP error -32000: Connection closed
   ↓ 33 分钟无 MCP 操作
16:37:22  Defender: ECS 配置变更 (Tag 更新 + DLP 保护启用)
16:37:23  Defender: 检测引擎热重载 (CheckToEnableIOAV → LoadingEngine)
16:37:25  Defender: 引擎重新加载 (Controls\211 = 0x1, WdConfigHash 重置)
16:37:25  Defender: 服务初始化完成 (LoadingEngine → ServiceStartedSuccessfully)
   ↓ 4 秒后
16:37:29  uvx 成功: Installed 32 packages in 695ms
16:37:39  阶跃: Connect MCPServer Done

16:47:43  Defender 安全引擎正式更新: 1.445.411.0 → 1.445.472.0
```

**数据来源**：
- 阶跃日志: `%APPDATA%\stepfun-desktop\logs\2026-03-11 15-56-41.log`
- Defender 日志: `Microsoft-Windows-Windows Defender/Operational` 事件 ID 5007, 2000

#### 机制解释

1. uvx 下载 .whl 文件到临时目录
2. Defender 和/或腾讯管家实时保护同时扫描并锁定该文件
3. uvx 无法写入/打开文件 → `os error -2147024786`
4. 关闭腾讯管家防护后，Defender 单独的 IOAV 扫描不会锁定 .whl 文件
5. 两个安全软件同时开启时才会触发文件锁定

#### 实验验证

| 时间 | 腾讯管家防护 | Windows Defender | 结果 |
|------|------------|-----------------|------|
| 21:48 | 开启 | 开启 | 失败（httpx 被锁） |
| 21:51 | 开启 | 开启 | 成功（重试，缓存已存在） |
| 22:02 | **关闭** | 开启 | **成功（首次直接通过）** |

**结论：腾讯管家 + Defender 双锁问题。** 两个安全软件同时开启时，文件锁定行为会叠加，导致 uvx 下载的 .whl 文件被锁定。关闭其中任意一个即可解决。

#### 解决方案

**方案一（推荐）：将 uv 缓存目录添加到 Windows Defender 排除列表**

```
C:\Users\<用户名>\AppData\Local\uv\cache\
C:\Users\<用户名>\AppData\Roaming\uv\
C:\Users\<用户名>\.stepfun\cache\
```

在 PowerShell（管理员）中执行：
```powershell
Add-MpPreference -ExclusionPath "C:\Users\<用户名>\AppData\Local\uv\cache"
Add-MpPreference -ExclusionPath "C:\Users\<用户名>\AppData\Roaming\uv"
Add-MpPreference -ExclusionPath "C:\Users\<用户名>\.stepfun\cache"
```

**方案二：临时关闭腾讯管家实时防护**

在腾讯管家设置中关闭实时防护（QQPCRTP 服务仍运行但不再扫描）。注意：这会降低系统安全性，建议仅在配置 MCP 服务器时临时关闭。

**方案三：重试**

uvx 第一次安装时被锁定失败，第二次重试时 .whl 文件已在缓存中，不受 IOAV 扫描影响，直接成功。只需在阶跃中重新添加 MCP 配置即可。

#### 可能的原因（已排除）

以下推测均已排除：
- 腾讯管家单独导致（关闭后 Defender 仍会触发）
- uv 缓存损坏（清理缓存后问题复现）
- 网络问题（下载正常，写入失败）

---

### 3. 代码层面问题（已解决）

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'mcp.server.mcpserver'` | 导入路径错误 | 使用 `from mcp.server import FastMCP` |
| `coroutine 'main' was never awaited` → `MCP error -32000: Connection closed` | `main()` 定义为 `async def`，hatch 入口点同步调用 | 改为 `def main()` 内部用 `asyncio.run(_run())` |

---

### 4. 版本号缓存问题（已解决，2026-03-12）

#### 现象

修改 `server.py` 源码（修复 `async def main()` 为 sync `main()`）后，阶跃客户端仍然运行旧代码，报错：

```
[stderr]: <coroutine object main at 0x0000021FD3BEC130>
[stderr]: sys:1: RuntimeWarning: coroutine 'main' was never awaited
MCP error -32000: Connection closed
```

#### 排查过程

1. **首次怀疑 Defender 锁文件**：检查 Windows Defender 操作日志（Event ID 5007/2000），发现当日无异常事件。腾讯管家已卸载，排除双锁问题。
2. **确认包安装成功**：阶跃日志显示 `Installed 39 packages in 504ms`，uvx 构建环境创建成功，无 Defender 干扰。
3. **对比缓存与源码**：

   | 位置 | `main()` 形式 | 说明 |
   |------|-------------|------|
   | 源码 `sdk/uvx/src/mcp_uvx_sdk/server.py` | `def main():` + `asyncio.run(_run())` | **正确（已修复）** |
   | 阶跃缓存 `.stepfun/cache/sdists-v9/.../mcp_uvx_sdk-1.0.0.whl` | `async def main():` | **旧版** |

4. **根因确认**：`pyproject.toml` 版本号仍为 `1.0.0`，uvx 发现有同版本缓存 `.whl` 直接使用，**不重新构建**。

#### 根因

**uvx 通过版本号判断是否需要重新构建。** 缓存的 `.whl` 文件（在 `sdists-v9` 中）以版本号为 key，版本号不变则永远使用旧包，即使源码已修改。

缓存路径示例：
```
.stepfun/cache/sdists-v9/path/5f966e875e9727bb/AvhBqjEOS99DZaNWSO2aY/mcp_uvx_sdk-1.0.0-py3-none-any.whl
```

#### 解决方案

**更新 `pyproject.toml` 版本号**（如 `1.0.0` → `1.1.0`）：

```toml
[project]
name = "mcp-uvx-sdk"
version = "1.1.0"   # ← 每次修改源码后递增
```

版本号变更后，uvx 发现缓存中无对应版本，强制从最新源码重建。

#### 经验教训

- **清缓存不够**：清理 `archive-v0` 只删除了构建环境，`sdists-v9` 中的 `.whl` 仍然存在
- **版本号是关键**：每次修改源码后必须同步更新版本号，这是最可靠的强制重建方式
- **区分错误类型**：同样是 `Connection closed`，可能是代码问题（coroutine never awaited）或 Defender 锁文件，需先查看日志区分

---

## NPX vs UVX 对比

| 特性 | NPX (Node.js) | UVX (Python) |
|-----|---------------|--------------|
| 运行本地项目 | `npx -y ./local-dir` 直接运行 | 需要先构建/安装包 |
| 依赖处理 | 使用项目内的 node_modules | 需要创建临时虚拟环境 |
| Windows 兼容 | 非常成熟 | uv 工具相对较新 |
| 阶跃支持 | `npx -y C:/path/to/npx` 正常 | ✅ 当前可用 |
| 阶跃内置 | Node.js v22.18.0 (动态下载) | uvx 0.9.17 (内置) |

**关键差异**: NPX 可以直接执行本地 JS 文件，而 UVX 需要从 PyPI 下载依赖并在临时虚拟环境中运行。

---

## 如果 UVX 再次失败

### 排查步骤

1. 查看阶跃日志:
   ```
   C:\Users\<用户名>\AppData\Roaming\stepfun-desktop\logs\
   ```

2. 在命令行用 verbose 模式测试:
   ```bash
   uvx --verbose --from <项目路径> mcp-uvx-test --help 2>&1
   ```

3. 检查 uv 缓存状态:
   ```bash
   uv cache clean
   ```

4. 检查网络连接:
   ```bash
   curl -I https://mirrors.cloud.tencent.com/pypi/simple/mcp/
   ```

5. 如果遇到文件操作错误（如 `os error -2147024786`），优先排查杀毒软件干扰

6. 如果修改了服务器代码但运行的是旧版本，需要清理阶跃缓存（见下方"缓存问题排查"）

### 缓存问题：代码更新后仍运行旧版

**现象**：修改了 `src/` 下的代码，但阶跃调用的仍是旧版。

**原因**：阶跃内置 uvx 会将构建环境缓存在 `.stepfun\cache\` 中，不会自动检测源码变更。

**排查方法**：

```powershell
# 1. 查看当前运行的 mcp-uvx-test 进程的实际路径
Get-Process -Name "mcp-uvx-test" -ErrorAction SilentlyContinue |
    Select-Object Id, Path
# 如果路径是 .stepfun\cache\... 说明用的是缓存

# 2. 检查进程启动时间
Get-Process -Name "mcp-uvx-test" -ErrorAction SilentlyContinue |
    Format-List Name, Id, StartTime
```

**五个独立的缓存位置**：

| # | 路径 | 用途 | 清理方式 | 是否影响阶跃 |
|---|------|------|---------|------------|
| 1 | `AppData\Local\uv\cache\archive-v0` | 系统 uvx 构建环境缓存（含 Scripts/*.exe 和 Lib/site-packages/） | 手动删除目录 | 间接影响 |
| 2 | `AppData\Local\uv\cache\sdists-v9` | 系统 uvx 源码分发包缓存（.whl 等） | `uv cache clean` 或手动删除 | 间接影响 |
| 3 | `.stepfun\cache\archive-v0` | 阶跃内置 uvx 构建环境缓存 | 手动删除目录 | **直接影响** |
| 4 | `.stepfun\cache\sdists-v9` | **阶跃内置 uvx .whl 包缓存（关键！）** | 手动删除目录 | **直接影响** |
| 5 | `stdio/uvx/build/` | 本地手动构建产物 | 手动删除目录 | 不影响 |

**注意**：位置 1 和 2 在同一个 `uv\cache` 目录下但子目录不同。位置 3 和 4 在 `.stepfun\cache\` 下，**和系统 uv 完全独立**。`uv cache clean` 只清理系统 uv 缓存，不影响阶跃缓存。

**位置 4 是最容易遗漏的**：阶跃内置 uvx 在 `sdists-v9/path/` 下缓存构建好的 `.whl` 文件，以版本号为 key。如果 `pyproject.toml` 版本号未变，uvx 直接使用缓存的 .whl，**不会重新构建**，即使源码已修改。

**正确操作顺序**：

1. **在阶跃客户端删除 MCP 配置**（这会终止旧进程）
2. **确认进程已停止**：`Get-Process -Name "mcp-uvx-sdk"` 无结果
3. **清理全部五个缓存位置**：
   ```bash
   # 系统 uv 构建环境缓存
   rm -rf ~/AppData/Local/uv/cache/archive-v0/*mcp-uvx-sdk*
   rm -rf ~/AppData/Local/uv/cache/archive-v0/*mcp-uvx*

   # 系统 uv 源码分发包缓存
   uv cache clean

   # 阶跃内置 uvx 构建环境缓存
   rm -rf ~/.stepfun/cache/archive-v0

   # 阶跃内置 uvx .whl 包缓存（关键！）
   rm -rf ~/.stepfun/cache/sdists-v9

   # 本地构建产物
   rm -rf stdio/uvx/build/
   ```
4. **更新 `pyproject.toml` 版本号**（如 `1.0.0` → `1.1.0`）
5. **重新添加 MCP 配置**（阶跃会用新代码重新构建）

**预防措施（首选）**：每次修改源码后，同步更新 `pyproject.toml` 中的版本号（如 `1.0.0` → `1.1.0`）。uvx 通过版本号判断是否需要重新构建，版本号变更后即使缓存存在也会强制拉取新代码。同时确保 `pyproject.toml` 包含 `[build-system]` 声明：

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**如果更新版本号后仍运行旧版**，再执行上述全部缓存清理操作。

### 备选方案

1. **使用 NPX 模式**（已验证完全正常）
2. **使用 HTTP 模式**
3. **向阶跃团队反馈**

---

## Windows 环境排查经验

Windows 环境比 Linux/Mac 更复杂，以下是实际遇到的问题和排查方法。

### 常见 Windows 特有问题

| 问题 | 说明 | 排查方法 |
|------|------|---------|
| 杀毒软件锁定文件 | Defender 或第三方安全软件实时扫描会锁定临时文件，导致 uvx 下载的 .whl 无法打开 | 查看 Defender 操作日志，将缓存目录加入排除列表 |
| 路径格式 | 反斜杠、空格、中文路径在配置中容易出错 | 统一使用正斜杠 `C:/path/to` |
| GUI ≠ 服务 | 关闭安全软件 GUI 界面不等于关闭后台服务/实时保护 | 用 `Get-Service` 检查服务状态 |
| 内置工具链冲突 | 客户端内置的 uvx/Python 可能与系统版本不同 | 检查客户端的 PATH 注入顺序 |
| 编码问题 | GBK vs UTF-8 导致 PowerShell 输出乱码 | 用 `-Encoding UTF8` 或将命令写入 .ps1 脚本执行 |

### 排查 Windows Defender 干扰

本次问题的核心排查过程：

1. **从错误码入手**：`os error -2147024786` = Windows 文件锁定错误

2. **查看阶跃客户端日志**，记录 uvx 失败的确切时间

3. **交叉比对 Defender 操作日志**：
   ```powershell
   # 查看 Defender 在该时间段的所有事件
   Get-WinEvent -FilterHashtable @{
       LogName = 'Microsoft-Windows-Windows Defender/Operational'
       StartTime = '<失败时间前5分钟>'
       EndTime = '<失败时间后10分钟>'
   } -MaxEvents 100
   ```
   重点关注的 Event ID：
   - `5007` — 配置变更（IOAV 开关、引擎重载）
   - `2000` — 安全引擎版本更新
   - `2010` — 云端保护签名更新

4. **检查引擎版本是否变更**：
   ```powershell
   # 查看当前引擎版本
   Get-MpComputerInformation | Select-Object AMProductVersion, EngineVersion
   ```

5. **如果确认为 Defender 导致**，将 uv 缓存和阶跃缓存都加入排除列表：
   ```
   C:\Users\<用户名>\AppData\Local\uv\cache\
   C:\Users\<用户名>\AppData\Roaming\uv\
   C:\Users\<用户名>\.stepfun\cache\
   ```

### 排查第三方安全软件干扰

以腾讯电脑管家为例：

```powershell
# 检查服务状态（关闭 GUI 不等于停止服务）
Get-Service -Name "QQPCRTP" | Format-List Name, Status, StartType

# 查看 WMI 安全产品状态
Get-CimInstance -Namespace "root/SecurityCenter2" -ClassName AntiVirusProduct |
    Format-List displayName, productState

# 搜索服务启停事件
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Service Control Manager'
    StartTime = '<排查时间范围>'
} | Where-Object { $_.Message -match 'QQPCRTP' }
```

注意：关闭安全软件的 GUI（托盘图标）通常不会停止后台保护服务。需要确认实际服务状态。

---

## 相关文件

- [README.md](./README.md) - UVX 模式说明
- [TEST_REPORT.md](./TEST_REPORT.md) - 测试报告
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - 开发指南
