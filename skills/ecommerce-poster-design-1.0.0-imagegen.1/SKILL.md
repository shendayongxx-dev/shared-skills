---
name: ecommerce-poster-design
description: "根据商品图、商品信息、卖点、价格促销、营销目标和画布规格，调用 Codex ImageGen 生成或编辑电商商品营销主视觉，并执行可验证的硬性合规检查。用于电商海报、商品主图或营销主视觉生成；不用于普通艺术海报、非商品宣传、消费者评分或主观美学评分任务。"
---

# 电商商品营销主视觉设计 Skill 1.0（ImageGen）

> 当前独立版本为 `1.0.0-imagegen.1`。它在 1.0.0 基线上接入 Codex 系统 `imagegen` Skill 与内置 `image_gen` 工具。C 2.0.1 分类库保持不变；第三方种子原图不随 Skill 分发。

## 版本边界

这是 1.0 的消融 Baseline 正式实现。固定流程为：

`输入校验 → 人群/购买动机/场景识别 → C 库检索 → style_guide → 生成计划 → 海报生成或定向重画 → 硬性合规 → 输出`

Skill 1.0 ImageGen 版不包含、也不运行消费者 Agent、美学 Agent、LLM/VLM-as-a-Judge 或主观评分路由。ImageGen 只负责生成与编辑，不承担评分。硬性合规通过后立即输出；2.0/3.0 接口不在本版本执行。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，按输入契约检查必填信息并建立 `protected_content`。
2. 读取 `assets/config/version.json`；确认生成后端为 Codex 系统 `imagegen` Skill 与内置 `image_gen` 工具，两个 Agent 开关均为 `false`。
3. 读取 [references/c-assets.md](references/c-assets.md)，校验并检索外接分类资产。
4. 读取 [references/imagegen-integration.md](references/imagegen-integration.md)，按生成/编辑契约调用 ImageGen。
5. 生成完成后读取 [references/hard-compliance.md](references/hard-compliance.md)，逐项执行硬性检查。

## 必填输入

- 商品图；
- 商品名称或品类；
- 已确认的卖点；
- 价格及促销信息；
- 营销目标；
- 画布宽高和输出格式。

缺少必填信息时，返回缺失字段列表并停止生成。不得猜造价格、折扣、商品数量、活动时间、Logo、法务文案或商品特征。

## 执行流程

### 1 输入校验与保护内容

把商品主体、Logo、商品名称、价格、折扣、活动时间、关键卖点、行动提示和法务文案写入 `protected_content`。重画只能调整未保护的视觉表达；不得缩写、替换、删除或改变保护内容的含义。

### 2 校验 C 库

优先运行：

```text
python scripts/validate_classification.py assets/classification
```

若运行环境不能执行脚本，按 [references/c-assets.md](references/c-assets.md) 中的同等规则人工校验。`valid=true` 仅表示可联调，只有 `production_ready=true` 才具备正式接入条件。C 库损坏、缺文件或版本不兼容时，不中断主流程；使用文档中的全局默认风格，同时记录 `warning`、失败文件和回退原因。

### 3 分类与检索

仅根据已提供信息判断 `audience_id`、`motivation_id` 和 `scenario_id`，并保存判断依据与置信度。证据不足的维度必须为 null，不得用常识或默认类别补位，也不得生成 taxonomy 中不存在的标签。

规则检索顺序固定为：精确三维 → 二维通配 → 单维通配 → `R-DEFAULT`。未知维度只允许匹配 `*`；同层级选择 `priority` 最大的 active 规则。按 C 资产契约编译继承并选择一个完整色板，案例必须通过审核、权利和种子门禁。将命中的规则和案例组装成结构化 `style_guide`；生成模块只能消费 `style_guide`，不能绕过契约直接猜测 C 库含义。

完成标签识别后，优先运行以下确定性选择器；将三个 ID 替换为本次识别结果：

```text
python scripts/select_style.py assets/classification P01 M01 S01 --request-id REQ-001
```

缺少某维证据时用 `null` 传入，例如：

```text
python scripts/select_style.py assets/classification null M04 S04 --request-id REQ-002
```

### 4 生成计划

在生成前明确商品层、品牌层、文字层、背景层和布局层。计划至少包含：

- 商品和 Logo 的位置、大小及禁止变更项；
- 标题、卖点、价格、促销和行动提示的层级；
- 配色、字体方向、构图和商品占比；
- 参考规则与案例 ID；
- 画布规格和输出格式。

### 5 ImageGen 生成与硬性合规

默认调用 Codex 系统 `imagegen` Skill，并使用内置 `image_gen` 工具制作海报。具体输入映射、参考图角色、提示词约束、保存策略和失败处理遵循 [references/imagegen-integration.md](references/imagegen-integration.md)。只有内置工具不可用或持续失败时，才说明回退条件；未经用户明确确认，不切换到需要 API Key 的 CLI 路径。

本地商品图或待编辑图必须先通过可用的图片查看能力载入上下文。新建海报时不传历史生成图；编辑现有海报时只传本次需要编辑的目标图和必要参考图。提示词必须消费已编译的 `style_guide`，逐字携带 `protected_content`，并明确每张参考图的角色。

生成器返回的尺寸若与请求只有近似比例但像素不一致，先保留原始结果，再用确定性高质量重采样得到精确画布；硬性合规检查以最终交付文件为准。`logo_ref` 为空时不得从包装商标推导或绘制独立 Logo；多组件商品必须明确商品数量和包装组件数量。

生成后按硬性检查清单逐项输出 `pass/fail`、证据、问题位置和修复建议。

硬性检查失败时，携带 `problem_list` 和原始 `protected_content` 返回生成步骤进行定向重画。任何重画结果都必须重新执行完整硬性检查，不得直接输出。

局部编辑超时、返回空结果或图片不可读时，记录工具错误，并在同一目标轮次进行受保护内容等价重生成。工具失败本身不产生候选、不消耗重画次数；成功得到的新候选只计一次。

### 6 有界重试与结束

默认最多生成 1 个首版并按 `assets/config/version.json` 的上限重画 3 次。每轮保存结构化日志。

- 检查通过：立即输出；
- 达到重画上限仍未通过：停止，选择硬性问题最少且严重度最低的候选，输出该候选、未解决问题、明确 warning 和全部轮次日志；
- 不得把失败候选描述为完全通过。

## 输出

最终输出必须包含：

- 海报文件或可访问的生成结果；
- ImageGen 调用模式（生成或编辑）、输入图片角色和最终交付文件路径；
- 硬性合规报告；
- 分类标签、规则 ID、案例 ID 和回退层级；
- `protected_content`；
- warning 列表；
- Skill、Schema 和资产版本；
- 每轮生成配置、检查结果和修改记录。

## 禁止事项

- 不把“美观”作为硬性合规依据；
- 不用主观高分覆盖价格、Logo、商品保真或文字准确性失败；
- 不把 C 库内容整段写回本文件；
- 不包含或调用消费者 Agent、美学 Agent 或 2.0/3.0 评分路由；
- 不把 ImageGen 当作事实来源或评分器；
- 不声称复现论文或商业平台的内部模型；
- 不进行无限重试。
