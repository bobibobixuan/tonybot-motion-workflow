# Changelog

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
