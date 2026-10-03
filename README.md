# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前正式版本

| Skill | 版本 | 发布状态 | C 正式库 | 发布标签 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `1.0.0` | STABLE | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0` |

`ecommerce-poster-design` 1.0.0 已完成正式验收：C 2.0.1 分类库接入，6 个内部参考种子覆盖 S01–S06，分类资产达到 `production_ready=true`，并通过中文/英文双版本端到端验收。

## 下载与安装

推荐从 [GitHub Release：ecommerce-poster-design-v1.0.0](https://github.com/shendayongxx-dev/shared-skills/releases/tag/ecommerce-poster-design-v1.0.0) 下载发布包，将其中的 `ecommerce-poster-design` 整个目录复制到本机 Codex Skills 目录。详细的 Windows、macOS/Linux 安装、升级和验证步骤见 [INSTALL.md](INSTALL.md)。

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

- `skills/ecommerce-poster-design/`：可运行 Skill 源码；
- `tests/ecommerce-poster-design/`：不含用户私有商品素材的输入与测试记录；
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
- 1.0 继续关闭消费者 Agent 与美学 Agent；新增此类能力必须进入后续版本设计。
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
