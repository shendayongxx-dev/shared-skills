# 1.0 + Aesthetic Agent 消融集成契约

## 冻结版本

- baseline：`shendayongxx-dev/shared-skills` tag `ecommerce-poster-design-v1.0.0-imagegen.1`
- baseline commit：`fdd3b20d74c170460f79465a241cffee012e6652`
- baseline 已内置：C 2.0.1 分类库、Codex ImageGen 生成层、HC-01～HC-12 与最多 3 次重画
- aesthetic agent：`zqian8245-hash/ecommerce-aesthetic-agent`
- aesthetic commit：`5f0baa0d10c5e1e114ac9a05fb33580110f31d33`
- aesthetic 源码归档 SHA-256：`5644cdb4f785693890c4f473ae4271d8cb6f343b938736b8fb055d07e7dd283c`
- ImageGen baseline 版本：`1.0.0-imagegen.1`
- 用户提供 `.skill` SHA-256：`a988195aacf4b92f999a985d20c0b3fcda0e354cdfc3794b94e46e5e989c625e`
- 用户提供 `.zip` SHA-256：`f217d9fa6b03f1eb03fea77e8ec04ebd7ca105a2ea342976efb1e27bdf722827`
- PRE 参考快照：[aesthetic-agent-pre-workflow.md](aesthetic-agent-pre-workflow.md)

vendored aesthetic 目录保持上游文件原样；适配逻辑只放在 baseline 外层的 `scripts/aesthetic_adapter.py`。上游 README 将当前迭代规则称为 v2.4，但 `SKILL.md` 仍以 v2/v2.3 描述参考库能力，机器接口 `schema_version` 为 2.0。因此实验记录应以 commit SHA 为准，不把“v2.4”当作可验证的软件版本号。

## 职责边界

| 职责 | 1.0 baseline | ImageGen | aesthetic agent | 外层适配器 |
|---|---|---|---|---|
| 输入校验、C 分类、style guide | 唯一负责 | 只消费生成提示词 | 只消费映射后的标签 | 确定性映射 |
| 海报生成/编辑工具调用 | 唯一调度 | 唯一执行 | 只给建议与提示词 | 不生成图片 |
| HC-01～HC-12 硬性保护 | 唯一权威 | 不负责 | 可再次发现风险，但不能覆盖 baseline | 合并时硬检优先 |
| 六维视觉评分 | 不负责 | 不负责 | 唯一负责 | 原样保留固定 JSON |
| 消费者/Persona 评价 | 禁用 | 不负责 | 禁止输出 | 固定记录 `false` |
| 轮次预算 | 首版 + 最多 3 次重画 | 每次只生成一个候选 | 自带 8 轮在本版禁用 | 防止嵌套 |
| 最终状态 | `passed/degraded/blocked` | 无通过状态 | `score/pass` | 单独计算 `ablation_pass` |

## 每轮顺序

1. baseline 形成生成计划并调用 ImageGen 生成或编辑一个候选。
2. baseline 对候选执行完整 HC-01～HC-12。
3. 硬检失败：只使用 baseline 的硬检修复动作，若仍有预算则重画。
4. 硬检通过：适配器准备 aesthetic 固定输入和 protected-content sidecar。
5. 视觉模型实际查看本轮候选、明确选定的原商品图以及可用参考图，写出符合 vendored `schemas/review.schema.json` 的内部 review。
6. 运行 vendored `scripts/evaluate.mjs`，得到固定 `agent-result.json`。
7. 美学通过：当前候选的 `ablation_pass=true`。美学未通过：仅在 baseline 剩余预算内将建议加入下一次 ImageGen 请求；新候选重新从步骤 2 开始。

任何轮次都不得先跑美学改图再跳过硬检。不能把提示词中的“保护商品”视为已完成保护。

## 输入字段映射

