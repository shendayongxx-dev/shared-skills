# shared-skills：1.0 ImageGen + 美学 Agent 消融版本

当前为独立发布分支 `release/ecommerce-poster-design-v1.0.0-imagegen-aesthetic-agent.1`。本分支以 `ecommerce-poster-design-v1.0.0-imagegen.1` 为唯一 baseline，只追加美学 Agent，不合入 `main`。

正式 1.0 baseline 已经包含 C 2.0.1 分类库；`1.0.0-imagegen.1` 又在该流程的生成层接入 Codex ImageGen。因此本消融版本的唯一新增实验变量是美学 Agent，不是 C 库，也不是消费者/Persona Agent。

## 可用版本

| Skill | 版本 | 发布状态 | C 正式库 | 发布标签 |
|---|---|---|---|---|
| `ecommerce-poster-design` | `1.0.0` | 历史稳定版 | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0` |
| `ecommerce-poster-design` | `1.0.0-imagegen.1` | 1.0 ImageGen 独立版 | 已接入 2.0.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` |
| `ecommerce-poster-design` | `1.0.0-imagegen-aesthetic-agent.1` | 独立美学消融版本 | 继承 baseline 的 2.0.1 | `ecommerce-poster-design-v1.0.0-imagegen-aesthetic-agent.1` |
| `ecommerce-poster-design` | `2.0.1` | 当前正式版 | 已接入 2.0.1 | `ecommerce-poster-design-v2.0.1` |

1.0.0 原目录和测试完整保留。1.0.0-imagegen.1 在独立目录中为 1.0 主流程接入 Codex ImageGen，不包含消费者 Agent或美学 Agent。1.0.0-imagegen-aesthetic-agent.1 继承该 baseline 的 C 库、ImageGen、硬性合规和最多 3 次重画，只在硬检通过后增加美学六维评价；消费者 Agent 关闭，美学 Agent 自带的 8 轮循环禁用。2.0.1 是另一条包含消费者 Agent 的正式版本线。目录对应关系见 [VERSIONS.md](VERSIONS.md)。

## 下载与安装

本分支用于美学消融实验时，应安装 `skills/ecommerce-poster-design-1.0.0-imagegen-aesthetic-agent.1/`。只需要无美学评价的对照组时安装 1.0.0-imagegen.1；需要原始兼容流程时安装 1.0.0。安装时将所选版本目录复制到 Codex Skills 目录，并命名为 `ecommerce-poster-design`。通用步骤见 [INSTALL.md](INSTALL.md)。

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
- `skills/ecommerce-poster-design-1.0.0-imagegen-aesthetic-agent.1/`：本分支新增的美学消融 Skill；
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
- 1.0.0 与 1.0.0-imagegen.1 两个 baseline 目录继续关闭消费者 Agent 与美学 Agent，且不得被其他版本覆盖；
- 本消融版本只对 1.0.0-imagegen.1 追加美学 Agent；消费者 Agent 关闭，C 库和 baseline 状态语义不变；
- 美学 `pass` 不得覆盖 baseline 硬性合规结果，最终另记 `ablation_pass`；
- 本分支不合入 `main`；
- 2.0.1 的 ImageGen 属于整体 Skill 生成层，消费者 Agent 只负责评价和路由；
- 相关提交和 PR 会自动运行分类资产、规则选择、发布状态和测试素材检查。

开始修改前请先阅读 [项目状态](PROJECT_STATUS.md) 和 [协作规则](CONTRIBUTING.md)。
