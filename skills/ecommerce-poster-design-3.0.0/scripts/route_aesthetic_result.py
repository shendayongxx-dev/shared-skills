#!/usr/bin/env python3
"""Validate and route a deterministic aesthetic rc.4 result."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


DIMENSION_MINIMUMS = {
    "composition": 16,
    "hierarchy": 16,
    "color": 12,
    "typography": 16,
    "consistency": 12,
    "finish": 8,
}
CONSUMER_DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}
AESTHETIC_LABELS = [
    "构图与视觉平衡", "视觉层级", "配色与对比", "字体与排版",
    "风格与场景适配", "材质光影与细节完成度",
]
CONSUMER_LABELS = {
    "product_recognition": "商品与品牌识别",
    "benefit_clarity": "核心利益与卖点传达",
    "offer_visibility": "价格促销与交易信息",
    "population_scene_fit": "人群—动机—场景适配",
    "purchase_drive": "信任与行动驱动",
}


def context_hash(workflow):
    candidate = workflow["candidate"]
    payload = json.dumps({
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "protected_content": candidate["protected_content"],
        "consumer_score": workflow["consumer_result"]["score"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_consumer(consumer, workflow):
    candidate = workflow.get("candidate", {})
    if workflow.get("schema_version") != "A-D-AESTHETIC-3.0":
        raise ValueError("workflow must use A-D-AESTHETIC-3.0")
    if workflow.get("consumer_result") != consumer:
        raise ValueError("consumer result is not the result embedded in this workflow")
    scores = consumer.get("dimension_scores") or {}
    valid = (
        consumer.get("schema_version") == "A-D-2.0"
        and consumer.get("agent_name") == "consumer_agent"
        and consumer.get("pass") is True
        and consumer.get("hard_fail") is False
        and consumer.get("next_route") == "aesthetic_agent"
        and not consumer.get("regressed_dimensions")
        and type(consumer.get("score")) is int and consumer["score"] >= 80
        and set(scores) == CONSUMER_DIMENSIONS
        and all(type(scores[name]) is int and scores[name] >= 14 for name in CONSUMER_DIMENSIONS)
        and set(consumer.get("locked_dimensions", [])) == CONSUMER_DIMENSIONS
        and candidate.get("request_id") == consumer.get("request_id")
        and candidate.get("loop_state", {}).get("version_id") == consumer.get("version_id")
        and candidate.get("protected_content") == consumer.get("protected_content")
    )
    if not valid:
        raise ValueError("aesthetic routing requires the current passing consumer result with five locks")


def validate_result(result, workflow):
    required = {"agent_name", "score", "pass", "problem_list", "modify_suggestion", "protected_content", "meta"}
    if set(result) != required or result.get("agent_name") != "aesthetic_agent":
        raise ValueError("expected the fixed seven-field aesthetic result")
    if result.get("protected_content") != workflow["candidate"].get("protected_content"):
        raise ValueError("aesthetic result changed protected content")
    if type(result.get("pass")) is not bool:
        raise ValueError("aesthetic pass must be boolean")
    if len(result.get("problem_list", [])) != len(result.get("modify_suggestion", [])):
        raise ValueError("aesthetic problems and suggestions must be paired")
    if len(result.get("problem_list", [])) > 3:
        raise ValueError("aesthetic feedback may contain at most three pairs")
    meta = result.get("meta")
    if not isinstance(meta, dict) or set(meta) != {"judge_dimensions", "confidence"}:
        raise ValueError("invalid aesthetic meta")
    confidence = meta.get("confidence")
    if type(confidence) not in (int, float) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ValueError("aesthetic confidence must be within 0..1")
    score = result.get("score")
    if score is None:
        if result.get("pass") is not False or meta.get("judge_dimensions") != [] or confidence != 0:
            raise ValueError("blocked aesthetic result must be pass=false with empty dimensions and zero confidence")
        return
    if type(score) is not int or not 0 <= score <= 100:
        raise ValueError("aesthetic score must be an integer within 0..100 or null")
    if meta.get("judge_dimensions") != AESTHETIC_LABELS:
        raise ValueError("aesthetic dimensions must use the canonical order")


def validate_details(result, details, workflow):
    candidate = workflow["candidate"]
    if not isinstance(details, dict):
        raise ValueError("aesthetic details are required for a scored result")
    expected = {
        "rubric_version": "3.0.0-rc.4",
        "score": result["score"],
        "pass": result["pass"],
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "context_hash": context_hash(workflow),
    }
    for key, value in expected.items():
        if details.get(key) != value:
            raise ValueError(f"aesthetic details mismatch: {key}")
    scores = details.get("dimension_scores")
    if not isinstance(scores, dict) or set(scores) != set(DIMENSION_MINIMUMS):
        raise ValueError("aesthetic details must contain all six dimension scores")
    calculated_pass = (
        result["score"] >= 80
        and all(type(scores[key]) is int and scores[key] >= minimum for key, minimum in DIMENSION_MINIMUMS.items())
        and not details.get("critical_issues")
    )
    if calculated_pass != result["pass"]:
        raise ValueError("aesthetic pass contradicts score, dimension minimums, or critical issues")


def select_best(history):
    eligible = [item for item in history if isinstance(item, dict)
                and item.get("hard_compliance_pass") is True
                and item.get("consumer_pass") is True
                and type(item.get("aesthetic_score")) is int]
    return max(eligible, key=lambda item: item["aesthetic_score"]) if eligible else None


def build_generation_edit_contract(result, consumer, details, workflow):
    """Create the authoritative, machine-readable scope for an aesthetic retry."""
    candidate = workflow["candidate"]
    scores = details["dimension_scores"]
    editable = [key for key, minimum in DIMENSION_MINIMUMS.items() if scores[key] < minimum]
    if not editable:
        raise ValueError("failed aesthetic result has no below-threshold dimension; scope review required")
    evidence = consumer.get("meta", {}).get("dimension_evidence", {})
    consumer_locks = {
        key: {
            "label": CONSUMER_LABELS[key],
            "score": consumer["dimension_scores"][key],
            "minimum": 14,
            "evidence": evidence.get(key, ""),
            "policy": "freeze_function_and_visual_relationship",
        }
        for key in sorted(CONSUMER_DIMENSIONS)
    }
    locked_aesthetic = [key for key in DIMENSION_MINIMUMS if key not in editable]
    return {
        "contract_version": "aesthetic-edit-lock/1.0",
        "generation_mode": "local_edit_only",
        "baseline_candidate": {
            "request_id": candidate["request_id"],
            "version_id": candidate["loop_state"]["version_id"],
            "poster_image": candidate["poster_image"],
            "context_hash": details["context_hash"],
        },
        "editable_aesthetic_dimensions": editable,
        "locked_aesthetic_dimensions": locked_aesthetic,
        "locked_consumer_dimensions": consumer_locks,
        "immutable_protected_content": deepcopy(consumer["protected_content"]),
        "advisory_instructions": deepcopy(result["modify_suggestion"]),
        "forbidden_changes": [
            "商品与品牌识别关系",
            "卖点及核心利益的表达与可理解性",
            "价格促销、交易信息和CTA的可发现性",
            "已通过的人群—动机—场景联系",
            "已通过的信任与购买行动驱动力",
            "八组protected_content的文字、数量、含义、位置关系与可读性",
            "本轮editable_aesthetic_dimensions之外的构图、层级、配色、排版、风格场景或材质功能",
        ],
        "required_post_generation_checks": [
            "HC-01..HC-12",
            "consumer_agent_with_previous_result_and_all_five_locks",
            "reject_if_regressed_dimensions_nonempty",
            "aesthetic_agent",
        ],
        "on_consumer_regression": "reject_candidate_and_restore_baseline_candidate",
    }


def route_result(result, consumer, details, workflow, version, redraw_attempts, history=None):
    if type(redraw_attempts) is not int or redraw_attempts < 0:
        raise ValueError("redraw_attempts must be a nonnegative integer")
    validate_consumer(consumer, workflow)
    validate_result(result, workflow)
    flags = version.get("feature_flags", {})
    if flags.get("consumer_agent") is not True or flags.get("aesthetic_agent") is not True:
        raise ValueError("consumer and aesthetic feature flags must be enabled")
    retry = version.get("retry_policy", {})
    max_attempts = retry.get("max_redraw_attempts")
    if type(max_attempts) is not int or max_attempts < 0 or retry.get("counter_scope") != "global_across_hard_compliance_consumer_and_aesthetic":
        raise ValueError("invalid unified retry policy")
    common = {
        "request_id": consumer["request_id"],
        "version_id": consumer["version_id"],
        "aesthetic_score": result["score"],
        "aesthetic_confidence": result["meta"]["confidence"],
        "global_redraw_attempts": redraw_attempts,
        "max_redraw_attempts": max_attempts,
        "protected_content": consumer["protected_content"],
        "locked_dimensions": sorted(consumer["locked_dimensions"]),
        "consumer_dimension_scores": deepcopy(consumer["dimension_scores"]),
    }
    if result["score"] is None:
        return {**common, "status": "blocked", "action": "complete_aesthetic_input",
                "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"]}
    validate_details(result, details, workflow)
    if result["pass"] is True:
        return {**common, "status": "passed", "action": "complete", "details_verified": True}
    if redraw_attempts >= max_attempts:
        best = select_best(history or [])
        return {**common, "status": "degraded", "action": "return_best_candidate",
                "reason": "global redraw limit exhausted", "best_candidate": best,
                "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"]}
    failed_dimensions = [key for key, minimum in DIMENSION_MINIMUMS.items()
                         if details["dimension_scores"][key] < minimum]
    if not failed_dimensions:
        return {**common, "status": "blocked", "action": "complete_aesthetic_scope",
                "reason": "critical issue is not bound to a below-threshold aesthetic dimension; human scope review required",
                "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"]}
    edit_contract = build_generation_edit_contract(result, consumer, details, workflow)
    return {**common, "status": "in_progress", "action": "regenerate_then_full_pipeline",
            "next_global_redraw_attempt": redraw_attempts + 1,
            "problem_list": result["problem_list"], "modify_suggestion": result["modify_suggestion"],
            "generation_edit_contract": edit_contract}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result")
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--details", required=True)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        routed = route_result(load(args.result), load(args.consumer_result), load(args.details),
                              load(args.workflow_input), load(args.config), args.redraw_attempts,
                              load(args.history) if args.history else [])
        rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("aesthetic router: " + str(exc))


if __name__ == "__main__":
    main()
