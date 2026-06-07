# Tonybot Motion Studio

> **AI 辅助动作创作工作台** — 从需求到 .rob 的完整动作创作闭环。

Tonybot Motion Studio 围绕 Tonybot 机器人动作文件构建，从单纯的逆向工程和自动化脚本，
升级为涵盖 **AI 辅助创作、3D 预览、关键帧编辑、安全审计和 .rob 导出** 的完整工作流平台。

核心能力：

1. `.rob` / `ACT-40` 动作文件逆向与 `EYPT`/`TEA-32` 独立加解密。
2. **Tonybot 3D 动作预览器** — FK 骨骼姿态预览，拖拽 .rob 即可播放，减少线下反复掰机器人调动作。
3. **motion.json** — 可编辑动作工程格式，AI/人类友好，版本控制友好。
4. 基于官方动作库的安全编舞拼接与自动审计。
5. 从舞蹈需求 → AI motion.json → 3D 预览 → 关键帧微调 → 安全审计 → 导出 .rob 的完整闭环。

一句话简介：

> AI-assisted Tonybot motion creation, 3D preview, keyframe editing, safety audit, and .rob export.

## 项目信息

- 当前版本：`0.6.0`
- 仓库状态：`Public / Active`
- 默认分支：`main`
- 平台环境：`Windows + Python 3.13`
- 授权方式：公开可见，但默认不授予开源再分发权，见 [LICENSE](LICENSE)

## 仓库首页导读

如果第一次进入这个仓库，推荐先从新的文档目录进入：

1. [python-toolkit/文档/README.md](python-toolkit/文档/README.md)：文档总索引和阅读路径。
2. [python-toolkit/文档/01-项目总览.md](python-toolkit/文档/01-项目总览.md)：看项目定位、边界和目录分工。
3. [python-toolkit/文档/02-动作文件与逆向.md](python-toolkit/文档/02-动作文件与逆向.md)：看 `.rob` / `EYPT` 逆向结论。
4. [python-toolkit/文档/03-安全模型与约束.md](python-toolkit/文档/03-安全模型与约束.md)：看安全模型、回正规范和约束边界。
5. [python-toolkit/文档/04-编舞规范与工作流.md](python-toolkit/文档/04-编舞规范与工作流.md)：看从需求到 `.rob` 的生成流程。
6. [python-toolkit/文档/05-设备控制算法.md](python-toolkit/文档/05-设备控制算法.md)：看设备端行为逻辑。
7. [python-toolkit/文档/06-验证与发布.md](python-toolkit/文档/06-验证与发布.md)：看验证命令和发版规则。
8. [python-toolkit/文档/07-动作库目录.md](python-toolkit/文档/07-动作库目录.md)：**官方动作库完整索引**，编舞选段第一参考。
9. [python-toolkit/文档/08-编舞标准化工作流.md](python-toolkit/文档/08-编舞标准化工作流.md)：**标准化 SOP**，从舞蹈创意到 .rob 的完整流程。
10. [python-toolkit/文档/09-Python开发指南.md](python-toolkit/文档/09-Python开发指南.md)：**Python 开发指南**，三种方式用代码生成 .rob 动作文件。
11. [python-toolkit/文档/10-队列安全动作分组.md](python-toolkit/文档/10-队列安全动作分组.md)：**多机并排同跳安全分组**，整理禁用动作、谨慎动作和队列安全动作。

历史文档（动作文件逆向说明、动作安全规范、编舞工作流说明、算法指南）已随工具链迁移到 `python-toolkit/` 目录。

## 版本与发布文件

- [VERSION](VERSION)：当前仓库版本号。
- [CHANGELOG.md](CHANGELOG.md)：版本变更记录。
- [文档/](文档/)：新的专题文档目录。
- [LICENSE](LICENSE)：当前仓库许可说明。

## 目录结构

当前仓库分为三个区域：

- **`python-toolkit/`** — 现有 Python 工具链（v0.4.0 整合），包含所有源码、动作库、编舞和文档。
- **`wondercode-toolkit/`** — 面向 WonderCode / 官方积木转换工具的 Python API 对齐文档与示例。
- **根目录** — 仓库级版本文件、说明和后续扩展入口。

`python-toolkit/` 内部结构：

- `main.py`：Tonybot 设备端 MicroPython 主程序。
- `文档/`：整合后的专题文档目录。
- `动作/`：官方动作库、解密后的明文样本和生成的 `.rob` 动作文件。
- `编舞/`：编舞 JSON、编译报告 JSON 和时间线 HTML。
- `rob_reverse.py`：解析 `.rob` / `ACT-40` 文件。
- `rob_crypto.py`：独立实现 `EYPT` 的 `TEA-32` 加解密。
- `rob_library.py`：批量破解、解析和导出动作库。
- `rob_safety.py`：从官方动作库学习安全包络并执行审计。
- `rob_compose.py`：把动作段拼接成新的 `.rob` 文件。
- `dance_workflow.py`：把舞蹈需求 JSON 编译成 `.rob`、报告 JSON 和时间线 HTML。
- `tonybot_physics.py`：正向运动学（FK）模型，计算 16 舵机姿态的质心、支撑多边形和平衡得分。
- `可视化模拟器/动作模拟器.html`：**Tonybot 3D 动作预览器（Motion Viewer）**，Three.js 渲染机器人骨骼，16 舵机滑块实时驱动，支持 `.rob` 拖拽加载与帧播放。**仅做 3D FK 姿态预览，不输出安全结论**。目标是减少线下反复掰机器人调动作的试错成本。

