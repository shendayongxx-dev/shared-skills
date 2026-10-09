"""Deterministic scoring; output protects A's eight-group object unchanged."""
import argparse, json
from copy import deepcopy
from common import DIMENSIONS, DIMENSION_LABELS, load_json, root_dir, write_json
from schema_check import check
from validate_input import validate, context_hash
from subcriteria import calculate

def error_result(errors, context):
    # Preserve recoverable state even on unreadable poster or incomplete input.
    safe=context if isinstance(context,dict) else {}
    pc=safe.get("protected_content")
    schema=load_json(root_dir()/"assets/schemas/output.schema.json")["properties"]["protected_content"]
    if check(pc,schema): pc=None
    old=safe.get("loop_state",{}).get("locked_dimensions",[])
    old=[d for d in old if d in DIMENSIONS] if isinstance(old,list) else []
    return {"schema_version":"A-D-2.0","request_id":str(safe.get("request_id","")),"version_id":str(safe.get("loop_state",{}).get("version_id","")),
            "agent_name":"consumer_agent","score":None,"pass":False,"dimension_scores":None,
            "problem_list":["输入或图像无法完成评价"],"modify_suggestion":["补充meta.input_errors列出的信息；保留原始保护对象与累计锁"],
            "protected_content":deepcopy(pc),"locked_dimensions":list(dict.fromkeys(old)),"regressed_dimensions":[],
            "hard_fail":False,"next_route":"complete_input",
            "meta":{"judge_dimensions":[],"confidence":0,"input_errors":errors,"unknown_dimensions":[],"context_hash":"","dimension_evidence":{}}}

def score_result(draft, context):
    errors=validate(context)
    if errors: return error_result(errors,context)
    if draft.get("input_errors"): return error_result(draft["input_errors"],context)
    if draft.get("image_error"): return error_result([draft["image_error"]],context)
    scores,evidence,_=calculate(draft,context)
    if set(scores)!=set(DIMENSIONS) or any(type(v) is not int or not 0<=v<=20 for v in scores.values()):
        raise ValueError("five integer dimension scores 0–20 required")
    if set(evidence)!=set(DIMENSIONS) or any(not isinstance(v,str) or not v.strip() for v in evidence.values()):
        raise ValueError("visible evidence required for every dimension")
    problems=draft["problem_list"]; suggestions=draft["modify_suggestion"]
    if not isinstance(problems,list) or not isinstance(suggestions,list) or len(problems)!=len(suggestions) or len(problems)>3:
        raise ValueError("paired string feedback, maximum 3")
    if any(not isinstance(x,str) or not x.strip() for x in problems+suggestions): raise ValueError("feedback must be nonempty strings")
    critical=draft.get("critical_issues",[])
    if not set(critical).issubset(problems): raise ValueError("critical issues must appear in problems")
    old=context["loop_state"]["locked_dimensions"]
    regressions=[d for d in old if scores[d]<14]
    total=sum(scores.values()); passed=total>=80 and min(scores.values())>=14 and not critical and not regressions
    if not passed and not problems: raise ValueError("failed evaluation needs actionable feedback")
    locks=list(dict.fromkeys(old+([] if critical else [d for d in DIMENSIONS if scores[d]>=14])))
    unknown=[d for d in DIMENSIONS if d=="population_scene_fit" and "null" in context["evaluation_context"]["scene_tags"]]
    confidence=draft["confidence"]
    if type(confidence) not in (int,float) or not 0<=confidence<=1: raise ValueError("confidence 0–1 required")
    if "protected_content" in draft and draft["protected_content"]!=context["protected_content"]:
        raise ValueError("D must not edit A protected_content")
    result={"schema_version":"A-D-2.0","request_id":context["request_id"],"version_id":context["loop_state"]["version_id"],
            "agent_name":"consumer_agent","score":total,"pass":bool(passed),"dimension_scores":scores,"problem_list":problems,
            "modify_suggestion":suggestions,"protected_content":deepcopy(context["protected_content"]),
            "locked_dimensions":locks,"regressed_dimensions":regressions,"hard_fail":bool(critical),
            "next_route":"aesthetic_agent" if passed else "poster_generation_skill",
            "meta":{"judge_dimensions":list(DIMENSION_LABELS),"confidence":confidence,"input_errors":[],
                    "unknown_dimensions":unknown,"context_hash":context_hash(context),"dimension_evidence":evidence}}
    errors=validate_output(result)
    if errors: raise ValueError(errors)
    return result

def validate_output(result):
    return check(result,load_json(root_dir()/"assets/schemas/output.schema.json"))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("--context",required=True);p.add_argument("--output");p.add_argument("--details-output");a=p.parse_args()
    draft=load_json(a.input); context=load_json(a.context)
    result=score_result(draft,context)
    if a.details_output:
        details=calculate(draft,context)[2] if result["score"] is not None else {"score":None,"input_errors":result["meta"]["input_errors"]}
        details.update(request_id=result["request_id"],version_id=result["version_id"],context_hash=result["meta"]["context_hash"])
        write_json(a.details_output,details)
    if a.output: write_json(a.output,result)
    else: print(json.dumps(result,ensure_ascii=False,indent=2))
