# 12 — motion.json 动作工程格式规范

## 概述

`motion.json` 是 Tonybot Motion Studio 的可编辑动作工程格式。
它是人类可读、AI 可生成、版本控制友好的 JSON 文件，
编译后可导出为设备端加载的 `.rob` 二进制动作文件。

## 设计原则

1. **人类可读**：纯 JSON，适合手动编辑和代码审查。
2. **AI 友好**：结构化字段，方便 AI 生成和解析。
3. **双向可转换**：可从 `.rob` 导出，也可编译为 `.rob`。
4. **可标注**：每帧带 `label` 和 `notes`，支持编舞标注。
5. **自描述**：包含 `name`、`description`、`fps` 等元数据。

## Schema

```json
{
  "version": "1.0",
  "name": "示例舞蹈",
  "description": "一段适合展示的机器人舞蹈",
  "fps": 50,
  "neutral_pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
  "frames": [
    {
      "id": 0,
      "label": "立正起始",
      "duration": 500,
      "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": "开场立正姿态，保持 500ms"
    }
  ],
  "export": {
    "rob": {
      "filename": "示例舞蹈.rob",
      "encrypt": false
    }
  }
}
```

## 字段详解

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✅ | 格式版本号，当前 `"1.0"` |
| `name` | string | ✅ | 动作名称，用于生成文件名 |
| `description` | string | ❌ | 动作描述，供 AI 和人工参考 |
| `fps` | number | ❌ | 参考帧率，默认 50。不影响编译，仅用于预览和插值计算 |
| `neutral_pose` | number[16] | ❌ | 16 舵机中性值数组，默认立正姿态。用于插值和回正参考 |
| `frames` | array | ✅ | 帧数组，至少 1 帧 |
| `export` | object | ❌ | 导出配置 |

### 帧字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | number | ✅ | 帧序号，从 0 开始递增 |
| `label` | string | ❌ | 帧标签，如"立正起始""挥手第一拍" |
| `duration` | number | ✅ | 本帧持续时长（ms），范围 40–1800 |
| `pose` | number[16] | ✅ | 16 个舵机值，范围 0–1000 |
| `notes` | string | ❌ | 帧备注，如修改原因、过渡说明 |

### 导出配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `export.rob.filename` | string | ❌ | 导出文件名，默认 `{name}.rob` |
| `export.rob.encrypt` | boolean | ❌ | 是否 EYPT 加密，默认 `false`（明文 ACT-40） |

## pose 映射关系

`pose[0]` 到 `pose[15]` 严格对应 Tonybot 舵机 `ID1` 到 `ID16`，**顺序不能改变**。权威映射见 `data/servo-map.json` 和 `knowledge/docs/14-servo-layout.md`。

| pose 索引 | 舵机 ID | joint | axis_type | 中位值 |
|-----------|---------|-------|-----------|--------|
| pose[0] | ID1 | `r_hip_yaw` | `yaw_vertical` | 500 |
| pose[1] | ID2 | `r_ankle_axis` | `unknown_pitch_or_roll` | 387 |
| pose[2] | ID3 | `r_knee` | `pitch_lateral` | 500 |
| pose[3] | ID4 | `r_hip_pitch` | `pitch_lateral` | 593 |
| pose[4] | ID5 | `r_hip_roll` | `roll_longitudinal` | 500 |
| pose[5] | ID6 | `r_elbow` | `pitch_lateral` | 575 |
| pose[6] | ID7 | `r_shoulder_axis_2` | `unknown_yaw_or_roll` | 800 |
| pose[7] | ID8 | `r_shoulder_pitch` | `pitch_lateral` | 724 |
| pose[8] | ID9 | `l_hip_yaw` | `yaw_vertical` | 500 |
| pose[9] | ID10 | `l_ankle_axis` | `unknown_pitch_or_roll` | 612 |
| pose[10] | ID11 | `l_knee` | `pitch_lateral` | 500 |
| pose[11] | ID12 | `l_hip_pitch` | `pitch_lateral` | 406 |
| pose[12] | ID13 | `l_hip_roll` | `roll_longitudinal` | 500 |
| pose[13] | ID14 | `l_elbow` | `pitch_lateral` | 425 |
| pose[14] | ID15 | `l_shoulder_axis_2` | `unknown_yaw_or_roll` | 200 |
| pose[15] | ID16 | `l_shoulder_pitch` | `pitch_lateral` | 275 |

## 约束规则

| 约束 | 值 | 说明 |
|------|-----|------|
| 舵机值范围 | 0–1000 | 超出会触发安全审计 violations |
| 单帧时长 | 40–1800 ms | 设备端硬件限制 |
| 单文件帧数 | 1–510 | 设备加载帧数上限 |
| 帧 ID 递增 | id = 前帧 id + 1 | 必须连续递增 |
| 首帧/末帧 | 建议为立正或安全姿态 | 确保设备启停安全 |

## 完整示例

```json
{
  "version": "1.0",
  "name": "挥手问候",
  "description": "右手挥手两次的简短问候动作",
  "fps": 50,
  "neutral_pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
  "frames": [
    {
      "id": 0,
      "label": "立正起始",
      "duration": 500,
      "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": ""
    },
    {
      "id": 1,
      "label": "抬右手",
      "duration": 300,
      "pose": [500, 387, 500, 593, 500, 575, 800, 400, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": "肩前抬使大臂上扬"
    },
    {
      "id": 2,
      "label": "挥手右",
      "duration": 200,
      "pose": [500, 387, 500, 593, 500, 700, 600, 400, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": "肘弯 + 臂外展模拟挥手"
    },
    {
      "id": 3,
      "label": "挥手左",
      "duration": 200,
      "pose": [500, 387, 500, 593, 500, 300, 900, 400, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": ""
    },
    {
      "id": 4,
      "label": "挥手右",
      "duration": 200,
      "pose": [500, 387, 500, 593, 500, 700, 600, 400, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": ""
    },
    {
      "id": 5,
      "label": "回正",
      "duration": 300,
      "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
      "notes": "收回到立正"
    }
  ],
  "export": {
    "rob": {
      "filename": "挥手问候.rob",
      "encrypt": false
    }
  }
}
```

## 与 .rob 的关系

| 属性 | motion.json | .rob (ACT-40) |
|------|-------------|---------------|
| 格式 | JSON 文本 | 二进制 |
| 可编辑性 | ✅ 任意文本编辑器 | ❌ 需专用工具 |
| 可 diff | ✅ git diff 友好 | ❌ 二进制不可 diff |
| 标注 | ✅ label + notes | ❌ 无标注字段 |
| 加密 | 明文 | 可选 EYPT |
| 设备加载 | ❌ 需编译 | ✅ 直接加载 |

motion.json 编译为 .rob 时：
- `version`、`name`、`description`、`fps`、`neutral_pose` 不写入 .rob
- 每帧的 `duration` 写入帧头 uint16
- 每帧的 `pose[16]` 写入前 16 个槽位的第一个字
- 后 24 个槽位填充 filler triplet（`0x5555 0x0000 0x0000`）
- `label` 和 `notes` 仅存在于 motion.json，不出现在 .rob 中

## 版本兼容

| 格式版本 | 最低 Motion Studio 版本 | 说明 |
|----------|------------------------|------|
| 1.0 | 0.6.0 | 初始版本 |
