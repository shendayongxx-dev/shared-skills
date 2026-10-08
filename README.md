# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前正式版本

| Skill | 版本 | 发布状态 | 生成后端 | 消费者 Agent | 发布标签 |
|---|---|---|---|---|---|
| `ecommerce-poster-design` | `2.0.1` | STABLE | Codex ImageGen | `1.5.3` | `ecommerce-poster-design-v2.0.1` |

`ecommerce-poster-design` 2.0.1 已接入 Codex 系统 `imagegen` Skill、内置 `image_gen` 工具、C 2.0.1 分类库和消费者 Agent 1.5.3。分类资产达到 `production_ready=true`，消费者接口为 `A-D-2.0`。

## 下载与安装

从 [GitHub Release：ecommerce-poster-design-v2.0.1](https://github.com/shendayongxx-dev/shared-skills/releases/tag/ecommerce-poster-design-v2.0.1) 下载发布包，或按 [INSTALL.md](INSTALL.md) 从标签安装完整目录。

```text
<Codex Skills 目录>/
└── ecommerce-poster-design/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── evals/
    ├── modules/
    ├── references/
    └── scripts/
```

不要只复制 `SKILL.md`；ImageGen 集成契约、分类资产、消费者模块和校验脚本均为运行时组成部分。

## 仓库结构

- `skills/ecommerce-poster-design/`：2.0.1 可运行 Skill 源码；
- `tests/ecommerce-poster-design/evals/`：不含用户私有素材的评估定义；
- `PROJECT_STATUS.md`：当前发布状态与边界；
- `CONTRIBUTING.md`：分支、PR、接口兼容和资产规则；
- `CHANGELOG.md`：当前版本变更；
- `INSTALL.md`：安装、升级、回退和验证说明。

## 当前约束

- 默认使用 Codex 系统 `imagegen` Skill 和内置 `image_gen` 工具；
- 消费者 Agent 启用，美学 Agent 关闭；
- 硬性合规与消费者失败共用最多 3 次重画计数；
- 已定义的输入输出字段不得在普通功能 PR 中删除或改义；
- 第三方参考图片二进制、用户商品图、Logo 和生成结果不得进入公共仓库；
- 分类资产、消费者接口和发布状态必须通过自动校验。

开始修改前请阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
