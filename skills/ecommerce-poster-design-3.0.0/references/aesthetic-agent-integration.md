# 3.0 美学 Agent 接入

3.0 保留 2.0.1 的输入、分类、ImageGen、HC-01～HC-12 和消费者 A-D-2.0 链路，在消费者真实通过后调用 `modules/aesthetic-agent` v2.4。美学模块来源固定到提交 `5f0baa0d10c5e1e114ac9a05fb33580110f31d33`，且不修改原 2.0.1 Skill。

## 调度顺序

`输入 → C 分类/style_guide → 生成 → 完整硬检查 → 消费者 Agent → 美学 Agent → 完成或重画`

- 硬检查未通过：不得调用任何评价 Agent。
- 消费者未通过：按消费者建议重画，再从完整硬检查开始。
- 消费者通过且 `next_route=aesthetic_agent`：运行 `assemble_aesthetic_input.py`，再调用美学模块。
- 美学未通过：按美学内部 `redesign-plan.json` 和 `redesign-prompt.txt` 生成下一候选；新候选必须重新经过完整硬检查和消费者评价，不能直接复评美学。
- 美学通过：只有当前同版本硬检查、消费者和美学三者均通过，主流程才输出 `passed`。

## 接口适配

消费者 A-D-2.0 输入包含完整 `source_input`、`evaluation_context` 和八组 `protected_content`；美学固定业务输入只允许 `poster_image` 与 `product_input`。适配器只做确定性字段映射，不调用模型、不补写事实：

```text
python scripts/assemble_aesthetic_input.py \
  --consumer-input runs/v01/consumer-input.json \
  --consumer-result runs/v01/consumer-result.json \
  --hard-check-report runs/v01/hard-check.json \
  --consumer-report runs/v01/consumer-result.json \
  --input-output runs/v01/aesthetic-input.json \
  --context-output runs/v01/aesthetic-context.json
```

映射如下：

| 美学字段 | 3.0 上游来源 |
|---|---|
| `poster_image` | 消费者输入的 `poster_image` |
| `product_img` | `evaluation_context.product_img` |
| `selling_points` | `source_input.product.selling_points` |
| `price_text` | `source_input.commerce.price_text` |
| `marketing_target` | `source_input.marketing.goal` |
| `scene_tags` | `evaluation_context.scene_tags` |

同版本硬检查、消费者报告引用和八组保护内容进入 `aesthetic-context.json`，不污染美学固定业务输入。美学脚本将八组对象确定性展平为固定输出中的字符串数组；主流程路由时恢复并逐组保留消费者原对象，任何删改都会报错，而不是静默丢字段。

## 美学执行

视觉模型必须实际查看当前海报、原商品图和本地存在且有权使用的命中参考图，按美学模块 `schemas/review.schema.json` 形成内部 review。Node 脚本只计算分数和产物：

```text
node modules/aesthetic-agent/scripts/match-references.mjs --input runs/v01/aesthetic-input.json --out runs/v01/reference-match.json
node modules/aesthetic-agent/scripts/match-quality-examples.mjs --category <品类> --out runs/v01/quality-match.json
node modules/aesthetic-agent/scripts/evaluate.mjs \
  --input runs/v01/aesthetic-input.json \
  --review runs/v01/internal-review.json \
  --context runs/v01/aesthetic-context.json \
  --references runs/v01/reference-match.json \
  --quality-examples runs/v01/quality-match.json \
  --out runs/v01/aesthetic
```

参考图文件缺失时只能使用文字原则，必须记录 warning，不能声称模型看过图片。`score=0` 且 `confidence=0` 是未评价占位，路由为 `blocked`，不进入最佳分比较。

## 迭代路由

```text
python scripts/route_aesthetic_result.py runs/v01/aesthetic/agent-result.json \
  --consumer-result runs/v01/consumer-result.json \
  --assessment runs/v01/aesthetic/assessment-internal.json \
  --aesthetic-input runs/v01/aesthetic-input.json \
  --config assets/config/version.json \
  --generation-round 0 \
  --stagnation-count 0
```

- `complete`：美学正式通过；完成主流程。
- `regenerate_then_full_pipeline`：按建议重画，之后从 HC-01 重新检查。
- `change_design_direction_then_regenerate`：连续两轮相对历史最佳提升均小于 0.2，换设计方向后重画。
- `complete_aesthetic_input`：图片或评价依据缺失，停止并补齐输入。
- `return_best_candidate`：8 个美学生成轮次用尽，返回历史最高分候选并标记 `degraded/pass=false`。

`--generation-round` 只统计进入美学阶段后形成的新候选：首次进入美学评价时为 0，按美学建议成功形成一张新候选后为 1，最多到 8。进入美学前的硬检查/消费者重画仍遵循 2.0.1 原有最多 3 次计数；两类预算相互独立。美学返图重新经过消费者评价时，消费者路由必须使用 `phase=aesthetic_recheck` 和同一个美学生成轮次，不能重新使用前置 3 次预算。

`--stagnation-count` 是连续低提升轮数：本轮相对历史最佳提升小于 0.2 时加一，否则归零；达到 2 时输出换方向动作并把下一计数重置为 0。调度器必须把返回的 `next_stagnation_count` 传给下一轮，不能从完整分数历史重新推断，否则换方向后会被旧停滞记录重复触发。

当固定对外结果为 `pass=true` 时，`--assessment` 必须提供同次 `evaluate.mjs` 生成的 `assessment-internal.json`，`--aesthetic-input` 必须提供本轮实际输入。路由器会交叉核验海报/商品图/版本绑定、未舍入总分、六维各自门槛、`below_threshold`、integrated 上游资格和配置快照；缺少内部评估、跨候选误用报告或任一维低于 8 时都拒绝正式通过。未通过结果可省略这两个参数。

`--history` 接受仅含历轮有效美学分的 JSON 数组。未评价占位、硬检查失败和消费者失败不加入分数历史。始终保留真实候选路径与其三段报告，不能只记录分数。美学输出可以在八组展平值之后追加本轮确认的额外保护项，但不能删除、改写、重排或重复上游保护项；路由继续原样返回消费者八组对象。

## 验证

```text
python scripts/validate_consumer_integration.py .
python scripts/validate_aesthetic_integration.py .
python scripts/test_consumer_routing.py
python scripts/test_aesthetic_integration.py
node --test modules/aesthetic-agent/tests/evaluate.test.mjs modules/aesthetic-agent/tests/references.test.mjs modules/aesthetic-agent/tests/quality.test.mjs
```
