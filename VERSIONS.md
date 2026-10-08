# 版本目录

本仓库在 `main` 同时保留 ecommerce-poster-design 1.0.0 与 2.0.1。两个目录是独立、完整的 Skill，安装时只复制目标版本目录，并在 Codex Skills 目录中命名为 `ecommerce-poster-design`。

| 版本 | 仓库目录 | 定位 | 发布标签 |
|---|---|---|---|
| 1.0.0 | `skills/ecommerce-poster-design/` | 历史稳定版；不启用消费者 Agent | `ecommerce-poster-design-v1.0.0` |
| 2.0.1 | `skills/ecommerce-poster-design-2.0.1/` | 当前版；整体 Skill 使用 ImageGen，消费者 Agent 负责评价与路由 | `ecommerce-poster-design-v2.0.1` |

测试目录一一对应：

- `tests/ecommerce-poster-design/`：1.0.0 原始验收、夹具与冒烟测试；
- `tests/ecommerce-poster-design-2.0.1/`：2.0.1 评估用例。

## 能力边界

- ImageGen 集成在 2.0.1 整体 Skill 的生成层。
- `modules/consumer-agent/` 不生成或编辑图片，只读取已通过硬性合规的候选，产生评分、证据、问题清单和下一步路由。
- 1.0.0 的目录内容继续由 `ecommerce-poster-design-v1.0.0` 标签冻结，不回写 2.0.1 行为。
