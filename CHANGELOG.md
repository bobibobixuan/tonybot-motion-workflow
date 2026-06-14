# Changelog

## 0.7.7 - 2026-06-14

### Changed

- **模拟器按实测关节表重构**：`simulator/index.html` 改为三栏校对结构，新增实时 Pose、当前舵机详情、镜像对照和 16 路映射速查卡片，不再只是单纯的滑块面板。
- **配置层对象化**：`simulator/js/config.js` 重写为以 `SERVO_LAYOUT` 为核心的 16 路舵机对象数组，再派生 `neutral/direction/channel/joint/group`，避免多处散落硬编码。
- **数据源补齐校对字段**：`data/servo-map.json` 现包含 `neutral`、`direction_sign`、`tested_change`、`tested_motion_zh`、`group`、`mirror_id`，可直接用于页面与文档交叉审核。
- **渲染层去重**：`simulator/js/robot-scene.js` 改为从 `SERVO_LAYOUT` 派生 `JOINT_TO_SERVO_ID` 和渲染元数据，不再单独维护第二套舵机定义。
- **文档重写**：`simulator/README.md`、`knowledge/docs/13-3D动作预览器规范.md`、`knowledge/docs/14-servo-layout.md` 已按新关节映射和新页面结构重写；`README.md` 的启动方式与版本说明同步更新。

### Verified

- `node --check` 验证 `simulator/js/config.js`、`i18n.js`、`rob-parser.js`、`robot-scene.js`、`simulator-app.js`、`main.js`
- `ConvertFrom-Json` 验证 `data/servo-map.json`、`simulator/i18n/zh-CN.json`、`simulator/i18n/en-US.json`
- `python -m py_compile tools/python/tonybot_physics.py`
- 本地打开 `http://127.0.0.1:8126/simulator/`，确认页面可加载、映射卡片与滑块名称一致、控制台无错误

## 0.7.6 - 2026-06-14

### Changed

- **舵机映射结论落库**：`data/servo-map.json` 现将 `ID2/ID10` 明确为踝俯仰轴，`ID7/ID15` 明确为肩侧向轴，`ID8/ID16` 明确为肩根部旋转轴，并同步更新中英文标签与说明。
- **模拟器命名与分组同步**：`simulator/js/config.js`、`robot-scene.js`、`i18n/*.json` 与 `index.html` 已改用新的关节命名和中文标签；腿部滑块分组现直接展示全部 5 个腿部舵机，不再把 `ID1/5/9/13` 归为“未使用”。
- **规范文档更新**：`knowledge/docs/09-Python开发指南.md`、`12-motion-json格式规范.md`、`13-3D动作预览器规范.md`、`14-servo-layout.md` 已统一为新的实测结论，并保留 `ID1/2/9/10` 正方向细节需按真机重心微调的保守说明。
- **物理模型注释校正**：`tools/python/tonybot_physics.py` 去除了踝轴“未确认”的旧注释，使代码注释与当前实测结论一致。

### Verified

- `node --check` 验证 `simulator/js/config.js`、`i18n.js`、`rob-parser.js`、`robot-scene.js`、`simulator-app.js`、`main.js`
- `ConvertFrom-Json` 验证 `data/servo-map.json`、`simulator/i18n/zh-CN.json`、`simulator/i18n/en-US.json`
- `python -m py_compile tools/python/tonybot_physics.py`

## 0.7.5 - 2026-06-08

### Changed

- **FK 骨架升级为舵机驱动模型**：`simulator/js/robot-scene.js` 不再只把层级节点当普通关节 pivot，而是将每个 ID 渲染为 `servoCase + servoHorn + childRoot`。
- **setPose 语义修正**：当前姿态更新直接驱动各舵机的 `hornGroup.rotation`，例如 `ID3/ID11` 驱动膝舵机输出，`ID6/ID14` 驱动肘舵机输出，而不是转动抽象关节球。
- **串联机构重构**：腿部现在按 `ID1 -> ID5 -> ID4 -> ID3 -> ID2` / `ID9 -> ID13 -> ID12 -> ID11 -> ID10` 的舵机串联装配；手臂按 `ID8 -> ID7 -> ID6` / `ID16 -> ID15 -> ID14` 的舵机串联装配。
- **未确认轴仍保守处理**：`ID2/ID10` 与 `ID7/ID15` 继续保留为待实测轴向，但渲染层也已改成舵盘单轴输出，不再用普通万向关节近似。
- **文档同步**：`knowledge/docs/14-servo-layout.md` 已改为明确说明 3D 预览器当前采用的是分层单轴 FK 的舵机驱动模型。

### Verified

