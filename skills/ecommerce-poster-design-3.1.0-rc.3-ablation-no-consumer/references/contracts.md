# no-consumer 消融版数据合同

## 候选

候选沿用 `A-D-2.0` 的商品任务结构与八组 `protected_content`，但不进入消费者评估。每个候选必须包含 request_id、poster_image、loop_state.version_id、图片 SHA-256、生成日志和硬合规报告。

## 美学输入

严格使用：

```json
{
  "schema_version": "A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER",
  "ablation": {
    "id": "no-consumer",
    "base_version": "3.1.0-rc.3",
    "consumer_artifacts_used": false
  },
  "candidate": {}
}
```

不得增加消费者结果、分数、证据、锁或回退字段。

## 保护对象

`protected_content` 必须恰好包含：product_identity、product_quantity、brand_and_logo、price_and_unit、promotion_and_period、selling_points、cta、legal_text。所有阶段原样传递。

## 状态

- `passed`：当前同一候选通过硬合规、美学和最终质量门。
- `degraded`：预算耗尽，从硬合规通过候选中选择美学分最高者，并声明未验证消费者有效性。
- `blocked`：输入、图片或评价证据不可用。

所有产物必须记录 `ablation_id=no-consumer`、`ablation_base_version=3.1.0-rc.3`、`consumer_artifacts_used=false`，与对照组分目录保存。
