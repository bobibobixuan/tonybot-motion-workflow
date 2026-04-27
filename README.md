# Tonybot Motion Workflow

Tonybot Motion Workflow 是一个围绕 Tonybot 机器人动作文件构建的工具仓库，重点解决四类问题：

1. 设备端主控逻辑梳理。
2. `.rob` / `ACT-40` 动作文件逆向与 `EYPT` 解密。
3. 基于官方动作库的安全编舞与自动审计。
4. 从舞蹈需求到 JSON、再到 `.rob` 的可复用工作流。

一句话简介：

> Reverse engineer Tonybot `.rob` actions, rebuild `EYPT/TEA-32`, and generate safe choreography from JSON into `.rob`.

## 项目信息

- 当前版本：`0.1.1`
- 仓库状态：`Public / Active`
- 默认分支：`main`
- 平台环境：`Windows + Python 3.13`
- 授权方式：公开可见，但默认不授予开源再分发权，见 [LICENSE](LICENSE)

## 仓库首页导读

如果第一次进入这个仓库，推荐按下面顺序阅读：

1. [README.md](README.md)：看项目范围、目录结构和常用命令。
2. [动作文件逆向说明.md](动作文件逆向说明.md)：看 `.rob` / `EYPT` 逆向结果。
3. [动作安全规范.md](动作安全规范.md)：看动作安全边界和审计规则。
4. [编舞工作流说明.md](编舞工作流说明.md)：看从需求到 `.rob` 的工作流。
5. [算法指南.md](算法指南.md)：看设备端行为逻辑。

## 版本与发布文件

- [VERSION](VERSION)：当前仓库版本号。
- [CHANGELOG.md](CHANGELOG.md)：版本变更记录。
- [LICENSE](LICENSE)：当前仓库许可说明。

## 目录结构

- `main.py`：Tonybot 设备端 MicroPython 主程序。
- `动作/`：官方动作库、解密后的明文样本和生成的 `.rob` 动作文件。
- `编舞/`：编舞 JSON、编译报告 JSON 和时间线 HTML。
- `rob_reverse.py`：解析 `.rob` / `ACT-40` 文件。
- `rob_crypto.py`：独立实现 `EYPT` 的 `TEA-32` 加解密。
- `rob_safety.py`：从官方动作库学习安全包络并执行审计。
- `rob_compose.py`：把动作段拼接成新的 `.rob` 文件。
- `dance_workflow.py`：把舞蹈需求 JSON 编译成 `.rob`、报告 JSON 和时间线 HTML。
- `算法指南.md`：设备端主逻辑说明。
- `动作文件逆向说明.md`：动作容器和 `EYPT` 逆向结论。
- `动作安全规范.md`：安全包络与编舞审查规则。
- `编舞工作流说明.md`：需求到 `.rob` 的工作流说明。

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

1. 研究 Tonybot `.rob` 动作文件格式。
2. 把官方 `EYPT` 动作还原成明文 `ACT-40`。
3. 在不直接手写底层舵机轨迹的前提下，安全地拼接和生成新舞蹈。
4. 把“舞蹈需求 -> 研究摘要 -> 编舞 JSON -> `.rob` 文件 -> 安全审计”固化成流程。

## 快速开始

### 1. 生成编舞模板

```powershell
python dance_workflow.py init 编舞/示例舞蹈.json --name 示例舞蹈 --prompt "做一段适合展示的机器人舞蹈"
```

### 2. 构建 `.rob`、报告和时间线

```powershell
python dance_workflow.py build 编舞/159号自制舞蹈.json
```

构建后会得到：

1. `动作/<舞蹈名>.rob`
2. `编舞/<舞蹈名>.report.json`
3. `编舞/<舞蹈名>.timeline.html`

### 3. 单独执行安全审计

```powershell
python rob_safety.py "动作/159号自制舞蹈.rob"
```

### 4. 单独解密 / 重加密 `EYPT`

```powershell
python rob_crypto.py decrypt-file "动作/1号前进.rob" "动作/1号前进.python.plain.rob"
python rob_crypto.py encrypt-file "动作/1号前进.plain.rob" "动作/1号前进.python.rob"
```

## 环境说明

- 当前脚本在 Windows + Python 3.13 环境下验证过。
- 工作流脚本不依赖第三方 Python 包。
- `main.py` 运行依赖 Hiwonder 设备端运行时和硬件环境。

## 当前交付内容

当前仓库已经具备：

1. `ACT-40` / `EYPT` 文件格式解析与独立加解密实现。
2. 基于官方动作库样本学习的安全审计工具。
3. JSON 驱动的编舞工作流、报告 JSON 和 HTML 时间线可视化。
4. 一个已验证通过安全审计的示例舞蹈：`动作/159号自制舞蹈.rob`。

## GitHub 仓库描述建议

如果要在 GitHub 仓库描述栏里保持简洁，推荐使用这句：

`Tonybot .rob reverse engineering, EYPT/TEA-32 decryption, safe choreography auditing, and JSON-to-.rob workflow.`

## 仓库约定

- 官方与生成动作文件统一放在 `动作/` 目录。
- 编舞输入和可视化产物统一放在 `编舞/` 目录。
- `.rob` 文件在 git 中按二进制处理，不做文本 diff。
- 本地虚拟环境、缓存文件和 Python 编译产物不会纳入版本控制。

## 后续建议

如果继续扩展这个仓库，最自然的方向有两个：

1. 给官方动作库补标签和动作词典，降低编舞选段的人工成本。
2. 继续推明文三字段的物理语义，让工作流从“安全拼接”逐步升级到“受控生成”。