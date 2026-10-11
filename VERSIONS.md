# 版本与 Git 引用规则

## main

`main` 代表当前可用主线，只保留一个完整版本：

| 当前版本 | Skill 目录 | 测试目录 |
|---|---|---|
| 3.1.0-rc.3 | `skills/ecommerce-poster-design-3.1.0/` | `tests/ecommerce-poster-design-3.1.0/` |

## 消融实验（独立分支，不进入版本序列）

| 实验标识 | 固定基线 | Git 分支 | 唯一删除变量 |
|---|---|---|---|
| 3.1.0-rc.3-ablation-no-consumer | 3.1.0-rc.3 | `experiment/ecommerce-poster-design-3.1.0-rc.3-ablation-no-consumer` | 消费者 Agent、消费者评分、五维锁、回归检测及全部消费者产物依赖 |

消融分支不得合并回正式主线，不创建或复用正式发布 Tag，也不得改写 `latest_version`。

## Tags

Tag 是不可变发布快照。旧版本从 Tag 获取，不要求其目录继续存在于 `main`。

| 版本 | Tag | 状态 |
|---|---|---|
| 1.0.0 | `ecommerce-poster-design-v1.0.0` | 历史稳定版 |
| 1.0.0-imagegen.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` | 历史独立版 |
| 2.0.1 | `ecommerce-poster-design-v2.0.1` | 历史稳定版 |
| 3.0.0 | `ecommerce-poster-design-v3.0.0` | 历史稳定版 |
| 3.0.0 rebuilt rc4 | `ecommerce-poster-design-v3.0.0-rebuilt-rc4` | 3.1 基线 |
| 3.1.0-rc.3 | `ecommerce-poster-design-v3.1.0-rc.3` | 当前稳定标记版（版本号保留 rc.3） |

任何已发布 Tag 都不得强制更新或复用。修复发布新补丁版本，兼容功能发布新次版本，不兼容变更发布新主版本。

## Branches

- `main`：当前正式主线；
- `feature/<version>`：新功能开发；
- `fix/<version>-<topic>`：问题修复；
- `release/<version>`：需要独立冻结时使用的发布准备分支。
- `archive/<version>`：历史可验证快照；只有存在真实历史提交时才能创建；
- `history/<version>`：没有独立可运行提交时，仅记录迭代说明，不得宣称为安装快照；
- `experiment/<name>`：消融或对照实验，与 `main` 和正式 Tag 隔离。

开发分支可以更新；合并完成后可删除。已有历史分支不因本次目录整理而改写。
