# ecommerce-poster-design 2.0.1 安装与部署

## 从正式标签安装

仓库：`https://github.com/shendayongxx-dev/shared-skills`

正式标签：`ecommerce-poster-design-v2.0.1`

### Windows PowerShell

```powershell
git clone --branch ecommerce-poster-design-v2.0.1 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-2.0.1
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
New-Item -ItemType Directory -Force -Path (Split-Path $skillTarget) | Out-Null
Copy-Item -Recurse -LiteralPath '.\shared-skills-2.0.1\skills\ecommerce-poster-design' -Destination $skillTarget
```

### macOS / Linux

```bash
git clone --branch ecommerce-poster-design-v2.0.1 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-2.0.1
mkdir -p "$HOME/.codex/skills"
cp -R ./shared-skills-2.0.1/skills/ecommerce-poster-design "$HOME/.codex/skills/ecommerce-poster-design"
```

目标目录已存在时先备份或移走旧目录，不要把不同版本的文件合并复制。

## 运行依赖

- 支持 Skills 和内置 `image_gen` 工具的 Codex；
- Python 3.10 或更高版本，用于确定性校验与路由脚本；
- 默认内置 ImageGen 路径不需要 `OPENAI_API_KEY`。

## 安装后验证

在 Skill 目录运行：

```text
python scripts/validate_consumer_integration.py .
python scripts/validate_classification.py assets/classification
python scripts/test_consumer_routing.py
python scripts/select_style.py assets/classification P02 M03 S03 --request-id INSTALL-CHECK
```

验收标准：

- 集成校验输出 `valid=true`，生成后端为 `imagegen/image_gen`；
- 分类校验输出 `valid=true` 和 `production_ready=true`；
- 消费者路由测试 5 个场景全部通过；
- 风格选择命中 `R-001` 并返回案例 `C-030`。

验证后重新打开 Codex 会话，使 Skill 元数据重新载入。

## 运行时必填输入

- 商品图；
- 商品名称或品类；
- 已确认的卖点；
- 价格与促销信息；
- 营销目标；
- 画布宽高和输出格式。

Skill 不会自行猜造价格、折扣、商品特征、Logo、认证或活动时间。

## 升级与回退

升级前保留当前完整目录并阅读 `CHANGELOG.md` 与 `RELEASE_MANIFEST.json`。回退时使用目标发布标签的完整目录替换当前目录，不要混合复制 `assets`、`modules` 或 `references`。
