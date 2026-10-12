# 项目状态

## 当前主线

- 当前版本：`3.1.0-rc.5`
- 发布通道：`stable`
- main 内容策略：只保留当前完整版本
- Skill 目录：`skills/ecommerce-poster-design-3.1.0/`
- 测试目录：`tests/ecommerce-poster-design-3.1.0/`
- 发布 Tag：`ecommerce-poster-design-v3.1.0-rc.5`
- 分类资产：`production_ready=true`

## 当前工作流

`输入校验与画布归一化 → C 库检索 → Logo 预检 → 无 Logo 底图生成 → 确定性贴放 → Logo 合成验证 → 硬性合规 → 消费者 Agent → 美学 Agent → 最终质量仲裁 → 完成或统一预算内迭代`

- ImageGen 仅属于整体 Skill 生成层；
- 比例输入按短边至少 1080px 的最小整数倍确定性补全，生成前告知实际尺寸；
- 消费者 Agent 负责消费视角评价和路由；
- 美学 Agent 负责六维评价和局部修改建议，并在原量表内强制观察 Logo 视觉整合；
- 最终质量门核验证据和可定位缺陷，不新增第三套分数；
- Logo 缺失或错误为关键缺陷；矩形底色、边缘光晕、低对比、悬浮和 `TEXT_OVERLAP` 最低为中度；
- 所有返图重新执行硬检查、消费者、美学和最终质量仲裁；
- 首版不计重绘，后续成功返图统一共用最多 8 次预算。

## 历史版本策略

1.0.0、1.0.0-imagegen.1、2.0.1、3.0.0、3.1.0-rc.3 与 3.1.0-rc.4 已由对应 Tag 固定保存，不再占用 `main` 工作树。现有历史分支和 Tag 不重写、不移动。

## 发布一致性

- `RELEASE_MANIFEST.json` 是版本和目录指针的权威来源；
- `RELEASE_LOCK.json` 固定 rc.5 Skill 目录树哈希；
- 发布、压缩和安装后均运行 `scripts/validate_release_lock.py`；
- 不原地覆盖 rc.4；rc.5 始终整体替换并重新校验。

## 不得误判

- `production_ready=true` 表示分类资产门禁通过，不表示取得第三方图片版权；
- 第三方种子图只用于内部参考，不得提交或公开再分发；
- 用户商品素材、Logo、生成图片和凭据不得提交到公共仓库；
- 美学评分不能覆盖硬性合规或消费者门禁失败。
