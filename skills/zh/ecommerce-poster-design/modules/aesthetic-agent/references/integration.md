# A工作流接入

## 位置

```text
A生成候选
  → 硬检查
  → 消费者Agent
      ├─ score=null：补输入
      ├─ pass=false：A按消费者建议修改
      └─ pass=true：调用本美学Agent
          ├─ score=null：补输入/图像，不生成
          ├─ pass=false：A按美学局部提示词修改
          │    → 新图重新硬检查→消费者→美学
          └─ pass=true：A最终验收
```

## 输入

```json
{
  "schema_version": "A-D-AESTHETIC-3.0",
  "candidate": {"...": "完整A-D-2.0消费者输入"},
  "consumer_result": {"...": "该候选的A-D-2.0消费者正式输出"}
}
```

`candidate.poster_image`、`candidate.request_id`、`candidate.loop_state.version_id`、八组保护对象必须与消费者结果属于同一候选。A另存图片SHA256、硬检查报告、消费者/美学版本和模型版本；七字段美学响应不承担这些日志字段。

上游必须满足：消费者 `score>=80`、五维各≥14、`pass=true`、`hard_fail=false`、`next_route=aesthetic_agent`，并累计锁定五个消费者维度。否则A不应调用美学。

## 模型草稿

视觉模型依据实际图片生成符合 `schemas/evaluation-draft.schema.json` 的内部草稿。25项键必须与 `assets/rubric.json` 完全一致；每项含 `level`、`evidence`、`enhancement_evidence`、`root_issue_id`。同一根因复用同一root_issue_id，避免重复扣分。

失败时最多输出三对问题/建议。建议必须含允许编辑、禁止编辑、消费者功能锁和验收四段。通过后可不提建议；可选建议不得触发A重画。

无法读取图像或缺少关键事实时，草稿只提交非空 `evaluation_blocked`、成对问题/建议和confidence，计分器输出 `score=null`。

## 确定性计分

```powershell
python scripts/score_evaluation.py `
  --workflow-input workflow-input.json `
  --draft evaluation-draft.json `
  --output aesthetic-result.json `
  --details aesthetic-details.json
```

脚本验证消费者上游、保护对象、25项集合、档位、证据、4档增强证据、建议结构和硬问题，再计算输出。`aesthetic-result.json` 是业务响应；`aesthetic-details.json` 是A的内部审计记录。

## 输出

业务响应固定为：

```json
{
  "agent_name": "aesthetic_agent",
  "score": 82,
  "pass": true,
  "problem_list": [],
  "modify_suggestion": [],
  "protected_content": {},
  "meta": {
    "judge_dimensions": [
      "构图与视觉平衡",
      "视觉层级",
      "配色与对比",
      "字体与排版",
      "风格与场景适配",
      "材质光影与细节完成度"
    ],
    "confidence": 0.86
  }
}
```

消费者和美学都采用百分制，但维度不同，不能相加或平均。美学总线80不替代六个单维下限。

## A执行修改

美学不通过时，A只把本轮未达标维度对应建议交给制作模块，同时附当前海报、原商品素材、八组保护对象和消费者锁。A实际生成后创建新version_id及图片哈希，旧分数全部失效。新候选重新进入硬检查和消费者评价，消费者通过后再调用美学。

生成式整图编辑可能改变锁定区域；正式制作优先使用蒙版或分层素材，把商品、Logo和文字作为确定性图层。无论制作方式如何，都必须检查实际输出，不能用提示词宣称已经保留。
