# 项目状态

## 当前发布

- 版本：`2.0.1`
- 发布通道：`stable`
- 生产门禁：已通过
- 生成后端：Codex `imagegen` / `image_gen` 内置模式
- 消费者 Agent：`1.5.3`，接口 `A-D-2.0`，已启用
- 美学 Agent：未启用
- C 正式库：`2.0.1-a.1`，`production_internal_reference`

## 已实现

- 输入校验、P-M-S 分类、C 库检索、`style_guide`、ImageGen 生成或编辑、硬性合规、消费者评价和有限重画完整链路；
- `protected_content` 八组内容与锁定维度回归保护；
- 硬性合规与消费者失败共用最多 3 次重画计数；
- C 库 81 条案例元数据及覆盖 S01–S06 的 6 个合格内部参考种子；
- 内置 ImageGen 不可用时的显式失败和用户确认式 CLI/API 回退边界。

## 发布边界

- 消费者 Agent 通过后完成流程，不调用美学 Agent；
- `production_ready=true` 不代表项目取得第三方图片版权；
- 第三方种子原图、用户商品素材、Logo、生成海报和凭据不得提交到公开仓库；
- ImageGen 系统 Skill 源码不复制进本仓库，本仓库只维护调用契约。
