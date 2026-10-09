---
name: ecommerce-poster-design
description: "根据商品图、商品信息、卖点、价格促销、营销目标和画布规格，调用 Codex ImageGen 生成或编辑电商商品营销主视觉，依次执行硬性合规、目标消费者评价和六维美学评价，并进行受保护的有限迭代。用于电商海报、商品主图或营销主视觉生成；不用于普通艺术海报或非商品宣传。"
---

# 电商商品营销主视觉设计 Skill 3.0.0

> 当前版本为 `3.0.0`，从独立、未修改的 2.0.1 基线升级而来。在消费者 Agent 1.5.3、C 2.0.1 分类库和 A-D-2.0 接口之后接入美学 Agent v2.4。3.0 位于独立目录，不覆盖 2.0.1；第三方种子原图和美学参考图片不随 Skill 分发。

## 版本边界

这是 1.0 消融 Baseline 的兼容升级。固定流程为：

`输入校验 → 人群/购买动机/场景识别 → C 库检索 → style_guide → 生成计划 → 海报生成或定向重画 → 硬性合规 → 消费者 Agent → 美学 Agent → 输出或有限迭代`

消费者通过后不再直接完成：只有 `next_route=aesthetic_agent` 且当前候选的硬检查、消费者结果均真实通过，才进入美学评价。美学通过只代表视觉模块通过，不能覆盖上游内容错误。两类 Agent 的评分都是模型评价，不代替真人研究、盲评或硬性合规。

## 开始前

1. 读取 [references/contracts.md](references/contracts.md)，按输入契约检查必填信息并建立 `protected_content`。
2. 读取 `assets/config/version.json`；本集成必须保持 `consumer_agent=true`、`aesthetic_agent=true`。
3. 读取 [references/c-assets.md](references/c-assets.md)，校验并检索外接分类资产。
4. 读取 [references/imagegen-integration.md](references/imagegen-integration.md)，使用 Codex 系统 `imagegen` Skill 与内置 `image_gen` 工具执行生成或编辑。
5. 生成完成后读取 [references/hard-compliance.md](references/hard-compliance.md)，逐项执行硬性检查。
6. 硬性检查通过后读取 [references/consumer-agent-integration.md](references/consumer-agent-integration.md) 和 `modules/consumer-agent/SKILL.md`，按 A-D-2.0 合同评价。
7. 消费者通过后读取 [references/aesthetic-agent-integration.md](references/aesthetic-agent-integration.md) 和 `modules/aesthetic-agent/SKILL.md`，组装固定输入并执行六维美学评价。

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

### 5 生成与硬性合规

默认调用 Codex 系统 `imagegen` Skill，并使用内置 `image_gen` 工具制作海报；具体输入映射、参考图角色、提示词约束、保存策略和失败处理遵循 [references/imagegen-integration.md](references/imagegen-integration.md)。只有内置工具不可用或失败时，才说明回退条件；未经用户明确确认，不切换到需要 API Key 的 CLI 路径。生成后按硬性检查清单逐项输出 `pass/fail`、证据、问题位置和修复建议。

生成器返回的尺寸若与请求只有近似比例但像素不一致，先用确定性高质量重采样输出精确画布，再对该交付文件执行检查。`logo_ref` 为空时不得从包装商标推导或绘制独立 Logo；多组件商品必须在计划中明确“商品数量”和“包装组件数量”，避免套装歧义。

硬性检查失败时，携带 `problem_list` 和原始 `protected_content` 返回生成步骤进行定向重画。任何重画结果都必须重新执行完整硬性检查，不得直接输出。

局部编辑超时、返回空结果或图片不可读时，记录工具错误，并按 hard-compliance 的兜底协议在同一目标轮次进行受保护内容等价重生成。工具失败本身不产生候选、不消耗重画次数；成功得到的新候选只计一次。

### 6 消费者 Agent

只有完整硬性检查通过的候选才能进入消费者评价。使用 `modules/consumer-agent/scripts/assemble_input.py` 组装正式输入，并用其 `validate_input.py` 校验。消费者必须实际查看当前海报和相关商品参考图，先按 25 个子项生成内部草稿，再用 `score_evaluation.py` 确定性计算正式结果；不得让模型直接填写五维总分。

消费者 Agent 只负责读图评价、证据记录、评分和路由，不属于生成层，也不得直接调用 `imagegen` 或 `image_gen`。所有首版生成和定向重画均由整体 `ecommerce-poster-design` Skill 的第 5 步执行；消费者只返回问题与修改建议。

正式评分为五维各 20 分、总分 100。通过要求为总分至少 80、每维至少 14、无 `hard_fail`、无锁定维度回退。八组 `protected_content` 必须逐值原样返回。

