# ImageGen 集成契约

## 依赖边界

本 Skill 依赖 Codex 系统级 `imagegen` Skill 和内置 `image_gen` 工具。不要把系统 Skill 的 `SKILL.md`、脚本或参考资料复制进本目录；系统能力由 Codex 维护，本文件只定义电商海报工作流与它的接口约束。

## 调用规则

1. 使用内置 `image_gen` 作为默认生成与编辑路径，不要求用户提供 `OPENAI_API_KEY`。
2. 新建海报时按生成任务调用；保留商品主体、包装、Logo 或既有版式并局部修改时按编辑任务调用。
3. 本地商品图或待编辑图必须先通过可用的图片查看能力载入上下文，再作为 ImageGen 输入；明确标注每张图是“编辑目标”“商品参考”还是“风格参考”。
4. 每次调用只执行一个明确候选或一次定向修改。多候选需要分别调用并分别记录，不能把不同海报需求塞进同一提示词。
5. 生成提示词必须消费本 Skill 已编译的 `style_guide`，并原样携带 `protected_content`。不得绕过分类契约自行补造价格、折扣、活动时间、Logo、认证或商品卖点。

## 提示词映射

将生成计划整理为以下结构；没有依据的字段省略，不做猜测：

```text
Use case: ads-marketing
Asset type: ecommerce poster
Primary request: <本轮生成或定向修改目标>
Input images: <逐张编号及角色>
Scene/backdrop: <由 style_guide 和营销场景得出>
Subject: <商品主体、数量、包装组件>
Style/medium: <视觉风格>
Composition/framing: <布局、商品占比、文案留白>
Lighting/mood: <光线与情绪>
Color palette: <完整选中色板>
Text (verbatim): <所有必须原样出现的文案>
Constraints: <protected_content、画布、保真要求>
Avoid: <禁用内容、额外 Logo、虚构信息、水印>
```

编辑轮次必须重复列出不变量：只修改 `problem_list` 指定区域；商品外观、包装文字、Logo、价格及其他 `protected_content` 保持不变。

## 输出与落盘

- 预览候选可以先以内联结果检查；最终交付图必须复制或移动到当前任务的可写工作区，并记录绝对路径。
- 不覆盖用户原图或既有资产，除非用户明确要求；默认使用带版本号的新文件名。
- ImageGen 返回尺寸与目标像素不一致时，先保存原始结果，再按主 Skill 规则进行确定性高质量重采样；合规检查针对最终交付文件执行。

## 失败与回退

- 内置 `image_gen` 超时、空结果或图片不可读时，记录工具错误；工具失败不算有效候选，也不消耗重画次数。
- 可以在同一目标轮次重新调用内置工具，并保持全部保护内容和不变量。
- 内置工具持续不可用时，向用户说明 CLI/API 回退需要 `OPENAI_API_KEY`；只有用户明确同意后才能采用该路径。
