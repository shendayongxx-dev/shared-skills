# C 分类资产读取与生产接入规则

> **当前状态：C 2.0.1 已接入。** 正式资产位于 `assets/classification/`；6 个内部参考种子覆盖 S01–S06。第三方图片二进制不进入公开仓库，运行时使用来源 URL，并用固定 SHA-256 校验内容。

## A 组接口裁定

1. A 的 style guide schema 继续保持 `1.0`，C 源资产 schema 单独记录为 `source_schema_version`。
2. C 源 schema 已冻结为 `2.0.0`，规则版本为 `2.0.1`；旧 demo 和 rc 格式只保留兼容能力，不作为当前生产资产。
3. `taxonomy_version=1.0` 可继续保持，因为标签 ID 集合没有因接口升级而改号。
4. A 同时兼容旧 demo 的根目录 `case-index.csv` 和候选包的 `cases/case-index.csv`；正式 C 2.0 固定使用后者。
5. A 负责规则编译、案例门禁、动态信息层级和安全回退；C 负责 taxonomy、规则源数据、案例元数据、来源权利和测试证据。

## 资产位置

默认读取 `assets/classification/`。正式 C 2.0 目录为：

- `taxonomy.json`：标签总表；
- `rules.json`：标签组合到视觉规则；
- `cases/case-index.csv`：案例索引；
- `cases/metadata/*.json`：案例元数据；
- `cases/assets/`：可选本地案例图；当前第三方参考种子不在公开仓库保存原图；
- `authorization/`：内部参考使用批准记录；
- `manifest.json`：文件大小与 SHA-256 清单。

候选包可在外部目录运行校验器和选择器；通过前不得覆盖仓库内 demo 资产。

## 分类空值

- 每个维度只能依据原文证据分类；证据不足时 ID 为 `null`，不得用默认标签补位。
- 任一维度为 null 时必须 `needs_human_review=true`。
- 路由时，未知维度只允许匹配该维为 `*` 的规则；其余已知维度照常参与匹配。
- 命令行选择器用 `null`、`none` 或 `-` 表示空值。

## 规则匹配

仅使用 `status=active` 的标签和规则。

1. 三维完全相同为 `exact`；
2. 两维相同、一维为 `*` 为 `two_dimension`；
3. 一维相同、两维为 `*` 为 `single_dimension`；
4. 全部为 `*` 的 `R-DEFAULT` 为 `global`。

同层级按 `priority` 从高到低选择；仍相同时按 `rule_id` 确定性选择。不得因为不存在精确组合而编造规则。

## 继承编译契约

`extends_rule_id` 只允许指向 active 父规则，且禁止循环。

- `style` 对象按字段递归深合并；
- 子规则的标量覆盖父规则；
- 子规则的数组整项替换父数组，不拼接；
- 子规则缺失字段表示继承；
- active 规则不得用显式 null 清空必填字段；
- `match`、`priority`、`status` 和 `rule_id` 不继承；
- `recommended_case_ids` 使用选中子规则自身列表，不从父规则累加。

编译后的 active style 必须具有合法商品占比、信息密度、促销强度和可用色板。

## 色板与信息层级

- 新规则使用 `style.palette_sets`；每次只能选择一个完整色板，不能跨组拼色。
- 旧 demo 的 `style.palette` 由 A 包装成单一 legacy 色板，仅用于兼容测试。
- C 提供 `hierarchy_preference` 语义顺序；A 根据 `protected_content` 生成最终 `information_hierarchy`。
- 未提供价格、优惠、期限或 CTA 时，信息层级和生成内容均不得补写这些事实。

## 案例门禁

正式推荐案例必须同时满足：

1. `review_status=approved`；
2. `is_seed=true`；
3. 权利状态为 owned、licensed、permission_granted、public_domain、internal_authorized 或 internal_reference_authorized；
4. 不得是 `research_reference_only`；
5. case ID、metadata、来源 URL 和 checksum 可追溯；
6. 第三方内部参考种子必须为 `public_repository_allowed=false`，不得把原图作为项目资产公开再分发。

draft 案例即使被规则引用，也必须从 `source_case_ids` 中过滤，只能在 `source_case_statuses` 和 warning 中留下审计记录。`is_seed=true` 不得绕过 draft 或权利门禁。

## 校验结果含义

- `valid=true`：结构、引用、继承、色板和清单可读取，允许做接口联调；
- `production_ready=true`：在 valid 基础上，没有生产阻断项且存在合格种子案例；
- `valid=true, production_ready=false`：候选包可测试，但不得宣布正式接入。

## 正式接入完成条件

只有同时满足以下条件，才可以把 `c_library.status` 改为 `connected`：

1. C 组交付冻结 schema、taxonomy、rules、case index 和案例元数据；
2. `validate_classification.py` 返回 `valid=true` 与 `production_ready=true`；
3. 完成 exact、继承规则、部分 null 和全 null 的端到端回归；
4. 至少存在 6 个 approved 内部参考种子，完整覆盖 S01–S06，并具有来源 URL 与固定 checksum；
5. 更新版本号、变更记录和 `PROJECT_STATUS.md`；
6. 经项目负责人审核合并。

## 资产失败默认风格

若文件不存在、JSON/CSV 无法解析、Schema 不兼容、引用失效或没有默认规则，使用：

- 白色或浅中性背景；
- 深色高对比文字；
- 商品居中，占画面约 55%；
- 信息密度 3；
- 促销强度 3；
- 层级顺序：商品 → 商品名/核心卖点 → 已提供的价格促销 → 已提供的 CTA；
- 禁止低对比文字、遮挡商品、捏造促销和装饰性假 Logo。

此时 `fallback_level=asset_failure_default`，必须记录 warning 和失败原因。

## 第三方参考种子边界

当前 6 个种子由项目负责人批准用于内部分类、检索、风格分析、生成参考和测试。批准不等于取得图片版权；仓库不得包含第三方原图，输出也不得把参考图片直接当作最终设计成果交付。
