# 美学 Agent 接入：no-consumer 消融版

硬合规通过后直接组装 `A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER`。输入严格包含 `schema_version`、`ablation`、`candidate`，不得附加任何消费者评估产物。

```text
python scripts/assemble_aesthetic_input.py --candidate <candidate.json> --output <aesthetic-input.json>
python modules/aesthetic-agent/scripts/score_evaluation.py --workflow-input <aesthetic-input.json> --draft <draft.json> --output <result.json> --details <details.json>
python scripts/route_aesthetic_result.py <result.json> --details <details.json> --workflow-input <aesthetic-input.json> --redraw-attempts <n>
```

美学仍使用 rc.4 的 25 子项、六维权重和门槛。失败建议必须包含 `允许编辑：`、`禁止编辑：`、`保护范围：`、`验收：`。路由生成 `aesthetic-edit-lock-no-consumer/1.0`；只冻结八组保护内容和未开放的美学维度。

返图重新执行 HC-01～HC-12、美学和最终质量门。本消融版没有五维消费者锁、消费者基线或消费者回退判断，报告必须明确这一实验限制。
