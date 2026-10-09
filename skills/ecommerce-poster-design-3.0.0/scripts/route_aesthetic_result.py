#!/usr/bin/env python3
"""Deterministically route an aesthetic-agent verdict inside the bounded loop."""

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List


PROTECTED_LABELS = {
    "product_identity": "商品身份",
    "product_quantity": "商品数量",
    "brand_and_logo": "品牌与Logo",
    "price_and_unit": "价格与单位",
    "promotion_and_period": "促销与期限",
    "selling_points": "卖点",
    "cta": "行动提示",
    "legal_text": "法务文案",
}
CONSUMER_DIMENSIONS = {
    "product_recognition",
    "benefit_clarity",
    "offer_visibility",
    "population_scene_fit",
    "purchase_drive",
}
AESTHETIC_DIMENSIONS = [
    "构图与视觉平衡",
    "视觉层级",
    "配色与对比",
    "字体与排版",
    "风格与场景适配",
    "自然质感与完成度",
]
AESTHETIC_KEYS = ["composition", "hierarchy", "color", "typography", "consistency", "finish"]
ASSESSMENT_FIELDS = {
    "schema_version", "status", "score_unrounded", "threshold", "dimensions",
    "below_threshold", "config_snapshot", "design_plan", "generation_assets_ready",
    "overall_qualified", "run_binding",
}
ASSESSMENT_DIMENSION_FIELDS = {
    "key", "label", "score", "threshold", "gap", "pass", "evidence", "confidence",
}


def flatten_protected(value: Dict[str, Any]) -> List[str]:
    if not isinstance(value, dict) or set(value) != set(PROTECTED_LABELS):
        raise ValueError("consumer protected_content must contain the unchanged eight groups")
    rendered: List[str] = []
    for key, label in PROTECTED_LABELS.items():
        item = value[key]
        if key == "product_quantity":
            if item is not None:
                if type(item) is not int or item < 1:
                    raise ValueError("invalid protected product_quantity")
                rendered.append(f"{label}：{item}")
        else:
            if not isinstance(item, list) or not all(isinstance(text, str) and text for text in item):
                raise ValueError(f"invalid protected group: {key}")
            rendered.extend(f"{label}：{text}" for text in item)
    return rendered


def validate_passing_assessment(
    assessment: Dict[str, Any],
    public_score: float,
    version: Dict[str, Any],
    aesthetic_input: Dict[str, Any],
    expected_version_id: str,
) -> None:
    if not isinstance(assessment, dict):
        raise ValueError("pass=true requires assessment-internal.json")
    if set(assessment) != ASSESSMENT_FIELDS:
        raise ValueError("internal assessment does not match the current fixed contract")
    if assessment.get("schema_version") != "2.0" or assessment.get("status") != "pass":
        raise ValueError("passing public result requires an internal pass assessment")
    if assessment.get("overall_qualified") is not True:
        raise ValueError("passing assessment must be qualified by integrated upstream gates")
    if not isinstance(aesthetic_input, dict):
        raise ValueError("pass=true requires the exact aesthetic input for run binding")
    product_input = aesthetic_input.get("product_input") or {}
    expected_binding = {
        "poster_image": aesthetic_input.get("poster_image"),
        "product_img": product_input.get("product_img"),
        "context_version": expected_version_id,
    }
    if not all(isinstance(expected_binding[name], str) and expected_binding[name] for name in expected_binding):
        raise ValueError("aesthetic input and consumer version must provide a complete run binding")
    if assessment.get("run_binding") != expected_binding:
        raise ValueError("assessment run binding does not match the current candidate")
    threshold = assessment.get("threshold")
    score_unrounded = assessment.get("score_unrounded")
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or threshold != 8.5:
        raise ValueError("internal aesthetic threshold must be 8.5")
    if type(score_unrounded) not in (int, float) or not math.isfinite(score_unrounded) or score_unrounded < threshold:
        raise ValueError("internal aesthetic score does not meet the total threshold")
    if abs(float(public_score) - float(score_unrounded)) > 0.005000001:
        raise ValueError("public aesthetic score does not match the internal calculation")
    dimensions = assessment.get("dimensions")
    if not isinstance(dimensions, list) or len(dimensions) != len(AESTHETIC_KEYS):
        raise ValueError("passing assessment must contain all six dimensions")
    for index, (key, label) in enumerate(zip(AESTHETIC_KEYS, AESTHETIC_DIMENSIONS)):
        dimension = dimensions[index]
        if (
            not isinstance(dimension, dict)
            or set(dimension) != ASSESSMENT_DIMENSION_FIELDS
            or dimension.get("key") != key
            or dimension.get("label") != label
        ):
            raise ValueError("passing assessment dimensions must use canonical keys and order")
        score = dimension.get("score")
        dimension_threshold = dimension.get("threshold")
        if (
            type(score) not in (int, float)
            or not math.isfinite(score)
            or type(dimension_threshold) not in (int, float)
            or not math.isfinite(dimension_threshold)
            or dimension_threshold != 8
            or score < dimension_threshold
            or dimension.get("pass") is not True
            or type(dimension.get("gap")) not in (int, float)
            or not math.isfinite(dimension["gap"])
            or not isinstance(dimension.get("evidence"), str)
            or not dimension["evidence"]
            or type(dimension.get("confidence")) not in (int, float)
            or not math.isfinite(dimension["confidence"])
            or not 0 <= dimension["confidence"] <= 1
        ):
            raise ValueError(f"passing assessment dimension failed: {key}")
    if assessment.get("below_threshold") != []:
        raise ValueError("passing assessment cannot contain below-threshold dimensions")
    snapshot = assessment.get("config_snapshot") or {}
    if snapshot.get("total_threshold") != 8.5:
        raise ValueError("assessment config snapshot threshold mismatch")
    if snapshot.get("loop", {}).get("max_generation_rounds") != version.get("retry_policy", {}).get(
        "aesthetic_max_generation_rounds"
    ):
        raise ValueError("assessment loop budget does not match host configuration")


