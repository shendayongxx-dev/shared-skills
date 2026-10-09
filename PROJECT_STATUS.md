# 项目状态

## 当前主线

- 当前版本：`3.0.0`
- 发布通道：`stable`
- main 内容策略：只保留当前完整版本
- Skill 目录：`skills/ecommerce-poster-design-3.0.0/`
- 测试目录：`tests/ecommerce-poster-design-3.0.0/`
- 发布 Tag：`ecommerce-poster-design-v3.0.0`
- 分类资产：`production_ready=true`

## 当前工作流

`输入校验 → C 库检索 → 生成 → 硬性合规 → 消费者 Agent → 美学 Agent → 完成或有限迭代`

- ImageGen 仅属于整体 Skill 生成层；
- 消费者 Agent 负责消费视角评价和路由；
- 美学 Agent 负责六维评价和重设计方案；
- 所有返图重新执行硬检查、消费者评价和美学评价；
- 进入美学前最多 3 次重绘，美学阶段最多 8 个生成轮次。

## 历史版本策略

1.0.0、1.0.0-imagegen.1 和 2.0.1 已由对应 Tag 固定保存，不再占用 `main` 工作树。现有历史分支和 Tag 不重写、不移动。

## 独立消融实验

- 分支：`experiment/ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1`
- Tag：`ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1`
- 基线：`1.0.0`
- 流程：`生成 → 硬性合规 → 美学 Agent → 消费者 Agent`
- 状态：`experimental`，不替代 3.0.0，不直接合并进 `main`

## 不得误判

- `production_ready=true` 表示分类资产门禁通过，不表示取得第三方图片版权；
- 第三方种子图只用于内部参考，不得提交或公开再分发；
- 用户商品素材、Logo、生成图片和凭据不得提交到公共仓库；
- 美学评分不能覆盖硬性合规或消费者门禁失败。
