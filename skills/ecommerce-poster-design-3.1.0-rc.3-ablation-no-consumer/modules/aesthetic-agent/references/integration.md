# no-consumer 接口

调用 `scripts/assemble_aesthetic_input.py` 产生只含候选与消融身份的输入，再由本模块 `scripts/score_evaluation.py` 评分。输出仍为七字段美学结果，并另存确定性 details。任何消费者字段都视为实验污染，不得加入输入、输出或上下文哈希。
