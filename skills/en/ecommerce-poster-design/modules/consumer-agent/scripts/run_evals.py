"""Behavioral interface tests; no claim of model/visual evaluation."""
from copy import deepcopy
from common import load_json, root_dir, DIMENSIONS
from assemble_input import assemble
from assemble_input import normalize_supplement
from validate_input import validate
from score_evaluation import score_result, validate_output, error_result

root=root_dir()
c=load_json(root/"examples/a-to-d-input.json")
rubric=load_json(root/"assets/rubric.json")
d={"subcriteria":{row[0]:{"level":4,"evidence":"接口测试证据，不是实际图像评价"} for rows in rubric["subcriteria"].values() for row in rows},"critical_issues":[],"problem_list":[],"modify_suggestion":[],"confidence":0.9}
checks=0
def check(condition):
    global checks
    assert condition
    checks+=1
check(not validate(c))
r=score_result(d,c)
check(r["pass"] and r["score"]==100 and not validate_output(r))
check(r["protected_content"]==c["protected_content"])
# Provenance reminders alone do not invalidate complete evaluation content.
pending=deepcopy(c)
pending["source_input"]["original_brief"]={"handoff_provenance":{"protected_content_status":"按旧输入和PDF重建，生产联调前待A确认"}}
pending["style_guide"]["needs_human_review"]=True
check(not validate(pending))
pr=score_result(d,pending)
check(pr["score"]==100 and pr["meta"]["input_errors"]==[] and pr["protected_content"]==pending["protected_content"])
conflict=deepcopy(pending)
conflict["protected_content"]["price_and_unit"]=["错误价格"]
check(score_result(d,conflict)["next_route"]=="complete_input")
n=deepcopy(c)
n["style_guide"]["tags"]["audience_id"]=None;n["evaluation_context"]["scene_tags"][0]="null"
check(not validate(n) and score_result(d,n)["meta"]["unknown_dimensions"]==["population_scene_fit"])
bad=deepcopy(c);del bad["source_input"]["commerce"]["promotion_period"]
e=score_result(d,bad)
check(e["score"] is None and e["next_route"]=="complete_input" and not validate_output(e))
check(e["protected_content"]==c["protected_content"])
second=assemble(c["source_input"],c["style_guide"],c["protected_content"],"poster-v02.png","v02",2,r)
check(not validate(second) and second["loop_state"]["locked_dimensions"]==r["locked_dimensions"])
reg=deepcopy(d)
for row in rubric["subcriteria"]["offer_visibility"]: reg["subcriteria"][row[0]]["level"]=2
reg["problem_list"]=["价格可见度回退"];reg["modify_suggestion"]=["价格区；增大字号；保留原价；验收：可清晰发现"]
rr=score_result(reg,second)
check(not rr["pass"] and rr["regressed_dimensions"]==["offer_visibility"] and rr["next_route"]=="poster_generation_skill")
check(rr["locked_dimensions"]==r["locked_dimensions"])
unread=deepcopy(d);unread["image_error"]="图像不可读取"
ue=score_result(unread,second)
check(ue["locked_dimensions"]==r["locked_dimensions"] and ue["protected_content"]==r["protected_content"] and not validate_output(ue))
changed=deepcopy(second);changed["source_input"]["marketing"]["goal"]="更换目标"
check(bool(validate(changed)))
altered=deepcopy(d);altered["protected_content"]=[]
try: score_result(altered,c)
except ValueError: check(True)
else: raise AssertionError("D altered protection accepted")
hard=deepcopy(d)
hard["critical_issues"]=["价格冲突"];hard["problem_list"]=["价格冲突"];hard["modify_suggestion"]=["恢复原始价格"]
check(score_result(hard,c)["hard_fail"] and not score_result(hard,c)["pass"])
square=deepcopy(c["source_input"]);square["canvas"]["width"]=900;square["canvas"]["height"]=900
sq=assemble(square,c["style_guide"],c["protected_content"],"square.png")
check(sq["evaluation_context"]["aspect_ratio"]=="1:1" and sq["evaluation_context"]["orientation"]=="square")
check(c["evaluation_context"]["aspect_ratio"]=="3:4")
multi=deepcopy(c["source_input"]);multi["product"]["image_refs"].append("second-product.png")
mc=assemble(multi,c["style_guide"],c["protected_content"],"multi.png")
check(len(mc["source_input"]["product"]["image_refs"])==2 and mc["evaluation_context"]["product_img"]==multi["product"]["image_refs"][0])
check(mc["source_input"]["brand"]["logo_ref"]=="")
supplement=normalize_supplement({"theme":"新品首发","brand_tone":"克制高级","test_requirement":["价格逐字一致","Logo 不得重绘"]})
check(supplement=={"theme":"新品首发","required_information":["价格逐字一致","Logo 不得重绘"],"brand_requirements":["克制高级"]})
alias_context=assemble(c["source_input"],c["style_guide"],c["protected_content"],"alias.png",**supplement)
check(alias_context["evaluation_context"]["brand_requirements"]==["克制高级"] and alias_context["evaluation_context"]["required_information"]==["价格逐字一致","Logo 不得重绘"])
try: normalize_supplement({"unexpected_field":"x"})
except ValueError as exc: check("unsupported brief supplement fields" in str(exc))
else: raise AssertionError("unknown brief supplement field accepted")
quantity=deepcopy(c);quantity["protected_content"]["product_quantity"]=2
check(bool(validate(quantity)))
cross=deepcopy(second);cross["loop_state"]["previous_result"]["request_id"]="OTHER"
check(bool(validate(cross)))
from subcriteria import calculate
def rejected(draft):
    try: score_result(draft,c)
    except ValueError: return True
    return False
