# 版本与 Git 引用规则

## main

`main` 代表当前可用主线，只保留一个完整版本：

| 当前版本 | Skill 目录 | 测试目录 |
|---|---|---|
| 3.0.0 | `skills/ecommerce-poster-design-3.0.0/` | `tests/ecommerce-poster-design-3.0.0/` |

## Tags

Tag 是不可变发布快照。旧版本从 Tag 获取，不要求其目录继续存在于 `main`。

| 版本 | Tag | 状态 |
|---|---|---|
| 1.0.0 | `ecommerce-poster-design-v1.0.0` | 历史稳定版 |
| 1.0.0-imagegen.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` | 历史独立版 |
| 2.0.1 | `ecommerce-poster-design-v2.0.1` | 历史稳定版 |
| 3.0.0 | `ecommerce-poster-design-v3.0.0` | 当前发布版 |
| 1.0.0-aesthetic-first-ablation.1 | `ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1` | 独立实验快照 |

任何已发布 Tag 都不得强制更新或复用。修复发布新补丁版本，兼容功能发布新次版本，不兼容变更发布新主版本。

## Branches

- `main`：当前正式主线；
- `feature/<version>`：新功能开发；
- `fix/<version>-<topic>`：问题修复；
- `release/<version>`：需要独立冻结时使用的发布准备分支。
- `experiment/<version>`：不合并到 `main` 的消融或研究实验。

当前美学优先消融实验位于 `experiment/ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1`。它保留 1.0.0 基线的生成与硬合规，按“美学 Agent → 消费者 Agent”顺序评价。

开发分支可以更新；合并完成后可删除。已有历史分支不因本次目录整理而改写。
