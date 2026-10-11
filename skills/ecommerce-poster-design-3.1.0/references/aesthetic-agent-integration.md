# 3.0 美学 Agent rc.4 接入

本版本从 2.0.1 重建，在同候选硬检查和消费者评价正式通过后接入 `modules/aesthetic-agent` 3.0.0-rc.4。旧版美学 v2.4 已由 Git 标签冻结，不能混用其 0～10 评分、独立轮次或字符串保护内容接口。

## 调度顺序

```text
A 生成当前候选
→ HC-01～HC-12
→ 消费者 Agent A-D-2.0
  ├─ blocked / failed：补输入或统一预算内重画
  └─ pass=true + 五维全锁：美学 Agent
      ├─ score=null：补输入或图像，不生成
      ├─ pass=false：局部修改后回到 HC-01
      └─ pass=true：绑定校验后最终验收
```

任何新候选都会使旧报告失效，并必须重新经过完整链路。

## 组装输入

```text
python scripts/assemble_aesthetic_input.py \
  --candidate <consumer-input.json> \
  --consumer-result <consumer-result.json> \
  --output <aesthetic-input.json>
```

输出严格只有 `schema_version`、`candidate`、`consumer_result`。组装器校验 request、version、海报路径、八组保护对象、消费者分数、五个单维、回退状态、路由和五维锁，只封装，不补写事实。

## 视觉草稿与确定性计分

视觉模型实际查看当前海报原尺寸、360px 缩图、商品素材和任务要求，按 `schemas/evaluation-draft.schema.json` 提交 25 个子项。每项包含 0～4 档位、可定位证据、仅供 4 档使用的增强证据和根因 ID。

```text
python modules/aesthetic-agent/scripts/score_evaluation.py \
  --workflow-input <aesthetic-input.json> \
  --draft <evaluation-draft.json> \
  --output <aesthetic-result.json> \
  --details <aesthetic-details.json>
```

计分器产生固定七字段业务结果和独立审计明细。模型不能直接填写总分。

## 路由与统一预算

```text
python scripts/route_aesthetic_result.py <aesthetic-result.json> \
  --consumer-result <consumer-result.json> \
  --details <aesthetic-details.json> \
  --workflow-input <aesthetic-input.json> \
  --config assets/config/version.json \
  --redraw-attempts <global_count>
```

- `complete`：当前候选三重门禁通过；
- `regenerate_then_full_pipeline`：验证结构化消费者冻结合同后，以最后消费者通过版为底图做局部编辑，然后从 HC-01 重跑；
- `complete_aesthetic_scope`：关键问题没有绑定到未达标美学维度，停止生成并人工确认范围；
- `complete_aesthetic_input`：评价阻塞，补输入或图像，不生成；
- `return_best_candidate`：统一八次重画预算耗尽，返回历史最佳合规候选并标记 `degraded`。

`redraw_attempts` 是硬检查、消费者和美学共享的全局计数。只有成功形成新候选才加一，任何阶段和 Agent 都不能重置。

路由结果中的 `generation_edit_contract` 是生成授权，至少包含：消费者通过基线、仅可编辑的未达标美学维度、已锁定美学维度、五个消费者功能锁、八组不可变保护对象、参考建议、禁止变化和返图检查。建议只是参考；它与结构化锁冲突时不得执行。调用 ImageGen 前运行：

```text
python scripts/validate_generation_edit_contract.py <routed-result.json> \
  --workflow-input <aesthetic-input.json>
```

校验失败时不得生成。返图消费者复评必须继承原消费者通过结果和五个锁；任何 `regressed_dimensions` 都会淘汰返图并恢复基线。

## 正式通过校验

路由器对非空分数要求同次 `aesthetic-details.json`，并交叉核验 request、version、海报、保护对象、业务结果、六维门槛、消费者锁和 `context_hash`。

## 验证

```text
python modules/aesthetic-agent/tests/test_score_evaluation.py
python scripts/test_aesthetic_integration.py
python scripts/validate_aesthetic_integration.py .
```
