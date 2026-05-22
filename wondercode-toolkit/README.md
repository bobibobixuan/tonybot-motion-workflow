# WonderCode Toolkit

`wondercode-toolkit/` 用于沉淀 **依赖 Tonybot 官方积木转换工具** 的工作流，同时作为 `python-toolkit/` 生成动作组后的设备端调用层。

当前这部分内容的目标很直接：

1. 记录 WonderCode / 官方积木导出 Python 的真实结果。
2. 给出积木指令到 Hiwonder Python API 的一一映射。
3. 提供一份可直接保存、阅读和复用的完整示例脚本。

## 当前范围

- **路线**：积木编程 -> 官方转换工具 -> Python 源码
- **依赖**：`Hiwonder`、`Hiwonder_IIC`、`Hiwonder_BLE`
- **对象**：Tonybot 主程序、蜂鸣器、IMU、蓝牙、UART
- **不做的事**：这里不在本目录内部重复实现 `.rob` 容器逆向、`EYPT` 解密或动作文件重编译；这些继续由 `python-toolkit/` 负责

## 目录

- [文档/01-官方转换工具路线.md](文档/01-官方转换工具路线.md)：说明为什么这套内容以官方转换结果为准。
- [文档/02-完整积木指令映射.md](文档/02-完整积木指令映射.md)：Tonybot 常见积木到 Python API 的完整映射。
- [文档/03-融合工作流.md](文档/03-融合工作流.md)：把 `python-toolkit/` 生成的新动作组接到官方转换风格主程序里。
- [examples/tonybot_complete_blocks.py](examples/tonybot_complete_blocks.py)：按官方转换结果整理的设备控制示例脚本。
- [examples/tonybot_control_flow_blocks.py](examples/tonybot_control_flow_blocks.py)：流程控制积木的官方导出示例。
- [examples/tonybot_simple_dance.py](examples/tonybot_simple_dance.py)：可直接试跑的简易舞蹈示例。
- [examples/tonybot_custom_action_bridge.py](examples/tonybot_custom_action_bridge.py)：调用自定义动作组的桥接主程序示例。

## 使用方式

如果你现在的目标是“先在积木里搭逻辑，再导出 Python 看底层 API 怎么写”，建议顺序如下：

1. 先看 [文档/01-官方转换工具路线.md](文档/01-官方转换工具路线.md)。
2. 再查 [文档/02-完整积木指令映射.md](文档/02-完整积木指令映射.md)。
3. 最后对照 [examples/tonybot_complete_blocks.py](examples/tonybot_complete_blocks.py) 改自己的主程序。

如果你现在的目标是“继续用已验证的反编译/编舞工具链生成新动作组，再用官方风格主程序调用它们”，建议顺序如下：

1. 先看 [wondercode-toolkit/文档/03-融合工作流.md](C:/mycode/bot/wondercode-toolkit/文档/03-融合工作流.md)。
2. 在 `python-toolkit/` 里生成并审计新的 `.rob`。
3. 对照 [examples/tonybot_custom_action_bridge.py](examples/tonybot_custom_action_bridge.py) 在设备端调用对应编号。

## 说明

这里的示例代码以你提供的官方转换输出为基线，保留官方工具的调用风格，包括：

- `Hiwonder.startMain(start_main)`
- `Tonybot()` / `Buzzer()` / `UART()` / `BLE()`
- `imu.read_gyro_data()[0]` / `imu.read_angle()[0]`
- `ble.parse_uart_cmd("0")`
- `uart.parse_uart_cmd("0")`

## 交叉验证结论

当前已经用 `python-toolkit/` 的动作库索引和 `wondercode-toolkit/` 的官方转换代码做过一轮交叉验证，先确认两件事：

1. `runActionGroup(N, x)` 的第一个参数 `N` 确实对应动作组编号 / `.rob` 文件编号。
2. 适合默认拿来试机的原厂动作号包括 `0`（立正）、`9`（挥手）、`10`（鞠躬）、`49`（原地踏步）、`50`（扭腰）。

同时修正一处示例：

- `303` 在 `python-toolkit/` 里是“礼貌鞠躬”预设模块，对应来源是原厂 `10号鞠躬`，不是默认出厂动作号。
- 因此 `wondercode-toolkit/examples/tonybot_simple_dance.py` 已改为直接调用原厂 `10`，避免你在纯原厂动作环境里试跑失败。

目前仍保留一个待继续确认点：

- `python-toolkit/` 旧文档把 `runActionGroup(N, x)` 的第二个参数解释成“模式”，但你给出的官方转换结果把它表现成“次数”。后续应以官方转换结果优先。
