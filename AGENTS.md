# AGENTS.md — 项目规则

本文件是 Tonybot Motion Workflow 仓库的长期协作规则。Codex、Copilot 和其他 AI 协作者进入本仓库后，应先读取本文件，再读取 README 和相关专题文档。

## 1. 项目定位

本仓库围绕 Tonybot `.rob` 动作文件工作，核心目标是：

1. 解析 `.rob` / `ACT-40` 动作容器。
2. 独立复现 `EYPT` 保护层的 `TEA-32` 加解密。
3. 基于官方动作库做安全动作拼接和编舞。
4. 把编舞 JSON 编译成 `.rob`、审计报告和时间线 HTML。
5. 用 3D FK 模拟器可视化预览舵机姿态、质心、支撑面和平衡得分。

项目有两层知识来源：
- **官方 SDK 层**：Hiwonder Python SDK（`Hiwonder.Tonybot`、`Hiwonder.Buzzer`、`Hiwonder_IIC` 等）已从官方示例和 `main.py` 设备端源码中提取完整 API 参考，见记忆 `[[tonybot-python-api]]`。
- **逆向工程层**：`.rob`/`ACT-40` 容器格式和 `EYPT`/`TEA-32` 加密层通过逆向分析确认，结论已固化到工具链。

不要把本项目误判为普通 Web、Java、Gradle 或 Minecraft 模组项目。

## 2. 必读文档顺序

进入项目后按下面顺序建立上下文：

1. `README.md`：项目范围、目录结构和常用命令。
2. `python-toolkit/文档/07-动作库目录.md`：**官方动作库完整索引**，按功能分类，编舞选段第一参考。
3. `python-toolkit/动作文件逆向说明.md`：`.rob` / `EYPT` 逆向结论和验收标准。
4. `python-toolkit/动作安全规范.md`：动作安全边界和审计口径。
5. `python-toolkit/编舞工作流说明.md`：从需求到 `.rob` 的工作流。
6. `python-toolkit/算法指南.md`：设备端控制逻辑（含官方 SDK API 调用方式）。
7. `python-toolkit/文档/09-Python开发指南.md`：**Python API 参考**，三种方式用代码生成 .rob 文件。
8. `python-toolkit/可视化模拟器/动作模拟器.html`：**3D FK 模拟器**，双击即开，实时预览姿态和平衡。

## 3. 逆向工程规则

当前可作为已完成结论使用的部分：

1. `.rob` 外层容器是 `ACT-40`。
2. 文件结构是 `16 字节文件头 + frame_count * 248 字节帧区`。
3. 明文帧前 16 个槽位是有效动作槽位，后 24 个槽位是 filler。
4. `EYPT` 使用标准 `TEA-32`，密钥见 `python-toolkit/rob_crypto.py` 的 `ENCRYPT_ARRAY`。
5. 加密范围是完整文件头之后的 `data[16:]`，文件头本身不参与 TEA。
6. 4 个官方 `EYPT` 样本必须能解密成明文并重加密回原始密文，且逐字节一致。

当前不能作为已完成结论使用的部分：

1. 有效槽位第 2、第 3 个 16 位字段的精确物理语义。
2. 帧头保留字段在设备端是否有隐藏运行时用途。
3. 任意手写舵机轨迹的绝对硬件安全性。

## 4. 动作生成规则

默认采用“复用官方动作帧”的保守策略：

1. 优先从 `python-toolkit/动作/` 目录选取官方或已审计动作段。
2. 可以裁剪、重复、拼接动作帧。
3. 不要默认手写全新舵机轨迹。
4. 如确需自定义帧，必须让所有字段落在官方样本包络内。
5. 输出 `.rob` 前必须运行安全审计。

生成新舞蹈时，标准产物应包括：

1. `python-toolkit/编舞/<名称>.json`
2. `python-toolkit/动作/<名称>.rob`
3. `python-toolkit/编舞/<名称>.report.json`
4. `python-toolkit/编舞/<名称>.timeline.html`

## 5. 验证规则

改动 Python 脚本后至少执行：

```powershell
cd python-toolkit && uv run python -m py_compile rob_reverse.py rob_crypto.py rob_compose.py rob_safety.py dance_workflow.py main.py
```

改动 `rob_crypto.py`、`rob_reverse.py` 或逆向结论后，必须验证 4 个 `EYPT` 样本：

```powershell
cd python-toolkit && uv run python -c "import pathlib, rob_crypto; files=[p for p in pathlib.Path('动作').glob('*.rob') if p.read_bytes()[8:12]==b'EYPT']; failed=[p.name for p in files if rob_crypto.encrypt_action_bytes(rob_crypto.decrypt_action_bytes(p.read_bytes())) != p.read_bytes()]; print('eypt_files=', len(files)); print('failed=', failed); raise SystemExit(0 if len(files)==4 and not failed else 1)"
```

改动动作、编舞或安全规则后至少执行：

```powershell
cd python-toolkit && uv run python rob_safety.py "动作\159号自制舞蹈.rob"
```

合格标准：

1. Python 语法检查通过。
2. `EYPT` 样本往返无差异。
3. 安全审计输出 `violations=0`。

## 6. 版本和日志规则

任何功能、文档、资源或规则更新，都要同步维护版本记录：

1. 更新 `VERSION`。
2. 更新 `CHANGELOG.md`。
3. 在 `更新日志/` 下新增对应版本条目。

版本默认按 patch 递增；较大功能更新升 minor；major 只在用户明确要求时提升。

## 7. Windows 环境规则

本仓库在 Windows 上维护，注意以下问题：

1. PowerShell 读取中文 UTF-8 文件时显式使用 `-Encoding UTF8`。
2. 终端中文文件名可能显示乱码，但实际文件名仍是 UTF-8。
3. `apply_patch` 或某些写文件方式可能产生 NTFS `ReparsePoint` 属性。
4. 编辑后如果怀疑文件属性异常，用 `[System.IO.File]::ReadAllBytes` + `WriteAllBytes` 原地重写正式路径。
5. 不要用会破坏中文编码的 ANSI 读写方式处理 JSON、Markdown 或 lang 类文件。
6. 后续命令默认优先使用 PowerShell 7（`pwsh`），这样中文输出更稳定，不容易乱码；只有在 `pwsh` 明确不可用或宿主限制时才退回其他 shell。

## 8. Git 工作区规则

1. 仓库可能存在用户已有未提交改动，不要回滚无关文件。
2. 不要使用 `git reset --hard`、`git checkout --` 等破坏性命令，除非用户明确要求。
3. 修改前后用 `git status --short` 识别自己负责的文件范围。
4. 不要把临时验证产物留在 `python-toolkit/动作/` 或 `python-toolkit/编舞/` 目录。

## 9. 代码风格规则

1. Python 脚本尽量只依赖标准库。
2. 常量放在文件顶部，复用已有格式常量，例如帧长、槽位数和 TEA 参数。
3. 二进制解析保持小端规则明确，不要引入隐式平台端序。
4. 新增错误信息要直接指出文件、帧、槽位或字段。
5. 文档用中文说明工程结论，用命令块给出可复现步骤。
