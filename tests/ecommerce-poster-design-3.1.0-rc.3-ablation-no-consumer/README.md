# no-consumer 消融测试

固定基线：`3.1.0-rc.3`。

运行：

```text
cd skills/ecommerce-poster-design-3.1.0-rc.3-ablation-no-consumer
python scripts/test_no_consumer_ablation.py
python scripts/validate_no_consumer_ablation.py
python scripts/validate_logo_pipeline.py
python scripts/validate_classification.py assets/classification
```

验收重点：消费者模块和路由文件不存在；美学/最终质量输入没有消费者结果；编辑合同没有五维消费者锁；文字重叠与 Logo 悬空仍至少为 moderate；基线版本始终记录为 3.1.0-rc.3。
