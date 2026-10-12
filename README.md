# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前主线

`main` 只保留当前版本 `ecommerce-poster-design 3.1.0-rc.4`：

- Skill：`skills/ecommerce-poster-design-3.1.0/`
- 测试：`tests/ecommerce-poster-design-3.1.0/`
- 固定发布：`ecommerce-poster-design-v3.1.0-rc.4`

3.1.0-rc.4 的流程为：`输入校验与画布归一化 → 分类与 Style Guide → Logo 预检 → 生成/确定性贴放 → 硬性合规 → 消费者 Agent → 美学 Agent → 最终质量仲裁 → 完成或统一预算内迭代`。ImageGen 仅由整体 Skill 调用，消费者和美学 Agent 都不直接生成图片。

本版在 rc.3 的无分数最终质量门、异常高分反向复核、SVG Logo 安全管线和局部编辑合同基础上，新增确定性画布归一化。只提供比例时，以短边至少 1080px 的最小整数倍派生精确尺寸，不因缺少绝对像素而阻塞。

## 历史版本

历史版本不继续堆放在 `main`，通过不可变 Tag 获取：

| 版本 | Tag |
|---|---|
| 1.0.0 | `ecommerce-poster-design-v1.0.0` |
| 1.0.0-imagegen.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` |
| 2.0.1 | `ecommerce-poster-design-v2.0.1` |
| 3.0.0 | `ecommerce-poster-design-v3.0.0` |
| 3.0.0 rebuilt rc4 | `ecommerce-poster-design-v3.0.0-rebuilt-rc4` |
| 3.1.0-rc.3 | `ecommerce-poster-design-v3.1.0-rc.3` |

已有历史分支和 Tag 保持原指向，不重写、不移动。安装和迭代规则见 [INSTALL.md](INSTALL.md) 与 [VERSIONS.md](VERSIONS.md)。

## 版本迭代规则

1. 从最新 `main` 创建 `feature/<version>` 或 `fix/<version>-<topic>` 分支。
2. 在分支完成实现、测试和版本文档。
3. 通过 Pull Request 合并回 `main`；`main` 只保留最新完整版本目录。
4. 合并后创建新的带注释 Tag；已发布 Tag 永不移动。
5. 旧版本从对应 Tag 安装和回退，不在 `main` 复制保存。

第三方参考图片、用户商品图、Logo、生成结果和凭据不得提交到仓库。

发布前运行 `python scripts/validate_release_lock.py .`。该检查同时验证当前版本指针和 Skill 目录树哈希，防止文档、安装包与实际代码发生版本漂移。
