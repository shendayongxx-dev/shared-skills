# 3.1.0-rc.4 视觉验收计划

## 目标

验证比例画布能在不追问绝对像素的情况下确定性归一化；验证主流程最终质量门能拦截双 Agent 的虚假 Pass，同时不会让优秀海报发生无意义重画；并验证 SVG Logo 能作为权威源被安全转换、确定性贴放和审计。本轮不评价消费者或美学量表本身是否已经完成统计校准。

## 最小样本

使用 6 张真实海报，保持商品任务、保护内容和 P-M-S 标签完整：

- 2 张明显差：至少存在一个可定位的 severe 或 moderate 缺陷；
- 2 张一般：内容可用，但存在一个可通过局部编辑修复的 moderate 缺陷；
- 2 张优秀：没有 moderate 以上缺陷，minor 不超过 2 个。

尽量覆盖文字密度、商品呈现、价格层级、场景关系、材质光影和模板感。不要用缺少 Brief 或商品母图的图片测试正式 Pass。

## 每张图保存的文件

```text
case-XX/
  input.json
  poster.png
  consumer-result.json
  consumer-details.json
  aesthetic-result.json
  aesthetic-details.json
  final-quality-standard.json
  final-quality-adversarial.json   # 仅可疑高分时需要
  final-route.json
  human-review.json
```

## 人工验收字段

```json
{
  "expected_class": "bad|borderline|good",
  "expected_action": "regenerate_then_full_pipeline|invoke_adversarial_final_review|complete",
  "must_find_defects": ["TEXT_DENSITY_HIGH"],
  "must_not_edit": ["商品", "价格原文", "卖点原文"],
  "reviewer_comment": ""
}
```

## 通过标准

1. 两张明显差图均不得最终 Pass。
2. 两张一般图至少能定位一个具体区域和中度缺陷，并生成局部编辑合同。
3. 两张优秀图不得因“更高级、更有设计感”等抽象意见触发重画。
4. 可疑高分只触发一次反向复核，不增加全局重画次数。
5. 证据模板化或与画面矛盾时重新评价，不调用 ImageGen。
6. 所有返图合同冻结五个消费者维度和八组保护对象。
7. 新候选重新执行硬检查、消费者、美学和最终质量门。
8. SVG Logo 不由 ImageGen 重画；转换与贴放清单的哈希、尺寸和比例一致，合成后 HC-05 才可通过。
9. 仅给 `4:5` 比例时得到 `1080×1350`，方向派生为竖版，生成前告知实际尺寸且不因缺少绝对像素阻塞。

如果任一明显差图直接通过，3.1 不得提升为稳定版本；应先修最终缺陷扫描提示词或路由条件。如果优秀图被反复重画，应检查缺陷是否缺少位置、可见事实或达到中度严重度的依据。