- 对 `simulator/js/config.js`、`i18n.js`、`rob-parser.js`、`robot-scene.js`、`simulator-app.js`、`main.js` 建立临时 `.mjs` 镜像后执行 Node `--check`，结果 `syntax_check=ok`。

## 0.7.4 - 2026-06-08

### Changed

- **新增本地启动脚本**：添加 `simulator/start-simulator.ps1` 和 `simulator/start-simulator.cmd`，可从仓库根目录启动本地静态服务并打开 `http://127.0.0.1:8123/simulator/`。
- **启动说明更新**：`simulator/README.md` 现优先推荐使用启动脚本，而不是只依赖双击 `index.html`。

### Verified

- `pwsh -NoLogo -NoProfile -File .\simulator\start-simulator.ps1 -NoBrowser -Port 8125 -AutoStopAfterSec 2`
- `Invoke-WebRequest http://127.0.0.1:8125/simulator/ | Select-Object StatusCode`

## 0.7.3 - 2026-06-08

### Changed

- **模拟器入口拆模块**：`simulator/index.html` 改为通过 `./js/main.js` 启动，FK 骨架、i18n、`.rob` 解析和交互逻辑拆分到独立模块，便于后续维护。
- **FK 骨架实现落地**：3D 预览器现已使用分层单轴 FK；腿部层级为 `ID1 -> ID5 -> ID4 -> ID3 -> ID2` / `ID9 -> ID13 -> ID12 -> ID11 -> ID10`，手臂层级为 `ID8 -> ID7 -> ID6` / `ID16 -> ID15 -> ID14`。
- **未确认轴保守渲染**：`ID2/ID10` 与 `ID7/ID15` 继续保留为待实测轴向，但渲染层已统一改为临时单轴近似，不再回退到万向近似。
- **文档结论同步**：`knowledge/docs/14-servo-layout.md` 已从“当前仍使用简化 FK”更新为“已采用分层单轴 FK，未确认轴仍为临时单轴近似”。

### Verified

- 对 `simulator/js/config.js`、`i18n.js`、`rob-parser.js`、`robot-scene.js`、`simulator-app.js`、`main.js` 建立临时 `.mjs` 镜像后执行 Node `--check`，结果 `syntax_check=ok`。

## 0.7.2 - 2026-06-08

### Changed

- **FK 骨架改为分层单轴关节**：`simulator/index.html` 从“按端点摆段”的万向近似改为 `THREE.Group` 分层 pivot 骨架。
- **腿部层级明确化**：右腿采用 `ID1 -> ID5 -> ID4 -> ID3 -> ID2`，左腿采用 `ID9 -> ID13 -> ID12 -> ID11 -> ID10` 的层级结构；膝盖严格单轴 hinge，踝部继续保留为待实测单轴。
- **手臂层级明确化**：右臂采用 `ID8 -> ID7 -> ID6`，左臂采用 `ID16 -> ID15 -> ID14` 的层级结构；肘部严格单轴 hinge，肩第二轴继续保留为待实测单轴。
- **视觉更新逻辑重构**：`updateRobotModel` 现在只改各 pivot 的 `rotation`，不再直接给肢体 mesh 叠多轴旋转。
- **舵机模块挂载修正**：各 `ID` 模块随对应 pivot 层级一起运动，`ID1/ID9` 不再错误挂在脚部语义位置。
- **地面对齐保留**：通过脚底 mesh 的世界包围盒最低点做视觉落地对齐，但未引入 COM、支撑面、平衡分或安全结论。

### Verified

- `pwsh -NoLogo -Command "$node='C:\\Users\\21996\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\bin\\node.exe'; $html = Get-Content -Raw -Encoding UTF8 simulator/index.html; $match = [regex]::Match($html, '<script type=\"module\">(?<code>[\\s\\S]*?)</script>\\s*</body>'); $tmp = Join-Path $env:TEMP 'tonybot-simulator-module-check.mjs'; [System.IO.File]::WriteAllText($tmp, $match.Groups['code'].Value, [System.Text.UTF8Encoding]::new($false)); & $node --check $tmp"`

## 0.7.1 - 2026-06-08

### Changed