| aesthetic 字段 | 唯一来源 | 约束 |
|---|---|---|
| `poster_image` | 当前轮候选引用，由 `--poster-image` 显式传入 | 必须是本轮，不从 baseline brief 推断 |
| `product_input.product_img` | baseline `product.image_refs` | 只有一张时自动选择；多张时必须 `--product-image` 显式选定且值必须属于该数组 |
| `selling_points` | baseline `product.selling_points` | 原样复制，不摘要、不补写 |
| `price_text` | baseline `commerce.price_text` | 原样复制；不得把促销内容拼进价格字段 |
| `marketing_target` | baseline `marketing.goal` | 原样复制，不混入 Persona 推断 |
| `scene_tags` | `style_guide.tags` 中依次非空的 `audience_id`、`motivation_id`、`scenario_id` | 全为空时阻断美学评价，不用 `R-DEFAULT` 或自然语言猜标签 |

baseline 中没有可无损映射到固定 aesthetic 输入的商品名、品类、Logo、促销、活动期、CTA 和法务文案，写入 `protected-content-sidecar.json`，供视觉评价与生成计划逐项保护。不得扩展 aesthetic 固定输入 schema。

## 输出和 pass 语义

vendored `agent-result.json` 必须原样保存，字段只能是：`agent_name`、`score`、`pass`、`problem_list`、`modify_suggestion`、`protected_content`、`meta`。

- baseline `status=passed` 只表示硬性合规通过。
- aesthetic `pass=true` 表示总分 ≥8.5、每维 ≥8，且其内容保护检查通过。
- `ablation_pass=true` 只在 baseline hard pass 和 aesthetic pass 同时为真时成立。
- `score=0`、`confidence=0` 且问题以“无法评价”开头是未评价占位，不是 0 分样本；合并后 `score_state=unavailable`。
- 美学高分永远不能让硬检失败候选通过或进入“硬检通过候选”的选版集合。

## 冲突与推荐裁定

### 1. 3 次重画与 8 轮冲突

- 选项 A（本版采用）：保留 1.0 的 3 次重画上限，美学 Agent 每个硬检通过候选只评一次。
- 选项 B：允许美学 Agent 自己再生成最多 8 轮。

推荐 A。B 改变生成次数、成本和搜索空间，不是“只增加评价 Agent”的公平消融，应作为另一实验组。

### 2. upstream integrated 模式强制消费者 Agent

- 选项 A（本版采用）：vendored Agent 用 `standalone` context，外层单独合并 baseline 硬检。
- 选项 B：伪造消费者通过记录。
- 选项 C：真的加入消费者 Agent。

推荐 A。B 破坏真实性，C 增加第二个实验变量。

### 3. 固定输入缺少多项 protected content

- 选项 A（本版采用）：固定输入不变，增加外层只读 sidecar。
- 选项 B：修改 upstream input schema。

推荐 A。B 会让本实验使用一个非上游接口版本，并降低结果可复现性。

### 4. 最终状态命名冲突

- 选项 A（本版采用）：保留两套原始结果，再计算独立 `ablation_result`。
- 选项 B：用 aesthetic `pass` 覆盖 baseline `status`。

推荐 A。B 会让 baseline 结果无法与对照组逐项比较。

## 命令

准备固定输入：

```text
python scripts/aesthetic_adapter.py prepare --baseline-input task/baseline-input.json --style-guide task/style-guide.json --protected-content task/protected-content.json --poster-image task/round-01.png --out task/aesthetic-round-01
```

视觉模型写出 `review.json` 后运行上游确定性评分：

```text
node integrations/ecommerce-aesthetic-agent/scripts/evaluate.mjs --input task/aesthetic-round-01/aesthetic-input.json --review task/aesthetic-round-01/review.json --config integrations/ecommerce-aesthetic-agent/config.json --context task/aesthetic-round-01/context.json --out task/aesthetic-round-01/result
```

合并当前轮结果：

```text
python scripts/aesthetic_adapter.py merge --baseline-result task/baseline-result.json --aesthetic-result task/aesthetic-round-01/result/agent-result.json --out task/round-01-combined.json
```

脚本拒绝覆盖已有输出，重跑时使用新的轮次目录。