- `pass=true` 且 `next_route=aesthetic_agent`：调用 `scripts/assemble_aesthetic_input.py`，保留同版本上游报告与八组保护内容后进入美学 Agent；
- `next_route=poster_generation_skill`：把最多 3 组 `problem_list` 与 `modify_suggestion` 作为本轮必改项，连同原样保护内容和锁定维度返回生成步骤；重画后从 HC-01 至 HC-12 全量复查，再重新评价；
- `next_route=complete_input`：停止自动重画，列出 `meta.input_errors`，状态标记为 `blocked`，补全或消解冲突后再继续；
- 任何消费者结果都不能覆盖硬性合规失败。

用 `scripts/route_consumer_result.py` 对正式结果执行确定性路由，传入当前全局累计重画次数。该脚本只解释路由，不修改消费者结果，也不替代读图评价。

### 7 美学 Agent

美学 Agent 只接收固定业务输入 `poster_image` 和 `product_input`。不得把消费者的内部字段直接塞入业务输入；用适配器把商品母图、卖点、价格、营销目标和 C 标签确定性映射，同时把同版本硬检查、消费者报告以及八组 `protected_content` 放入调度上下文。

视觉模型必须实际查看当前海报与原商品图；命中且本地真实存在的参考图也必须实际传入模型。先形成符合 `modules/aesthetic-agent/schemas/review.schema.json` 的内部观察，再由 `evaluate.mjs` 确定性计算六维加权分。通过要求同时满足：总分至少 8.5、六维各至少 8、内容保护检查通过、当前同版本硬检查和消费者评价通过。

正式完成不能只信任七字段对外结果中的 `pass=true`。路由时同时传入同次生成的 `assessment-internal.json` 和本轮 `aesthetic-input.json`，确定性核对候选图/商品图/版本绑定、未舍入总分、六维门槛、`below_threshold`、配置快照和 `overall_qualified`；缺少内部评估或误用其他候选报告时不得通过。

- 美学通过：输出当前候选；
- 美学未通过：用独立的 `redesign-plan.json` 和 `redesign-prompt.txt` 调用整体生成层，成功形成候选后从 HC-01 至 HC-12、消费者、美学完整重跑；
- `score=0/confidence=0`：表示图片或依据不足的未评价占位，状态为 `blocked`，不能参与最佳候选比较；
- 美学输出删改任一保护项：接口校验失败并停止，不得自动猜回。

用 `scripts/route_aesthetic_result.py` 执行确定性路由，传入美学生成轮次、有效分数历史和连续低提升计数。连续两轮相对历史最佳分提升均小于 0.2 时必须换设计方向并把停滞计数归零；达到 8 个美学生成轮次后停止，并保留历史最高分且内容合规的候选。

### 8 有界重试与结束

默认生成 1 个首版。进入美学阶段前，保留 2.0.1 基线的硬合规/消费者累计重画上限 3 次；消费者首次通过并进入美学阶段后，建立 3.0 独立的美学生成轮次，最多 8 轮。美学触发的新候选必须重新经过硬检查和消费者评价；此时消费者路由使用 `phase=aesthetic_recheck`，按美学轮次继续或停止，不回退到前置 3 次计数。工具失败且未形成候选不计数。每轮保存结构化日志、三段检查结果、美学分项依据及候选路径。

- 硬性检查、消费者评价与美学评价均通过：输出 `passed`；
- 达到上限仍未通过：停止；优先返回同时通过硬检查和消费者评价、且美学分最高的候选。若没有这类候选，再按消费者分数和 1.0 硬性问题排序回退；输出 `degraded`、未解决问题、明确 warning 和全部轮次日志；
- 任一 Agent 输入或图像不可评价：输出 `blocked`，不得用重画掩盖输入错误；
- 不得把失败候选描述为完全通过。

## 输出

最终输出必须包含：

- 海报文件或可访问的生成结果；
- 硬性合规报告；
- 消费者 Agent 正式结果、五维证据和内部评分明细引用；
- 美学 Agent 固定结果、六维内部评分引用、参考匹配结果与重设计方案；
- 分类标签、规则 ID、案例 ID 和回退层级；
- `protected_content`；
- `locked_dimensions`、`regressed_dimensions` 和消费者模块版本；
- warning 列表；
- Skill、Schema 和资产版本；
- 每轮生成配置、检查结果和修改记录。

## 禁止事项

- 不把“美观”作为硬性合规依据；
- 不用主观高分覆盖价格、Logo、商品保真或文字准确性失败；
- 不把 C 库内容整段写回本文件；
- 不绕过硬检查或消费者 Agent 直接调用集成流程中的美学 Agent；
- 不把缺失的参考图路径描述为已实际看图；
- 不把消费者 Agent 的修改建议当作事实来源，不新增卖点、价格、促销或认证；
- 不使用旧版 0–10 分或七字段简化接口替代 A-D-2.0 正式合同；
- 不声称复现论文或商业平台的内部模型；
- 不进行无限重试。