missing=deepcopy(d);del missing["subcriteria"]["D1_1"];check(rejected(missing))
extra=deepcopy(d);extra["subcriteria"]["D9_1"]={"level":4,"evidence":"多余"};check(rejected(extra))
for value in (True,1.5,5,-1):
    bad=deepcopy(d);bad["subcriteria"]["D1_1"]["level"]=value;check(rejected(bad))
empty=deepcopy(d);empty["subcriteria"]["D1_1"]["evidence"]=" ";check(rejected(empty))
direct=deepcopy(d);direct["dimension_scores"]=dict.fromkeys(DIMENSIONS,20);check(rejected(direct))
na=deepcopy(d);na["subcriteria"]["D3_1"]={"level":None,"evidence":"无价格","not_applicable_reason":"任务不要求"};check(rejected(na))
half=deepcopy(d);half["subcriteria"]["D1_1"]["level"]=2
check(calculate(half,c)[0]["product_recognition"]==18)
anchors=[[4,4,4,4,4],[4,4,3,3,3],[4,4,3,4,4],[3,4,2,3,3],[4,3,3,2,3]]
nori=deepcopy(d)
for rows,levels in zip(rubric["subcriteria"].values(),anchors):
    for row,level in zip(rows,levels): nori["subcriteria"][row[0]]["level"]=level
check(calculate(nori,c)[0]==dict(zip(DIMENSIONS,[20,17,19,15,15])))
check(calculate(nori,c)[2]["score"]==86)
fact=deepcopy(d);fact["subcriteria"]["D3_1"]["level"]=0;check(rejected(fact))
nonpromo=deepcopy(c)
nonpromo["source_input"]["commerce"]["price_text"]=""
nonpromo["protected_content"]["price_and_unit"]=[]
nonpromo["evaluation_context"]["required_information"]=[]
nd=deepcopy(d)
for key in ("D3_1","D3_2"): nd["subcriteria"][key]={"level":None,"evidence":"无价格要求","not_applicable_reason":"非价格展示任务"}
check(score_result(nd,nonpromo)["dimension_scores"]["offer_visibility"]==20)
print("PASS:",checks,"A-D and subcriteria assertions; visual loop not exercised")
