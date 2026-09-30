# 输入输出与日志契约

## 输入契约

接受自然语言或等价结构化输入，但执行前必须规范化为：

```json
{
  "request_id": "REQ-001",
  "product": {
    "image_refs": ["商品图路径或附件引用"],
    "name": "商品名称",
    "category": "商品品类",
    "selling_points": ["已确认卖点"],
    "quantity": null
  },
  "brand": {
    "name": "品牌名",
    "logo_ref": "Logo 路径或附件引用",
    "required_elements": [],
    "forbidden_elements": []
  },
  "commerce": {
    "price_text": "完整价格文字",
    "promotion_text": "完整促销文字",
    "promotion_period": "活动时间",
    "legal_text": "法务或限制性文字"
  },
  "marketing": {
    "goal": "营销目标",
    "channel": "投放渠道",
    "usage_context": "使用或购买场景",
    "cta": "行动提示"
  },
  "canvas": {
    "width": 1080,
    "height": 1440,
    "format": "png",
    "language": "zh-CN"
  }
}
```

`quantity` 不明确时可为 null，但生成不得自行增加商品数量。Logo 不存在时 `logo_ref` 可为空；不得自行绘制假 Logo。

## protected content

```json
{
  "product_identity": [],
  "product_quantity": null,
  "brand_and_logo": [],
  "price_and_unit": [],
  "promotion_and_period": [],
  "selling_points": [],
  "cta": [],
  "legal_text": []
}
```

重画时必须逐值继承。只有用户提供的新事实可以改变保护内容。

## style guide

```json
{
  "schema_version": "1.0",
  "taxonomy_version": "1.0",
  "asset_version": "demo-1.0",
  "tags": {
    "audience_id": "P01",
    "motivation_id": "M01",
    "scenario_id": "S01"
  },
  "classification_evidence": [],
  "confidence": {
    "audience": 0.0,
    "motivation": 0.0,
    "scenario": 0.0
  },
  "source_rule_ids": ["R-001"],
  "source_case_ids": ["C-DEMO-001"],
  "fallback_level": "exact",
  "palette": [],
  "typography": {},
  "layout": {},
  "info_density": 3,
  "promotion_intensity": 3,
  "cta_guidance": "",
  "prohibited_styles": [],
  "warnings": []
}
```

`fallback_level` 只能是 `exact`、`two_dimension`、`single_dimension`、`global` 或 `asset_failure_default`。

## 硬性检查结果

```json
{
  "passed": false,
  "round": 1,
  "problem_list": [
    {
      "check_id": "HC-03",
      "severity": "critical",
      "location": "价格区域",
      "evidence": "输入价格与海报显示不一致",
      "repair_action": "恢复输入中的完整价格和单位"
    }
  ]
}
```

严重度只能是 `critical`、`major`、`minor`。存在任何 critical 或 major 问题时不得标记通过。

## 每轮日志

每轮至少保存：

- `request_id`、Skill 版本、Schema 版本、资产版本；
- 输入摘要和 protected content；
- 分类标签、依据、置信度、规则及案例 ID；
- 生成配置和输出引用；
- 硬性检查结果；
- 本轮修改建议及下一步；
- 轮次、开始结束时间、耗时；
- warning。

## 最终输出状态

- `passed`：硬性检查全部通过；
- `degraded`：达到上限，返回最佳候选和未解决问题；
- `blocked`：缺少必填输入，未开始生成。
