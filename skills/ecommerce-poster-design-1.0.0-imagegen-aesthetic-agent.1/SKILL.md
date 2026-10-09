---
name: ecommerce-poster-design
description: "以正式 ecommerce-poster-design 1.0.0-imagegen.1 为冻结 baseline，保留其内置 C 库、ImageGen 生成层和硬性合规流程，仅追加固定版本的美学 Agent 做六维评价与改图反馈。用于 1.0 ImageGen 的 +Aesthetic Agent 单变量对照实验；不运行消费者 Agent，也不把美学分数当作硬性合规结果。"
---

# 电商商品营销主视觉设计 Skill 1.0 ImageGen + Aesthetic Agent

> 独立部署版本为 `1.0.0-imagegen-aesthetic-agent.1`。唯一 baseline 是 GitHub 标签 `ecommerce-poster-design-v1.0.0-imagegen.1`（提交 `fdd3b20d74c170460f79465a241cffee012e6652`）。C 2.0.1 分类库和 ImageGen 已属于该 baseline；本版本只追加美学 Agent，1.0 主流程、硬性检查和重画预算保持不变。

## 版本边界

这是在冻结的 `1.0.0-imagegen.1` 上只追加 Aesthetic Agent 的独立实验组实现。它是 `+Aesthetic Agent` 组；不应称为“美学消融版”，因为美学模块并未被移除。固定流程为：

`输入校验 → 人群/购买动机/场景识别 → C 库检索 → style_guide → 生成计划 → ImageGen 生成或定向编辑 → 1.0 硬性合规 → 美学评价 → 输出或在剩余 1.0 预算内再次调用 ImageGen`

1.0 仍是唯一调度器和轮次所有者；ImageGen 只生成/编辑图片；美学 Agent 只负责六维视觉评价、修改建议和美学 `score/pass`。消费者 Agent 始终关闭。美学 Agent 不直接调用生成工具、不拥有独立 8 轮循环，也不改变 1.0 的 `passed/degraded/blocked` 语义。整体实验结果另记为 `experiment_result.pass = baseline_hard_pass && aesthetic_pass`。先阅读 [ImageGen 集成契约](references/imagegen-integration.md) 和 [Aesthetic Agent 实验集成契约](references/aesthetic-agent-experiment.md)。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，按输入契约检查必填信息并建立 `protected_content`。
2. 读取 `assets/config/version.json`；本实验必须保持 `consumer_agent=false`、`aesthetic_agent=true`、`generation_backend.skill=imagegen`，并保持 `max_redraw_attempts=3`。
3. 读取 [references/c-assets.md](references/c-assets.md)，校验并检索外接分类资产。
4. 读取 [references/imagegen-integration.md](references/imagegen-integration.md)，按生成/编辑契约调用系统 ImageGen。
5. 生成完成后读取 [references/hard-compliance.md](references/hard-compliance.md)，逐项执行硬性检查。
6. 只有当前候选完成硬性检查后，才按 [Aesthetic Agent 实验集成契约](references/aesthetic-agent-experiment.md) 准备固定输入并执行美学评价。

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

默认使用 Codex 系统 `imagegen` Skill 的内置 `image_gen` 工具制作海报。新建海报使用生成模式；需要保留当前候选的大部分内容并修复指定问题时使用编辑模式。每张本地商品图或编辑目标必须先实际查看，再按 [ImageGen 集成契约](references/imagegen-integration.md) 标注为编辑目标、商品参考或风格参考。

提示词必须消费已编译的 `style_guide`，逐字携带 `protected_content`，并明确画布、商品数量、每张输入图的角色和禁止事项。内置工具生成后，将项目使用的候选保存到当前任务工作区，使用带轮次的非覆盖文件名，并记录调用模式、最终提示词和文件路径。

生成后按硬性检查清单逐项输出 `pass/fail`、证据、问题位置和修复建议。ImageGen 不是事实来源，也不承担硬检或美学评分。

