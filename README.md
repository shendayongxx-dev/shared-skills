# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 可用版本

| Skill | 版本 | 发布状态 | C 正式库 | 发布标签 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `1.0.0` | 历史稳定版 | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0` |
| `ecommerce-poster-design` | `2.0.1` | 当前正式版 | 已接入 2.0.1 | `ecommerce-poster-design-v2.0.1` |

1.0.0 原目录和测试完整保留。2.0.1 在独立目录中加入消费者 Agent，并由整体 Skill 的生成层调用 Codex ImageGen；消费者 Agent 本身不调用生图工具。目录对应关系见 [VERSIONS.md](VERSIONS.md)。

## 下载与安装

推荐安装 2.0.1；需要兼容旧流程时可继续安装 1.0.0。详细步骤见 [INSTALL.md](INSTALL.md)。

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
- `skills/ecommerce-poster-design-2.0.1/`：2.0.1 Skill；
- `tests/ecommerce-poster-design/`：原样保留的 1.0.0 测试；
- `tests/ecommerce-poster-design-2.0.1/`：2.0.1 评估用例；
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
- 1.0 继续关闭消费者 Agent 与美学 Agent，且其目录内容不得被 2.0.1 覆盖；
- 2.0.1 的 ImageGen 属于整体 Skill 生成层，消费者 Agent 只负责评价和路由；
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
