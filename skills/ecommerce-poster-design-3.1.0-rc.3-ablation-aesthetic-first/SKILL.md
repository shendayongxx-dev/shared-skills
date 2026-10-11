---
name: ecommerce-poster-design-aesthetic-first-ablation
description: "基于 ecommerce-poster-design 3.1.0-rc.3 的顺序消融实验版：调用 Codex ImageGen 生成或编辑电商商品营销主视觉，保持原分类、生成、硬合规、量表、阈值、最终质量门和统一预算不变，仅把评价链调整为先专业美学、后消费者有效性，并执行对称回归保护。用于电商海报 Agent 顺序消融实验；不用于普通艺术海报或独立审美打分。"
---

# 电商商品营销主视觉设计 Skill 3.1.0-rc.3：美学优先消融版

> 实验版本 `3.1.0-rc.3-ablation-aesthetic-first`。基线为 `3.1.0-rc.3`；不得回写、覆盖或冒充稳定版。本实验只改变美学 Agent 与消费者 Agent 的先后关系，以及由该顺序必然引起的锁定、返图和路由适配。

## 实验边界

固定流程为：

`输入校验 → P-M-S 分类与 C 库检索 → style_guide → 生成 → HC-01～HC-12 → 美学 Agent → 消费者 Agent → 最终质量仲裁 → 最终验收或统一预算内迭代`

- 保持 rc.3 的输入、C 2.0.1 分类库、ImageGen 接入、Logo 管线、HC-01～HC-12、美学 3.0.0-rc.4 量表、消费者 1.5.3 量表、通过阈值、最终质量门和 8 次全局预算不变。
- 美学只在硬合规通过后评价，不依赖尚未产生的消费者分数或消费者锁。
- 美学通过后锁定六个美学维度，再进入消费者评价。
- 消费者通过后才进入最终质量仲裁；A-D-2.0 的 `next_route=aesthetic_agent` 在本实验中是接口兼容值，主流程解释为“消费者通过，进入最终质量门”，不得再次调用美学形成循环。
- 任一返图均生成新 `version_id`，旧候选的硬合规、美学和消费者结果立即失效，并从 HC-01 开始按美学→消费者顺序复检。
- 两个 Agent 都只评价与提出建议；只有主 Skill 可以调用 `imagegen` / `image_gen`。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，校验输入并建立八组 `protected_content`。
2. 读取 `assets/config/version.json`，确认 `evaluation_order=["aesthetic_agent","consumer_agent"]`、两模块启用且预算仍为全局 8 次。
3. 读取 [references/aesthetic-first-ablation.md](references/aesthetic-first-ablation.md)，遵守顺序适配、锁与回归规则。
4. 读取 [references/c-assets.md](references/c-assets.md)、[references/imagegen-integration.md](references/imagegen-integration.md) 和 [references/hard-compliance.md](references/hard-compliance.md)。
5. 最终质量仲裁继续使用 [references/final-quality-gate.md](references/final-quality-gate.md)，不得改变缺陷阈值或 rc.3 的 `TEXT_OVERLAP`、`LOGO_FLOATING` 强制路由。

## 必填输入与生成

必填商品图、商品名称或品类、已确认卖点、价格及促销、营销目标、画布宽高和输出格式。缺失时返回字段并停止；不得猜造价格、折扣、数量、活动时间、Logo、法务文案或商品特征。

生成、SVG Logo 安全预检、2048px 透明栅格化、预留安全区和确定性贴放完全沿用 rc.3。每张最终合成图才算候选。工具失败、空结果或不可读结果不形成候选，也不增加重画次数。

## 1. 硬性合规

每张候选先执行 HC-01～HC-12。失败则按可定位事实问题定向返图；新候选仍从 HC-01 开始。主观审美或消费者分数不能覆盖硬失败。

## 2. 美学 Agent（第一评价门）

运行 `scripts/assemble_aesthetic_input.py --candidate ...`，组装 `A-D-AESTHETIC-3.0-AF`。输入只含当前 A-D-2.0 候选，不伪造消费者结果。

美学模型必须查看原尺寸海报、360px 缩图、商品素材和任务要求，提交同 rc.3 的 25 个子项观察；确定性脚本计算六维与总分。阈值保持：总分≥80，且构图≥16、层级≥16、配色≥12、排版≥16、风格场景≥12、材质细节≥8，无关键问题。

