# 交付说明：ecommerce-poster-design 1.0.0-imagegen.1 + Aesthetic Agent

## 目的

本目录以正式标签 `ecommerce-poster-design-v1.0.0-imagegen.1` 为冻结 baseline，只追加 Aesthetic Agent。C 库和 ImageGen 都是 baseline 已有能力，不作为本实验新增变量。它不替代或回写 baseline release，不加入消费者/Persona Agent，也不改变 ImageGen 的生成职责。

## 相对 baseline 的改动

1. 独立部署名称和版本为 `ecommerce-poster-design-v1.0.0-imagegen-aesthetic-agent.1`；安装后的 Skill 调用名仍为 `$ecommerce-poster-design`。
2. `consumer_agent` 保持 `false`，`aesthetic_agent` 保持 `true`。
3. vendored 并固定 aesthetic agent commit `5f0baa0d10c5e1e114ac9a05fb33580110f31d33`。
4. 原样保留 baseline 的 Codex 系统 `imagegen` Skill 和内置 `image_gen` 生成/编辑后端；默认不要求 API Key。
5. 原样保留 baseline 的 [ImageGen 集成契约](references/imagegen-integration.md) 与 C 库；不重复接入或另立一套 C 库。
6. 保留 `scripts/aesthetic_adapter.py`、其单元测试和合并结果 schema。
7. 在每个 ImageGen 候选通过硬检后运行一次美学评价；baseline 的 C 分类、HC-01～HC-12 和最多 3 次重画不变。
8. 独立 `ablation_result` 不覆盖 baseline 状态或 aesthetic 固定输出。

完整字段映射、循环裁定和冲突选项见 [references/aesthetic-ablation.md](references/aesthetic-ablation.md)。

## 未改变的内容

- `1.0.0-imagegen.1` baseline 中 `assets/classification/` 的正式 C 2.0.1 资产；
- `scripts/validate_classification.py` 与 `scripts/select_style.py`；
- `references/contracts.md` 与 `references/hard-compliance.md` 的 baseline 契约；
- 首版 + 最多 3 次重画的预算；
- baseline 最终状态 `passed/degraded/blocked`；
- 生成计划和轮次仍由 1.0 调度；ImageGen 只执行生成或编辑。

## 已知边界

- aesthetic 仓库不含参考图原文件，只有文字索引与观察；宿主没有真实图片时不能声称做过图像对照。
- aesthetic 脚本只负责校验、计分和输出文件，不看图、不调用模型、不生成图片。
- ImageGen 不负责硬检或美学评分；美学 Agent 不直接调用 ImageGen。
- 内置 ImageGen 持续不可用时，CLI/API 回退需要用户明确同意并在本地配置 `OPENAI_API_KEY`。
- 多张商品母图需要人工明确本轮主商品图；适配器不会静默丢弃其余图片。
- C 三类标签全部未知时，baseline 可按全局规则继续，但 aesthetic 固定输入无法满足 `scene_tags.minItems=1`，因此该轮美学结果记为不可用，不能伪造标签。
- upstream README 称迭代规则为 v2.4，但无单一软件版本字段；实验以 commit SHA 和 schema 2.0 为准。

## 验证命令

```text
python scripts/validate_classification.py assets/classification
python scripts/select_style.py assets/classification P02 M03 S03 --request-id INSTALL-CHECK
node --test integrations/ecommerce-aesthetic-agent/tests/evaluate.test.mjs integrations/ecommerce-aesthetic-agent/tests/references.test.mjs integrations/ecommerce-aesthetic-agent/tests/quality.test.mjs
python -m unittest discover -s tests -p "test_*.py"
python tests/smoke_integration.py
```
