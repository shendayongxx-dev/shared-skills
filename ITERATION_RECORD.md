# ecommerce-poster-design 3.1.0-rc.2 迭代记录

状态：文档化历史里程碑，不是可安装发布快照。

本分支承接 `history/ecommerce-poster-design-3.1.0-rc.1`，用于记录 rc.2 在 rc.1 设计上的增量。rc.2 当时未形成独立 Git 提交，因此不得把本分支内容描述为 rc.2 完整代码。

计划增量：

- 增加 SVG Logo 安全预检，拒绝活动内容和外部资源。
- 将权威 SVG 确定性栅格化为至少 2048px 长边透明 PNG。
- ImageGen 只生成预留 Logo 区底图，Logo 由确定性脚本贴放。
- 保存源与派生哈希、尺寸、比例、Alpha 和渲染器信息。
- HC-05 要求 `logo-asset-preflight/1.0` 与 `logo-application/1.0` 证据。

可安装的 3.1 系列完整实现只存在于 `ecommerce-poster-design-v3.1.0-rc.3` Tag 和当前 `main`。
