# Python 开发指南：生成 .rob 动作文件

本指南介绍如何用 Python 代码生成 Tonybot `.rob` 动作文件，覆盖从单帧手写到完整编舞编译的三种方式。

> **⚠️ 重要约束**
>
> | 约束项 | 限制值 | 原因 |
> |--------|--------|------|
> | **单文件帧数上限** | ≤ 510 帧 | 设备端加载限制，超出可构建但无法加载到机器。超限编舞需拆成多段 |
> | **舵机值范围** | 0–1000 | 对应舵机 0°–180° 行程，超出可能损坏硬件 |
> | **单帧时长** | 40–1800 ms | 超出此范围的帧时长在官方动作库中从未出现 |
> | **安全审计** | violations=0 | 必须通过双层安全模型审计才能编译输出 |
> | **前后回正** | 必须包含 | 每个动作文件的开头和结尾必须回到稳定站姿（0号立正） |

---

## 背景

Tonybot 的 `.rob` 文件是 ACT-40 容器格式的二进制动作文件。官方只提供了 Windows GUI 工具（Bus Servo Control.exe）手工编辑。**本项目工具链用 Python 填补了编程化生成 .rob 的空白。**

```
Python 代码 / JSON 编舞规格
         │
         ▼
   rob_compose.py          ← 拼接/编译引擎
         │
         ▼
   rob_safety.py           ← 安全审计（双层模型）
         │
         ▼
   动作/<name>.rob         ← 设备可执行的动作文件
         │
         ▼
   Hiwonder.Tonybot()
   tony.runActionGroup(N)  ← 设备端播放
```

---

## 方式一：引用已有动作段（推荐，零手写）

不写任何舵机角度，只引用官方 `.rob` 文件进行裁剪、重复、拼接。

### Python API

```python
import json
from rob_compose import detect_actions_dir, normalize_segment, compile_recipe

actions_dir = detect_actions_dir()

# 定义段列表：每个段引用一个已有 .rob 文件
recipe = [
    normalize_segment({"source": "0号立正.rob",      "label": "stand"},     actions_dir),
    normalize_segment({"source": "303号礼貌鞠躬.rob",  "label": "bow"},       actions_dir),
    normalize_segment({"source": "308号标准踏步.rob",  "label": "march",   "repeat": 2}, actions_dir),
    normalize_segment({"source": "319号左右勾拳组合.rob", "label": "punch", "repeat": 2}, actions_dir),
    normalize_segment({"source": "0号立正.rob",      "label": "end"},       actions_dir),
]

# 编译输出
report = compile_recipe(recipe, "动作/我的动作.rob", actions_dir=actions_dir)
print(f"frames={report['frame_count']}, violations={len(report['violations'])}")
```

### Segment 字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `source` | str | 是 | `.rob` 文件名，从 `动作/` 目录查找 |
| `label` | str | 推荐 | 段标识名 |
| `repeat` | int | 否 | 重复次数，默认 1 |
| `frame_range` | [int, int] | 否 | 截取帧范围 `[start, end)` |
| `notes` | str | 否 | 备注说明 |

---

## 方式二：语义锚点写帧（中级，写 pose 不写舵机值）

库内置了从官方动作库学习出的 **语义锚点系统**，覆盖 13 种基础姿态和 20+ 种中间过渡态。你只需要写"从 stand 经过 twist_left_mid 到 twist_left"这样的语义序列，不用手写 16 个舵机值。

### 可用的语义锚点