硬性检查失败时，携带 `problem_list` 和原始 `protected_content` 返回生成步骤进行定向重画。任何重画结果都必须重新执行完整硬性检查，不得直接输出。

内置工具超时、空结果或图片不可读时记录工具错误；失败调用不产生候选，也不消耗重画次数。内置工具持续不可用时，只能说明 CLI/API 回退需要 `OPENAI_API_KEY`，用户明确同意前不得切换。

### 6 美学评价与适配

硬性检查通过后，运行 `scripts/aesthetic_adapter.py prepare`。字段来源固定如下：

- `poster_image`：本轮当前候选，不得使用上一轮路径；
- `product_img`：baseline `product.image_refs` 中明确选定的原商品图；多图时必须显式选择，不得静默取第一张；
- `selling_points`：baseline `product.selling_points` 原文；
- `price_text`：baseline `commerce.price_text` 原文；
- `marketing_target`：baseline `marketing.goal` 原文；
- `scene_tags`：本轮 `style_guide.tags` 中非空的 audience、motivation、scenario ID；全为空时不猜标签，美学评价记为不可用。

用支持看图的模型实际查看候选海报、原商品图和可用参考图，按 vendored Agent 的 `agent-prompt.md` 与 review schema 形成内部 review，再运行其 `scripts/evaluate.mjs`。必须使用 `standalone` context；不得为了满足上游 `integrated` 门禁而引入消费者 Agent。baseline 的 `protected_content` sidecar 必须一并提供给评价和后续改图。

美学未通过时，仅把 `modify_suggestion` 和内部 redesign prompt 作为下一次 1.0 调用 ImageGen 的附加视觉要求。ImageGen 仍由 1.0 主流程调用；美学 Agent 不直接拥有生成权限。新图必须从 HC-01 重新执行全部硬性检查。美学高分不能覆盖任何硬检失败。

### 7 有界重试与结束

默认最多生成 1 个首版并按 `assets/config/version.json` 的上限重画 3 次。每轮保存结构化日志。

- 硬性检查和美学评价均通过：立即输出，`experiment_result.pass=true`；
- 硬性检查通过但美学未通过且仍有预算：按美学建议定向重画；
- 达到重画上限：停止。任何硬检未通过时仍按 1.0 规则选择硬性问题最少且严重度最低的候选；存在硬检通过的候选时，只在这些候选中选择有效美学分最高者。输出 baseline 状态、美学结果、`experiment_result.pass=false`、未解决问题、warning 和全部轮次日志；
- 不得把失败候选描述为完全通过。

美学 Agent 的 `default_generation_rounds=8` 在本实验组中禁用，不能与 1.0 的轮次嵌套或相加。若要测试 8 轮，应另建实验组。

## 输出

最终输出必须包含：

- 海报文件或可访问的生成结果；
- ImageGen 的生成/编辑模式、输入图片角色、最终提示词和工作区文件路径；
- 硬性合规报告；
- 原样保存的 `aesthetic_agent` 固定 JSON；
- 独立 `experiment_result`，明确本组为 `aesthetic_agent_added`、baseline hard pass、美学 pass、score 状态和消费者 Agent 未使用；
- 分类标签、规则 ID、案例 ID 和回退层级；
- `protected_content`；
- warning 列表；
- Skill、Schema 和资产版本；
- 每轮生成配置、检查结果和修改记录。

## 禁止事项

- 不把“美观”作为硬性合规依据；
- 不用主观高分覆盖价格、Logo、商品保真或文字准确性失败；
- 不把美学 `pass` 改名或映射成 baseline 的 `passed`；
- 不调用消费者 Agent，不伪造消费者通过记录；
- 不启动美学 Agent 自带的 8 轮循环；
- 不把 ImageGen 当作硬性检查器、美学评分器或商品事实来源；
- 不在未经用户确认时切换到需要 API Key 的 ImageGen CLI 路径；
- 不把 C 库内容整段写回本文件；
- 不调用其他 2.0/3.0 Agent；
- 不声称复现论文或商业平台的内部模型；
- 不进行无限重试。
