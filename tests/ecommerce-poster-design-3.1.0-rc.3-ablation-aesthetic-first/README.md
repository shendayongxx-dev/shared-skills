# aesthetic-first 顺序消融测试

固定基线：`3.1.0-rc.3`。

唯一实验变量：消费者 Agent 与美学 Agent 的评价顺序由“消费者 → 美学”调整为“美学 → 消费者”。量表、阈值、硬性合规、最终质量门与全局 8 次预算保持不变。

运行：

```text
cd skills/ecommerce-poster-design-3.1.0-rc.3-ablation-aesthetic-first
python scripts/test_aesthetic_first_routing.py
python scripts/validate_aesthetic_first_ablation.py
python scripts/validate_logo_pipeline.py
python scripts/validate_classification.py assets/classification
```

验收重点：硬合规后先执行美学评价；美学未通过时不进入消费者评价；消费者返图必须保留六个美学锁；新候选从硬合规开始按美学 → 消费者顺序完整复检；稳定版发布指针始终保持 `3.1.0-rc.3`。

包内仍保留来自稳定基线的旧测试文件用于差异审计；其中依赖“消费者先行”接口的测试不属于本实验验收集。GitHub Actions 只把上列顺序消融测试、资产校验与 Logo 管线作为该实验的门禁，同时继续独立验证稳定版目录。
