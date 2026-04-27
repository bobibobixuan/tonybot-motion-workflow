# Changelog

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