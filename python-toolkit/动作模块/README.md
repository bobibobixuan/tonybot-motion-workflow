# 动作模块

这个目录存放“可复用自定义动作”的源规格。

- 每个模块 JSON 最终编译到 `动作/`，成为可在后续编舞中直接 `source` 引用的 `.rob` 文件。
- 当需要手写新动作时，先在这里封装成独立模块，再把生成出的 `.rob` 加入动作库。
- 模块规格沿用 `rob_compose.py` 的 `segments` 结构，因此既可以复用已有 `.rob`，也可以用 `frames` 写自定义帧。
- 当前提供一套批量生成脚本，可一次性写出 301-350 共 50 个预设模块。
- 生成后会同步写出 `动作模块/预设模块索引.md`，方便按编号快速查找。
- 另外还提供一套手写帧生成脚本，可一次性写出 351-400 共 50 个手写预设模块。
- 手写预设会同步写出 `动作模块/手写预设模块索引.md`，用于区分“包装模块”和“显式 pose 帧模块”。

常用方式：

- `python rob_compose.py 动作模块/201号科目三预备律动.json`
- `python rob_compose.py 动作模块/202号科目三切分锁点.json`
- `python rob_compose.py 动作模块/203号科目三收束锁点.json`
- `python 动作模块/generate_preset_modules.py`
- `python 动作模块/generate_handwritten_preset_modules.py`