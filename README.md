# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前发布状态

| Skill | 版本 | 状态 | C 正式库 | 最终 1.0 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `0.9.0-alpha.2` | PRE-RELEASE | 未接入 | 否 |

> **重要：这不是 Skill 1.0 最终版。** 当前版本完成了主流程、硬性合规、demo 冒烟测试及 C 候选接口适配，但 C 正式库仍未接入。`C-DEMO-*` 和外部 integration candidate 都不能作为已审核市场依据，也不能被标记成 C 正式库。

## 仓库结构

- `skills/ecommerce-poster-design/`：可运行 Skill 源码；
- `tests/ecommerce-poster-design/`：不含用户私有商品素材的输入与测试记录；
- `PROJECT_STATUS.md`：当前已经确定、尚未完成和禁止误判的事项；
- `CONTRIBUTING.md`：分支、PR、接口兼容和 C 库接入规则；
- `CHANGELOG.md`：版本变更记录。

## 当前不可变约束

- 1.0 预备流程顺序不随个人测试临时调整；
- 已定义的输入输出字段不得在普通功能 PR 中直接删除或改义；
- C 正式资产固定接入 `skills/ecommerce-poster-design/assets/classification/`；
- 未满足正式接入条件前，必须保持 `c_library.status=not_connected`；
- 只有项目负责人确认后，才能发布最终 `1.0.0`。
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
