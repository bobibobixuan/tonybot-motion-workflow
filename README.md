# Tonybot Action Simulator

> **Tonybot 动作模拟器** — 解析、预览、检索官方动作组的 3D FK 骨骼姿态预览器。

## 项目定位

Tonybot Action Simulator 以 **动作模拟器** 为核心，围绕 Tonybot 官方 `.rob` 动作文件，
提供 3D 骨骼预览、动作组 JSON 数据库和 Python 解析工具储备。

**不是** AI 编舞工作台，**不是** 安全仿真器。

## 快速开始

### 打开模拟器

双击 `simulator/index.html`，在浏览器中打开 3D 动作模拟器。

- 拖拽 `.rob` 文件到视口即可加载播放
- 16 舵机滑块实时驱动骨骼姿态
- 7 组预设姿态一键切换
- 支持 ACT-40 明文和 EYPT 加密文件

### 生成动作数据库

```powershell
cd tools/python
uv run python rob_library.py export-official-actions
```

产物：`data/official-actions/index.json` + `actions/*.json`

## 目录结构

```
simulator/              # 3D 动作模拟器（主入口）
  index.html
  i18n/zh-CN.json / en-US.json
data/
  official-actions/     # 官方动作组 JSON 数据库
    index.json
    categories.json
    schema.md
    actions/*.json
  raw-actions/          # 原始 .rob 文件（可选）
tools/
  python/               # Python 解析工具
    rob_reverse.py      # ACT-40 解析
    rob_crypto.py       # EYPT/TEA-32 加解密
    rob_library.py      # 批量分析 + export-official-actions
    rob_safety.py       # 安全审计
    rob_compose.py      # 动作拼接
    dance_workflow.py   # JSON→.rob 编译
    tonybot_physics.py  # FK 正向运动学
knowledge/
  docs/                 # 专题文档（01–13）
  wondercode/           # WonderCode 知识库
legacy/
  choreography/         # 旧编舞 JSON / 动作模块
  motion-studio/        # Motion Studio 架构规划存档
changelog/              # 版本更新日志
python-toolkit/         # 原工具链（保留，兼容旧引用）
wondercode-toolkit/     # 原 WonderCode 工具（保留）
```

## 版本

- 当前版本：`0.7.0`
- 仓库状态：`Public / Active`
- 默认分支：`main`

## 文档阅读顺序

1. `knowledge/docs/README.md`
2. `simulator/README.md`
3. `data/official-actions/schema.md`
4. `knowledge/docs/13-3D动作预览器规范.md`

## 许可证

见 [LICENSE](LICENSE)
