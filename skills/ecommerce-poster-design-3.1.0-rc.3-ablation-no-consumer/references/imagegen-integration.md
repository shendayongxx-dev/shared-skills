# ImageGen 接入：no-consumer 消融版

主 Skill 独占生图权限。使用内置 `image_gen`；未经用户确认不切换 CLI/API 回退。

新建候选按生成计划执行。美学或最终质量返图必须以当前硬合规通过候选为底图，并先验证对应的 no-consumer 编辑合同。只编辑合同授权的区域或美学维度，保持八组保护内容和其余已锁美学维度。

SVG Logo 是权威源：先运行 `prepare_logo_asset.mjs`，让 ImageGen 生成预留 Logo 区的底图，再运行 `apply_logo_asset.mjs` 确定性贴放。禁止模型重画、旋转、裁切、改色或改变 Logo 比例。

成功形成新候选才增加全局重绘计数。新候选必须重新执行 HC-01～HC-12、美学和最终质量门。
