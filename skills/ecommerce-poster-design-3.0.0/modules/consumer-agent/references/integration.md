# A 1.0 → 消费者接口 A-D-2.0
对应A仓库提交f7e6e5e58494985e513deebf07d4d57a555f7e30。本包只更新D和提供组装器；A 1.0 baseline仍不调用Agent，2.0须接入。
## 来源
- source_input：A原规范化product/brand/commerce/marketing/canvas完整对象及额外Brief；每轮不删减。
- protected_content：A建立的八组对象，HC-12逐值继承；D原样往返。商品数量null保持null。
- scene_tags：style_guide.tags的audience_id/motivation_id/scenario_id；null→"null"。
- product_img：image_refs[0]；其他商品图留在source_input。
- 比例/方向：canvas宽高约分与大小比较；1080×1440必须为3:4，不能默认4:5。
- logo_ref：source_input.brand.logo_ref，空值不创造Logo。
- verified_facts不再要求独立重复字段；商品事实从source_input和保护对象核对，规则提示不能当作可展示性能。
- required_information默认已知名称、卖点、交易条件、CTA；原Brief明确清单通过brief-supplement覆盖。
- theme从原Brief补充，可空；品牌气质从原Brief补充，默认只继承brand.required_elements/forbidden_elements。
- evaluation_focus由D按固定量表/P-M-S应用，不要求A编造。
- 案例编号/来源从style_guide完整继承，只使用其通过门禁的source_case_ids；不生成假案例。
## 调用
python3 scripts/assemble_input.py --source a-normalized.json --style style-guide.json --protected protected-content.json --poster poster.png --output consumer-input.json
可选--brief-supplement supplement.json（只含theme、required_information、brand_requirements）；--previous consumer-result.json --iteration 2 --version v02。
python3 scripts/validate_input.py consumer-input.json
模型读图生成25子项draft后（格式见examples/nori-draft-result.json；禁止直接填写五维分数）：
python3 scripts/score_evaluation.py draft.json --context consumer-input.json --output consumer-result.json --details-output scoring-details.json
v1.5.0仅改变D内部草稿和计算，A-D-2.0输入输出Schema保持不变。scoring-details.json由D保存，不增加A必填字段。A若负责执行模型调用，也需更新消费者提示词和内部draft组装，不能沿用旧草稿。旧评分结果保留历史，新版本评估重新建立基线。
## A动作表
| next_route | A动作 |
|---|---|
| poster_generation_skill | 定向重画→完整HC-01至HC-12→消费者复评；硬检查失败不进入D |
| aesthetic_agent | 美学开关为 true 时组装固定输入并调用；只有美学也通过才完成输出 |
| complete_input | 停止自动重画，记录blocked_stage=consumer_input；需扩展A blocked定义以包含生成后缺信息 |
## 回退与终止
A逐轮传回previous_result与累计locked_dimensions，保留所有版本及最后消费者通过版。
previous_result使用最近一次完成五维评价的正常结果。complete_input不是新的评价基线；补全后恢复原正常结果与累计锁，不能用空context_hash覆盖历史。
新版本regressed_dimensions非空时优先修复回退项，禁止覆盖最后通过版。
A统一计数所有重画（硬合规、消费者、美学），沿用配置上限而不在每次Agent调用时重置。
建议同一锁定维度连续两轮回退触发人工复核；上限耗尽输出degraded及最佳合规候选、未解决项，绝不改为pass。
锁定阈值14只防止跌破合格线，不能检测18→15的轻微退步；日志保留五维差值供分析。
美学Agent需要同样接收八组保护对象；两者的事实对象必须相等，冲突时blocked，不能字符串拼接。
