#!/usr/bin/env python3
"""Validate and route an aesthetic result without consumer artifacts."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

SCHEMA = "A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER"
DIMENSION_MINIMUMS = {
    "composition": 16, "hierarchy": 16, "color": 12,
    "typography": 16, "consistency": 12, "finish": 8,
}
AESTHETIC_LABELS = [
    "构图与视觉平衡", "视觉层级", "配色与对比", "字体与排版",
    "风格与场景适配", "材质光影与细节完成度",
]


def context_hash(workflow):
    candidate = workflow["candidate"]
    payload = json.dumps({
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "protected_content": candidate["protected_content"],
        "ablation": workflow["ablation"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_workflow(workflow):
    if not isinstance(workflow, dict) or set(workflow) != {"schema_version", "ablation", "candidate"}:
        raise ValueError("exact no-consumer workflow fields required")
    if workflow["schema_version"] != SCHEMA:
        raise ValueError("invalid no-consumer workflow schema")
    if workflow["ablation"] != {"id": "no-consumer", "base_version": "3.1.0-rc.3", "consumer_artifacts_used": False}:
        raise ValueError("invalid ablation identity")
    candidate = workflow["candidate"]
    if candidate.get("schema_version") != "A-D-2.0" or not candidate.get("request_id") or not candidate.get("poster_image"):
        raise ValueError("invalid current candidate")
    if not candidate.get("loop_state", {}).get("version_id") or not isinstance(candidate.get("protected_content"), dict):
        raise ValueError("candidate binding or protected content missing")
    return candidate


def validate_result(result, workflow):
    required = {"agent_name", "score", "pass", "problem_list", "modify_suggestion", "protected_content", "meta"}
    if set(result) != required or result.get("agent_name") != "aesthetic_agent":
        raise ValueError("expected fixed seven-field aesthetic result")
    if result.get("protected_content") != workflow["candidate"].get("protected_content"):
        raise ValueError("aesthetic result changed protected content")
    if type(result.get("pass")) is not bool:
        raise ValueError("aesthetic pass must be boolean")
    if len(result.get("problem_list", [])) != len(result.get("modify_suggestion", [])) or len(result.get("problem_list", [])) > 3:
        raise ValueError("aesthetic feedback must contain at most three paired items")
    meta = result.get("meta")
    if not isinstance(meta, dict) or set(meta) != {"judge_dimensions", "confidence"}:
        raise ValueError("invalid aesthetic meta")
    confidence = meta.get("confidence")
    if type(confidence) not in (int, float) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ValueError("aesthetic confidence must be within 0..1")
    score = result.get("score")
    if score is None:
        if result.get("pass") is not False or meta.get("judge_dimensions") != [] or confidence != 0:
            raise ValueError("invalid blocked aesthetic result")
        return
    if type(score) is not int or not 0 <= score <= 100 or meta.get("judge_dimensions") != AESTHETIC_LABELS:
        raise ValueError("invalid scored aesthetic result")


def validate_details(result, details, workflow):
    candidate = workflow["candidate"]
    expected = {
        "rubric_version": "3.0.0-rc.4", "score": result["score"], "pass": result["pass"],
        "request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"], "context_hash": context_hash(workflow),
        "ablation": workflow["ablation"],
    }
    if not isinstance(details, dict) or any(details.get(k) != v for k, v in expected.items()):
        raise ValueError("aesthetic details do not bind to current no-consumer candidate")
    scores = details.get("dimension_scores")
    if not isinstance(scores, dict) or set(scores) != set(DIMENSION_MINIMUMS):
        raise ValueError("all six aesthetic dimensions required")
    calculated = result["score"] >= 80 and all(scores[k] >= v for k, v in DIMENSION_MINIMUMS.items()) and not details.get("critical_issues")
    if calculated != result["pass"]:
        raise ValueError("aesthetic pass contradicts deterministic details")


def select_best(history):
    eligible = [x for x in history if isinstance(x, dict) and x.get("hard_compliance_pass") is True and type(x.get("aesthetic_score")) is int]
    return max(eligible, key=lambda x: x["aesthetic_score"]) if eligible else None


def build_contract(result, details, workflow):
    candidate = workflow["candidate"]
    editable = [k for k, minimum in DIMENSION_MINIMUMS.items() if details["dimension_scores"][k] < minimum]
    if not editable:
        raise ValueError("failed aesthetic result has no below-threshold dimension")
    return {
        "contract_version": "aesthetic-edit-lock-no-consumer/1.0",
        "generation_mode": "local_edit_only",
        "baseline_candidate": {
            "request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"],
            "poster_image": candidate["poster_image"], "context_hash": details["context_hash"],
        },
        "editable_aesthetic_dimensions": editable,
        "locked_aesthetic_dimensions": [k for k in DIMENSION_MINIMUMS if k not in editable],
        "immutable_protected_content": deepcopy(candidate["protected_content"]),
        "advisory_instructions": deepcopy(result["modify_suggestion"]),
        "forbidden_changes": ["八组 protected_content 的事实、数量、含义和可读性", "本轮未开放的美学维度"],
        "required_post_generation_checks": ["HC-01..HC-12", "aesthetic_agent_no_consumer", "final_quality_gate_no_consumer"],
        "ablation": deepcopy(workflow["ablation"]),
    }


def route_result(result, details, workflow, version, redraw_attempts, history=None):
    if type(redraw_attempts) is not int or redraw_attempts < 0:
        raise ValueError("redraw_attempts must be nonnegative integer")
    candidate = validate_workflow(workflow)
    validate_result(result, workflow)
    flags = version.get("feature_flags", {})
    if flags != {"consumer_agent": False, "aesthetic_agent": True, "final_quality_gate": True}:
        raise ValueError("invalid ablation feature flags")
    retry = version.get("retry_policy", {})
    if retry.get("counter_scope") != "global_across_hard_compliance_aesthetic_and_final_quality":
        raise ValueError("invalid ablation retry scope")
    maximum = retry.get("max_redraw_attempts")
    common = {
        "request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"],
        "aesthetic_score": result["score"], "aesthetic_confidence": result["meta"]["confidence"],
        "global_redraw_attempts": redraw_attempts, "max_redraw_attempts": maximum,
        "protected_content": deepcopy(candidate["protected_content"]), "ablation": deepcopy(workflow["ablation"]),
    }
    if result["score"] is None:
        return {**common, "status": "blocked", "action": "complete_aesthetic_input", "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"]}
    validate_details(result, details, workflow)
    if result["pass"]:
        return {**common, "status": "in_progress", "action": "invoke_final_quality_gate", "details_verified": True}
    if redraw_attempts >= maximum:
        return {**common, "status": "degraded", "action": "return_best_candidate", "reason": "global redraw limit exhausted", "best_candidate": select_best(history or [])}
    return {**common, "status": "in_progress", "action": "regenerate_then_full_pipeline", "next_global_redraw_attempt": redraw_attempts + 1, "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"], "generation_edit_contract": build_contract(result, details, workflow)}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result")
    parser.add_argument("--details", required=True)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    routed = route_result(load(args.result), load(args.details), load(args.workflow_input), load(args.config), args.redraw_attempts, load(args.history) if args.history else [])
    rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
