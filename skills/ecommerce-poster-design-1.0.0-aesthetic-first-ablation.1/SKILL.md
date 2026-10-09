---
name: ecommerce-poster-design-aesthetic-first-ablation
description: "基于电商海报 Skill 1.0 的实验分支：保留原生成与硬合规流程，依次运行美学 Agent 和消费者 Agent，用于 Agent 顺序消融实验。"
---

# 电商商品营销主视觉设计：美学优先消融实验

> 实验版本 `1.0.0-aesthetic-first-ablation.1`。原 1.0.0、消费者集成版和美学 Agent 仓库均不回写、不覆盖。

## 实验变量与固定流程

本实验只改变 1.0 硬性合规之后的评价链，固定顺序为：

`输入校验 → C 分类与 style_guide → 生成/定向重画 → 全量硬性合规 → 美学 Agent → 消费者 Agent → 输出或重画`

- 美学未通过：按美学建议重画；新图从完整硬性合规重新开始。
- 美学通过：才允许进入消费者 Agent。
- 消费者未通过：按消费者建议重画；新图仍须重新经过完整硬性合规和美学 Agent，不能直接回到消费者。
- 两者通过：输出当前候选。
- 任一模块返回输入阻塞、图片不可评价或保护内容不一致：停止自动重画并返回 `blocked`。

为保持与 1.0 消融基线的生成预算可比性，首版之外全局最多重画 3 次。硬合规、美学和消费者触发的重画共用该计数，任何 Agent 都不得重置预算。美学模块自身支持最多 8 轮，但本实验由更小的宿主全局预算截断。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，建立八组 `protected_content`。
2. 读取 `assets/config/version.json`，确认两个 Agent 开关均为 `true`，顺序为 `aesthetic_agent`、`consumer_agent`。
3. 读取 [references/c-assets.md](references/c-assets.md)，校验并检索 C 分类资产。
4. 生成或重画后读取 [references/hard-compliance.md](references/hard-compliance.md)，执行全部硬检查。
5. 硬检查通过后读取 [美学优先接入说明](references/aesthetic-first-ablation.md) 及两个模块各自的 `SKILL.md`。

## 1.0 保留步骤

必填输入、事实保护、C 库校验、标签判断、规则检索、`style_guide` 组装、生成计划和 HC-01 至 HC-12 硬性检查均沿用 1.0.0。不得猜造价格、折扣、数量、活动时间、Logo、法务文案、商品特征或认证。

只有完整硬性合规通过的当前候选才可进入 Agent 链。任何重画都必须重新执行全部硬检查；主观分数不能覆盖硬失败。

## 美学 Agent

使用 `scripts/assemble_aesthetic_input.py` 从同一份 A 规范化输入、C `style_guide` 和八组保护内容生成美学固定输入及保护内容快照。美学 Agent 必须实际查看当前海报、商品原图和可用参考图；Node 脚本只做检索、结构校验、计分与报告，不代替视觉观察或图片生成。

美学正式通过要求为总分至少 8.5、六个维度各至少 8，且内容保护检查通过。外部结果由模块自身生成后，再由 `scripts/route_aesthetic_result.py` 校验保护内容和路由：

- 通过：`invoke_consumer_agent`；
- 未通过且仍有预算：`redraw_then_full_hard_check_then_aesthetic`；
- 未评价或保护内容不一致：`blocked`；
- 预算耗尽：`degraded`，保留历史中硬合规通过且美学分最高的候选，不伪造通过。

## 消费者 Agent

消费者模块按 A-D-2.0 接口工作：查看当前海报及商品参考图，先提交 25 个子项档位与证据，再用确定性脚本汇总五维分数。通过要求为总分至少 80、每维至少 14、无 `hard_fail`、无锁定维度回退；八组保护内容必须逐值原样返回。

使用 `scripts/route_consumer_result.py` 路由：

- 通过：`complete_ablation`。A-D-2.0 的 `next_route=aesthetic_agent` 在本实验表示接口兼容值；由于同版本候选已先通过美学，不再次调用，避免循环。
- 未通过且仍有预算：`redraw_then_full_hard_check_then_aesthetic`；
- `complete_input` 或保护内容不一致：`blocked`；
- 预算耗尽：`degraded`。

## 输出与实验记录

最终输出必须包含海报、硬合规报告、美学结果及内部报告引用、消费者正式结果及评分明细引用、C 标签/规则/案例、八组保护内容、锁定与回退维度、全局重画次数、每轮 Agent 顺序和版本、warnings 与最终状态。

每轮至少记录 `candidate_id`、硬检查结果、美学结果、消费者结果（若美学通过）、触发重画的模块、建议、累计次数和下一动作。只有两个 Agent 对同一候选均通过时才可标记 `passed`。

## 验证

```text
python scripts/validate_ablation_integration.py .
python scripts/test_ablation_routing.py
python modules/consumer-agent/scripts/run_evals.py
node --test modules/aesthetic-agent/tests/evaluate.test.mjs modules/aesthetic-agent/tests/references.test.mjs modules/aesthetic-agent/tests/quality.test.mjs
```

脚本回归只证明接口与路由没有破坏，不等于视觉质量或消费者判断已通过真人校准。真实消融实验必须固定输入、生成模型、随机种子/提示词策略、全局预算和量表版本。
