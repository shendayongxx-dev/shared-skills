# ecommerce-poster-design 安装与部署

## 安装当前 3.0.0

```powershell
git clone --branch ecommerce-poster-design-v3.0.0 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-3.0.0
$skillTarget = Join-Path $env:USERPROFILE '.codex\skills\ecommerce-poster-design'
Copy-Item -Recurse -LiteralPath '.\shared-skills-3.0.0\skills\ecommerce-poster-design-3.0.0' -Destination $skillTarget
```

安装后在 Skill 目录运行：

```text
python scripts/validate_classification.py assets/classification
python scripts/validate_consumer_integration.py .
python scripts/validate_aesthetic_integration.py .
python scripts/test_consumer_routing.py
python scripts/test_aesthetic_integration.py
```

## 安装历史版本

历史版本只从固定 Tag 安装：

```text
ecommerce-poster-design-v1.0.0
ecommerce-poster-design-v1.0.0-imagegen.1
ecommerce-poster-design-v2.0.1
```

示例：

```powershell
git clone --branch ecommerce-poster-design-v2.0.1 --depth 1 https://github.com/shendayongxx-dev/shared-skills.git shared-skills-2.0.1
```

克隆后按该 Tag 中的 `README.md`、`INSTALL.md` 和 `RELEASE_MANIFEST.json` 找到对应版本目录。不要混合复制不同版本的文件。

## 升级与回退

升级前备份当前完整 Skill 目录。升级时用新 Tag 的完整目录替换安装目录，不做跨版本文件覆盖合并。

回退时重新克隆目标历史 Tag，并完整安装该 Tag 中的 Skill。版本以 `assets/config/version.json` 为准。

本 Skill 的确定性脚本仅依赖 Python 标准库，建议使用 Python 3.10 或更高版本。第三方种子图、用户商品素材、Logo、生成图片和凭据不得随安装包公开分发。
