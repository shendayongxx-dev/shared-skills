# 消费者 Agent 接入说明

## 版本与边界

- 主流程版本：3.0.0（继承 2.0.1 消费者接口）；
- 消费者模块：`modules/consumer-agent`，版本 1.5.3；
- 正式接口：A-D-2.0；
- 消费者开关与美学开关均开启；消费者真实通过后才进入美学模块；
- 1.0.0 仍是无 Agent 的消融基线，不回写或覆盖其发布标签。

消费者模块只评价一次并返回 JSON。主流程负责图片生成、硬性合规、日志、路由、统一重画计数和停止条件。

## 输入组装

每轮保留 A 的完整规范化输入、C 的完整 `style_guide` 和八组 `protected_content`。不要为接入消费者模块删减旧字段，也不要从案例库反推商品事实。

```text
python modules/consumer-agent/scripts/assemble_input.py \
  --source <normalized-input.json> \
  --style <style-guide.json> \
  --protected <protected-content.json> \
  --poster <current-poster.png> \
  --output <consumer-input.json>

python modules/consumer-agent/scripts/validate_input.py <consumer-input.json>
```

原任务另有主题、必需展示清单或品牌气质时，通过 `--brief-supplement` 提供。第二轮开始使用 `--previous`、`--iteration` 和 `--version` 继承最近一次完成五维评价的正常结果。`complete_input` 结果不能覆盖正常历史基线。

`brief-supplement` 支持 `theme`、`required_information`、`brand_requirements`，并兼容早期视觉验收中的 `brand_tone`、`test_requirement` 别名。后四项可以是单个字符串或字符串数组；未知字段会返回列出支持字段的明确错误，不再以 Python `unexpected keyword argument` 异常退出。

## 评价与计算

实际评价者必须读取当前海报及所有相关商品参考图，按消费者模块的 `SKILL.md`、量表、25 子项档位和候选边界生成内部草稿。然后用确定性汇总器生成正式 A-D-2.0 输出：

```text
python modules/consumer-agent/scripts/score_evaluation.py <model-draft.json> \
  --context <consumer-input.json> \
  --output <consumer-result.json> \
  --details-output <scoring-details.json>
```

不得沿用旧版 0–10 分、七字段简化 JSON 或模型直接填写五维总分的草稿。正式阈值为总分不低于 80、每维不低于 14、无硬失败、无锁定维度回退。

## 路由表

| 消费者结果 | 2.0 主流程动作 |
|---|---|
| `pass=true` 且 `next_route=aesthetic_agent` | 美学开关为 true，组装固定美学输入与同版本调度上下文后调用美学 Agent |
| 前置阶段 `next_route=poster_generation_skill` | 使用 2.0.1 原有累计重画计数（最多 3 次），随后全量硬检查并复评 |
| 美学返图复检阶段 `next_route=poster_generation_skill` | 当前美学生成轮次已经消耗；若未到第 8 轮，则按消费者问题生成下一美学候选并全量复查 |
| `next_route=complete_input` | 停止自动重画，输出 `blocked` 和具体输入错误 |
| `hard_fail=true` | 不得通过；按建议修复后重新执行完整硬检查 |
| `regressed_dimensions` 非空 | 优先修复回退项，不覆盖最后消费者通过版 |

进入美学前，硬性合规与消费者修改共用 2.0.1 原有 `max_redraw_attempts=3`。进入美学后改用独立 `aesthetic_max_generation_rounds=8`；每张美学返图仍从 HC-01 至 HC-12 全量复查，再重跑消费者和美学评价。两个阶段的计数不得混用或互相重置。达到相应阶段上限时输出 `degraded`，不得伪造 `pass=true`。

图像编辑工具超时、返回空结果或产生不可读文件时，按硬合规文档的兜底协议记录工具错误并改用等价重生成。只有实际形成新候选才增加全局重画计数。

使用确定性路由器解释结果：

```text
python scripts/route_consumer_result.py <consumer-result.json> \
  --config assets/config/version.json \
  --redraw-attempts <前置阶段累计重画次数> \
  --phase pre_aesthetic

python scripts/route_consumer_result.py <consumer-result.json> \
  --config assets/config/version.json \
  --redraw-attempts <冻结的前置阶段累计重画次数> \
  --phase aesthetic_recheck \
  --aesthetic-generation-round <当前美学生成轮次>
```

## 验证

```text
python scripts/validate_consumer_integration.py .
python scripts/test_consumer_routing.py
python modules/consumer-agent/scripts/run_evals.py
```

第一条检查主版本、开关、模块、Schema 和关键脚本是否齐全；第二条运行消费者组件的确定性回归。真实海报读图与重画仍应使用视觉样例做端到端测试。