```python
from rob_safety import SEMANTIC_ANCHORS

# 基础姿态（13 种）
SEMANTIC_ANCHORS["stand"]         # [500,387,500,593,500,575,800,724,...] 立正
SEMANTIC_ANCHORS["step"]          # 踏步
SEMANTIC_ANCHORS["slide_left"]    # 左侧滑
SEMANTIC_ANCHORS["slide_right"]   # 右侧滑
SEMANTIC_ANCHORS["twist_left"]    # 左扭腰
SEMANTIC_ANCHORS["twist_right"]   # 右扭腰
SEMANTIC_ANCHORS["guard"]         # 格斗预备
SEMANTIC_ANCHORS["punch_left"]    # 左出拳
SEMANTIC_ANCHORS["punch_right"]   # 右出拳
SEMANTIC_ANCHORS["kick_left"]     # 左踢腿
SEMANTIC_ANCHORS["kick_right"]    # 右踢腿
SEMANTIC_ANCHORS["squat"]         # 下蹲
SEMANTIC_ANCHORS["bow_open"]      # 浅鞠躬
SEMANTIC_ANCHORS["bow_deep"]      # 深鞠躬

# 中间过渡态（20+ 种，自动插值生成）
SEMANTIC_ANCHORS["weight_left"]    # 重心左移 (stand-slide_left 50%)
SEMANTIC_ANCHORS["weight_right"]   # 重心右移
SEMANTIC_ANCHORS["step_mid"]       # 踏步中途
SEMANTIC_ANCHORS["twist_left_mid"] # 左扭腰中途
SEMANTIC_ANCHORS["twist_right_mid"]# 右扭腰中途
SEMANTIC_ANCHORS["punch_left_mid"] # 左拳中途
SEMANTIC_ANCHORS["punch_right_mid"]# 右拳中途
SEMANTIC_ANCHORS["kick_left_mid"]  # 左踢中途
SEMANTIC_ANCHORS["kick_right_mid"] # 右踢中途
SEMANTIC_ANCHORS["squat_mid"]      # 下蹲中途
SEMANTIC_ANCHORS["bow_mid"]        # 鞠躬中途
SEMANTIC_ANCHORS["bow_deep_mid"]   # 深鞠躬中途
SEMANTIC_ANCHORS["guard_left"]     # 左格斗
SEMANTIC_ANCHORS["guard_right"]    # 右格斗
SEMANTIC_ANCHORS["squat_left"]     # 左下蹲
SEMANTIC_ANCHORS["squat_right"]    # 右下蹲
```

### 用锚点写帧序列

```python
from rob_safety import SEMANTIC_ANCHORS as P

# 定义一个帧序列：(duration_ms, anchor_name)
my_frames = [
    (200, "stand"),
    (120, "twist_left_mid"),
    (160, "twist_left"),
    (120, "twist_left_mid"),
    (120, "stand"),
    (120, "twist_right_mid"),
    (160, "twist_right"),
    (120, "twist_right_mid"),
    (200, "stand"),
]

# 转换为 frame spec
frames_spec = [
    {"duration": d, "pose": P[a]}
    for d, a in my_frames
]
```

### 编译为 .rob

```python
from rob_compose import normalize_segment, compile_recipe, detect_actions_dir

actions_dir = detect_actions_dir()

recipe = [
    normalize_segment({
        "label": "my-twist-dance",
        "frames": frames_spec,
    }, actions_dir),
]

report = compile_recipe(recipe, "动作/我的扭腰.rob", actions_dir=actions_dir)
print(f"frames={report['frame_count']}, violations={len(report['violations'])}")
```

---

## 方式三：自定义舵机值（高级，完全控制）

直接写 16 个关节的舵机角度值。

### 关节映射

Tonybot 有 16 个有效关节（舵机通道）。以下映射已由站立位、单舵机手臂测试和腿部测试确认：

