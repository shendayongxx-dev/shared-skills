# 验证记录

验证日期：2026-10-09（Asia/Shanghai）

## 已通过

- `python scripts/validate_ablation_integration.py .`
  - 独立实验版本、两个开关、Agent 顺序、共享 3 次重画预算和模块文件均正确。
- `python scripts/test_ablation_routing.py`
  - 12 个路由场景通过，覆盖美学通过/失败/预算耗尽/未评价/保护冲突/缺六维明细，以及消费者通过/失败/预算耗尽/输入阻塞/保护冲突。
- `python scripts/validate_classification.py assets/classification`
  - C 分类资产 `valid=true`、`production_ready=true`；81 个案例中 6 个种子案例覆盖 S01–S06，无错误或警告。
- `python modules/consumer-agent/scripts/run_evals.py`
  - 36 项 A-D 接口及 25 子项计算断言通过。
- `node --test modules/aesthetic-agent/tests/evaluate.test.mjs modules/aesthetic-agent/tests/references.test.mjs modules/aesthetic-agent/tests/quality.test.mjs`
  - 美学模块 31 项测试全部通过。
- 使用消费者模块 NORI 示例运行 `assemble_aesthetic_input.py`，成功生成美学固定输入与八组保护内容适配快照。

## 2026-10-09 实际案例补充

已使用一组中英文商品案例完成真实图片联调。两个版本的首个候选均依次通过 12 项硬合规、美学 Agent（8.58）和消费者 Agent（98），最终路由为 `complete_ablation`，重画次数为 0。联调同时验证并修正了美学模块通用保护前缀与 A 组八组保护对象后缀的适配规则。

为遵守仓库资产边界，用户商品图、Logo、Brief PDF、生成海报和逐轮运行记录均未提交。因为该案例首版通过，图片重画分支仍由确定性回归覆盖；模型评分也不等同于真人校准结论。
