---
name: ecommerce-poster-design-no-aesthetic
description: "基于 ecommerce-poster-design 3.1.0-rc.3 生成或编辑高完成度电商商品营销主视觉，完整保留原生成设计能力、分类、Logo、硬合规、消费者 Agent、最终质量仲裁与统一预算，仅移除美学 Agent 及其产物。用于 no-aesthetic 单变量消融实验；禁止把消融误解为降低画面质量或采用空背景后贴商品。"
---

# 电商商品营销主视觉设计 Skill 3.1.0-rc.3-ablation-no-aesthetic

> 消融基线严格固定为 `ecommerce-poster-design-v3.1.0-rc.3`。仅移除美学 Agent `3.0.0-rc.4` 及其评分、六维锁、编辑合同和全部输入/输出依赖；保留 rc.3 的 C 2.0.1 分类库、ImageGen、SVG Logo 管线、HC-01～HC-12、消费者 Agent 1.5.3、最终质量门、强制缺陷路由和全局 8 次预算。不得把本实验版登记为 rc.3 正式版或 stable。

## 单变量解释（强制）

- “no-aesthetic”只表示移除美学 Agent 的评估、分数、反馈与路由，不表示关闭生成阶段的视觉设计、构图、光影、材质、场景融合或专业完成度要求。
- 首次候选必须以商品原图为权威参考，在一次完整海报生成/编辑中共同完成商品、场景、光影、接触阴影、透视和文字布局。禁止先生成空背景，再把商品或整套信息机械贴入。
- SVG Logo 仍按 rc.3 的确定性安全管线后置应用；这是唯一允许的固定合成步骤。Logo 底图是“除独立 Logo 外已经完整的海报”，不是空背景板。
- 若商品出现贴图边缘、悬浮、光向冲突、比例或透视不一致，按现有硬合规/最终质量缺陷路由处理；不得以“已移除美学评估”为理由接受。
- 为保证实验可归因，除美学 Agent 及其产物外，不得主动削减或替换基线生成能力、提示词质量、场景整合方式和质量门槛。

## 固定流程

`输入校验 → P-M-S 分类与 C 库检索 → style_guide → Logo 预检 → 生成 → HC-01～HC-12 → 消费者 Agent → 最终质量仲裁 → 验收或统一预算内迭代`

- 不存在美学评价阶段，不调用、读取或模拟美学 Agent。
- 不生成美学总分、六维分数、美学证据、美学锁或 `aesthetic-edit-lock`。
- 消费者接口保持 A-D-2.0 原样；其通过结果中的兼容值 `next_route=aesthetic_agent` 由主流程解释为 `invoke_final_quality_gate`，不得真的调用美学模块。
- 最终质量门仍是 rc.3 的独立无分数缺陷仲裁；它不输出审美分，也不得宣称替代被消融的专业美学评价。
- 每张新候选使旧硬检查、消费者结果和最终质量结果失效，并从 HC-01 开始复检。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，校验输入并建立八组 `protected_content`。
2. 读取 `assets/config/version.json`，确认 `aesthetic_agent=false`、`ablation.id=no-aesthetic`、消费者和最终质量门开启、预算为全局 8 次。
3. 读取 [references/no-aesthetic-ablation.md](references/no-aesthetic-ablation.md)，遵守接口兼容、锁和候选选择适配。
4. 读取 [references/c-assets.md](references/c-assets.md)、[references/imagegen-integration.md](references/imagegen-integration.md) 和 [references/hard-compliance.md](references/hard-compliance.md)。
5. 硬检查通过后按 [references/consumer-agent-integration.md](references/consumer-agent-integration.md) 调用消费者 Agent。
6. 消费者通过后直接按 [references/final-quality-gate.md](references/final-quality-gate.md) 执行无分数仲裁。

## 必填输入与保护内容

必填商品图、商品名称或品类、已确认卖点、价格及促销、营销目标、画布宽高和输出格式。缺失时返回具体字段并停止；不得猜造价格、折扣、数量、活动时间、Logo、法务文案或商品特征。

建立 A-D-2.0 的八组保护对象：商品身份、商品数量、品牌与 Logo、价格与单位、促销与活动时间、卖点、CTA、法务文字。后续候选和报告必须绑定同一 `request_id`、`version_id`、海报文件、图片哈希和保护对象。

## 1. 分类、计划与生成

运行 `scripts/validate_classification.py` 与 `scripts/select_style.py`。证据不足的 P-M-S 维度保持 `null`；按精确三维、二维通配、单维通配、`R-DEFAULT` 检索。生成计划明确商品、品牌、文字、背景、布局、画布和保护区域。

