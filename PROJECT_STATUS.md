# 项目状态

## 当前发布

- 版本：`0.9.0-alpha.2`
- 发布通道：`pre-release`
- 定位：Skill 1.0 的前置可运行基线
- 最终 1.0：否
- 生产稳定版：否
- C 正式库：未接入
- 当前分类资产：`demo_only`

## 当前已经确定

- 输入校验、分类匹配、style guide、生成、硬性合规、有限重画、结构化输出的主流程顺序。
- 输入、`protected_content`、`style_guide`、硬检查报告、运行日志和结果文件的字段职责。
- C 库的固定接入目录：`skill/zh/ecommerce-poster-design/assets/classification/`。
- 分类的四级回退规则和最多 3 次定向重画。
- C 候选包的嵌套 case index、规则继承、成组色板、部分 null 路由和案例审批门禁适配。
- 1.0 不启用消费者 Agent、美学 Agent或主观评分路由。

## 当前尚未完成

- C 组正式 taxonomy、rules、case index 和案例资产接入。
- C 源 schema 2.0 冻结，以及 draft 种子标记、严格空值测试和继承金标准修订。
- 基于 C 正式库的 exact / two_dimension 回归验证。
- 最终 1.0 的版本冻结与发布确认。

## 不得误判

- 通过现有冒烟测试不等于 C 正式库已经接入。
- 外部候选包返回 `valid=true` 只表示可联调；`production_ready=false` 时不得落为正式资产。
- `C-DEMO-*` 不是真实市场证据，不得用于业务结论。
- 未满足 `references/c-assets.md` 的正式接入完成条件前，不得改成最终 `1.0.0`。
