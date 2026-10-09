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
  "source_schema_version": "2.0.0",
  "taxonomy_version": "1.0",
  "asset_version": "2.0.1",
  "tags": {
    "audience_id": null,
    "motivation_id": "M01",
    "scenario_id": "S01"
  },
  "classification_evidence": [],
  "confidence": {
    "audience": 0.0,
    "motivation": 0.0,
    "scenario": 0.0
  },
  "needs_human_review": true,
  "source_rule_ids": ["R-201"],
  "inheritance_chain": ["R-201"],
  "source_case_ids": [],
  "source_case_statuses": [],
  "source_case_references": [],
  "fallback_level": "single_dimension",
  "selected_palette_set": {
    "palette_id": "R-201-P1",
    "colors": []
  },
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

- `schema_version` 是 A 输出的 style guide 契约版本；`source_schema_version` 是 C 源资产版本，二者不得混用。
- 分类证据不足时对应 tag 为 null，且 `needs_human_review=true`；未知维度只允许匹配 `*`。
- `inheritance_chain` 按父规则到选中规则排列。
- `selected_palette_set` 是本次完整选中的色板；兼容字段 `palette` 必须等于其 `colors`，不得跨色板拼接。
- `source_case_ids` 只包含通过审核、权利和种子门禁的案例；被过滤案例只记录在 `source_case_statuses` 与 warning。
- `source_case_references` 提供内部参考种子的来源 URL、固定 SHA-256 和使用范围。第三方图片只用于内部参考，不是项目自有资产，也不得从公开仓库再分发。
- `layout.information_hierarchy` 由 A 根据 `protected_content` 和 C 的层级偏好生成，不得补写未提供的价格、期限或 CTA。

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

若图像编辑失败，还要记录 `tool_error`（工具、错误类型、耗时、是否产出候选）和 `fallback_mode`。没有产出可检查图片的工具错误不算独立重画轮；随后成功生成的等价候选按一次重画计数。

最终海报在进入 HC-10 前必须归一化到请求中的精确像素尺寸。原始生成尺寸、归一化算法和归一化后尺寸都写入生成配置；归一化后仍需复查安全区、Logo、文字和商品形态。

进入消费者评价的轮次还必须保存：

- A-D-2.0 输入引用、消费者模块版本与 `context_hash`；
- 正式消费者结果、五维分数、证据、锁定维度和回退维度；
- 25 子项内部评分明细引用；
- `next_route` 以及主流程对该路由的解释；
- 全局累计重画次数，不能在 Agent 调用时重置。

## 最终输出状态

- `passed`：硬性检查全部通过；
- `degraded`：达到上限，返回最佳候选和未解决问题；
- `blocked`：缺少必填输入，或消费者评价所需输入冲突、缺失、图片不可读而停止自动迭代。

在 3.0 中，`passed` 要求硬性合规、消费者 Agent 和美学 Agent 对同一候选版本全部通过。消费者返回 `next_route=aesthetic_agent` 时，主流程按 [美学接入说明](aesthetic-agent-integration.md) 组装固定输入并调用美学模块。
