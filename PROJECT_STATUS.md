# 项目状态

## 当前主线

- 当前版本：`3.1.0-rc.3`（当前稳定标记版；版本号保留 rc.3）
- 发布通道：`stable`
- main 内容策略：只保留当前完整版本
- Skill 目录：`skills/ecommerce-poster-design-3.1.0/`
- 测试目录：`tests/ecommerce-poster-design-3.1.0/`
- 发布 Tag：`ecommerce-poster-design-v3.1.0-rc.3`
- 分类资产：`production_ready=true`

## 当前工作流

`输入校验 → C 库检索 → Logo 预检 → 生成与确定性贴放 → 硬性合规 → 消费者 Agent → 美学 Agent → 最终质量仲裁 → 完成或统一预算内迭代`

- ImageGen 仅属于整体 Skill 生成层；
- 消费者 Agent 负责消费视角评价和路由；
- 美学 Agent 负责六维评价和局部修改建议；
- 最终质量门核验证据和可定位缺陷，不新增第三套分数；
- `TEXT_OVERLAP` 与 `LOGO_FLOATING` 最低为中度并强制局部重绘；
- 所有返图重新执行硬检查、消费者、美学和最终质量仲裁；
- 首版不计重绘，后续成功返图统一共用最多 8 次预算。

## 独立实验

- `experiment/ecommerce-poster-design-3.1.0-rc.3-ablation-no-consumer`：移除消费者 Agent 的组件消融；
- `experiment/ecommerce-poster-design-3.1.0-rc.3-ablation-aesthetic-first`：把双 Agent 顺序调整为“美学 → 消费者”的顺序消融，实验快照 Tag 为 `ecommerce-poster-design-v3.1.0-rc.3-ablation-aesthetic-first.1`。

两项实验均与 `main` 隔离，不改变当前稳定版与正式发布 Tag。

## 历史版本策略

1.0.0、1.0.0-imagegen.1、2.0.1 和 3.0.0 已由对应 Tag 固定保存，不再占用 `main` 工作树。现有历史分支和 Tag 不重写、不移动。

## 不得误判

- `production_ready=true` 表示分类资产门禁通过，不表示取得第三方图片版权；
- 第三方种子图只用于内部参考，不得提交或公开再分发；
- 用户商品素材、Logo、生成图片和凭据不得提交到公共仓库；
- 美学评分不能覆盖硬性合规或消费者门禁失败。
