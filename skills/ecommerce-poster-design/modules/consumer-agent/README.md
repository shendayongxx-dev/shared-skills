# 02消费者Agent-skill

从目标消费者的角度评估电商海报，并输出主流程可以执行的修改建议。

**当前版本：v1.5.3｜输入输出接口：A-D-2.0**

v1.5.3收紧D4_2：按主要信息区的利益优先级与整体一致性区分3/4档，不要求购买动机占据主标题。同任务冻结D5疑虑清单；通过后的建议标为可选优化，不要求消费者流程重画。A-D合同、权重和通过阈值不变，需重新建立评分基线。

v1.5.2区分必需输入错误与交接来源提醒：完整一致的测试输入不会仅因保护对象来自重建、needs_human_review=true或缺C资产版本而停止评分。按本次给定事实和标签评价，不代表独立认证产品事实或批准生产交接；正式联调仍需A/C确认来源。D5档位、量表权重与接口保持1.5.1规则。

v1.5.1加入五维25子项相邻档位边界与候选案例参考，并收紧D5证据、品牌身份、疑虑回应和行动理由的选档条件。候选案例不是人工金标准；权重、计算公式、通过阈值和A-D接口不变。参见[档位边界](references/candidate-boundaries.md)。量表更新后需重新建立评分基线，不能将与旧版分差直接当成海报改进。

消费者能看懂商品吗？能理解卖点带来的好处吗？价格和活动条件是否清楚？是否适合指定人群和使用场景？是否有理由相信并行动？本项目围绕这些问题评价，不是单纯判断画面好不好看。

## 这个项目做什么

接收海报、商品参考图、完整设计任务和上游分类标签，输出固定JSON：评分、通过判断、问题、修改建议及迭代保护信息。

仓库提供模型评价指令、评分规则、接口合同和计算校验脚本。它**不独立调用模型API、不生成海报、不控制迭代**，也不代替美学评价或真人消费者测试；实际读图模型和海报生成模块由主流程接入。

## 在设计流程中的位置

主流程生成海报并完成硬合规检查后，再交给消费者Agent。

- 不通过：主流程按建议修改，重新做硬检查，再送消费者复评。
- 通过：进入美学Agent；未启用美学模块时，由主流程按约定完成当前流程。
- 输入不足或图片不可读：停止自动重画，先补全输入。

美学修改后也要重新检查消费者维度，不能把旧版通过结论直接套到新海报上。

团队分工：A组负责主流程与生成，C组提供分类及案例库，本仓库是D组的消费者评估组件。版本保存、硬合规、迭代上限和异常处理由A组管理。

## 怎么评分

| 维度 | 消费者要回答的问题 | 满分 |
|---|---|---:|
| 商品与品牌识别 | 我知道卖什么、哪个品牌吗？ | 20 |
| 核心利益与卖点说服力 | 我知道它有什么用、有什么好处吗？ | 20 |
| 价格、促销与交易信息 | 多少钱、什么时候有效、下一步做什么？ | 20 |
| 人群—动机—场景适配 | 它是否适合我的需求和使用环境？ | 20 |
| 信任与行动驱动 | 我有理由相信它并采取行动吗？ | 20 |

每维5个子项，共25项。模型逐项提供0–4档及可见证据，程序计算：

`子项贡献 = 子项满分 × 档位 ÷ 4`

保留子项小数，维度汇总后四舍五入，再将五维整数分相加。不接受模型直接填写五维分数。非促销任务按规则处理不适用交易项，不因任务未要求价格而扣分。

通过条件：**总分≥80，每维≥14，无硬失败，且已锁定维度没有跌破14分。**阈值是工程初值，仍需人工样本校准。

完整规则见[五维评分说明](references/rubric.md)、[25项选档标准](references/subcriteria-anchors.md)及[权重配置](assets/rubric.json)。

### 人群、动机、场景如何影响评分

P为人群、M为购买动机、S为使用场景，来自上游分类；消费者Agent不重新分类。它们改变判断重点，不改变五维各20分的权重。

例如“职场通勤／品质信任／通勤车载”会重点检查快速理解、可靠材质与性能依据，以及移动使用关系。场景可以通过文案表达，不强制添加人物、汽车或特定背景。案例只作参考；无人工评分标注时，不能因为风格相似就给高分。

## 输入与输出

### 输入：保留完整设计任务

不能只传海报、卖点和价格。正式输入包含：当前海报、商品参考图、完整商品与品牌信息、交易及营销要求、画布要求、上游分类结果、八组保护内容，以及主题、必需展示清单、品牌约束和迭代状态。

