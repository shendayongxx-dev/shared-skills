"""Generate synthetic interface examples; not visual evaluation."""
from copy import deepcopy
from common import load_json, write_json, root_dir
from score_evaluation import score_result
from assemble_input import assemble

root=root_dir(); c=load_json(root/"examples/nori-input.json")
d=load_json(root/"examples/nori-draft-result.json")
write_json(root/"examples/consumer-output-iterate.json",score_result(d,c))
p=deepcopy(d)
for item in p["subcriteria"].values(): item["level"]=4
p["problem_list"]=[];p["modify_suggestion"]=[]
r=score_result(p,c);write_json(root/"examples/consumer-output-pass.json",r)
e=c["evaluation_context"]
second=assemble(c["source_input"],c["style_guide"],c["protected_content"],"poster-v02.png","v02",2,r,e["theme"],e["required_information"],e["brand_requirements"])
write_json(root/"examples/consumer-regression-input.json",second)
reg=deepcopy(p)
for i in range(1,6): reg["subcriteria"]["D3_"+str(i)]["level"]=2
reg["problem_list"]=["演示：交易可见度回退"]
reg["modify_suggestion"]=["对象：交易区；操作：恢复字号与对比度；保留价格日期CTA；验收：信息清楚且维度达到14分"]
write_json(root/"examples/consumer-output-regression.json",score_result(reg,second))
bad=deepcopy(d);bad["image_error"]="演示：海报不可读，请提供可访问图片"
write_json(root/"examples/consumer-output-complete-input.json",score_result(bad,c))
