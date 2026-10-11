---
name: ecommerce-poster-design
description: "根据商品素材与营销信息生成电商主视觉，并执行硬性合规、专业美学和最终质量仲裁。本目录是基于 3.1.0-rc.3 的 no-consumer 消融实验版，明确不调用、不读取也不模拟消费者评估 Skill；只用于对照实验，不作为稳定生产版本。"
---

# 电商商品营销主视觉设计 Skill 3.1.0-rc.3-ablation-no-consumer

> 消融基线严格固定为 `3.1.0-rc.3`。仅移除消费者 Agent 1.5.3 及其评分、五维锁、回归检测和所有输入/输出依赖；保留 rc.3 的 C 2.0.1 分类库、ImageGen 生成、SVG Logo 管线、美学 Agent rc.4、最终质量门、文字重叠/Logo 悬空强制路由和统一重绘预算。禁止把本消融版标记为 rc.3 正式版或稳定版。

## 固定流程

`输入校验 → P-M-S 分类与 C 库检索 → style_guide → Logo 预检 → 生成 → HC-01～HC-12 → 美学 Agent → 最终质量仲裁 → 验收或统一预算内迭代`

- 不存在消费者评估阶段。
- 不读取 `consumer_result`、消费者五维分数、消费者证据、累计锁或回退字段。
- 不生成伪消费者结果，不用常量 Pass 绕过接口。
- 商品、品牌、价格、促销和文案事实由八组保护内容与硬合规继续保护。
- 美学与最终质量门只评价当前候选和当前图像证据；它们不声称替代消费者有效性评价。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，校验输入并建立八组 `protected_content`。
2. 读取 `assets/config/version.json`，确认 `consumer_agent=false`、`ablation.no_consumer=true`。
3. 读取 [references/c-assets.md](references/c-assets.md) 完成分类资产校验与检索。
4. 读取 [references/imagegen-integration.md](references/imagegen-integration.md) 完成生成与 Logo 管线。
5. 每张候选执行 [references/hard-compliance.md](references/hard-compliance.md)。
6. 硬检查通过后，按 [references/aesthetic-agent-integration.md](references/aesthetic-agent-integration.md) 直接进入美学评价。
7. 美学通过后，按 [references/final-quality-gate.md](references/final-quality-gate.md) 执行 no-consumer 最终仲裁。
8. 实验记录必须携带 `ablation_id=no-consumer` 和基线版本 `3.1.0-rc.3`。

## 必填输入与保护内容

必填商品图、商品名称或品类、已确认卖点、价格促销、营销目标、画布尺寸和输出格式。缺失时阻塞，不猜造事实。

建立八组保护对象：商品身份、商品数量、品牌与 Logo、价格与单位、促销与活动时间、卖点、CTA、法务文字。所有候选、硬检查、美学结果和最终质量结果必须绑定同一 request、version、poster_image、图片哈希和保护对象。

## 1. 分类、计划与生成

按精确三维、二维通配、单维通配、`R-DEFAULT` 检索 P-M-S 与 C 库；证据不足的标签保持 `null`。生成计划明确商品、品牌、文字、背景、布局、画布与保护区域。

使用系统 `imagegen` / `image_gen`。未经用户确认，不使用需要 API Key 的 CLI 回退。SVG Logo 先由 `prepare_logo_asset.mjs` 安全栅格化，ImageGen 只生成预留区底图，再由 `apply_logo_asset.mjs` 确定性贴放；禁止模型重画、改色或改变 Logo 比例。

每张成功候选获得新 `version_id` 和 SHA-256；工具失败且没有新图片不计重绘次数。

## 2. 硬性合规

每张候选执行 HC-01～HC-12。失败时按可定位问题重绘；所有返图从 HC-01 重新开始。硬检查是本消融版保护交易事实和商品真实性的唯一功能门，不能被美学高分覆盖。

## 3. 美学 Agent（无消费者输入）

运行：

```text
python scripts/assemble_aesthetic_input.py --candidate <candidate.json> --output <aesthetic-input.json>
python modules/aesthetic-agent/scripts/score_evaluation.py --workflow-input <aesthetic-input.json> --draft <draft.json> --output <result.json> --details <details.json>
```

输入 Schema 为 `A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER`，严格只含 `schema_version`、`ablation` 和 `candidate`。模型查看原图、360px 缩图、原商品素材和任务，提交 25 个子项观察；脚本计算六维和总分。

通过要求：总分≥80，且构图≥16/20、层级≥16/20、配色≥12/15、排版≥16/20、风格场景≥12/15、材质细节≥8/10，无关键问题。

- `score=null`：补齐图片或输入，不生成、不计数。
- `pass=false`：生成 `aesthetic-edit-lock-no-consumer/1.0`，只开放未达标美学维度，冻结其余美学维度和八组保护内容。
- `pass=true`：进入最终质量仲裁，不直接交付。

美学建议不得出现消费者分数、消费者锁或 `regressed_dimensions`。新候选仍须重新执行硬检查、美学和最终质量门。

## 4. 最终质量仲裁（无消费者证据）

只有同一候选通过硬检查与美学后才能进入。最终门查看原图、360px 缩图和商品参考，不创建新分数，只核验美学证据和可见缺陷。

`TEXT_OVERLAP` 与 `LOGO_FLOATING` 仍至少为 `moderate`；不得因修复简单降为 `minor`。存在任一 moderate 以上缺陷或超过两个 minor 时生成 `final-quality-edit-lock-no-consumer/1.0`，只编辑定位区域。

可疑高美学分触发一次同图反向复核；没有消费者高分触发条件，也没有消费者证据审计字段。每张成功返图重新执行硬检查、美学和最终质量门。

## 5. 统一预算与输出

首版不计重绘；硬检查、美学和最终质量门产生的成功返图共用最多 8 次预算，不因阶段变化重置。

- 同一候选全部通过：`passed`。
- 预算耗尽：只从硬合规通过的候选中选美学分最高者，输出 `degraded`。
- 输入或图像不可评价：`blocked`。

输出必须包含海报、硬检查、美学结果与明细、最终质量结果、P-M-S/C 库命中、八组保护内容、版本与图片哈希、全局重绘日志，以及：

```json
{
  "ablation_id": "no-consumer",
  "ablation_base_version": "3.1.0-rc.3",
  "consumer_agent_present": false,
  "consumer_artifacts_used": false
}
```

## 禁止事项

- 不调用、导入、读取或模拟消费者 Agent。
- 不保留消费者模块作为隐藏回退。
- 不把美学 Pass 描述成消费者有效性已验证。
- 不与 rc.3 正式对照组共用结果目录、缓存、历史候选或报告。
- 不让美学 Agent 或最终质量仲裁直接生成图片。
- 不把本消融版发布为稳定版。