查看[完整输入示例](examples/nori-input.json)和[输入Schema](assets/schemas/input.schema.json)。图片路径只是引用；必须让模型实际读取图片，不能只发送无法访问的本地路径。

### 输出：主流程读取的固定JSON

| 字段 | 用途 |
|---|---|
| `score`、`dimension_scores` | 总分、五维分；未完成评价时为null |
| `pass` | 是否通过当前消费者评价 |
| `problem_list`、`modify_suggestion` | 最多3个配对问题和可执行建议；通过时可给可选优化 |
| `protected_content` | 八组事实保护对象，原样返回 |
| `locked_dimensions`、`regressed_dimensions` | 已达标维度与本轮跌破保护线的维度 |
| `hard_fail` | 已确认事实错误、商品改造或必需信息缺失等硬失败 |
| `next_route` | 重画、进入美学评价或补输入 |
| `meta` | 证据、置信度及上下文标识等分析信息 |

完整合同见[输出Schema](assets/schemas/output.schema.json)。查看[通过](examples/consumer-output-pass.json)、[需重画](examples/consumer-output-iterate.json)、[补输入](examples/consumer-output-complete-input.json)、[维度回退](examples/consumer-output-regression.json)四种示例。它们是模拟接口数据，不是真实海报评分。

## 使用步骤

在仓库根目录运行以下命令，需要Python 3，无需额外第三方Python库。

### 1. 验证组件

```bash
python3 scripts/run_evals.py
python3 scripts/validate_input.py examples/nori-input.json
```

当前包含33项回归检查，覆盖计算、输入错误、保护内容及维度回退。它不调用模型，也不测试真实海报重画。

### 2. 组装实际输入

将示例源文件替换为主流程的实际资料，海报替换为可读取的实际图片：

```bash
python3 scripts/assemble_input.py --source examples/nori-a-normalized.json --style examples/nori-style-guide.json --protected examples/nori-a-protected.json --brief-supplement examples/nori-brief-supplement.json --poster poster-v01.png --output consumer-input.json
python3 scripts/validate_input.py consumer-input.json
```

主题、展示清单和品牌约束必须来自原任务，不得从案例倒推事实。示例不能替代A实际的保护对象和分类结果。

### 3. 模型读图，程序计算

给支持图像输入的模型加载[SKILL.md](SKILL.md)及其评分参考，并提供完整输入、海报和商品参考图。模型先生成25子项内部草稿，格式见[草稿示例](examples/nori-draft-result.json)。然后运行：

```bash
python3 scripts/score_evaluation.py model-draft.json --context consumer-input.json --output consumer-result.json --details-output scoring-details.json
```

`consumer-result.json`交给主流程；`scoring-details.json`由消费者评估侧保存，记录25项权重、档位、证据及计算过程。内部草稿不是正式A-D输出。

### 4. 按路由继续

| `next_route` | 主流程动作 |
|---|---|
| `poster_generation_skill` | 定向修改→硬合规检查→消费者复评 |
| `aesthetic_agent` | 进入美学评价，或按模块开关处理 |
| `complete_input` | 停止重画，补全错误清单中的输入或图片 |

下一轮组装输入时使用`--previous consumer-result.json --iteration 2 --version v02`继承历史状态。完整来源和循环规则见[接口接入说明](references/integration.md)。

## 防止反复修改、来回退步

事实保护和维度锁定是两件事：

- 事实保护：商品身份、品牌、价格、活动条件等不能被重画改坏，八组保护对象原样传递。
- 维度锁定：达标项以后仍要评，不能跌破14分；不是禁止所有修改，也不是检测所有细微退步，例如18→15不会触发回退。

主流程保存最后通过版，统一累计重画次数；超过上限仍有问题时报告未解决项，不强行改成通过。

## 当前能力与限制

- v1.5.0已支持25子项自动计算、固定JSON输出和防回退状态处理。正式A-D-2.0输入输出不变，旧版直接填写五维分数的内部草稿不再接受。
- 主流程1.0不能仅凭本仓库自动完成Agent闭环，仍需接入读图模型、生成模块和路由。
- 程序保证结构与计算，不保证模型判断一定正确；关键输入缺失时应补全，不猜测评分。
- 评分是消费者视角的模型模拟，不代表真实购买行为、实际产品认证、最终交付或双语任务全部完成。
- 有效性需用人工对照、同图重复评分、单变量缺陷及真实重画前后对比验证，见[测试建议](evals/consumer-evaluation-agent.eval.md)。

## 许可

[MIT](LICENSE)
