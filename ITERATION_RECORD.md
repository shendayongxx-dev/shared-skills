# ecommerce-poster-design 3.1.0-rc.1 迭代记录

状态：文档化历史里程碑，不是可安装发布快照。

本分支从 `ecommerce-poster-design-v3.0.0` 对应提交分出，用于补齐 3.0 → 3.1.0-rc.1 的功能演进记录。rc.1 当时未形成独立 Git 提交，因此不得把本分支内容描述为 rc.1 完整代码。

计划增量：

- 在硬性合规、消费者 Agent 和美学 Agent 之后增加 `FINAL-QUALITY-3.1` 无分数最终质量仲裁。
- 双 Agent 的 `pass=true` 仅作为上游建议，最终交付由主流程结合画面证据决定。
- 对异常饱和高分执行同候选反向证据复核。
- 引入 `final-quality-edit-lock/1.0`，只开放可定位缺陷区域。

可安装的 3.1 系列完整实现只存在于 `ecommerce-poster-design-v3.1.0-rc.3` Tag 和当前 `main`。
