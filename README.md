# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前发布状态

| Skill | 版本 | 状态 | C 正式库 | 最终 1.0 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `1.0.0-rc.1` | RELEASE CANDIDATE | 已接入 2.0.1 | 待最终确认 |

> **当前已完成 Skill 1.0 候选版搭建。** C 2.0.1 分类库已接入，6 个内部参考种子覆盖 S01–S06，分类资产校验达到 `production_ready=true`。第三方参考图片不进入公开仓库；最终 `1.0.0` 仍需项目负责人确认发布。

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
- C 库状态、种子数量和生产门禁必须由自动校验结果支持；
- 只有项目负责人确认后，才能发布最终 `1.0.0`。
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