def route_result(
    result: Dict[str, Any],
    consumer_result: Dict[str, Any],
    version: Dict[str, Any],
    generation_round: int,
    score_history: List[float],
    stagnation_count: int = 0,
    assessment: Dict[str, Any] = None,
    aesthetic_input: Dict[str, Any] = None,
) -> Dict[str, Any]:
    if type(generation_round) is not int or generation_round < 0:
        raise ValueError("generation_round cannot be negative")
    if type(stagnation_count) is not int or stagnation_count < 0:
        raise ValueError("stagnation_count cannot be negative")
    flags = version.get("feature_flags", {})
    if flags.get("aesthetic_agent") is not True:
        raise ValueError("aesthetic_agent feature flag is not enabled")
    retry = version.get("retry_policy", {})
    max_rounds = retry.get("aesthetic_max_generation_rounds")
    stagnation_rounds = retry.get("aesthetic_stagnation_rounds")
    min_gain = retry.get("aesthetic_min_total_gain")
    if type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("invalid aesthetic_max_generation_rounds")
    if type(stagnation_rounds) is not int or stagnation_rounds < 1:
        raise ValueError("invalid aesthetic_stagnation_rounds")
    if type(min_gain) not in (int, float) or not math.isfinite(min_gain) or min_gain < 0:
        raise ValueError("invalid aesthetic_min_total_gain")
    if generation_round > max_rounds:
        raise ValueError("generation_round exceeds configured limit")
    if not isinstance(score_history, list) or not all(
        type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 10 for score in score_history
    ):
        raise ValueError("score_history must contain 0..10 scores")
    if len(score_history) > generation_round:
        raise ValueError("score_history cannot contain more evaluated candidates than prior rounds")
    if stagnation_count >= stagnation_rounds:
        raise ValueError("stagnation_count must reset after reaching the change-direction threshold")
    consumer_scores = consumer_result.get("dimension_scores") or {}
    if not (
        consumer_result.get("schema_version") == "A-D-2.0"
        and consumer_result.get("agent_name") == "consumer_agent"
        and consumer_result.get("pass") is True
        and consumer_result.get("hard_fail") is False
        and consumer_result.get("next_route") == "aesthetic_agent"
        and not consumer_result.get("regressed_dimensions")
        and isinstance(consumer_result.get("version_id"), str)
        and bool(consumer_result["version_id"])
        and type(consumer_result.get("score")) is int
        and consumer_result["score"] >= 80
        and set(consumer_scores) == CONSUMER_DIMENSIONS
        and all(type(consumer_scores[name]) is int and consumer_scores[name] >= 14 for name in CONSUMER_DIMENSIONS)
    ):
        raise ValueError("aesthetic routing requires the current passing consumer result")

    required = {"agent_name", "score", "pass", "problem_list", "modify_suggestion", "protected_content", "meta"}
    if set(result) != required or result.get("agent_name") != "aesthetic_agent":
        raise ValueError("expected the fixed aesthetic_agent output contract")
    meta = result.get("meta")
    if not isinstance(meta, dict) or set(meta) != {"judge_dimensions", "confidence"}:
        raise ValueError("aesthetic meta must contain only judge_dimensions and confidence")
    dimensions = meta.get("judge_dimensions")
    if dimensions != AESTHETIC_DIMENSIONS:
        raise ValueError("aesthetic judge_dimensions must contain the canonical six dimensions in order")
    for name in ("problem_list", "modify_suggestion", "protected_content"):
        if not isinstance(result.get(name), list) or not all(
            isinstance(item, str) and item for item in result[name]
        ):
            raise ValueError(f"aesthetic {name} must be a string list")
    score = result.get("score")
    confidence = meta.get("confidence")
    if type(result.get("pass")) is not bool:
        raise ValueError("aesthetic pass must be boolean")
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 10:
        raise ValueError("aesthetic score must be within 0..10")
    if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("aesthetic confidence must be within 0..1")
    if len(result.get("problem_list", [])) != len(result.get("modify_suggestion", [])):
        raise ValueError("aesthetic problems and suggestions must be paired")

    protected_object = consumer_result.get("protected_content")
    expected_flat = flatten_protected(protected_object)
    returned_protected = result.get("protected_content")
    if returned_protected[:len(expected_flat)] != expected_flat:
        raise ValueError("aesthetic result changed or dropped protected content")
    additional_protected = returned_protected[len(expected_flat):]
    if len(additional_protected) != len(set(additional_protected)) or any(
        item in expected_flat for item in additional_protected
    ):
        raise ValueError("aesthetic additional protected_content contains duplicate entries")

    common = {
        "aesthetic_score": score,
        "aesthetic_confidence": confidence,
        "generation_round": generation_round,
        "max_generation_rounds": max_rounds,
        "protected_content": protected_object,
    }
    if score == 0 and confidence == 0:
        return {
            **common,
            "status": "blocked",
            "action": "complete_aesthetic_input",
            "reason": "aesthetic evaluation is incomplete and cannot enter score comparison",
            "problem_list": result.get("problem_list", []),
            "modify_suggestion": result.get("modify_suggestion", []),
        }

    updated_history = [*score_history, float(score)]
    if result.get("pass") is True:
        if score < 8.5:
            raise ValueError("aesthetic pass=true contradicts the total threshold")
        validate_passing_assessment(
            assessment,
            score,
            version,
            aesthetic_input,
            consumer_result.get("version_id"),
        )
        return {
            **common,
            "status": "passed",
            "action": "complete",
            "assessment_verified": True,
            "score_history": updated_history,
        }

    if generation_round >= max_rounds:
        best_score = max(updated_history)
        return {
            **common,
            "status": "degraded",
            "action": "return_best_candidate",
            "reason": "aesthetic generation budget exhausted",
            "best_score": best_score,
            "best_history_index": updated_history.index(best_score),
            "score_history": updated_history,
            "problem_list": result.get("problem_list", []),
            "modify_suggestion": result.get("modify_suggestion", []),
        }

    previous_best = max(score_history) if score_history else None
    gain = float("inf") if previous_best is None else float(score) - previous_best
    next_stagnation_count = stagnation_count + 1 if gain < min_gain else 0
    stagnated = next_stagnation_count >= stagnation_rounds
    if stagnated:
        next_stagnation_count = 0
    return {
        **common,
        "status": "in_progress",
        "action": "change_design_direction_then_regenerate" if stagnated else "regenerate_then_full_pipeline",
        "next_generation_round": generation_round + 1,
        "score_gain_vs_previous_best": None if previous_best is None else gain,
        "next_stagnation_count": next_stagnation_count,
        "score_history": updated_history,
        "problem_list": result.get("problem_list", []),
        "modify_suggestion": result.get("modify_suggestion", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--generation-round", type=int, required=True)
    parser.add_argument("--stagnation-count", type=int, default=0)
    parser.add_argument("--assessment")
    parser.add_argument("--aesthetic-input")
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    consumer = json.loads(Path(args.consumer_result).read_text(encoding="utf-8"))
    version = json.loads(Path(args.config).read_text(encoding="utf-8"))
    history = json.loads(Path(args.history).read_text(encoding="utf-8")) if args.history else []
    assessment = json.loads(Path(args.assessment).read_text(encoding="utf-8")) if args.assessment else None
    aesthetic_input = json.loads(Path(args.aesthetic_input).read_text(encoding="utf-8")) if args.aesthetic_input else None
    routed = route_result(
        result,
        consumer,
        version,
        args.generation_round,
        history,
        args.stagnation_count,
        assessment,
        aesthetic_input,
    )
    rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
