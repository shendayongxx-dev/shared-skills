# 美学优先消融接入说明

## 目的

在不改动 1.0.0 基线的前提下，验证评价顺序 `aesthetic_agent → consumer_agent`。该顺序以实验请求为准；美学模块原文中关于其他主流程顺序的说明不覆盖本实验编排。

## 数据流

1. A 1.0 生成候选并执行完整硬检查。
2. `assemble_aesthetic_input.py` 从 A 的规范化输入和 C 的 `style_guide` 建立美学固定输入，同时把八组保护对象按固定组序展平为字符串数组。由于美学模块会先生成自身的通用保护说明，宿主必须把该数组原样写入内部 review 的 `design_plan.preserve_additional`；公开结果中允许通用说明作为前缀，但 A 的完整数组必须作为连续、同序、未改写的后缀，不能让模型自行改写。
3. 美学 Agent 实际看图并由自身 `evaluate.mjs` 生成固定结果。
4. `route_aesthetic_result.py` 同时读取公开结果和 `assessment-internal.json`，核对 Agent、总分、六维分项、未评价状态及展平保护内容；只有六维明细与公开结果一致通过才进入消费者。
5. 消费者输入继续使用原始八组对象，不从美学数组反向重建，避免类型和顺序丢失。通过 `modules/consumer-agent/scripts/assemble_input.py` 组装并校验。
6. 消费者结果由 `route_consumer_result.py` 解释。通过即完成；失败重画后回到步骤 1。

## 命令示例

```text
python scripts/assemble_aesthetic_input.py \
  --source runtime/a-normalized.json \
  --style runtime/style-guide.json \
  --protected runtime/protected-content.json \
  --poster runtime/poster-v01.png \
  --output runtime/aesthetic-input.json \
  --protected-output runtime/aesthetic-protected.json

node modules/aesthetic-agent/scripts/evaluate.mjs \
  --input runtime/aesthetic-input.json \
  --review runtime/aesthetic-review.json \
  --out runtime/aesthetic-v01

python scripts/route_aesthetic_result.py runtime/aesthetic-v01/agent-result.json \
  --assessment runtime/aesthetic-v01/assessment-internal.json \
  --expected-protected runtime/protected-content.json \
  --config assets/config/version.json \
  --redraw-attempts 0
```

美学通过后，使用消费者模块的 `assemble_input.py`、`validate_input.py` 和 `score_evaluation.py` 生成正式结果，再运行：

```text
python scripts/route_consumer_result.py runtime/consumer-result.json \
  --expected-protected runtime/protected-content.json \
  --config assets/config/version.json \
  --redraw-attempts 0
```

## 保护内容适配

八组对象的权威副本始终是 A 的 JSON：`product_identity`、`product_quantity`、`brand_and_logo`、`price_and_unit`、`promotion_and_period`、`selling_points`、`cta`、`legal_text`。美学接口所需数组仅按该顺序展平，并作为美学输出的连续原样后缀；消费者结果必须与权威对象深度相等。任何不一致都进入 `blocked`，不得依靠字符串拼接修复。

## 路由真值表

| 阶段 | 结果 | 动作 |
|---|---|---|
| 硬合规 | fail | 重画；预算累计；重新硬检查 |
| 美学 | pass | 调用消费者 |
| 美学 | fail | 重画；重新硬检查后先复评美学 |
| 美学 | 未评价/保护冲突 | blocked |
| 消费者 | pass | 完成实验链 |
| 消费者 | fail | 重画；重新硬检查后先复评美学 |
| 消费者 | complete_input/保护冲突 | blocked |
| 任一重画请求 | 已达 3 次 | degraded，返回最佳合规候选及未解决项 |

## 消融记录要求

对照实验应固定数据集、输入事实、C 标签、生成模型、提示词策略、随机性、画布、全局重画预算、美学量表和消费者量表。每个候选记录两个 Agent 的调用资格和结果，不能把“美学未通过所以未调用消费者”当作消费者缺失数据之外的结论。
