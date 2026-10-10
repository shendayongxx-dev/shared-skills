# 版本目录

本仓库并列保留 ecommerce-poster-design 1.0.0、1.0.0-imagegen.1、2.0.1 与基于 2.0.1 的 3.0.0 集成候选版。各目录独立完整，安装时只复制一个目标版本目录。

| 版本 | 仓库目录 | 定位 | 发布标签 |
|---|---|---|---|
| 1.0.0 | `skills/ecommerce-poster-design/` | 历史稳定版；不启用消费者 Agent | `ecommerce-poster-design-v1.0.0` |
| 1.0.0-imagegen.1 | `skills/ecommerce-poster-design-1.0.0-imagegen.1/` | 1.0 独立版；整体 Skill 使用 ImageGen，不包含消费者 Agent或美学 Agent | `ecommerce-poster-design-v1.0.0-imagegen.1` |
| 2.0.1 | `skills/ecommerce-poster-design-2.0.1/` | 当前稳定基线；整体 Skill 使用 ImageGen 与消费者 Agent | `ecommerce-poster-design-v2.0.1` |
| 3.0.0 | `skills/ecommerce-poster-design-3.0.0/` | 从 2.0.1 重建；消费者五维全锁后进入美学 Agent 3.0.0-rc.4 | `ecommerce-poster-design-v3.0.0-rebuilt-rc4` |

测试目录一一对应：

- `tests/ecommerce-poster-design/`：1.0.0 原始验收、夹具与冒烟测试；
- `tests/ecommerce-poster-design-2.0.1/`：2.0.1 评估用例。
- `tests/ecommerce-poster-design-3.0.0/`：3.0.0 集成评估用例。

## 能力边界

- ImageGen 集成在 2.0.1/3.0.0 整体 Skill 的生成层。
- ImageGen 也集成在 1.0.0-imagegen.1 的生成层；该版本在硬性合规通过后结束，不进入消费者或美学评价。
- `modules/consumer-agent/` 不生成或编辑图片，只读取已通过硬性合规的候选，产生评分、证据、问题清单和下一步路由。
- `modules/aesthetic-agent/` 不生成图片；它读取同版本上游通过记录，产生 25 子项观察、六维确定性评分和局部修改建议。
- 1.0.0 的目录继续由发布标签冻结；3.0.0 不回写 2.0.1 的文件或行为边界。旧美学 v2.4 集成由 `ecommerce-poster-design-v3.0.0-legacy-aesthetic-v2.4` 冻结。