## 当前结论

### `.rob` 容器

- 所有动作文件使用 `ACT-40` 容器。
- 文件格式为 `16 字节头 + 帧数组`。
- 单帧固定 `248` 字节。
- 明文帧中前 `16` 个槽位有效，后 `24` 个槽位是 filler。

### `EYPT` 保护层

- `EYPT` 的真实算法已经独立复现。
- 保护层使用标准 `TEA-32`。
- 前 `16` 字节文件头不参与加密。
- 真正加密的是完整帧区 `data[16:]`。

### 编舞与安全

- 编舞优先复用官方动作段，不直接手写新舵机轨迹。
- 新动作在输出前会自动执行安全审计。
- 审计基于官方动作库学习出的时长、字段范围和跳变包络。

## 适用场景

这个仓库目前最适合下面几类工作：

1. **动作创作**：从 AI 提示或手动设计出发，生成 motion.json，预览、微调、审计后导出 .rob。
2. **离线预览**：拖拽 .rob 到 3D 预览器，直接在浏览器里播放骨骼动画，无需连接真机。
3. **安全审计**：对任意 .rob 文件运行 `rob_safety.py`，检查舵机值和跳变是否在官方包络内。
4. **逆向研究**：解析 ACT-40 容器、EYPT 加密层，独立复现 TEA-32 加解密。
5. **批量分析**：用 `rob_library.py` 解析整个动作库，导出逐动作 JSON 统计数据。
6. **编舞闭环**：从舞蹈需求 → AI/motion.json → 3D 预览 → 关键帧微调 → 安全审计 → 导出 .rob。

## 快速开始

以下命令在 `python-toolkit/` 目录下执行：

### 1. 生成编舞模板

```powershell
cd python-toolkit
python dance_workflow.py init 编舞/示例舞蹈.json --name 示例舞蹈 --prompt "做一段适合展示的机器人舞蹈"
```

### 2. 构建 `.rob`、报告和时间线

```powershell
cd python-toolkit
python dance_workflow.py build 编舞/159号自制舞蹈.json
```

构建后会得到：

1. `动作/<舞蹈名>.rob`
2. `编舞/<舞蹈名>.report.json`
3. `编舞/<舞蹈名>.timeline.html`

### 3. 单独执行安全审计

```powershell
cd python-toolkit
python rob_safety.py "动作/159号自制舞蹈.rob"
```

### 4. 单独解密 / 重加密 `EYPT`

```powershell
cd python-toolkit
python rob_crypto.py decrypt-file "动作/1号前进.rob" "动作/1号前进.python.plain.rob"
python rob_crypto.py encrypt-file "动作/1号前进.plain.rob" "动作/1号前进.python.rob"
```

### 5. 批量破解和导出动作库

```powershell
cd python-toolkit
python rob_library.py analyze
python rob_library.py export-json
python rob_library.py decrypt-eypt
```

默认产物：

1. `python-toolkit/动作库解析报告.json`
2. `python-toolkit/动作库解析/*.json`
3. `python-toolkit/动作库解密/*.plain.rob`

## 环境说明

- 当前脚本在 Windows + Python 3.13 环境下验证过。
- 工作流脚本不依赖第三方 Python 包。
- `main.py` 运行依赖 Hiwonder 设备端运行时和硬件环境。

## 当前交付内容

当前仓库已经具备：

1. `ACT-40` / `EYPT` 文件格式解析与独立加解密实现。
2. 动作库批量破解、逐动作 JSON 导出和库级字段统计。
3. 基于官方动作库样本学习的安全审计工具。
4. JSON 驱动的编舞工作流、报告 JSON 和 HTML 时间线可视化。
5. 一个已验证通过安全审计的示例舞蹈：`动作/159号自制舞蹈.rob`。

## GitHub 仓库描述建议

`Tonybot Motion Studio — AI-assisted motion creation, 3D preview, keyframe editing, safety audit, and .rob export.`

## 仓库约定

- 官方与生成动作文件统一放在 `python-toolkit/动作/` 目录。
- 编舞输入和可视化产物统一放在 `python-toolkit/编舞/` 目录。
- `.rob` 文件在 git 中按二进制处理，不做文本 diff。
- 本地虚拟环境、缓存文件和 Python 编译产物不会纳入版本控制。

## 后续建议

如果继续扩展这个仓库，最自然的方向有两个：

1. 给官方动作库补标签和动作词典，降低编舞选段的人工成本。（见阶段 2 路线图）
2. 继续推明文三字段的物理语义，逐步从安全拼接升级到受控生成。（见阶段 2/3 路线图）
3. 实现 motion.json ↔ .rob 双向转换原型。（见阶段 2 路线图）
4. 实现 AI 辅助 motion.json 生成和动作库智能匹配。（见阶段 3 路线图）

完整路线图见 [11-Motion-Studio架构规划.md](python-toolkit/文档/11-Motion-Studio架构规划.md)。
