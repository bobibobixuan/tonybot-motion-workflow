# Tonybot 3D 动作预览器（Motion Viewer）

本目录包含 Tonybot Motion Studio 的 **预览层** — Tonybot 3D 动作预览器（Motion Viewer），
一个基于 Three.js 的纯 FK 骨骼姿态预览工具。

## 如何打开

双击 `动作模拟器.html` 即可在默认浏览器中打开。推荐使用 Chrome、Edge 或 Firefox 最新版。

## 依赖说明

预览器通过 ESM import 从 unpkg CDN 加载 Three.js 0.160.0：

```
https://unpkg.com/three@0.160.0/build/three.module.js
https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js
```

需要浏览器能访问上述两个地址。首次加载可能需要几秒下载 JS 模块。

## 支持的操作

- **拖拽 .rob 文件**：直接把 `.rob` 文件拖到 3D 视口中即可加载播放。
- **点击 📂 按钮**：通过文件选择器加载 `.rob` 文件。
- **舵机滑块**：右侧面板 16 个滑块实时驱动 3D 骨骼姿态。
- **预设姿态**：一键切换到立正/军礼/展臂等 7 组预设。
- **帧播放**：加载 `.rob` 后出现时间轴，支持播放/暂停、逐帧、速度调节。
- **键盘快捷键**：`← →` 逐帧，空格键播放/暂停，`R` 重置姿态。

## 在 Motion Studio 中的定位

本预览器是 Tonybot Motion Studio 四层架构中的 **motion-viewer（预览层）**。

- 负责：FK 骨骼姿态渲染、.rob 加载、帧播放、16 舵机滑块调试、Pose 复制
- 目标：减少线下反复掰机器人调动作的试错成本

## 安全声明

⚠️ **本预览器不是安全仿真器。**

- 仅做 3D FK 骨骼姿态预览，**不输出安全结论**。
- 不计算 COM（质心）、支撑面、平衡分。
- 真正的安全审计由 `python-toolkit/rob_safety.py` 和 `dance_workflow.py build` 流程负责（motion-workflow 层）。
- 预览器中的"帧跳变提示"仅辅助发现舵机值突变，不构成安全判断。

## 架构文档

- Motion Studio 架构规划：`python-toolkit/文档/11-Motion-Studio架构规划.md`
- 预览器详细规范：`python-toolkit/文档/13-3D动作预览器规范.md`
