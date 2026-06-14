# Tonybot Action Simulator

`simulator/` 是当前仓库的主可视化入口。它不是普通的“骨骼 Demo”，而是围绕 **16 路舵机实测映射** 搭建的动作校对工具。

## 定位

这个页面只做三件事：

1. 把 `pose[0]..pose[15]` 按 `ID1..ID16` 渲染成 3D FK 姿态。
2. 让你逐路拖动舵机，直接核对“站立值、镜像关系、增减方向和关节功能”。
3. 读取 `.rob` 文件，按帧预览动作并提示大跳变。

它**不**输出以下任何结论：

1. 平衡分
2. 质心轨迹
3. 支撑面
4. 安全通过/失败

安全审计仍由 `tools/python/rob_safety.py` 负责。

## 关节映射基准

模拟器当前以 `data/servo-map.json` 为权威数据源，核心结论如下：

1. `ID1..ID5` 是右腿。
2. `ID6..ID8` 是右臂。
3. `ID9..ID13` 是左腿。
4. `ID14..ID16` 是左臂。
5. `ID7` / `ID15` 是肩侧向轴。
6. `ID8` / `ID16` 是肩根部旋转轴。
7. `ID2` / `ID10` 是踝俯仰轴。

标准站立帧：

```text
[500, 387, 500, 593, 500, 575, 800, 724,
 500, 612, 500, 406, 500, 425, 200, 275]
```

## 页面结构

页面是三栏结构：

1. 左栏：实时 Pose、当前舵机详情、镜像对照、16 路映射速查。
2. 中栏：3D 视口，只做姿态预览。
3. 右栏：16 路舵机滑块、预设动作、时间轴播放。

这意味着你不用再同时对照文档和代码，页面本身就能做交叉审核。

## 打开方式

推荐直接运行启动脚本：

```powershell
pwsh -NoLogo -NoProfile -File .\simulator\start-simulator.ps1
```

或双击：

- `simulator/start-simulator.cmd`

默认地址：

- `http://127.0.0.1:8123/simulator/`

也可以双击 `simulator/index.html` 直接打开，但读取 `data/` 下 JSON 数据时不如本地服务稳定。

## 主要能力

1. 3D FK 舵机驱动模型，层级为右腿 `1→5→4→3→2`、左腿 `9→13→12→11→10`、右臂 `8→7→6`、左臂 `16→15→14`。
2. 16 路滑块实时驱动，可直接观察镜像关系。
3. `.rob` 文件拖拽加载，支持 ACT-40 明文与 EYPT 加密。
4. 帧时间轴播放、暂停、逐帧和倍速。
5. 当前 Pose 一键复制。
6. 以映射卡片形式展示每路舵机的 `ID / joint / 站立值 / 轴向 / 镜像`。
7. 帧跳变提示只展示数值突变，不附带安全判断。

## 验证建议

每次改模拟器后，至少做以下检查：

1. `node --check simulator/js/*.js` 对模块做语法检查。
2. `Get-Content -Raw -Encoding UTF8 data/servo-map.json | ConvertFrom-Json | Out-Null`
3. 启动本地服务并打开页面，确认：
   - 16 路滑块都能渲染
   - 左栏映射卡片和右栏滑块名称一致
   - 拖动任意滑块后 3D 姿态立即更新
   - 控制台无报错

## 相关文件

1. `simulator/index.html`：页面骨架和样式
2. `simulator/js/config.js`：16 路舵机对象化配置
3. `simulator/js/robot-scene.js`：3D 舵机驱动渲染
4. `simulator/js/simulator-app.js`：滑块、参考面板、时间轴和 `.rob` 加载
5. `data/servo-map.json`：舵机映射权威数据
6. `knowledge/docs/13-3D动作预览器规范.md`
7. `knowledge/docs/14-servo-layout.md`
