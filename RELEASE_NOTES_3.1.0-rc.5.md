# ecommerce-poster-design 3.1.0-rc.5

## 发布定位

在 rc.4 基础上修复 Logo 后贴链路可能被跳过，以及透明 Logo 合成后出现矩形底色、边框或边缘光晕却仍被放行的问题。保留消费者 Agent 1.5.3、C 2.0.1 分类库、确定性画布归一化和六维美学权重。

## 主要更新

- 保持“先生成无 Logo 底图，再确定性贴入权威 Logo”的制作顺序。
- 增加 `logo_preflight_passed → logo_applied → logo_verified → candidate_ready` 强制状态链；底图不能进入评价或交付。
- 新增 `verify_logo_application.py` 与 `logo-verification/1.0`，绑定权威源、派生 Logo、底图、合成输出和最终候选哈希。
- Logo 预检升级为 `logo-asset-preflight/1.1`，区分“存在 Alpha 通道”和“实际存在透明像素”；全不透明资产强制进入背景伪影视觉复核。
- 最终质量合同升级为 `FINAL-QUALITY-3.2`，新增 `LOGO_MISSING`、`LOGO_INCORRECT`、`LOGO_BACKGROUND_ARTIFACT`、`LOGO_EDGE_HALO` 和 `LOGO_CONTRAST_LOW`。
- Logo 缺失或错误固定为 `critical`；矩形底色、边缘光晕、低对比和悬浮固定为至少 `moderate`。
- 美学模块升级为 `3.0.0-rc.5`，在原六维和 25 子项内强制观察 Logo 尺寸、位置、留白、对齐、对比、分组和融合感，不新增维度或改变权重。
- 增加透明 Logo、全不透明资产提示、候选哈希绑定和 Logo 缺陷路由回归测试。

## 版本边界

- rc.4 分支、Tag 和 Release 保持不可变，不原地覆盖。
- rc.5 使用新 Tag `ecommerce-poster-design-v3.1.0-rc.5`。
- 主 Skill 为 `3.1.0-rc.5`，美学模块为 `3.0.0-rc.5`，最终质量合同为 `FINAL-QUALITY-3.2`。
- GitHub Release 使用本文件作为正文。
