#!/usr/bin/env python3
"""Route a consumer result after a bound aesthetic pass in the AF experiment."""
import argparse, json
from copy import deepcopy
from pathlib import Path

CDIMS={"product_recognition","benefit_clarity","offer_visibility","population_scene_fit","purchase_drive"}
AMINS={"composition":16,"hierarchy":16,"color":12,"typography":16,"consistency":12,"finish":8}

def load(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def require(ok,msg):
    if not ok: raise ValueError(msg)

def route(result,aesthetic,details,version,attempts):
    require(version.get("evaluation_order")==["aesthetic_agent","consumer_agent"],"wrong evaluation order")
    require(result.get("schema_version")=="A-D-2.0" and result.get("agent_name")=="consumer_agent","consumer result required")
    require(aesthetic.get("agent_name")=="aesthetic_agent" and aesthetic.get("pass") is True,"passing aesthetic result required")
    scores_a=details.get("dimension_scores",{})
    require(set(scores_a)==set(AMINS) and all(scores_a[k]>=v for k,v in AMINS.items()) and not details.get("critical_issues"),"aesthetic details do not establish six locks")
    require(details.get("request_id")==result.get("request_id") and details.get("version_id")==result.get("version_id"),"results belong to different candidates")
    require(aesthetic.get("protected_content")==result.get("protected_content"),"protected content changed between agents")
    maximum=version["retry_policy"]["max_redraw_attempts"]
    common={"request_id":result.get("request_id"),"version_id":result.get("version_id"),"consumer_score":result.get("score"),"dimension_scores":result.get("dimension_scores"),"locked_dimensions":result.get("locked_dimensions",[]),"locked_aesthetic_dimensions":deepcopy(scores_a),"aesthetic_context_hash":details.get("context_hash"),"protected_content":deepcopy(result.get("protected_content")),"global_redraw_attempts":attempts,"max_redraw_attempts":maximum}
    if result.get("next_route")=="complete_input": return {**common,"status":"blocked","action":"complete_input"}
    cs=result.get("dimension_scores",{}); reg=result.get("regressed_dimensions") or []
    if result.get("pass") is True:
        require(result.get("next_route")=="aesthetic_agent","consumer compatibility route changed")
        require(isinstance(result.get("score"),int) and result["score"]>=80 and set(cs)==CDIMS and all(cs[k]>=14 for k in CDIMS) and result.get("hard_fail") is False and not reg,"invalid consumer pass")
        return {**common,"status":"in_progress","action":"invoke_final_quality_gate","route_mapping":"aesthetic_agent->final_quality_gate"}
    require(result.get("next_route")=="poster_generation_skill","failed consumer route invalid")
    if attempts>=maximum: return {**common,"status":"degraded","action":"return_best_eligible_candidate","reason":"global redraw limit exhausted"}
    failed=[k for k in CDIMS if not isinstance(cs.get(k),int) or cs[k]<14]
    contract={"contract_version":"consumer-edit-lock/1.0-af","generation_mode":"local_edit_only","baseline_candidate":{"request_id":result["request_id"],"version_id":result["version_id"],"poster_image":details["poster_image"],"aesthetic_context_hash":details.get("context_hash")},"editable_consumer_dimensions":sorted(failed),"locked_consumer_dimensions":sorted(CDIMS-set(failed)),"locked_aesthetic_dimensions":deepcopy(scores_a),"immutable_protected_content":deepcopy(result["protected_content"]),"advisory_instructions":deepcopy(result.get("modify_suggestion",[])),"required_post_generation_checks":["HC-01..HC-12","aesthetic_agent_against_last_pass_baseline","reject_on_aesthetic_regression","consumer_agent_if_aesthetic_passes"]}
    return {**common,"status":"in_progress","action":"regenerate_then_full_aesthetic_first_pipeline","next_global_redraw_attempt":attempts+1,"generation_edit_contract":contract}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("result");p.add_argument("--aesthetic-result",required=True);p.add_argument("--aesthetic-details",required=True);p.add_argument("--config",default="assets/config/version.json");p.add_argument("--redraw-attempts",type=int,required=True);p.add_argument("--output");a=p.parse_args()
    try:
        v=route(load(a.result),load(a.aesthetic_result),load(a.aesthetic_details),load(a.config),a.redraw_attempts);s=json.dumps(v,ensure_ascii=False,indent=2)+"\n";Path(a.output).write_text(s,encoding="utf-8") if a.output else print(s,end="")
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as exc: raise SystemExit("consumer AF router: "+str(exc))
if __name__=="__main__": main()
