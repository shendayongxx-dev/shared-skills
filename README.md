# shared-skills

用于共享、版本迭代和协作维护 Codex Skills。

## 当前主线

`main` 只保留当前版本 `ecommerce-poster-design 3.0.0`：

- Skill：`skills/ecommerce-poster-design-3.0.0/`
- 测试：`tests/ecommerce-poster-design-3.0.0/`
- 固定发布：`ecommerce-poster-design-v3.0.0`

3.0.0 的流程为：`生成 → 硬性合规 → 消费者 Agent → 美学 Agent → 完成或有限迭代`。ImageGen 仅由整体 Skill 调用，消费者和美学 Agent 都不直接生成图片。

## 历史版本

历史版本不继续堆放在 `main`，通过不可变 Tag 获取：

| 版本 | Tag |
|---|---|
| 1.0.0 | `ecommerce-poster-design-v1.0.0` |
| 1.0.0-imagegen.1 | `ecommerce-poster-design-v1.0.0-imagegen.1` |
| 2.0.1 | `ecommerce-poster-design-v2.0.1` |
| 3.0.0 | `ecommerce-poster-design-v3.0.0` |

已有历史分支和 Tag 保持原指向，不重写、不移动。安装和迭代规则见 [INSTALL.md](INSTALL.md) 与 [VERSIONS.md](VERSIONS.md)。

## 版本迭代规则

1. 从最新 `main` 创建 `feature/<version>` 或 `fix/<version>-<topic>` 分支。
2. 在分支完成实现、测试和版本文档。
3. 通过 Pull Request 合并回 `main`；`main` 只保留最新完整版本目录。
4. 合并后创建新的带注释 Tag；已发布 Tag 永不移动。
5. 旧版本从对应 Tag 安装和回退，不在 `main` 复制保存。

第三方参考图片、用户商品图、Logo、生成结果和凭据不得提交到仓库。