- **舵机映射建模细化**：新增 `data/servo-map.json`，为 16 个舵机补齐 `id/channel/joint/label_zh/label_en/axis_type/motion_zh/confidence/needs_calibration`。
- **轴向语义明确化**：引入 `yaw_vertical`、`pitch_lateral`、`roll_longitudinal`、`unknown_yaw_or_roll`、`unknown_pitch_or_roll` 五类轴向枚举，避免把所有关节简单写成 pitch/roll。
- **保留待确认轴**：`ID1/ID9` 继续记为 `r_hip_yaw` / `l_hip_yaw`；`ID2/ID10` 记为 `r_ankle_axis` / `l_ankle_axis`；`ID7/ID15` 记为 `r_shoulder_axis_2` / `l_shoulder_axis_2`，不武断写死最终轴向。
- **文档同步**：新增 `knowledge/docs/14-servo-layout.md`，并更新 `knowledge/docs/12-motion-json格式规范.md`、`knowledge/docs/13-3D动作预览器规范.md`、`knowledge/docs/README.md`。
- **模拟器标签同步**：更新 `simulator/index.html` 与 `simulator/i18n/zh-CN.json`、`simulator/i18n/en-US.json` 中的通道标签和内部 joint 命名；肩部第二轴在当前 FK 中仍仅作临时预览近似。

### Verified

- `pwsh -NoLogo -Command "Get-Content -Raw -Encoding UTF8 data/servo-map.json | ConvertFrom-Json | Out-Null; Get-Content -Raw -Encoding UTF8 simulator/i18n/zh-CN.json | ConvertFrom-Json | Out-Null; Get-Content -Raw -Encoding UTF8 simulator/i18n/en-US.json | ConvertFrom-Json | Out-Null"`

## 0.7.0 - 2026-06-06

### Changed

