# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 可用版本

| Skill | 版本 | 发布状态 | C 正式库 | 发布标签 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `1.0.0` | 历史稳定版 | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0` |
| `ecommerce-poster-design` | `1.0.0-imagegen.1` | 1.0 ImageGen 独立版 | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` |
| `ecommerce-poster-design` | `2.0.1` | 当前正式版 | 已接入 2.0.1 | `ecommerce-poster-design-v2.0.1` |
| `ecommerce-poster-design` | `3.0.0` | 重建验证候选版 | 继承 2.0.1 | `ecommerce-poster-design-v3.0.0-rebuilt-rc4` |

1.0.0、1.0.0-imagegen.1 与 2.0.1 原目录和测试完整保留。1.0.0-imagegen.1 为 1.0 主流程接入 ImageGen；新 3.0.0 从 2.0.1 重建，在消费者通过且五维全锁后调用美学 Agent 3.0.0-rc.4。旧 v2.4 集成由 `ecommerce-poster-design-v3.0.0-legacy-aesthetic-v2.4` 冻结。目录对应关系见 [VERSIONS.md](VERSIONS.md)。

## 下载与安装

需要美学 Agent 时安装 3.0.0；生产稳定流程使用 2.0.1；需要 1.0 流程且希望使用 ImageGen 时安装 1.0.0-imagegen.1。详细步骤见 [INSTALL.md](INSTALL.md)。

安装完成后，技能目录必须保持如下层级：

```text
<Codex Skills 目录>/
└── ecommerce-poster-design/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

不要只复制 `SKILL.md`；分类资产、参考契约和校验脚本都是 1.0 运行所需内容。

## 仓库结构

- `skills/ecommerce-poster-design/`：原样保留的 1.0.0 Skill；
- `skills/ecommerce-poster-design-1.0.0-imagegen.1/`：1.0.0-imagegen.1 独立 Skill；
- `skills/ecommerce-poster-design-2.0.1/`：2.0.1 Skill；
- `skills/ecommerce-poster-design-3.0.0/`：从 2.0.1 重建的美学 Agent rc.4 集成候选版；
- `tests/ecommerce-poster-design/`：原样保留的 1.0.0 测试；
- `tests/ecommerce-poster-design-2.0.1/`：2.0.1 评估用例；
- `tests/ecommerce-poster-design-3.0.0/`：3.0.0 集成评估用例；
- `PROJECT_STATUS.md`：当前已经确定、尚未完成和禁止误判的事项；
- `CONTRIBUTING.md`：分支、PR、接口兼容和 C 库接入规则；
- `CHANGELOG.md`：版本变更记录。
- `INSTALL.md`：成员下载、安装、升级和验证说明。

## 当前不可变约束

- 1.0 正式流程顺序不随个人测试临时调整；
- 已定义的输入输出字段不得在普通功能 PR 中直接删除或改义；
- C 正式资产固定接入 `skills/ecommerce-poster-design/assets/classification/`；
- C 库状态、种子数量和生产门禁必须由自动校验结果支持；
- 第三方参考图片二进制、用户商品图、Logo 和生成结果不得进入公共仓库；
- 1.0 继续关闭消费者 Agent 与美学 Agent，且其目录内容不得被后续版本覆盖；
- 2.0.1 的 ImageGen 属于整体 Skill 生成层，消费者 Agent 只负责评价和路由；
- 3.0.0 的美学 Agent 只负责 25 子项观察、六维确定性评分与局部修改建议；任何重画必须重跑硬检查和消费者评价；
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
