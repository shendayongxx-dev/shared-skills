# ecommerce-poster-design 安装与部署

## 选择版本

- 美学集成候选版 3.0.0：仓库目录 `skills/ecommerce-poster-design-3.0.0/`；
- 当前稳定版 2.0.1：仓库目录 `skills/ecommerce-poster-design-2.0.1/`；
- 1.0 ImageGen 独立版 1.0.0-imagegen.1：仓库目录 `skills/ecommerce-poster-design-1.0.0-imagegen.1/`；
- 历史稳定版 1.0.0：仓库目录 `skills/ecommerce-poster-design/`，内容保持冻结。

无论选择哪个版本，复制到本机 Codex Skills 目录后，目标目录都应命名为 `ecommerce-poster-design`。不要把不同版本的文件混合到同一安装目录。

## 安装 3.0.0（美学集成候选版）

```powershell
git clone --branch main --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
Copy-Item -Recurse -LiteralPath '.\shared-skills\skills\ecommerce-poster-design-3.0.0' -Destination $skillTarget
```

3.0.0 基于未修改的 2.0.1；ImageGen 由整体 Skill 调用，`modules/consumer-agent` 与 `modules/aesthetic-agent` 只负责评价和路由。安装后运行：

```text
python scripts/validate_classification.py assets/classification
python scripts/validate_consumer_integration.py .
python scripts/validate_aesthetic_integration.py .
python scripts/test_consumer_routing.py
python scripts/test_aesthetic_integration.py
```

## 安装 2.0.1（稳定版，无美学 Agent）

```powershell
git clone --branch main --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
Copy-Item -Recurse -LiteralPath '.\shared-skills\skills\ecommerce-poster-design-2.0.1' -Destination $skillTarget
```

安装后运行：

```text
python scripts/validate_classification.py assets/classification
python scripts/validate_consumer_integration.py .
python scripts/test_consumer_routing.py
```

## 安装 1.0.0-imagegen.1

正式版本标签为 `ecommerce-poster-design-v1.0.0-imagegen.1`。该版本保持 1.0 的输入、分类、硬性合规和有限重画流程，由整体 Skill 调用 Codex ImageGen；不包含消费者 Agent或美学 Agent。

```powershell
git clone --branch ecommerce-poster-design-v1.0.0-imagegen.1 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-1.0.0-imagegen.1
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
Copy-Item -Recurse -LiteralPath '.\shared-skills-1.0.0-imagegen.1\skills\ecommerce-poster-design-1.0.0-imagegen.1' -Destination $skillTarget
```

安装后运行：

```text
python scripts/validate_classification.py assets/classification
python scripts/select_style.py assets/classification P02 M03 S03 --request-id INSTALL-CHECK
```

## 安装 1.0.0

正式版本标签为 `ecommerce-poster-design-v1.0.0`。成员应从该标签或对应 GitHub Release 安装，不要直接下载正在开发的功能分支。

仓库地址：`https://github.com/shendayongxx-dev/shared-skills`

Release 页面：`https://github.com/shendayongxx-dev/shared-skills/releases/tag/ecommerce-poster-design-v1.0.0`

最省事的方式是下载 Release 附件 `ecommerce-poster-design-1.0.0.zip`，解压后直接复制其中的 `ecommerce-poster-design` 目录。以下 Git 命令适用于需要固定版本源码的成员。

### Windows PowerShell

```powershell
git clone --branch ecommerce-poster-design-v1.0.0 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-1.0.0
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
New-Item -ItemType Directory -Force -Path (Split-Path $skillTarget) | Out-Null
Copy-Item -Recurse -LiteralPath '.\shared-skills-1.0.0\skills\ecommerce-poster-design' -Destination $skillTarget
```

如果目标目录已存在，请先备份并确认其中没有未合并的本地修改；不要直接覆盖不明来源的旧目录。

### macOS / Linux

```bash
git clone --branch ecommerce-poster-design-v1.0.0 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-1.0.0
mkdir -p "$HOME/.codex/skills"
cp -R ./shared-skills-1.0.0/skills/ecommerce-poster-design "$HOME/.codex/skills/ecommerce-poster-design"
```

如果使用了自定义 Codex Skills 目录，请把完整的 `ecommerce-poster-design` 文件夹复制到该目录，而不是固定使用示例路径。

## 安装后验证

本 Skill 的确定性脚本仅依赖 Python 标准库，建议使用 Python 3.10 或更高版本。

进入已安装的 Skill 目录后运行：

```text
python scripts/validate_classification.py assets/classification
python scripts/select_style.py assets/classification P02 M03 S03 --request-id INSTALL-CHECK
```

验收标准：

- 第一条命令输出 `valid=true`；
- 第一条命令输出 `production_ready=true`；
- `eligible_seed_cases=6`；
- `eligible_seed_scenarios=6`；
- 第二条命令命中 `R-001`，并返回案例 `C-030`。

验证通过后重新打开 Codex 会话，使新安装的 Skill 被发现。可以使用 `$ecommerce-poster-design` 显式调用，也可以在提供完整商品营销主视觉需求时自动触发。

## 运行时必须提供

- 商品图；
- 商品名称或品类；
- 已确认的卖点；
- 价格与促销信息；
- 营销目标；
- 画布宽高和输出格式。

缺少以上信息时，Skill 会返回缺失字段，不会自行猜造价格、折扣、商品特征、Logo 或活动时间。

## C 库与种子说明

- C 2.0.1 的 taxonomy、规则、案例元数据、来源 URL、审核状态和校验值已包含在 Skill 内；
- 6 个种子为“内部参考”，不是项目自有版权图片；
- 公共仓库与 Release 不包含第三方种子图片二进制；
- 没有种子原图时，Skill 仍可根据结构化 `style_guide` 运行；
- 如内部环境允许拉取参考图，必须核对元数据中的 SHA-256，且不得再次公开分发原图。

## 升级与回退

升级前保留当前完整 Skill 目录，并阅读新版本 `CHANGELOG.md` 和 `RELEASE_MANIFEST.json`。不要把两个版本的 `assets/classification` 混合复制。

需要回退时，删除或移走当前安装目录，再从目标发布标签重新复制完整目录。版本是否一致，以 `assets/config/version.json` 为准。

## 贡献者部署

贡献者不要直接修改正式标签。请从 `main` 创建独立分支，完成验证后提交 Pull Request。接口、资产和测试要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。
