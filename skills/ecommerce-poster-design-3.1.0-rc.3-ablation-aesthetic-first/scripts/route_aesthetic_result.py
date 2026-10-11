#!/usr/bin/env python3
"""Validate and route an aesthetic-first deterministic result."""
import argparse, json
from copy import deepcopy
from pathlib import Path

MINIMUMS = {"composition":16,"hierarchy":16,"color":12,"typography":16,"consistency":12,"finish":8}

def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def require(ok, msg):
    if not ok: raise ValueError(msg)

def route(result, details, workflow, version, attempts):
    require(workflow.get("schema_version") == "A-D-AESTHETIC-3.0-AF", "aesthetic-first workflow required")
    require(workflow.get("evaluation_phase") == "pre_consumer", "wrong evaluation phase")
    candidate = workflow["candidate"]
    require(result.get("agent_name") == "aesthetic_agent", "aesthetic result required")
    require(result.get("protected_content") == candidate.get("protected_content"), "protected content changed")
    require(version.get("evaluation_order") == ["aesthetic_agent","consumer_agent"], "wrong evaluation order")
    maximum = version["retry_policy"]["max_redraw_attempts"]
    common = {"request_id":candidate["request_id"],"version_id":candidate["loop_state"]["version_id"],"aesthetic_score":result.get("score"),"global_redraw_attempts":attempts,"max_redraw_attempts":maximum,"protected_content":deepcopy(candidate["protected_content"])}
    if result.get("score") is None:
        return {**common,"status":"blocked","action":"complete_aesthetic_input"}
    scores = details.get("dimension_scores", {})
    require(set(scores) == set(MINIMUMS), "six aesthetic dimensions required")
    calculated = result["score"] >= 80 and all(scores[k] >= v for k,v in MINIMUMS.items()) and not details.get("critical_issues")
    require(calculated == result.get("pass"), "aesthetic pass contradicts details")
    if calculated:
        return {**common,"status":"in_progress","action":"invoke_consumer_agent","locked_aesthetic_dimensions":deepcopy(scores),"aesthetic_context_hash":details.get("context_hash")}
    if attempts >= maximum:
        return {**common,"status":"degraded","action":"return_best_eligible_candidate","reason":"global redraw limit exhausted"}
    editable = [k for k,v in MINIMUMS.items() if scores[k] < v]
    require(editable, "failed result without below-threshold dimension needs scope review")
    locked = [k for k in MINIMUMS if k not in editable]
    contract = {"contract_version":"aesthetic-edit-lock/1.1-af","generation_mode":"local_edit_only","baseline_candidate":{"request_id":candidate["request_id"],"version_id":candidate["loop_state"]["version_id"],"poster_image":candidate["poster_image"],"context_hash":details.get("context_hash")},"editable_aesthetic_dimensions":editable,"locked_aesthetic_dimensions":locked,"locked_consumer_dimensions":{},"immutable_protected_content":deepcopy(candidate["protected_content"]),"advisory_instructions":deepcopy(result.get("modify_suggestion",[])),"required_post_generation_checks":["HC-01..HC-12","aesthetic_agent","consumer_agent_if_aesthetic_passes"]}
    return {**common,"status":"in_progress","action":"regenerate_then_hard_compliance_then_aesthetic","next_global_redraw_attempt":attempts+1,"generation_edit_contract":contract}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("result"); p.add_argument("--details",required=True); p.add_argument("--workflow-input",required=True); p.add_argument("--config",default="assets/config/version.json"); p.add_argument("--redraw-attempts",type=int,required=True); p.add_argument("--output"); a=p.parse_args()
    try:
        value=route(load(a.result),load(a.details),load(a.workflow_input),load(a.config),a.redraw_attempts); rendered=json.dumps(value,ensure_ascii=False,indent=2)+"\n"
        Path(a.output).write_text(rendered,encoding="utf-8") if a.output else print(rendered,end="")
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as exc: raise SystemExit("aesthetic-first router: "+str(exc))
if __name__ == "__main__": main()
