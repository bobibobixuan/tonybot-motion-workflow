# Tonybot Action Simulator

Tonybot 动作模拟器 — 3D FK 骨骼姿态预览器。Tonybot Action Simulator 项目的主入口。

## 打开方式

双击 `index.html` 在浏览器中打开。推荐 Chrome / Edge / Firefox。

## 依赖

- Three.js 0.160.0（ESM import from unpkg CDN）
- 需要浏览器可访问 `unpkg.com`

## 功能

- 3D 骨骼渲染 + OrbitControls 视角控制
- 16 舵机滑块实时驱动姿态
- .rob 文件拖拽加载（ACT-40 + EYPT TEA-32 解密）
- 帧时间轴播放/暂停/逐帧/速度调节
- 7 组预设姿态一键切换
- 📋 一键复制当前 Pose（16 个整数）
- 帧跳变提示（仅展示舵机值变化，非安全结论）
- i18n 国际化（zh-CN / en-US）

## 数据来源

- 官方 .rob 动作文件位于 `data/raw-actions/`
- 解析后的 JSON 数据位于 `data/official-actions/actions/`

## 定位

⚠️ 本模拟器是纯 FK 骨骼姿态预览工具，**不是安全仿真器**。
安全审计由 `tools/python/rob_safety.py` 负责。

## 相关文档

- `knowledge/docs/13-3D动作预览器规范.md`
- `data/official-actions/schema.md`