- `score=null`：补齐评价输入，返回 `blocked`；不生成、不计数。
- `pass=false`：只开放未达标美学维度；冻结已达标美学维度和八组保护内容。由于消费者尚未评价，不得伪造五个消费者锁。
- `pass=true`：保存正式结果、六维明细、证据和 `aesthetic_context_hash`，锁定六个美学维度并进入消费者 Agent。

美学失败返图使用 `aesthetic-edit-lock/1.1-af`：以当前候选为底图，默认 `local_edit_only`，只编辑未达标美学维度。返图后重新跑硬合规和完整美学评价；美学通过前不得调用消费者。

## 3. 消费者 Agent（第二评价门）

只有当前同一 `request_id`、`version_id`、图片哈希和八组保护对象的美学结果正式通过，才组装消费者输入。消费者仍按 A-D-2.0 提交 25 项观察，由确定性脚本计算总分与五维。阈值不变：总分≥80、五维各≥14、`hard_fail=false`、无回归。

- `next_route=complete_input`：返回 `blocked`，补齐输入，不以重画掩盖缺失。
- 未通过且存在可定位消费者缺陷：建立 `consumer-edit-lock/1.0-af`，只开放与失败消费者维度直接对应的区域或关系，冻结八组保护对象和当前已通过的六个美学维度。
- 通过且五维全锁：把接口值 `next_route=aesthetic_agent` 解释为 `invoke_final_quality_gate`；不得再次调用美学。

消费者返图后，旧美学 Pass 不可沿用。新候选从 HC-01 开始，重新运行美学；把最后美学通过结果作为回归基线。若任一已锁美学维度降到门槛以下、出现新关键问题，或保护对象变化，立即淘汰返图并恢复最后美学通过候选。门槛以上的下降写入日志，但不自动判回归；最终质量门仍可依据可见缺陷退回。

## 4. 最终质量仲裁

只有当前同一候选依次通过硬合规、美学和消费者，才执行 `FINAL-QUALITY-3.1`。仲裁仍无第三套分数，核对两类证据与画面是否一致，并扫描 rc.3 的全部可定位缺陷。

- 证据矛盾、模板化或缺定位：重评同一候选，不生成、不计数。
- 可疑高分：对同一候选执行一次反向复核。
- 存在 critical、severe、moderate，或 minor 超过 2 个：生成 `final-quality-edit-lock/1.0` 并局部返图。
- `TEXT_OVERLAP` 与 `LOGO_FLOATING` 仍至少为 moderate，并执行 1～2 次局部修复尝试。
- 每张最终质量返图仍从 HC-01→美学→消费者→最终质量门完整复检。

最终质量编辑合同必须同时冻结八组保护对象、当前六个美学锁和五个消费者锁；若修复目标与任一锁冲突，缩小编辑范围或返回 `blocked`，不得静默解除锁。

## 5. 统一预算与候选选择

首版不计入重画。硬合规、美学、消费者和最终质量门导致的成功返图共用 rc.3 的全局 8 次预算；切换 Agent、语言、维度或方向不得重置。

- 同一候选完整通过四道检查：`passed`。
- 预算耗尽：仅在硬合规、美学和消费者均通过的候选中，按最终质量缺陷更少、严重度更低优先；仍并列时选择消费者分更高者，再选择美学分更高者。输出 `degraded`、遗留问题和完整日志。
- 没有同时通过两个 Agent 的候选时，不得用单门高分冒充通过；返回 `degraded` 或 `blocked` 并明确缺失门禁。

## 输出

输出海报、硬合规报告、美学结果及六维/25项审计、消费者结果及五维/25项审计、最终质量结果、P-M-S 与资产引用、八组保护对象、六个美学锁、五个消费者锁、Skill/Schema/模块版本、每轮顺序、版本与图片哈希、全局次数、修改合同以及 `passed|degraded|blocked`。

## 禁止事项

- 不在硬合规失败时调用任一评价 Agent。
- 不在美学未通过时调用消费者 Agent。
- 不把消费者的兼容路由值再次解释为调用美学。
- 不为首轮美学伪造消费者结果、消费者分数或消费者锁。
- 不沿用返图前的任何 Pass；新候选必须全链复检。
- 不让 Agent 直接生成图片，不改变量表、阈值、全局预算或最终质量规则。
- 不把本实验版登记为 stable 或覆盖 rc.3。
