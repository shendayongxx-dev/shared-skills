# 消费者 Agent 接入：no-aesthetic 消融版

## 版本与边界

- 实验版本：`3.1.0-rc.3-ablation-no-aesthetic`；基线：`3.1.0-rc.3`。
- 消费者模块保持 1.5.3、A-D-2.0、量表、阈值、Schema 和模块文件不变。
- 美学开关关闭；消费者正式通过且五维全锁后直接进入最终质量门。
- A-D-2.0 的 Pass 仍返回兼容值 `next_route=aesthetic_agent`。主流程只把它解释为 `invoke_final_quality_gate`，不得调用或模拟美学 Agent。

消费者模块只评价并返回 JSON。主流程负责生成、硬合规、路由、全局计数、最终质量门和停止条件。

## 输入与计分

每轮保留完整规范化输入、`style_guide` 和八组 `protected_content`。使用：

```text
python modules/consumer-agent/scripts/assemble_input.py \
  --source <normalized-input.json> \
  --style <style-guide.json> \
  --protected <protected-content.json> \
  --poster <current-poster.png> \
  --output <consumer-input.json>

python modules/consumer-agent/scripts/validate_input.py <consumer-input.json>
python modules/consumer-agent/scripts/score_evaluation.py <model-draft.json> \
  --context <consumer-input.json> \
  --output <consumer-result.json> \
  --details-output <scoring-details.json>
```

实际评价者必须查看当前海报与商品参考图并提交 25 项观察；确定性脚本汇总总分与五维。通过条件保持：总分≥80、每维≥14、无硬失败、无锁定维度回退。

第二轮开始使用 `--previous`、`--iteration` 和 `--version` 继承最近一次完整消费者结果。`complete_input` 不能覆盖正常历史基线。

## 路由

| 消费者结果 | 本实验主流程动作 |
|---|---|
| `pass=true` 且 `next_route=aesthetic_agent` | 保存当前候选与五个锁，解释为 `invoke_final_quality_gate` |
| `next_route=poster_generation_skill` | 按问题定向返图，随后从 HC-01 完整复检 |
| `next_route=complete_input` | `blocked`，补齐输入，不生成 |
| `hard_fail=true` | 不得通过，修复后重跑硬检查与消费者评价 |
| `regressed_dimensions` 非空 | 淘汰返图，恢复最后消费者通过候选 |

硬合规、消费者和最终质量门共用 `max_redraw_attempts=8`。工具失败但没有新候选时不计数。

使用路由器：

```text
python scripts/route_consumer_result.py <consumer-result.json> \
  --config assets/config/version.json \
  --redraw-attempts <当前全局累计次数>
```

## 验证

```text
python scripts/validate_consumer_integration.py .
python scripts/test_consumer_routing.py
python modules/consumer-agent/scripts/run_evals.py
```
