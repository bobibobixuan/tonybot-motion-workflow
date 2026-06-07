# 11 — Tonybot Motion Studio 架构规划

## a. 项目新定位

| 项目 | 旧定位 | 新定位 |
|------|--------|--------|
| 名称 | Tonybot Motion Workflow | **Tonybot Motion Studio** |
| 核心描述 | .rob 逆向 + 自动编舞 + 安全审计 | **AI 辅助动作创作工作台** |
| 产出 | .rob 动作文件 | **motion.json → .rob + 预览 + 审计报告** |
| 用户 | 逆向工程师 / 开发者 | **机器人舞蹈创作者 / 编舞师 / 教育者** |

新 slogan：

> Tonybot Motion Studio — AI 辅助的 Tonybot 动作创作、3D 预览、关键帧编辑、安全审计和 .rob 导出工作流。

## b. 目标用户和使用场景

| 角色 | 场景 | 核心操作 |
|------|------|----------|
| 编舞师 | 设计一段机器人舞蹈 | 用 AI 生成 motion.json → 3D 预览 → 调关键帧 → 导出 .rob |
| 教育者 | 准备课堂演示动作 | 从官方动作库挑选预设 → 微调特定帧 → 安全审计 → 部署 |
| 机器人玩家 | 自定义动作 | 拖拽 .rob 预览 → 滑块微调 → 复制 Pose → 写入新动作 |
| 开发者 | 批量生成/验证动作 | CLI 工作流：motion.json → build → audit → 导出 |

核心闭环：

```
需求/AI 提示
  ↓
motion.json（可编辑动作工程）
  ↓
3D 动作预览器（Motion Viewer）—— 快速预览、滑块微调
  ↓
关键帧编辑器（Motion Editor）—— 逐帧标注、修改、复制
  ↓
安全审计（rob_safety.py）—— 自动检查 violations
  ↓
导出 .rob —— 部署到 Tonybot 真机
```

## c. 四层架构

项目内部按四层组织，各层职责清晰：

```
┌─────────────────────────────────────────────┐
│          motion-workflow (工作流层)           │
│  dance_workflow.py  — JSON→.rob 编译         │
│  rob_compose.py      — 动作段拼接             │
│  rob_safety.py       — 安全审计               │
└─────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────┐
│          motion-editor (编辑层) [规划中]       │
│  关键帧编辑器 — 逐帧可视编辑                   │
│  motion.json 读写 — 标注/修改/复制帧           │
│  姿态插值 — 在两个关键帧间生成过渡              │
└─────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────┐
│          motion-viewer (预览层) ✅            │
│  动作模拟器.html — Tonybot 3D 动作预览器       │
│  Three.js FK 骨骼渲染                        │
│  .rob 加载 / 帧播放 / 16 舵机滑块              │
│  复制 Pose / 帧跳变提示                       │
│  仅做姿态预览，不输出安全结论                   │
└─────────────────────────────────────────────┘
                      ↑
┌─────────────────────────────────────────────┐
│          motion-core (核心层) ✅              │
│  rob_reverse.py  — ACT-40 解析               │
│  rob_crypto.py   — EYPT/TEA-32 加解密        │
│  tonybot_physics.py — FK 正向运动学           │
│  rob_library.py  — 动作库批量分析             │
└─────────────────────────────────────────────┘
```

| 层 | 状态 | 职责 |
|----|------|------|
| motion-core | ✅ 已完成 | 二进制解析、加解密、FK 计算、库分析 |
| motion-viewer | ✅ 已完成 | 3D 骨骼预览、.rob 加载、帧播放、滑块调试 |
| motion-editor | 🔲 规划中 | 关键帧可视编辑、motion.json 标注、插值生成 |
| motion-workflow | ✅ 已完成 | JSON→.rob 编译、动作拼接、安全审计 |

## d. motion.json — 可编辑动作工程格式

`motion.json` 是 Motion Studio 的核心交换格式。

- 人类可读（JSON），适合 AI 生成、手动编辑、版本控制 diff
- 包含元数据、中性姿态、逐帧数据、导出配置
- 可编译为 `.rob` 二进制文件，也可从 `.rob` 反向导出
- 帧带 `label` 和 `notes`，方便标注节拍和修改意图

详细 schema 见：`python-toolkit/文档/12-motion-json格式规范.md`

## e. .rob 与 motion.json 的关系

```
.rob (二进制)  ←→  motion.json (工程格式)
   ACT-40              JSON
   EYPT 加密            明文可编辑
   248B/帧              16 个 uint16/帧 + duration + label
   设备直接加载          人类/AI/版本控制友好
```

| 方向 | 工具 | 说明 |
|------|------|------|
| `.rob` → `motion.json` | （规划中） | 从设备动作反编为可编辑工程 |
| `motion.json` → `.rob` | `dance_workflow.py build` | 编译为设备可加载的动作文件 |

## f. 3D 预览器边界

- ✅ 预览器负责：FK 骨骼姿态渲染、.rob 加载、帧播放、16 舵机滑块调试、Pose 复制
- ❌ 预览器不负责：安全审计、COM 结论、平衡分、支撑面分析
- 预览器中的"帧跳变提示"仅列出舵机值突变，不输出安全判断
- 安全审计是 `motion-workflow` 层的职责，由 `rob_safety.py` 执行

详见：`python-toolkit/文档/13-3D动作预览器规范.md`

## g. 后续三阶段路线图

### 阶段 1：格式标准化（当前 0.6.0）

- [x] 定义 motion.json schema
- [x] 文档化四层架构
- [x] 预览器正式命名和规范化
- [ ] motion.json ↔ .rob 双向转换原型

### 阶段 2：编辑层（0.7.x 目标）

- [ ] 关键帧 Web 编辑器（内嵌于预览器或独立页面）
- [ ] 帧标注（label / notes）可视编辑
- [ ] 帧复制/粘贴/删除/移动
- [ ] 两帧间姿态插值生成中间帧
- [ ] 从预览器导出 motion.json
- [ ] 从预览器直接调用 rob_safety.py（CLI 桥接）

### 阶段 3：AI 集成（0.8.x 目标）

- [ ] AI 提示 → motion.json 生成（基于动作库训练）
- [ ] 自然语言描述动作 → 自动匹配动作库片段
- [ ] AI 辅助过渡帧生成
- [ ] 多人协作编舞（motion.json diff/merge）
- [ ] 批量动作变体生成（同一动作的不同风格版本）

---

> 当前版本 0.6.0 处于阶段 1，重点完成架构文档和格式规范化。
> 现有 `dance_workflow.py` / `rob_safety.py` / `rob_crypto.py` 行为保持不变。