| 通道 | 关节 | stand 值 | 说明 |
|------|------|----------|------|
| 1 | 右髋旋转轴 | 500 | 控制右腿及右脚尖内旋、外旋 |
| 2 | 右踝俯仰轴 | 387 | 控制右脚掌前后倾斜 |
| 3 | 右膝轴 | 500 | 控制右膝弯曲和伸直 |
| 4 | 右髋前后轴 | 593 | 控制右大腿前抬和后摆 |
| 5 | 右髋侧摆轴 | 500 | 控制右腿侧向展开、回收和身体侧倾 |
| 6 | 右肘轴 | 575 | 控制右小臂弯曲和伸直 |
| 7 | 右肩侧向轴 | 800 | 控制右臂外展和收回 |
| 8 | 右肩根部旋转轴 | 724 | 控制整条右臂前后转动、上举和下放 |
| 9 | 左髋旋转轴 | 500 | 控制左腿及左脚尖内旋、外旋 |
| 10 | 左踝俯仰轴 | 612 | 控制左脚掌前后倾斜 |
| 11 | 左膝轴 | 500 | 控制左膝弯曲和伸直 |
| 12 | 左髋前后轴 | 406 | 控制左大腿前抬和后摆 |
| 13 | 左髋侧摆轴 | 500 | 控制左腿侧向展开、回收和身体侧倾 |
| 14 | 左肘轴 | 425 | 控制左小臂弯曲和伸直 |
| 15 | 左肩侧向轴 | 200 | 控制左臂外展和收回 |
| 16 | 左肩根部旋转轴 | 275 | 控制整条左臂前后转动、上举和下放 |

> 注意：舵机角度范围约为 0–1000（对应约 0°–180°）。`ID1` / `ID2` / `ID9` / `ID10` 的“增大到底对应脚尖上翘还是下压、内旋还是外旋”仍建议按真机重心效果微调，但其关节类别已经确认。

### 手写帧

```python
from rob_compose import normalize_segment, compile_recipe, detect_actions_dir
from rob_reverse import FILLER_TRIPLET, ACTIVE_CHANNELS

actions_dir = detect_actions_dir()

# 完全手写的帧：16 个关节值
custom_frames = [
    {
        "duration": 200,
        "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
        #        躯干 右肩 左肩 右肩R 左肩R 右肘 左肘 右髋 左髋 右膝 左膝 右踝 左踝 右脚 左脚 头
    },
    {
        "duration": 150,
        "pose": [540, 330, 568, 612, 505, 575, 800, 724, 530, 612, 500, 406, 500, 425, 200, 275],
    },
    {
        "duration": 200,
        "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
    },
]

recipe = [
    normalize_segment({
        "label": "handcraft",
        "frames": custom_frames,
    }, actions_dir),
]

report = compile_recipe(recipe, "动作/我的手写动作.rob", actions_dir=actions_dir)
```

### 自定义帧的完整字段

如果不只用 `pose`（仅关节角度），还可以指定全部三个通道字段：

```python
# 完整通道控制（40 通道 × 3 字段）
full_frame = {
    "duration": 200,
    "marker": 0x5555,       # 帧分隔标记，默认 0x5555
    "reserved_a": 0,         # 保留字段 A
    "reserved_b": 0,         # 保留字段 B
    "channels": [
        # 前 16 个槽位：有效数据 (position, field2, field3)
        (500, 0, 0),  # ch1
        (387, 0, 0),  # ch2
        # ... 共 16 组
    ],
    # 后 24 个槽位自动填充 FILLER_TRIPLET (0x5555, 0, 0)
}
```

---

## 工具函数参考

### `rob_safety.mix()` — 线性插值

```python
from rob_safety import mix

# 在两个 16 维 pose 之间按 ratio (0~1) 插值
mid_pose = mix(pose_a, pose_b, 0.5)
```

### `rob_safety.classify_pose()` — 语义分类

```python
from rob_safety import classify_pose

label, distance = classify_pose(my_pose)
# label: 最近的语义状态名 ("stand", "punch_left", ...)
# distance: 与该锚点的 L1 距离
```

### `rob_safety.learn_reference_envelope()` — 学习安全包络

```python
from rob_safety import learn_reference_envelope, audit_frame_sequence

# 从官方动作库学习安全边界
envelope = learn_reference_envelope("动作/")
print(f"duration range: {envelope.duration_min}..{envelope.duration_max}")
print(f"transition L1 p95: {envelope.transition_l1_p95}")

# 对一组帧执行审计
result = audit_frame_sequence(frames_bytes, envelope, "my-action")
for v in result["violations"]:
    print(f"VIOLATION: {v}")
```

### `rob_reverse.parse_file()` / `parse_plain_frame()`