使用系统 `imagegen` / `image_gen`；未经用户确认，不切换到需要 API Key 的 CLI。ImageGen 必须接收商品原图作为权威参考并生成除独立 Logo 外的完整海报，不得只生成空场景。SVG Logo 先由 `prepare_logo_asset.mjs` 安全栅格化为至少 2048px 长边透明 PNG，在完整海报中预留 Logo 安全区，再由 `apply_logo_asset.mjs` 确定性贴放。不得让模型重画、改色、裁切、旋转或改变 Logo 比例。

每张成功候选获得新 `version_id` 和 SHA-256。工具失败、空结果或不可读结果不形成候选，也不增加全局重画次数。

## 2. 硬性合规

每张候选执行 HC-01～HC-12。失败时按可定位事实问题定向返图；所有返图从 HC-01 重新开始。消费者高分或最终质量结论不能覆盖硬失败。

## 3. 消费者 Agent

只有硬检查完整通过的当前候选才能进入消费者评价。使用 `modules/consumer-agent/scripts/assemble_input.py` 组装 A-D-2.0 输入；模型查看当前海报和商品参考图并提交 25 项观察，由确定性脚本计分。

通过要求保持 rc.3 不变：总分≥80、五维各≥14、`hard_fail=false`、无锁定维度回退、八组保护对象一致。

- `next_route=poster_generation_skill`：按建议定向返图，再执行完整链路。
- `next_route=complete_input`：返回 `blocked`，补齐输入，不以重画掩盖缺失。
- `pass=true` 且 `next_route=aesthetic_agent`：把兼容路由解释为 `invoke_final_quality_gate`；保存五个消费者锁，禁止调用美学 Agent。
- `regressed_dimensions` 非空：淘汰返图并恢复最后消费者通过候选；不得用回退候选覆盖基线。

消费者通过后的可选优化不得触发消费者重画；只有最终质量门登记的可定位缺陷可继续触发局部返图。

## 4. 最终质量仲裁

只有当前同一候选通过硬检查和消费者门禁后才能进入。仲裁者必须查看原尺寸海报、360px 缩图和商品参考素材；只核验消费者证据与可见缺陷，不创建美学分或第三套分数。

按 `FINAL-QUALITY-3.1-ABLATION-NO-AESTHETIC` 扫描商品呈现、信息层级、排版、配色场景和视觉完成度。每个缺陷必须有代码、严重度、位置、可见事实、最小修复动作、可编辑对象和保护对象。

- 证据矛盾、模板化或无定位：重评同一候选，不生成、不计数。
- 消费者高分命中 rc.3 的可疑条件：对同一候选执行一次反向复核，不生成、不计数。
- `TEXT_OVERLAP` 与 `LOGO_FLOATING` 至少为 `moderate`，默认仅开放相关文字/Logo及必要留白，允许 1～2 次局部修复。
- 存在任一 critical、severe、moderate，或 minor 超过 2 个：生成 `final-quality-edit-lock-no-aesthetic/1.0` 并局部返图。
- 新候选从 HC-01→消费者→最终质量门完整复检；五个消费者锁和八组保护内容始终冻结。

## 5. 统一预算与候选选择

首版不计重画。硬合规、消费者和最终质量门导致的成功返图共用最多 8 次全局预算，不因阶段、语言或设计方向变化而重置。

- 同一候选通过硬合规、消费者和最终质量门：`passed`。
- 预算耗尽：只在硬合规与消费者均通过的候选中选择；依次优先最终质量已通过、缺陷最高严重度更低、加权缺陷更少、缺陷数量更少、消费者分更高者，输出 `degraded` 和遗留问题。
- 没有可评价输入或图片：`blocked`。
- 不得用美学分或伪美学 Pass 参与选择。

## 输出

输出海报、硬合规报告、消费者结果与五维/25项审计、最终质量结果、P-M-S 与资产引用、八组保护对象、五个消费者锁、版本与图片哈希、全局次数、修改合同和 `passed|degraded|blocked`，并携带：

```json
{
  "ablation_id": "no-aesthetic",
  "ablation_base_version": "3.1.0-rc.3",
  "aesthetic_agent_present": false,
  "aesthetic_artifacts_used": false
}
```

## 禁止事项

- 不调用、导入、读取或模拟美学 Agent。
- 不保留美学模块作为隐藏回退，不伪造美学分数、证据、结果或锁。
- 不把最终质量门描述成美学 Agent 或专业美学评分的替代品。
- 不把消费者的兼容路由值再次解释为实际调用美学。
- 不在硬检查或消费者未通过时执行最终质量门。
- 不让消费者 Agent 或最终质量仲裁直接生成图片。
- 不与 rc.3 正式对照组共用结果目录、缓存、历史候选或报告。
- 不把本实验版发布为 stable，不回写或覆盖 rc.3 基线。
- 不把“移除美学 Agent”解释为生成空背景、后贴商品、模板化降质或放弃专业画面质量。
