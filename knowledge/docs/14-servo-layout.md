# 14 舵机布局与轴向建模

本文档定义 Tonybot Action Simulator 当前采用的舵机布局建模口径，权威数据文件为 `data/servo-map.json`。

## 目标

本建模层只回答三件事：

1. `pose[0]` 到 `pose[15]` 固定对应哪一个舵机 ID。
2. 每个舵机在动作语义上更接近哪一类轴向。
3. 哪些轴向已经较高可信，哪些仍必须靠单舵机小幅实测确认。

本文档**不**修改 `.rob` 解析逻辑，也**不**改变 `pose[16]` 的顺序。

## 轴向枚举

### `yaw_vertical`

绕垂直轴做水平旋转，例如髋部水平转向、肩根水平旋转。

### `pitch_lateral`

绕左右水平轴做前后俯仰或屈伸，例如膝盖、肘部、髋部前后摆、肩部前抬。

### `roll_longitudinal`

绕前后水平轴做侧向翻转，例如髋侧抬、肩侧抬。

### `unknown_yaw_or_roll`

已确认该轴位于双轴关节总成，但仅凭照片和现有动作片段还不能区分它究竟是 `yaw_vertical` 还是 `roll_longitudinal`。

### `unknown_pitch_or_roll`

已确认该轴位于单轴踝部总成，但仅凭照片和现有动作片段还不能区分它究竟更接近 `pitch_lateral` 还是 `roll_longitudinal`。

## 建模原则

1. `pose[0]` 到 `pose[15]` 的顺序固定对应 `ID1` 到 `ID16`，不得为了“更好理解”而重排。
2. 照片只能帮助确认舵机的大致物理布局，例如它位于髋部、膝部、踝部还是肩部。
3. 最终轴向必须通过**单舵机、小幅度、低风险**的真机实测确认，不能只凭外观照片或单个舞姿截图写死。
4. 对暂未确认的轴，数据层必须保留不确定性，而不是简单命名成 `pitch` 或 `roll`。

## 当前映射

| pose 索引 | 舵机 ID | joint | axis_type | 说明 |
|-----------|---------|-------|-----------|------|
| `pose[0]` | ID1 | `r_hip_yaw` | `yaw_vertical` | 右髋水平旋转轴，暂不标成 foot_yaw。 |
| `pose[1]` | ID2 | `r_ankle_axis` | `unknown_pitch_or_roll` | 右踝轴，需实测区分 pitch/roll。 |
| `pose[2]` | ID3 | `r_knee` | `pitch_lateral` | 右膝屈伸。 |
| `pose[3]` | ID4 | `r_hip_pitch` | `pitch_lateral` | 右髋前后摆。 |
| `pose[4]` | ID5 | `r_hip_roll` | `roll_longitudinal` | 右髋侧抬。 |
| `pose[5]` | ID6 | `r_elbow` | `pitch_lateral` | 右肘屈伸。 |
| `pose[6]` | ID7 | `r_shoulder_axis_2` | `unknown_yaw_or_roll` | 右肩第二轴，待实测区分 shoulder_yaw / shoulder_roll。 |
| `pose[7]` | ID8 | `r_shoulder_pitch` | `pitch_lateral` | 右肩前后摆。 |
| `pose[8]` | ID9 | `l_hip_yaw` | `yaw_vertical` | 左髋水平旋转轴，暂不标成 foot_yaw。 |
| `pose[9]` | ID10 | `l_ankle_axis` | `unknown_pitch_or_roll` | 左踝轴，需实测区分 pitch/roll。 |
| `pose[10]` | ID11 | `l_knee` | `pitch_lateral` | 左膝屈伸。 |
| `pose[11]` | ID12 | `l_hip_pitch` | `pitch_lateral` | 左髋前后摆。 |
| `pose[12]` | ID13 | `l_hip_roll` | `roll_longitudinal` | 左髋侧抬。 |
| `pose[13]` | ID14 | `l_elbow` | `pitch_lateral` | 左肘屈伸。 |
| `pose[14]` | ID15 | `l_shoulder_axis_2` | `unknown_yaw_or_roll` | 左肩第二轴，待实测区分 shoulder_yaw / shoulder_roll。 |
| `pose[15]` | ID16 | `l_shoulder_pitch` | `pitch_lateral` | 左肩前后摆。 |

## 关于 3D 预览器

当前 3D 预览器仍使用简化 FK 做姿态可视化：

1. `ID7` / `ID15` 在现有 FK 中仍沿用“肩侧抬式”的临时显示方式，方便连续查看动作趋势。
2. 这只是**预览实现上的临时近似**，不代表这两个舵机已经被确认为 `roll_longitudinal`。
3. `ID2` / `ID10` 当前也只保留为踝部单轴占位，不在数据层硬写死为 pitch 或 roll。

后续如果拿到单舵机实测记录，应优先更新 `data/servo-map.json`，再同步文档和预览器实现。