```python
from rob_reverse import parse_file, parse_plain_frame

# 解析 .rob 文件
parsed = parse_file("动作/0号立正.rob")
print(f"frames: {parsed['frame_count']}")

# 解析单帧
frame_info = parse_plain_frame(parsed["frames"][0])
print(f"duration: {frame_info['duration']}")
print(f"pose: {[ch[0] for ch in frame_info['channels'][:16]]}")
```

---

## 完整示例：从零生成一段短舞蹈

```python
"""
生成一段简单舞蹈：立正 → 扭腰左右摆动 → 鞠躬 → 立正
"""
from rob_safety import SEMANTIC_ANCHORS as P, mix
from rob_compose import detect_actions_dir, compile_recipe, normalize_segment

actions_dir = detect_actions_dir()

# 1. 定义帧序列（语义锚点 + 时长）
sequence = [
    (200, "stand"),
    (100, "twist_left_mid"),
    (150, "twist_left"),
    (100, "twist_left_mid"),
    (100, "stand"),
    (100, "twist_right_mid"),
    (150, "twist_right"),
    (100, "twist_right_mid"),
    (200, "stand"),
    (150, "bow_mid"),
    (200, "bow_open"),
    (150, "bow_mid"),
    (250, "stand"),
]

frames_spec = [{"duration": d, "pose": P[a]} for d, a in sequence]

# 2. 编译
recipe = [
    normalize_segment({"label": "twist-bow", "frames": frames_spec}, actions_dir),
]
report = compile_recipe(recipe, "动作/我的短舞蹈.rob", actions_dir=actions_dir)

# 3. 结果
print(f"输出: {report['output']}")
print(f"帧数: {report['frame_count']}")
print(f"总时长: {sum(s['duration_ms'] for s in report['segments'])} ms")
print(f"安全违规: {len(report['violations'])}")
if report["violations"]:
    for v in report["violations"]:
        print(f"  - {v}")
```

运行：
```powershell
uv run python my_dance.py
```

---

## 混合方式：复用 + 手写

最常见的实际用法是混合两种方式：

```python
recipe = [
    # 开场用官方回正
    normalize_segment({"source": "302号快速回正.rob", "label": "reset"}, actions_dir),
    normalize_segment({"source": "0号立正.rob",     "label": "stand"},  actions_dir),

    # 自定义手写舞蹈主体
    normalize_segment({"label": "custom-dance", "frames": my_custom_frames}, actions_dir),

    # 收尾回到官方鞠躬和立正
    normalize_segment({"source": "303号礼貌鞠躬.rob",  "label": "bow"}, actions_dir),
    normalize_segment({"source": "0号立正.rob",      "label": "end"},  actions_dir),
]
```

---

## 安全约束

所有手写帧必须通过安全审计才能编译。双层模型检查：

| 层 | 检查内容 | 违规后果 |
|----|----------|----------|
| 统计包络 | 舵机值范围、帧时长、单关节跳变、总姿态 L1 跳变 | **阻断构建** |
| 语义约束 | 高负载状态准备/回收、左右对冲直切、未见状态迁移 | **阻断构建** |

如果构建被阻断，需要根据违规信息调整帧序列后重试。常见的修复方法：
- 在极端姿态之间插入中间态帧
- 确保帧时长在 40-1800ms 范围内
- 高负载动作（出拳/踢腿/下蹲）前后加预备和回收帧

---

## 设备端部署

生成的 `.rob` 文件放到 Tonybot 设备上后，在 MicroPython 中调用：

```python
import Hiwonder
tony = Hiwonder.Tonybot()

# 通过 BLE 命令触发
# CMD|2|<动作组编号>|$

# 或直接在代码中调用
tony.runActionGroup(N, 0)    # 播放一次
tony.runActionGroup(N, 1)    # 循环播放
tony.waitForStop(5000)       # 等待完成或超时
tony.stopActionGroup()       # 强制停止
tony.isRunning()             # 检查是否在播放
```

> `.rob` 文件编号与 `runActionGroup()` 的参数对应。新生成的 `.rob` 需放入设备的动作存储区才能被调用。
