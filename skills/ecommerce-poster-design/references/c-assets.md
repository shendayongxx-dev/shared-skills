# C 分类资产读取规则

> **当前状态：正式 C 库未接入。** 仓库内只有 `C-DEMO-*` 演示资产。任何成员都不得将 demo 资产改名为正式资产、删除 `demo_only` 标记，或据此宣称完成 C 接入。

## 资产位置

默认读取 `assets/classification/`：

- `taxonomy.json`：标签总表；
- `rules.json`：标签组合到视觉规则；
- `case-index.csv`：案例索引；
- `cases/*.json`：案例元数据；
- `cases/*`：可选种子案例图。

正式 C 库到达后替换这些资产，不修改 `SKILL.md`、输入输出字段或主流程顺序。接入完成前必须保持 `assets/config/version.json` 中 `c_library.status=not_connected`。

## 正式接入完成条件

只有同时满足以下条件，才可以把 `c_library.status` 改为 `connected`：

1. C 组交付的 `taxonomy.json`、`rules.json`、`case-index.csv` 和案例文件均已落位；
2. `validate_classification.py` 返回 `valid=true` 且无错误；
3. 至少完成一个 exact 或 two_dimension 命中的回归用例；
4. 更新版本号、变更记录和 `PROJECT_STATUS.md`；
5. 经项目负责人审核合并。

## 引用规则

- taxonomy 的 `id` 是唯一程序关联键；中文 `name` 仅用于展示。
- rules 和 case index 中的标签 ID 必须存在于 taxonomy。
- 规则和案例不得使用未经登记的 ID。
- 标签改名不得改变 ID；废弃标签标记为 `deprecated`。

## 匹配

仅使用 `status=active` 的标签和规则。

1. 三维完全相同为 `exact`；
2. 两维相同、一维为 `*` 为 `two_dimension`；
3. 一维相同、两维为 `*` 为 `single_dimension`；
4. 全部为 `*` 的 `R-DEFAULT` 为 `global`。

同层级按 `priority` 从高到低选择。不得因为不存在精确组合而编造规则。

## 资产失败默认风格

若文件不存在、JSON/CSV 无法解析、Schema 不兼容、引用失效或没有默认规则，使用：

- 白色或浅中性背景；
- 深色高对比文字；
- 商品居中，占画面约 55%；
- 信息密度 3；
- 促销强度 3；
- 层级顺序：商品 → 商品名/核心卖点 → 价格促销 → CTA；
- 禁止低对比文字、遮挡商品、捏造促销和装饰性假 Logo。

此时 `fallback_level=asset_failure_default`，必须记录 warning 和失败原因。

## Demo 资产限制

当前随 Skill 提供的 `C-DEMO-*` 为管道演示数据，不是市场验证案例，不得在报告中作为真实调研证据。正式联调时由 C 组真实资产替换。
