#!/usr/bin/env python3
"""Route FINAL-QUALITY-3.1 for the rc.3 no-aesthetic ablation."""

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

SCHEMA = "FINAL-QUALITY-3.1-ABLATION-NO-AESTHETIC"
ABLATION = {"id": "no-aesthetic", "base_version": "3.1.0-rc.3", "aesthetic_artifacts_used": False}
SEVERITIES = {"critical", "severe", "moderate", "minor"}
MAJOR = {"critical", "severe", "moderate"}
SEVERITY_WEIGHT = {"critical": 4, "severe": 3, "moderate": 2, "minor": 1}
CONSUMER_DIMENSIONS = {"product_recognition", "benefit_clarity", "offer_visibility", "population_scene_fit", "purchase_drive"}
ALLOWED_CODES = {
    "COMPETING_FOCAL_POINTS", "PRODUCT_TOO_SMALL", "PRODUCT_OCCLUDED", "PRODUCT_FLOATING",
    "PRODUCT_DISTORTED", "QUANTITY_AMBIGUOUS", "TEXT_DENSITY_HIGH", "ALIGNMENT_INCONSISTENT",
    "TEXT_OVERLAP", "LOGO_FLOATING", "TYPE_STYLE_CONFLICT", "PRICE_HIERARCHY_WEAK",
    "CTA_HIERARCHY_WEAK", "SAFE_MARGIN_WEAK", "COLOR_CONTRAST_LOW", "DECORATION_OVERLOAD",
    "SCENE_PRODUCT_MISMATCH", "GENERIC_TEMPLATE_LOOK", "LIGHTING_CONFLICT", "MATERIAL_ARTIFICIAL",
    "AI_ARTIFACT", "OTHER_VISIBLE_DEFECT",
}
ALLOWED_CATEGORIES = {"product", "hierarchy", "typography", "color_scene", "finish"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def count_level4(details):
    return sum(
        item.get("level") == 4
        for dimension in (details.get("dimensions") or {}).values()
        for item in dimension.get("items", [])
        if isinstance(item, dict)
    )


def validate_upstream(consumer, details, workflow):
    require(isinstance(workflow, dict) and workflow.get("schema_version") == "A-D-2.0", "current A-D-2.0 consumer workflow input required")
    require(consumer.get("schema_version") == "A-D-2.0" and consumer.get("agent_name") == "consumer_agent", "A-D-2.0 consumer result required")
    require(workflow.get("request_id") == consumer.get("request_id"), "consumer request mismatch")
    require(workflow.get("loop_state", {}).get("version_id") == consumer.get("version_id"), "consumer version mismatch")
    require(workflow.get("protected_content") == consumer.get("protected_content"), "consumer protected content mismatch")
    scores = consumer.get("dimension_scores") or {}
    require(
        consumer.get("pass") is True and consumer.get("hard_fail") is False
        and consumer.get("next_route") == "aesthetic_agent" and not consumer.get("regressed_dimensions")
        and type(consumer.get("score")) is int and consumer["score"] >= 80
        and set(scores) == CONSUMER_DIMENSIONS
        and all(type(scores[key]) is int and scores[key] >= 14 for key in CONSUMER_DIMENSIONS)
        and set(consumer.get("locked_dimensions") or []) == CONSUMER_DIMENSIONS,
        "final quality gate requires the current passing consumer result with five locks",
    )
    require(isinstance(details, dict), "consumer scoring details required")
    require(details.get("request_id") == consumer["request_id"], "consumer details request mismatch")
    require(details.get("version_id") == consumer["version_id"], "consumer details version mismatch")
    require(details.get("score") == consumer["score"], "consumer details score mismatch")
    return workflow


def validate_review(review, candidate):
    required = {"schema_version", "request_id", "version_id", "poster_image", "review_mode", "image_views", "evidence_audit", "defects", "no_moderate_or_major_defect", "confidence", "ablation"}
    require(isinstance(review, dict) and set(review) == required, "exact no-aesthetic final review fields required")
    require(review.get("schema_version") == SCHEMA and review.get("ablation") == ABLATION, "invalid review schema or ablation identity")
    require(review.get("request_id") == candidate.get("request_id"), "final review request mismatch")
    require(review.get("version_id") == candidate.get("loop_state", {}).get("version_id"), "final review version mismatch")
    require(review.get("poster_image") == candidate.get("poster_image"), "final review poster mismatch")
    require(review.get("review_mode") in {"standard", "adversarial"}, "invalid final review mode")
    require(review.get("image_views") == {"original": True, "thumbnail_360": True, "product_reference": True}, "all image views are required")
    audit = review.get("evidence_audit")
    require(isinstance(audit, dict) and set(audit) == {"consumer_evidence_supported", "contradictions", "generic_evidence_findings"}, "consumer-only evidence audit required")
    require(type(audit["consumer_evidence_supported"]) is bool, "consumer evidence support flag must be boolean")
    for key in ("contradictions", "generic_evidence_findings"):
        require(isinstance(audit[key], list) and len(audit[key]) == len(set(audit[key])) and all(nonempty(x) for x in audit[key]), "invalid evidence list")
    defects = review.get("defects")
    require(isinstance(defects, list) and len(defects) <= 6, "defects must contain at most six items")
    identities = set()
    for defect in defects:
        require(isinstance(defect, dict), "defect must be an object")
        require(set(defect) == {"code", "category", "severity", "region", "observation", "required_action", "editable_objects", "protected_objects"}, "invalid defect fields")
        require(defect["code"] in ALLOWED_CODES and defect["category"] in ALLOWED_CATEGORIES and defect["severity"] in SEVERITIES, "invalid defect taxonomy")
        require(defect["code"] not in {"TEXT_OVERLAP", "LOGO_FLOATING"} or defect["severity"] in MAJOR, f'{defect["code"]} must be moderate or higher')
        require(all(nonempty(defect[key]) for key in ("region", "observation", "required_action")), "localized defect evidence required")
        for key in ("editable_objects", "protected_objects"):
            require(isinstance(defect[key], list) and defect[key] and len(defect[key]) == len(set(defect[key])) and all(nonempty(x) for x in defect[key]), "defect object scopes must be unique nonempty lists")
        identity = (defect["code"], defect["region"], defect["observation"])
        require(identity not in identities, "duplicate defect")
        identities.add(identity)
    has_major = any(item["severity"] in MAJOR for item in defects)
    require(type(review.get("no_moderate_or_major_defect")) is bool and review["no_moderate_or_major_defect"] is (not has_major), "severity summary mismatch")
    confidence = review.get("confidence")
    require(type(confidence) in (int, float) and not isinstance(confidence, bool) and math.isfinite(confidence) and 0 <= confidence <= 1, "invalid confidence")


def suspicious_reasons(consumer, details, version):
    thresholds = version["final_quality_gate"]["suspicious_score"]
    reasons = []
    if consumer["score"] >= thresholds["consumer_total_at_least"]:
        reasons.append("consumer_total")
    if all(value >= thresholds["consumer_all_dimensions_at_least"] for value in consumer["dimension_scores"].values()):
        reasons.append("consumer_dimensions_saturated")
    if count_level4(details) >= thresholds["consumer_level4_count_at_least"]:
        reasons.append("consumer_level4_saturation")
    return reasons


def build_contract(review, consumer, candidate):
    return {
        "contract_version": "final-quality-edit-lock-no-aesthetic/1.0",
        "generation_mode": "local_edit_only",
        "baseline_candidate": {"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "poster_image": candidate["poster_image"]},
        "authorized_defects": deepcopy(review["defects"]),
        "editable_regions": sorted({item["region"] for item in review["defects"]}),
        "editable_objects": sorted({value for item in review["defects"] for value in item["editable_objects"]}),
        "protected_objects": sorted({value for item in review["defects"] for value in item["protected_objects"]}),
        "locked_consumer_dimensions": deepcopy(consumer["dimension_scores"]),
        "immutable_protected_content": deepcopy(consumer["protected_content"]),
        "required_post_generation_checks": ["HC-01..HC-12", "consumer_agent_with_previous_result_and_all_five_locks", "reject_if_regressed_dimensions_nonempty", "final_quality_gate_no_aesthetic"],
        "on_consumer_regression": "reject_candidate_and_restore_baseline_candidate",
        "ablation": ABLATION.copy(),
    }


def candidate_rank(item):
    defects = item.get("final_quality_defects")
    if not isinstance(defects, list):
        defects = [] if item.get("final_quality_pass") is True else [{"severity": "critical"}] * 7
    weights = [SEVERITY_WEIGHT.get(value.get("severity"), 4) for value in defects if isinstance(value, dict)]
    maximum = max(weights, default=0)
    return (item.get("final_quality_pass") is True, -maximum, -sum(weights), -len(defects), item.get("consumer_score", -1))


def select_best(history):
    eligible = [item for item in history if isinstance(item, dict) and item.get("hard_compliance_pass") is True and item.get("consumer_pass") is True]
    return max(eligible, key=candidate_rank) if eligible else None


def route_result(review, consumer, consumer_details, workflow, version, redraw_attempts, history=None):
    require(type(redraw_attempts) is int and redraw_attempts >= 0, "invalid redraw count")
    require(version.get("skill_version") == "3.1.0-rc.3-ablation-no-aesthetic", "wrong skill version")
    require(version.get("feature_flags") == {"consumer_agent": True, "aesthetic_agent": False, "final_quality_gate": True}, "invalid no-aesthetic feature flags")
    candidate = validate_upstream(consumer, consumer_details, workflow)
    validate_review(review, candidate)
    gate = version.get("final_quality_gate") or {}
    require(gate.get("schema_version") == SCHEMA and gate.get("mode") == "defect_based_no_score", "invalid final quality configuration")
    maximum = version.get("retry_policy", {}).get("max_redraw_attempts")
    require(type(maximum) is int and maximum >= 0, "invalid global redraw limit")
    suspicious = suspicious_reasons(consumer, consumer_details, version)
    common = {
        "request_id": consumer["request_id"], "version_id": consumer["version_id"],
        "final_quality_schema": SCHEMA, "review_mode": review["review_mode"],
        "global_redraw_attempts": redraw_attempts, "max_redraw_attempts": maximum,
        "suspicious_score_reasons": suspicious, "defects": deepcopy(review["defects"]),
        "consumer_dimension_scores": deepcopy(consumer["dimension_scores"]),
        "protected_content": deepcopy(consumer["protected_content"]),
        "ablation": ABLATION.copy(), "final_pass": False,
    }
    audit = review["evidence_audit"]
    if not audit["consumer_evidence_supported"] or audit["contradictions"] or audit["generic_evidence_findings"]:
        return {**common, "status": "in_progress", "action": "reevaluate_current_candidate", "reason": "consumer evidence is unsupported, contradictory, or generic", "evidence_audit": deepcopy(audit)}
    if review["confidence"] < gate["minimum_review_confidence"]:
        return {**common, "status": "blocked", "action": "complete_final_quality_input", "reason": "final quality review confidence is below the configured minimum"}
    major = [item for item in review["defects"] if item["severity"] in MAJOR]
    minor = [item for item in review["defects"] if item["severity"] == "minor"]
    needs_revision = bool(major) or len(minor) > gate["max_minor_defects_for_pass"]
    if needs_revision and redraw_attempts >= maximum:
        return {**common, "status": "degraded", "action": "return_best_candidate", "reason": "global redraw limit exhausted at final quality gate", "best_candidate": select_best(history or [])}
    if needs_revision:
        return {**common, "status": "in_progress", "action": "regenerate_then_full_pipeline",
                "next_global_redraw_attempt": redraw_attempts + 1,
                "generation_edit_contract": build_contract(review, consumer, candidate)}
    if review["review_mode"] == "standard" and suspicious and gate.get("adversarial_review_on_suspicious_score") is True:
        return {**common, "status": "in_progress", "action": "invoke_adversarial_final_review", "reason": "high or saturated consumer scores require one score-free reverse review"}
    return {**common, "status": "passed", "action": "complete", "final_pass": True, "minor_defect_count": len(minor)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review")
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--consumer-details", required=True)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        routed = route_result(load(args.review), load(args.consumer_result), load(args.consumer_details), load(args.workflow_input), load(args.config), args.redraw_attempts, load(args.history) if args.history else [])
        rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("final quality router: " + str(exc))


if __name__ == "__main__":
    main()
