# ImageGen 集成契约

## 依赖边界

整体 `ecommerce-poster-design` Skill 依赖 Codex 系统级 `imagegen` Skill 和内置 `image_gen` 工具。该能力属于主流程的生成层，不属于 `modules/consumer-agent`。消费者 Agent 只能评价候选并返回路由，不得调用生图工具。不要把系统 Skill 的 `SKILL.md`、脚本或参考资料复制进本目录；系统能力由 Codex 维护，本文件只定义电商海报工作流与它的接口约束。

## 调用规则

1. 使用内置 `image_gen` 作为默认生成与编辑路径，不要求用户提供 `OPENAI_API_KEY`。
2. 新建海报时按生成任务调用；美学返图必须按编辑任务调用，并使用最后消费者通过版作为唯一编辑目标。
3. 本地商品图或待编辑图必须先通过可用的图片查看能力载入上下文，再作为 ImageGen 输入；明确标注每张图是“编辑目标”“商品参考”还是“风格参考”。
4. 每次调用只执行一个明确候选或一次定向修改。多候选需要分别调用并分别记录，不能把不同海报需求塞进同一提示词。
5. 生成提示词必须消费本 Skill 已编译的 `style_guide`，并原样携带 `protected_content`。不得绕过分类契约自行补造价格、折扣、活动时间、Logo、认证或商品卖点。
6. 美学返图调用前必须用 `scripts/validate_generation_edit_contract.py` 验证路由结果。缺少合同、合同跨版本、五个消费者锁不完整或编辑维度与锁定维度重叠时停止，不调用 ImageGen。
7. `generation_mode=local_edit_only` 时优先使用蒙版或分层编辑。不能可靠限制编辑范围时返回 `blocked`，不得降级为无约束整图重生成。

## SVG Logo 预处理与应用

ImageGen 的本地参考输入按可读的位图处理，不把 SVG 直接可读或可精确复现视为稳定能力。`brand.logo_ref` 为 SVG 时执行以下固定链路：

1. 保留 SVG 为权威品牌源，不覆盖、不改写；先运行安全预检，拒绝脚本、事件属性、外部资源、`foreignObject` 和无有效尺寸/viewBox 的文件。
2. 使用工作区提供的 Node 与 Sharp 运行 `scripts/prepare_logo_asset.mjs`，默认把长边栅格化为 2048px；大幅画布或较大 Logo 可提高到 4096px，但不得低于 Logo 最终展示宽度的 2 倍。
3. 清单必须绑定 SVG 与 PNG 的绝对路径、SHA-256、宽高、纵横比、Alpha 状态、渲染器版本，以及 `crop=false / recolor=false / rotation=0`。
4. 首次 ImageGen 提示词不得要求模型重画 Logo；应在布局中预留干净、安全、无遮挡的 Logo 区域，并禁止额外品牌文字或假 Logo。
5. 底图归一化到目标画布后，用 `scripts/apply_logo_asset.mjs` 按明确 `left/top/width` 做确定性合成。坐标来自本轮布局计划；脚本保持纵横比并在越界时失败。
6. 只有合成后的最终候选进入 HC-01～HC-12、消费者、美学和最终质量门。底图不算独立候选，也不单独消耗重画次数。

示例：

```text
node scripts/prepare_logo_asset.mjs \
  --input <logo.svg> --output <logo.prepared.png> \
  --manifest <logo.preflight.json> --long-edge 2048 \
  --sharp-module <workspace-node-modules>/sharp

node scripts/apply_logo_asset.mjs \
  --poster <normalized-base.png> --logo <logo.prepared.png> \
  --output <candidate.png> --manifest <logo.application.json> \
  --left <x> --top <y> --width <pixels> \
  --sharp-module <workspace-node-modules>/sharp
```

若运行环境没有 Sharp，允许使用能产生等价清单且保持比例/颜色/透明度的受控 SVG 渲染器；不得把网页截图、模型重绘或未知在线转换站当作等价替代。无法安全转换时返回 `blocked`。

## 提示词映射

将生成计划整理为以下结构；没有依据的字段省略，不做猜测：

```text
Use case: ads-marketing
Asset type: ecommerce poster
Primary request: <本轮生成或定向修改目标>
Input images: <逐张编号及角色；确定性后贴 Logo 不作为 ImageGen 重绘参考>
Scene/backdrop: <由 style_guide 和营销场景得出>
Subject: <商品主体、数量、包装组件>
Style/medium: <视觉风格>
Composition/framing: <布局、商品占比、文案留白>
Lighting/mood: <光线与情绪>
Color palette: <完整选中色板>
Text (verbatim): <所有必须原样出现的文案>
Constraints: <protected_content、画布、保真要求>
Edit contract: <baseline_candidate、editable_aesthetic_dimensions、locked_aesthetic_dimensions、locked_consumer_dimensions>
Avoid: <禁用内容、额外 Logo、任何模型重画品牌标志或品牌文字、虚构信息、水印>
```

编辑轮次必须重复列出不变量：只修改 `generation_edit_contract.editable_aesthetic_dimensions` 授权的区域；商品外观、包装文字、Logo、价格、其他 `protected_content`、五个消费者功能和已达标美学维度保持不变。`modify_suggestion` 与合同冲突时以合同为准。

编辑完成后必须把最后消费者通过结果作为 `previous_result` 复评。出现任何 `regressed_dimensions` 时淘汰返图、恢复合同中的 `baseline_candidate`，不得将返图继续送入美学评价。

## 输出与落盘

- 预览候选可以先以内联结果检查；最终交付图必须复制或移动到当前任务的可写工作区，并记录绝对路径。
- 不覆盖用户原图或既有资产，除非用户明确要求；默认使用带版本号的新文件名。
- ImageGen 返回尺寸与目标像素不一致时，先保存原始结果，再按主 Skill 规则进行确定性高质量重采样；合规检查针对最终交付文件执行。

## 失败与回退

- 内置 `image_gen` 超时、空结果或图片不可读时，记录工具错误；工具失败不算有效候选，也不消耗重画次数。
- 可以在同一目标轮次重新调用内置工具，并保持全部保护内容和不变量。
- 内置工具持续不可用时，向用户说明 CLI/API 回退需要 `OPENAI_API_KEY`；只有用户明确同意后才能采用该路径。
