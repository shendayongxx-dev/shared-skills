---
name: 02-consumer-agent-skill
description: Evaluate e-commerce posters using A-group complete briefs and C-group locked P-M-S tags. Return 0–100 scores, actionable feedback, unchanged eight-group protected content and regression locks.
license: MIT
metadata:
  author: xyu
  version: 1.5.3
  last_reviewed: 2026-10-05
---
# 消费者 Agent：A-D-2.0 接口
只评价一次并输出纯JSON。A管理生成、硬合规、日志、重试和Agent开关；C提供分类资产及规则。读取references/integration.md了解组装和路由；读取assets/schemas/input.schema.json、output.schema.json了解正式合同。
## 完整输入
source_input保留A的完整规范化输入及额外原始Brief字段。style_guide保留C选择结果。protected_content必须是A的八组对象，包含product_quantity的整数或null。evaluation_context由scripts/assemble_input.py确定性组装；显式主题、额外展示要求和品牌气质从原任务补充，不能从案例或风格推造事实。
product_img默认第一张主图，但查看source_input.product.image_refs全部相关参考。品牌无logo_ref时只评已有品牌文字识别，不要求创建Logo。
P-M-S顺序固定，允许字符串"null"；与style_guide.tags逐项一致。空维度只按已知Brief和标签评价，不凭空补分类、不因未知自动扣分或满分；记录不确定性。已知项与Brief冲突时返回complete_input要求A/C核对，不强迫改变合法的Brief场景。
## 评分
先盲观察当前图，再对照完整输入。读取references/rubric.md与evaluation-lenses.md。
五维20分，总分100；模型必须提交assets/rubric.json定义的25个subcriteria，每项level为0–4整数及非空evidence。不得直接填写dimension_scores或dimension_evidence；汇总器计算二者，使用十进制四舍五入。读取references/subcriteria-anchors.md选档。P决定表达门槛，M决定利益证据优先级，S决定使用关系，不改变总权重。案例无人工评分标注时只作表达参考。
pass=总分>=80且每维>=14且无hard_fail且无锁定维度回退。模型评分是模拟判断。
每次选档同时读取references/candidate-boundaries.md：其中的相邻档位条件用于判断，案例ID仅为未经完整人工标注的候选表达参考，不能转移事实或直接决定分数。D5关键疑虑须在查看海报前从任务确定；看图后先记录证据，再比较边界。不满足4档增强条件不得因整体好看升级；重要事实缺输入仍返回complete_input，不当作低档。1.5.1边界更新后建立新评分轨道，不能与旧量表结果直接解释为海报改善。
明确事实冲突、商品/Logo改造、必需信息缺失为hard_fail并写入critical_issues；事实未提供为输入问题。
## 可执行反馈
通过后的残余问题建议标为“可选优化”，不触发消费者重画；仍按pass与next_route进入美学流程。未通过的建议标为“本轮必改”。不新增输出字段。
problem_list与modify_suggestion一一对应，最多3个优先问题；每条建议包括“对象/位置；操作；准确内容；保护项；验收标准”。所有失败必须有动作，未覆盖问题下一轮继续处理。
protected_content由汇总器从输入深复制，D不得增删、合并、翻译、重排其值。事实保护与维度保护分开；资产位置/比例可在Brief允许范围内优化。
locked_dimensions继承旧锁加本轮达标项，最低分14。每轮重新检查全部维度，旧锁跌破14写入regressed_dimensions。硬失败不新增锁，旧锁保留。输入错误也保留可恢复的保护对象和旧锁。
context_hash冻结Brief、C结果、保护内容及补充要求；更改这些内容应建立新测试轨道，不能混入旧版本比较。
## 异常与路由
先区分“评价必需内容问题”与“交接来源待确认”。评价以调用者本次提供的商品事实、完整Brief、八组对象和锁定标签为比较基准，不代表D独立认证性能或批准生产交接。
仅必需输入缺失、字段/事实相互矛盾、标签与Brief存在影响判断的冲突、图像不可读，或海报的重要新增主张缺少输入支持且无法判定是否错误时，返回score=null、dimension_scores=null、pass=false、next_route=complete_input。缺失保护对象为null；完整对象原样保留；所有阻断原因列入meta.input_errors，写明无法判断什么以及缺少/冲突的具体值。
handoff_provenance中的“旧输入/PDF重建、尚未A逐值确认”、needs_human_review=true、未提供C分类资产版本或案例引用，仅表示来源/交接待确认；单独出现不得进入draft.input_errors，不得停止评分，不要求额外证明已给的商品事实。只要本次必需内容完整、内部一致且标签不冲突，按给定基准完成测试评分。相关evidence可注明“按本次给定事实/标签评价，生产交接待A/C确认”，不把来源提醒作为海报问题、不自动扣分、不宣称生产验收通过。
生产联调由A在进入正式自动迭代前确认重建保护对象和分类选择；D评分pass只代表本次海报消费者阈值达标，不覆盖A的交接确认。不得删除来源提醒、将needs_human_review改false或伪造A/C确认来绕过检查。以上为同一接口的处理边界，不新增测试模式字段。
正常失败：next_route=poster_generation_skill。通过：next_route=aesthetic_agent，A按美学开关决定调用或结束。每次重画先通过完整硬检查再调用D。
## 脚本
scripts/assemble_input.py组装A资产。scripts/validate_input.py校验schema与语义。
模型draft包含subcriteria、critical_issues、problem_list、modify_suggestion、confidence；旧版五维直接分数草稿不再接受。输入问题或读图失败仍用input_errors/image_error提前返回。scripts/score_evaluation.py draft.json --context input.json --output result.json --details-output scoring-details.json确定性汇总；明细留D内部，A-D-2.0正式输入输出Schema不变。
scripts/run_evals.py执行接口回归。实际读图与海报重画须另行视觉联调，脚本不会自动调用模型。