- **主线重构**：项目从「Tonybot Motion Studio / AI 编舞工作台」收敛为「Tonybot Action Simulator / 动作模拟器」。
- **新主入口**：`simulator/index.html` — 3D 动作模拟器，含 i18n 国际化（zh-CN/en-US）。
- **新数据结构**：`data/official-actions/` — 204 个官方动作组 JSON 数据库（index.json + categories.json + actions/*.json）。
- **工具集中化**：`tools/python/` — 复制 rob_*.py 等核心脚本，路径去中文依赖，rob_library.py 新增 export-official-actions 命令。
- **知识归档**：`knowledge/docs/`（原文档）、`knowledge/wondercode/`（原 WonderCode 工具）。
- **历史归档**：`legacy/choreography/`（编舞）、`legacy/motion-studio/`（Motion Studio 规划）。
- **更新日志迁移**：`更新日志/` → `changelog/`。
- **原目录保留不动**：`python-toolkit/` 和 `wondercode-toolkit/` 保持原样。
- **README/AGENTS 全面更新**以反映新定位。
- **未引入**：COM/支撑面/平衡分、React/Vite、AI 编舞。

## 0.6.0 - 2026-06-05

### Changed

- **项目定位升级**：从「Tonybot Motion Workflow 自动编舞工具链」升级为「Tonybot Motion Studio：AI 辅助动作创作工作台」。
  - 核心闭环：需求 → AI/motion.json → 3D 预览 → 关键帧微调 → 安全审计 → 导出 .rob。
  - 标题、简介、适用场景、GitHub 描述全面更新。
- **四层架构定义**：motion-core（核心层）→ motion-viewer（预览层）→ motion-editor（编辑层，规划中）→ motion-workflow（工作流层）。
- **motion.json 格式规范**：新增可编辑动作工程格式，含完整 schema、pose 映射、约束规则和示例（`12-motion-json格式规范.md`）。
- **架构规划文档**：新增 `11-Motion-Studio架构规划.md`，含项目新定位、目标用户、四层架构、三阶段路线图（格式标准化 → 编辑层 → AI 集成）。
- **文档体系重构**：
  - 预览器规范从 `11-3D动作预览器规范` 重编号为 `13-3D动作预览器规范`（参照 Motion Studio 新编号体系）。
  - `文档/README.md` 阅读顺序扩展为 1–13，新增 Motion Studio 架构规划、motion.json 格式规范和预览器规范。
  - `可视化模拟器/README.md` 补充 Motion Studio 预览层定位和架构文档引用。
- **现有脚本行为不变**：`rob_reverse.py`、`rob_crypto.py`、`rob_safety.py`、`dance_workflow.py` 保持原有行为。
- **预览器无审计功能回归**：未重新加入 COM、支撑面、平衡分等安全审计模块。
- **AGENTS.md** 更新架构定位和文档引用。

## 0.5.2 - 2026-06-05

### Changed

- **3D 动作预览器规范化**：将 `动作模拟器.html` 正式定位为「Tonybot 3D 动作预览器 / Motion Viewer」。
  - 标题统一为「Tonybot 3D 动作预览器」，保留「无安全审计版」提示。
  - 新增 📋 复制 Pose 按钮：一键复制当前 16 舵机值到剪贴板（JSON 数组格式）。
  - 新增帧信息条：顶部显示总帧数、当前已播时长、总时长。
  - 新增帧跳变提示区：相邻帧舵机值变化超过阈值时列出 ID 列表，仅展示突变不输出安全结论。
  - 更新启动控制台日志。
- **文档体系更新**：
  - 新增 `python-toolkit/文档/11-3D动作预览器规范.md`：模块定位、输入格式、舵机映射、UI 功能清单、禁止事项、验证流程、与 rob_safety.py 关系。
  - 新增 `python-toolkit/可视化模拟器/README.md`：打开方式、CDN 依赖、操作说明、定位声明。
  - 更新 `python-toolkit/文档/README.md`：阅读顺序追加第 11 项。
  - 更新根目录 `README.md`：修正预览器描述，删除 COM/支撑面/平衡仪表表述。

### Verified

- `python-toolkit/可视化模拟器/动作模拟器.html` 结构检查通过，JS 语法完整。

## 0.5.1 - 2026-06-05

### Changed

- **3D 模拟器去审计化**：从 `动作模拟器.html` 彻底删除安全审计/平衡判断/支撑面分析功能，定位改为纯 FK 骨骼姿态预览器。
  - 删除顶部平衡分显示（`bal-score`/`bal-status`/平衡仪表）。
  - 删除物理切换按钮（`btn-toggle-physics`/⚖️）。
  - 删除 COM 质心可视化（红球 + 投影虚线）。
  - 删除支撑多边形可视化（绿色半透明面 + 边框）。
  - 删除双脚地面指示环（`rFootRing`/`lFootRing`）。
  - 删除 `updatePhysicsLayer()` 和 `updateBalanceUI()` 函数。
  - 删除 `physicsGroup` 及全部子对象。
  - 标题改为「Tonybot 3D 动作预览器 · 无安全审计版」。
  - 保留全部 FK 骨骼渲染、16 舵机滑块、.rob 加载/帧播放、预设姿态。

## 0.5.0 - 2026-01-20

### Added

- 新增 `python-toolkit/可视化模拟器/动作模拟器.html`：基于 Three.js 的 Tonybot 3D FK 动作模拟器，支持实时姿态预览、平衡分析和 `.rob` 动作帧播放。
  - 16 舵机滑块面板，按右臂/左臂/右腿/左腿分组，实时驱动 3D 骨骼模型。
  - 完整翻译 `tonybot_physics.py` 正向运动学（FK）到 JavaScript，包含 `SERVO_NEUTRAL`、`SERVO_DIRECTION`、关节角度映射、质心计算、支撑多边形和平衡评分。
  - 物理可视化层：红色 COM 球 + 投影虚线、半透明绿色支撑多边形、双脚地面指示环、0–100 平衡得分实时仪表。
  - 支持加载 `.rob` 文件（ACT-40 二进制 + EYPT TEA-32 解密），逐帧播放/自动循环播放，速度可调。
  - 7 组预设姿态一键切换（立正/军礼/展臂/捶胸/正步/伸手/大鹏展翅）。
  - OrbitControls 相机控制、拖拽/快捷键操作、深浅色主题自适应。

## 0.4.9 - 2026-05-22

### Changed

- 按新要求把 `python-toolkit/build_industrial_school_song_queue_safe_merged.py` 和 `169号工业校歌队列广播体操合并版` 重构为 `1分16秒精简版`：保留前半段主歌到第一轮收束，删除后半段重复展开。
- 调整 `169` 的收尾结构，改为 `beat-30-torch-passing` 之后直接接短收势，再用 `19号快速立正` 回正，不再保留原先更长的后半段和最终立正保护段。
- 重新生成 `python-toolkit/动作/169号工业校歌队列广播体操合并版.rob`、对应 `report.json` 和 `timeline.html`；新版为 `193` 帧、总时长 `76000ms`，且保持 `violations=0`。

### Verified

- `C:\\Users\\21996\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe python-toolkit/build_industrial_school_song_queue_safe_merged.py`

## 0.4.8 - 2026-05-22

### Changed

- 将 `python-toolkit/build_industrial_school_song_queue_safe_merged.py` 重构为 `169号工业校歌官方上半身队列版` 生成器，不再从 `167/168` 直接拼接旧规格，而是只允许引用官方 `0-104` 号动作库。
- 重写 `python-toolkit/编舞/169号工业校歌队列广播体操合并版.json`，把原有手写模块和预设模块全部替换为官方动作切片；主体仅保留 `9/26/27/48/53/54/57/58/62` 等上肢主导动作，并移除鞠躬、扭腰、交替拳手写段等非纯官方来源。
- 重新生成 `python-toolkit/动作/169号工业校歌队列广播体操合并版.rob`、对应 `report.json` 和 `timeline.html`；新版为 `369` 帧、总时长 `150500ms`，相对旧版 `150490ms` 的差值为 `+10ms`，这是纯官方上半身片段 `50ms` 裁切粒度下的最近可实现值。

### Verified

- `C:\\Users\\21996\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe python-toolkit/build_industrial_school_song_queue_safe_merged.py`

## 0.4.7 - 2026-05-18

### Fixed

- `python-toolkit/编舞/167号工业校歌队列广播体操版A.json` 的 `beat-07-reform-spring` 从 `389号手写低位提振` 改为 `391号手写开场点头`，修正真机在约 `17s~18s` 出现的失稳风险。
- `python-toolkit/编舞/169号工业校歌队列广播体操合并版.json` 同步移除 `389号手写低位提振`，确保合并版不再带入该危险段。

### Changed

- 更新 `python-toolkit/文档/10-队列安全动作分组.md`，将 `389号手写低位提振` 从队列推荐动作中移出并标记为谨慎动作，避免继续误判为稳定队列段。

## 0.4.6 - 2026-05-17

### Added

- 新增 `python-toolkit/build_industrial_school_song_queue_safe_merged.py`，自动生成并构建 `169号工业校歌队列广播体操合并版`，把 A/B 两段队列安全版压缩到单文件 510 帧限制以内。
- 新增 `python-toolkit/build_breakdance_showcase.py`，自动生成并构建 `170号霹雳舞炫技版`。

### Changed

- 将 PowerShell 7 偏好追加到全局 `C:\\Users\\21996\\.codex\\AGENTS.md`，后续默认优先用 `pwsh`，必要时可由 `cmd` 拉起，避免中文输出乱码。

## 0.4.5 - 2026-05-17

### Added

- 新增 `python-toolkit/文档/10-队列安全动作分组.md`，把动作库整理为禁用动作、谨慎动作和多人队列表演推荐动作，明确将 `17号/326号大鹏展翅`、侧滑、前进、转向等列为队列安全黑名单。
- 新增 `python-toolkit/编舞/167号工业校歌队列广播体操版A.json`，作为工业校歌多人队列表演安全版 Part A。
- 新增 `python-toolkit/编舞/168号工业校歌队列广播体操版B.json`，作为工业校歌多人队列表演安全版 Part B。

### Changed

- 更新 `python-toolkit/文档/README.md` 和根目录 `README.md`，补充队列安全动作分组文档入口。
- 工业校歌新的队列版明确禁用 `326号大鹏展翅`、`311号左右侧滑往返`、`342号前行两步` 以及全部转向/位移动作，改用展示姿态、招手问候、捶胸强调、伸右手、手写扭腰和交替拳构成广播体操风格上半身编舞。

## 0.4.4 - 2026-05-17

### Added

- 新增 `wondercode-toolkit/文档/03-融合工作流.md`，明确 `python-toolkit/` 负责生成新动作组，`wondercode-toolkit/` 负责以官方转换风格主程序调用这些动作组。
- 新增 `wondercode-toolkit/examples/tonybot_custom_action_bridge.py`，示范如何从官方风格主程序里调用已由 `python-toolkit` 生成并部署到设备上的自定义动作组。

### Changed

- 更新 `wondercode-toolkit/README.md`，把目录定位从“仅官方转换记录”扩展为“官方调用层 + 自定义动作组桥接层”。

## 0.4.3 - 2026-05-17

### Fixed

- 通过 `python-toolkit/` 动作库索引与 `wondercode-toolkit/` 官方转换样例交叉验证后，修正 `wondercode-toolkit/examples/tonybot_simple_dance.py` 的鞠躬动作编号：`303` 改为原厂 `10`，避免把预设模块编号误当成出厂动作号直接调用。

### Changed

- 更新 `wondercode-toolkit/README.md`，补充当前交叉验证结论，明确原厂动作号与预设模块号的区别。

## 0.4.2 - 2026-05-17

### Added

- 新增 `wondercode-toolkit/examples/tonybot_simple_dance.py`，提供一个可直接试跑的 Tonybot 简易舞蹈示例：立正 -> 原地踏步 -> 扭腰 -> 挥手 -> 鞠躬 -> 立正。

### Changed

- 更新 `wondercode-toolkit/README.md` 示例索引，补充简易舞蹈入口。

## 0.4.1 - 2026-05-17

### Added

- 新增 `wondercode-toolkit/` 子目录，专门整理 WonderCode / Tonybot 官方积木转换工具导出的 Python 路线。
- 新增 `wondercode-toolkit/README.md`，明确该目录以官方转换结果为准，不再以反向编译为核心。
- 新增 `wondercode-toolkit/文档/01-官方转换工具路线.md`，说明积木 -> 官方转换工具 -> Python 的工作流边界。
- 新增 `wondercode-toolkit/文档/02-完整积木指令映射.md`，整理 Tonybot 主程序、蜂鸣器、IMU、蓝牙、UART 的积木到 Python API 映射。
- 新增 `wondercode-toolkit/examples/tonybot_complete_blocks.py`，收录你提供的完整官方转换示例代码。
- 新增 `wondercode-toolkit/examples/tonybot_control_flow_blocks.py`，收录流程控制积木的官方转换示例代码。

### Changed

- 更新 `README.md` 目录结构说明，补充 `wondercode-toolkit/` 的定位。
- 更新 `wondercode-toolkit/文档/02-完整积木指令映射.md`，补充等待、系统时间、循环、条件、返回、结束循环的导出规则。

## 0.4.0 - 2026-05-17

### Changed

- 将现有 Python 工具链整合到 `python-toolkit/` 目录，为新的 Python 架构腾出根目录空间。
- 所有源码（`rob_*.py`、`dance_workflow.py`、`main.py`、`bip_industrial_school_song.py`）、动作库、编舞、文档、更新日志统一迁移到 `python-toolkit/`。

## 0.3.2 - 2026-05-13

### Fixed

- 工业校歌 Python 版替换 2 处会位移的动作，确保多机同步表演时机器人原地不动：
  - beat-08（启新航）：`342号前行两步` → `328号伸右手×2`（用手势指向前方替代真走）
  - beat-36（青春无悔）：`342号前行两步` → `308号标准踏步×1`（原地踏步保持节奏不位移）

## 0.3.1 - 2026-05-13

### Fixed

- 工业校歌 Python 版替换全部 8 处不稳定动作模块：
  - 7 处 `326号大鹏展翅`（双臂大展开 + 可能单脚支撑 → 会摔）替换为 `305号展示姿态` 或 `325号捶胸强调`（双臂近身，双脚站稳）
  - 1 处 `311号左右侧滑往返`（侧滑单脚重心偏移 → 会摔）替换为 `304号招手问候`（双脚不离地）
- 修复后两段均通过安全审计（violations=0），且符合 510 帧设备加载限制

## 0.3.0 - 2026-05-13

### Added

- 新增 [bip_industrial_school_song.py](bip_industrial_school_song.py)，工业校歌机器人展示舞 Python 版。严格按《工业校歌编舞.md》逐拍展开 57 个 8 拍 + 谢幕，自动依 510 帧限制拆为 Part A（368 帧，前奏+第一段主歌+第一段副歌）和 Part B（291 帧，间奏+第二段主歌+最后副歌+谢幕）。
- `rob_compose.py` 和 `rob_safety.py` 新增 `MAX_ACTION_FRAMES = 510` 设备加载帧数上限检查，编译和审计时超限会阻断。

### Changed

- 修正 510 限制语义：是设备端加载帧数上限（≤510 帧/文件），非动作组编号上限。超限可构建但无法加载到机器，需拆段。
- 更新 [文档/09-Python开发指南.md](文档/09-Python开发指南.md) 重要约束表，明确帧数上限的阻断原因。

## 0.2.3 - 2026-05-13

### Added

- `rob_compose.py` 和 `rob_safety.py` 新增 `MAX_ACTION_FRAMES = 510` 设备端帧数上限常量，编译和审计时自动检查，超限会阻断并给出明确错误信息。

### Changed

- [文档/09-Python开发指南.md](文档/09-Python开发指南.md) 新增重要约束表，列出五项硬限制：单文件帧数 ≤510、舵机值 0–1000、单帧时长 40–1800ms、安全审计 violations=0、前后回正。

## 0.2.2 - 2026-05-13

### Added

- 新增 [文档/09-Python开发指南.md](文档/09-Python开发指南.md)，完整覆盖三种用 Python 代码生成 `.rob` 动作文件的方式：引用已有动作段、语义锚点写帧、自定义舵机值。含关节映射表、完整 API 参考和端到端示例。

## 0.2.1 - 2026-05-13

### Added

- 新增 [文档/07-动作库目录.md](文档/07-动作库目录.md)，按功能分类整理全部官方动作（0-104号）、预设模块（301-350号）、手写模块（351-400号）和完整编舞（150-165号），编舞选段可直接查表。
- 新增 [文档/08-编舞标准化工作流.md](文档/08-编舞标准化工作流.md)，从舞蹈创意到 `.rob` 的六步 SOP，桥接官方 Hiwonder SDK 与项目工具链。
- 从官方示例和 `main.py` 设备端源码提取完整 Hiwonder Python SDK API 参考（`Hiwonder.Tonybot`、`Hiwonder.Buzzer`、`Hiwonder_IIC`、`Hiwonder_BLE` 等），写入项目记忆。

### Changed

- 更新 [AGENTS.md](AGENTS.md)，补充 SDK 层知识来源引用和动作库目录文档的阅读顺序。
- 更新 [文档/README.md](文档/README.md) 和 [README.md](README.md)，补充新增文档入口。
- 项目定位从"纯逆向工程"升级为"逆向工程 + SDK 对齐"，工具链与设备端 API 知识互补。

## 0.2.0 - 2026-05-12

### Added

- 新增 [编舞/165号工业校歌逐拍精细版.json](编舞/165号工业校歌逐拍精细版.json)，严格按《工业校歌编舞》拆成 `beat-01` 到 `beat-57`，并单独保留最后半个 8 拍谢幕。
- 生成对应产物：
  - `动作/165号工业校歌逐拍精细版.rob`
  - `编舞/165号工业校歌逐拍精细版.report.json`
  - `编舞/165号工业校歌逐拍精细版.timeline.html`

### Changed

- 工业校歌从 `164号工业校歌初稿` 的结构化概括版升级为逐拍精细版，逐组覆盖前奏、两段主歌、两段副歌、间奏、结尾和谢幕。
- 固定记忆动作按设计文档稳定复用：“福建工校”“精英殿堂”“桃李芬芳”“播种希望”均有独立动作组和复现说明。
- 将总时长调整到 `247320 ms`，贴近设计文档标注的 `4:07`。

### Verified

- `uv run python dance_workflow.py build "编舞\\165号工业校歌逐拍精细版.json"`
- `uv run python rob_safety.py "动作\\165号工业校歌逐拍精细版.rob"`

## 0.1.9 - 2026-05-12

### Added

- 新增 [编舞/164号工业校歌初稿.json](编舞/164号工业校歌初稿.json)，按《工业校歌编舞》要求生成一版可运行的机器人校歌展示舞初稿。
- 生成对应产物：
  - `动作/164号工业校歌初稿.rob`
  - `编舞/164号工业校歌初稿.report.json`
  - `编舞/164号工业校歌初稿.timeline.html`

### Changed

- 初稿采用“结构先行”的编舞策略，先落下前奏、两段主歌、两段副歌、间奏与谢幕结构，再把“福建工校”“精英殿堂”“桃李芬芳”“播种希望”四个记忆动作写成可重复母题。
- 编舞继续沿用前后自动回正规范，开场和收尾都通过 `guards` 注入保护段。

### Verified

- `uv run python dance_workflow.py build "编舞\\164号工业校歌初稿.json"`
- `uv run python rob_safety.py "动作\\164号工业校歌初稿.rob"`

## 0.1.8 - 2026-05-12

### Removed

- 删除 `动作/` 目录下 10 个与原件逐字节一致的重复 `.rob` 文件，文件名带 ` (1)` 后缀。
- 删除仓库根目录 `__pycache__/` 缓存目录。

### Changed

- 对 `动作/` 和 `动作库解析/` 中带 ` (1)` 后缀的重复项做内容比对，只清理已确认和原件完全一致的二进制动作文件。
- 保留内容不一致的解析 JSON，避免误删可能仍有研究价值的差异样本。

## 0.1.7 - 2026-05-12

### Added

- 新增 `文档/` 目录，集中维护仓库级专题文档索引与整合说明。
- 新增 6 份专题文档，覆盖项目总览、动作逆向、安全模型、编舞工作流、设备控制算法、验证与发布。

### Changed

- 更新 `README.md` 的首屏导读，默认从 `文档/README.md` 和各专题文档进入。
- 保留根目录原有专题文档作为详细正文和历史兼容入口，不再让说明结构分散在仓库首页。

### Verified

- `uv run python -m py_compile rob_reverse.py rob_crypto.py rob_compose.py rob_safety.py dance_workflow.py main.py`

## 0.1.6 - 2026-05-12

### Added

- `rob_safety.py` 新增“控制语义 + 运动学/硬件约束”审计层：
  - 基于语义锚点把帧分类为站姿、侧滑、扭腰、出拳、踢腿、下蹲、鞠躬等控制状态。
  - 学习官方动作库中的语义状态半径和状态迁移集合。
  - 对高负载姿态增加准备/回收中间态检查、最小时长检查和左右对冲直切禁止规则。

### Changed

- 安全模型从单层“统计包络”升级为“双层模型”：
  - 第一层仍保留字段范围、单关节跳变和总姿态跳变约束。
  - 第二层新增语义状态与高负载过渡约束，用于拦截统计包络内但控制语义不合理的动作。
- 更新 `动作安全规范.md`，补充新的安全模型口径。

### Verified

- `uv run python -m py_compile rob_reverse.py rob_crypto.py rob_compose.py rob_safety.py dance_workflow.py main.py`
- `uv run python dance_workflow.py build "编舞\\162号科目三完整版.json"`
- `uv run python rob_safety.py "动作\\162号科目三完整版.rob"`

## 0.1.5 - 2026-05-12

### Added

- `rob_compose.py` 新增顶层 `guards` 配置，支持用 `pre_segments` / `post_segments` 在编舞主体前后注入固定保护段，用于自动回正、稳定起拍和稳定收尾。

### Changed

- `编舞/162号科目三完整版.json` 改为通过 `guards` 显式插入“302号快速回正 + 0号立正”的开场和收尾保护段，解决真机开头与结束需要自动回正的问题。
- `编舞工作流说明.md` 补充 `guards` 字段说明，明确前后自动回正应通过保护段机制配置，而不是散落在主体节拍里。

### Verified

- `uv run python -m py_compile rob_reverse.py rob_crypto.py rob_compose.py rob_safety.py dance_workflow.py main.py`
- `uv run python dance_workflow.py build "编舞\\162号科目三完整版.json"`
- `uv run python rob_safety.py "动作\\162号科目三完整版.rob"`

## 0.1.4 - 2026-05-12

### Added

- 新增 [rob_library.py](rob_library.py)，支持批量分析动作库、导出逐动作 JSON，并把 `EYPT` 动作解密到独立目录。
- 新增 `动作库解析报告.json`、`动作库解析/` 和 `动作库解密/` 产物，用于复现完整动作库内容解析和受保护样本破解结果。

### Changed

- 更新 `.rob` 逆向说明，补充当前 204 个动作文件的库级统计、帧头一致性、filler 校验和第 2/3 字段成对出现的观察结论。

## 0.1.3 - 2026-05-11

### Added

- 新增 [AGENTS.md](AGENTS.md)，固化 Tonybot Motion Workflow 项目规则，覆盖项目定位、逆向结论、动作生成、安全验证、版本日志和 Windows 环境注意事项。

## 0.1.2 - 2026-05-11

### Added

- 完善 `.rob` / `EYPT` 逆向工程指南，补充“逆向是否成功”的判定口径、可复现验收清单和未完成边界。
- 新增独立验证命令说明，覆盖 Python 语法检查、`EYPT` 解密、重加密逐字节比对和明文结构解析。
- 同步更新动作安全规范中的当前参考库统计，匹配 `rob_safety.py` 最新审计输出。

## 0.1.1 - 2026-04-27

### Changed

- 将仓库定位从私有初始化状态调整为公开展示状态。
- 更新 [README.md](README.md) 的仓库标题、简介、状态字段和适用场景说明。
- 更新 [LICENSE](LICENSE) 以匹配公开可见但非开源授权的使用方式。
- 准备将 GitHub 仓库名称调整为更贴合项目主题的命名。

## 0.1.0 - 2026-04-27

### Added

- 初始化 Git 仓库并推送到 GitHub 私有远端。
- 新增 [README.md](README.md)、[VERSION](VERSION)、[CHANGELOG.md](CHANGELOG.md) 和 [LICENSE](LICENSE)。
- 新增 [rob_crypto.py](rob_crypto.py)，独立实现 `EYPT` 的 `TEA-32` 加解密。
- 新增 [rob_safety.py](rob_safety.py)，提供官方动作库学习包络与安全审计能力。
- 新增 [dance_workflow.py](dance_workflow.py)，支持从编舞 JSON 生成 `.rob`、报告 JSON 和时间线 HTML。
- 新增 [编舞/159号自制舞蹈.json](编舞/159号自制舞蹈.json) 与对应报告、时间线产物。

### Changed

- 重构 [rob_compose.py](rob_compose.py)，从硬编码配方升级为 JSON 驱动编译入口。
- 整理工作区目录，将官方动作库统一归档到 [动作](动作) 目录。
- 完善文档体系，补充动作逆向说明、安全规范和编舞工作流说明。

### Verified

- `EYPT` 四个官方样本已完成独立解密 / 重加密逐字节校验。
- `动作/159号自制舞蹈.rob` 已通过独立安全审计，当前结果为 `violations=0`。
