#!/usr/bin/env python3
"""Route the score-free FINAL-QUALITY-3.2 host arbitration result."""

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path


SEVERITIES = {"critical", "severe", "moderate", "minor"}
MAJOR_SEVERITIES = {"critical", "severe", "moderate"}
CONSUMER_DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}
REVIEW_FIELDS = {
    "schema_version", "request_id", "version_id", "poster_image", "review_mode",
    "image_views", "evidence_audit", "defects", "no_moderate_or_major_defect", "confidence",
}
DEFECT_FIELDS = {
    "code", "category", "severity", "region", "observation", "required_action",
    "editable_objects", "protected_objects",
}
ALLOWED_CODES = {
    "COMPETING_FOCAL_POINTS", "PRODUCT_TOO_SMALL", "PRODUCT_OCCLUDED", "PRODUCT_FLOATING",
    "PRODUCT_DISTORTED", "QUANTITY_AMBIGUOUS", "TEXT_DENSITY_HIGH", "ALIGNMENT_INCONSISTENT",
    "TEXT_OVERLAP", "LOGO_MISSING", "LOGO_INCORRECT", "LOGO_BACKGROUND_ARTIFACT",
    "LOGO_EDGE_HALO", "LOGO_CONTRAST_LOW", "LOGO_FLOATING", "PRODUCT_SCENE_COMPOSITE_ARTIFACT",
    "TYPE_STYLE_CONFLICT", "PRICE_HIERARCHY_WEAK", "CTA_HIERARCHY_WEAK", "SAFE_MARGIN_WEAK",
    "COLOR_CONTRAST_LOW", "DECORATION_OVERLOAD", "SCENE_PRODUCT_MISMATCH", "GENERIC_TEMPLATE_LOOK",
    "LIGHTING_CONFLICT", "MATERIAL_ARTIFICIAL", "AI_ARTIFACT", "OTHER_VISIBLE_DEFECT",
}
ALLOWED_CATEGORIES = {"product", "brand", "hierarchy", "typography", "color_scene", "finish"}
LOGO_MODERATE_CODES = {"LOGO_BACKGROUND_ARTIFACT", "LOGO_EDGE_HALO", "LOGO_CONTRAST_LOW", "LOGO_FLOATING"}
INTEGRATION_MODERATE_CODES = {"PRODUCT_SCENE_COMPOSITE_ARTIFACT"}
LOGO_CRITICAL_CODES = {"LOGO_MISSING", "LOGO_INCORRECT"}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def count_level4(details):
    count = 0
    dimensions = details.get("dimensions") if isinstance(details, dict) else None
    if not isinstance(dimensions, dict):
        return 0
    for dimension in dimensions.values():
        for item in dimension.get("items", []) if isinstance(dimension, dict) else []:
            if isinstance(item, dict) and item.get("level") == 4:
                count += 1
    return count


def validate_upstream(consumer, consumer_details, aesthetic, aesthetic_details, workflow):
    require(isinstance(workflow, dict) and workflow.get("schema_version") == "A-D-AESTHETIC-3.0", "formal aesthetic workflow input required")
    candidate = workflow.get("candidate") or {}
    embedded = workflow.get("consumer_result")
    require(embedded == consumer, "consumer result is not bound to the current workflow")
    require(candidate.get("request_id") == consumer.get("request_id"), "consumer request mismatch")
    require(candidate.get("loop_state", {}).get("version_id") == consumer.get("version_id"), "consumer version mismatch")
    require(candidate.get("protected_content") == consumer.get("protected_content"), "consumer protected content mismatch")
    scores = consumer.get("dimension_scores") or {}
    require(
        consumer.get("schema_version") == "A-D-2.0"
        and consumer.get("agent_name") == "consumer_agent"
        and consumer.get("pass") is True
        and consumer.get("hard_fail") is False
        and consumer.get("next_route") == "aesthetic_agent"
        and not consumer.get("regressed_dimensions")
        and type(consumer.get("score")) is int and consumer["score"] >= 80
        and set(scores) == CONSUMER_DIMENSIONS
        and all(type(scores[key]) is int and scores[key] >= 14 for key in CONSUMER_DIMENSIONS)
        and set(consumer.get("locked_dimensions", [])) == CONSUMER_DIMENSIONS,
        "final quality gate requires the current passing consumer result with five locks",
    )
    require(isinstance(consumer_details, dict), "consumer scoring details required")
    require(consumer_details.get("request_id") == consumer["request_id"], "consumer details request mismatch")
    require(consumer_details.get("version_id") == consumer["version_id"], "consumer details version mismatch")
    require(consumer_details.get("score") == consumer["score"], "consumer details score mismatch")
    require(
        isinstance(aesthetic, dict)
        and aesthetic.get("agent_name") == "aesthetic_agent"
        and aesthetic.get("pass") is True
        and type(aesthetic.get("score")) is int
        and aesthetic["score"] >= 80,
        "final quality gate requires a passing aesthetic result",
    )
    require(aesthetic.get("protected_content") == consumer.get("protected_content"), "aesthetic protected content mismatch")
    require(isinstance(aesthetic_details, dict), "aesthetic scoring details required")
    require(aesthetic_details.get("request_id") == consumer["request_id"], "aesthetic details request mismatch")
    require(aesthetic_details.get("version_id") == consumer["version_id"], "aesthetic details version mismatch")
    require(aesthetic_details.get("poster_image") == candidate.get("poster_image"), "aesthetic details poster mismatch")
    require(aesthetic_details.get("score") == aesthetic["score"], "aesthetic details score mismatch")
    require(aesthetic_details.get("pass") is True, "aesthetic details must record pass=true")
    return candidate


def validate_review(review, candidate):
    require(isinstance(review, dict) and set(review) == REVIEW_FIELDS, "final review must use the exact FINAL-QUALITY-3.2 fields")
    require(review.get("schema_version") == "FINAL-QUALITY-3.2", "unsupported final review schema")
    require(review.get("request_id") == candidate.get("request_id"), "final review request mismatch")
    require(review.get("version_id") == candidate.get("loop_state", {}).get("version_id"), "final review version mismatch")
    require(review.get("poster_image") == candidate.get("poster_image"), "final review poster mismatch")
    require(review.get("review_mode") in {"standard", "adversarial"}, "invalid final review mode")
    views = review.get("image_views")
    require(isinstance(views, dict) and set(views) == {"original", "thumbnail_360", "product_reference"}, "exact image view confirmations required")
    require(all(views[key] is True for key in views), "final review must inspect original, thumbnail and product reference")
    audit = review.get("evidence_audit")
    audit_fields = {"consumer_evidence_supported", "aesthetic_evidence_supported", "contradictions", "generic_evidence_findings"}
    require(isinstance(audit, dict) and set(audit) == audit_fields, "invalid evidence audit")
    require(type(audit["consumer_evidence_supported"]) is bool and type(audit["aesthetic_evidence_supported"]) is bool, "evidence support flags must be boolean")
    for key in ("contradictions", "generic_evidence_findings"):
        require(isinstance(audit[key], list) and len(audit[key]) == len(set(audit[key])) and all(nonempty(x) for x in audit[key]), key + " must be unique nonempty strings")
    defects = review.get("defects")
    require(isinstance(defects, list) and len(defects) <= 6, "defects must be a list with at most six items")
    identities = set()
    for defect in defects:
        require(isinstance(defect, dict) and set(defect) == DEFECT_FIELDS, "invalid defect fields")
        require(defect["code"] in ALLOWED_CODES, "unknown defect code")
        require(defect["category"] in ALLOWED_CATEGORIES, "unknown defect category")
        require(defect["severity"] in SEVERITIES, "unknown defect severity")
        require(defect["code"] != "TEXT_OVERLAP" or defect["severity"] in MAJOR_SEVERITIES,
                "TEXT_OVERLAP must be moderate or higher")
        require(defect["code"] not in LOGO_MODERATE_CODES or defect["severity"] in MAJOR_SEVERITIES,
                f'{defect["code"]} must be moderate or higher')
        require(defect["code"] not in INTEGRATION_MODERATE_CODES or defect["severity"] in MAJOR_SEVERITIES,
                f'{defect["code"]} must be moderate or higher')
        require(defect["code"] not in LOGO_CRITICAL_CODES or defect["severity"] == "critical",
                f'{defect["code"]} must be critical')
        require(all(nonempty(defect[key]) for key in ("region", "observation", "required_action")), "defect needs region, observation and required action")
        for key in ("editable_objects", "protected_objects"):
            require(isinstance(defect[key], list) and defect[key] and len(defect[key]) == len(set(defect[key])) and all(nonempty(x) for x in defect[key]), "defect object lists must be unique nonempty strings")
        identity = (defect["code"], defect["region"], defect["observation"])
        require(identity not in identities, "duplicate defect")
        identities.add(identity)
    has_major = any(item["severity"] in MAJOR_SEVERITIES for item in defects)
    require(type(review.get("no_moderate_or_major_defect")) is bool, "no_moderate_or_major_defect must be boolean")
    require(review["no_moderate_or_major_defect"] is (not has_major), "defect severity contradicts no_moderate_or_major_defect")
    confidence = review.get("confidence")
    require(type(confidence) in (int, float) and not isinstance(confidence, bool) and math.isfinite(confidence) and 0 <= confidence <= 1, "confidence must be finite 0..1")


def suspicious_reasons(consumer, consumer_details, aesthetic, aesthetic_details, config):
    thresholds = config["final_quality_gate"]["suspicious_score"]
    reasons = []
    if consumer["score"] >= thresholds["consumer_total_at_least"]:
        reasons.append("consumer_total")
    if all(value >= thresholds["consumer_all_dimensions_at_least"] for value in consumer["dimension_scores"].values()):
        reasons.append("consumer_dimensions_saturated")
    if count_level4(consumer_details) >= thresholds["consumer_level4_count_at_least"]:
        reasons.append("consumer_level4_saturation")
    if aesthetic["score"] >= thresholds["aesthetic_total_at_least"]:
        reasons.append("aesthetic_total")
    if count_level4(aesthetic_details) >= thresholds["aesthetic_level4_count_at_least"]:
        reasons.append("aesthetic_level4_saturation")
    return reasons


def build_edit_contract(review, consumer, candidate):
    return {
        "contract_version": "final-quality-edit-lock/1.0",
        "generation_mode": "local_edit_only",
        "baseline_candidate": {
            "request_id": candidate["request_id"],
            "version_id": candidate["loop_state"]["version_id"],
            "poster_image": candidate["poster_image"],
        },
        "authorized_defects": deepcopy(review["defects"]),
        "editable_regions": sorted({item["region"] for item in review["defects"]}),
        "editable_objects": sorted({value for item in review["defects"] for value in item["editable_objects"]}),
        "protected_objects": sorted({value for item in review["defects"] for value in item["protected_objects"]}),
        "locked_consumer_dimensions": deepcopy(consumer["dimension_scores"]),
        "immutable_protected_content": deepcopy(consumer["protected_content"]),
        "required_post_generation_checks": [
            "HC-01..HC-12",
            "consumer_agent_with_previous_result_and_all_five_locks",
            "reject_if_regressed_dimensions_nonempty",
            "aesthetic_agent",
            "final_quality_gate",
        ],
        "on_consumer_regression": "reject_candidate_and_restore_baseline_candidate",
    }


def select_best(history):
    eligible = [item for item in history if isinstance(item, dict)
                and item.get("hard_compliance_pass") is True
                and item.get("consumer_pass") is True
                and item.get("aesthetic_pass") is True]
    return max(eligible, key=lambda item: (item.get("final_quality_pass") is True, item.get("aesthetic_score", -1))) if eligible else None


def route_result(review, consumer, consumer_details, aesthetic, aesthetic_details, workflow, version, redraw_attempts, history=None):
    require(type(redraw_attempts) is int and redraw_attempts >= 0, "redraw_attempts must be a nonnegative integer")
    candidate = validate_upstream(consumer, consumer_details, aesthetic, aesthetic_details, workflow)
    validate_review(review, candidate)
    require(version.get("skill_version") == "3.1.0-rc.7" and version.get("workflow_version") == "3.1", "final quality gate requires Skill 3.1.0-rc.7")
    require(version.get("feature_flags", {}).get("final_quality_gate") is True, "final quality gate feature flag is disabled")
    gate = version.get("final_quality_gate") or {}
    require(gate.get("schema_version") == "FINAL-QUALITY-3.2" and gate.get("mode") == "defect_based_no_score", "invalid final quality configuration")
    max_attempts = version.get("retry_policy", {}).get("max_redraw_attempts")
    require(type(max_attempts) is int and max_attempts >= 0, "invalid global redraw limit")
    suspicious = suspicious_reasons(consumer, consumer_details, aesthetic, aesthetic_details, version)
    common = {
        "request_id": consumer["request_id"],
        "version_id": consumer["version_id"],
        "final_quality_schema": review["schema_version"],
        "review_mode": review["review_mode"],
        "global_redraw_attempts": redraw_attempts,
        "max_redraw_attempts": max_attempts,
        "suspicious_score_reasons": suspicious,
        "defects": deepcopy(review["defects"]),
    }
    audit = review["evidence_audit"]
    evidence_valid = (
        audit["consumer_evidence_supported"] is True
        and audit["aesthetic_evidence_supported"] is True
        and not audit["contradictions"]
        and not audit["generic_evidence_findings"]
    )
    if not evidence_valid:
        return {**common, "status": "in_progress", "action": "reevaluate_current_candidate",
                "reason": "upstream pass evidence is unsupported, contradictory, or generic",
                "evidence_audit": deepcopy(audit)}
    if review["confidence"] < gate["minimum_review_confidence"]:
        return {**common, "status": "blocked", "action": "complete_final_quality_input",
                "reason": "final quality review confidence is below the configured minimum"}
    critical_or_severe = [item for item in review["defects"] if item["severity"] in {"critical", "severe"}]
    moderate = [item for item in review["defects"] if item["severity"] == "moderate"]
    minor = [item for item in review["defects"] if item["severity"] == "minor"]
    needs_revision = (
        bool(critical_or_severe)
        or len(moderate) > gate["max_moderate_defects_for_pass"]
        or len(minor) > gate["max_minor_defects_for_pass"]
    )
    if needs_revision:
        if redraw_attempts >= max_attempts:
            return {**common, "status": "degraded", "action": "return_best_candidate",
                    "reason": "global redraw limit exhausted at final quality gate",
                    "best_candidate": select_best(history or [])}
        return {**common, "status": "in_progress", "action": "regenerate_then_full_pipeline",
                "next_global_redraw_attempt": redraw_attempts + 1,
                "generation_edit_contract": build_edit_contract(review, consumer, candidate)}
    if (
        review["review_mode"] == "standard"
        and suspicious
        and gate.get("adversarial_review_on_suspicious_score") is True
    ):
        return {**common, "status": "in_progress", "action": "invoke_adversarial_final_review",
                "reason": "high or saturated upstream scores require one score-free reverse review"}
    return {**common, "status": "passed", "action": "complete", "final_pass": True,
            "minor_defect_count": len(minor)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review")
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--consumer-details", required=True)
    parser.add_argument("--aesthetic-result", required=True)
    parser.add_argument("--aesthetic-details", required=True)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        routed = route_result(
            load(args.review), load(args.consumer_result), load(args.consumer_details),
            load(args.aesthetic_result), load(args.aesthetic_details), load(args.workflow_input),
            load(args.config), args.redraw_attempts, load(args.history) if args.history else [],
        )
        rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("final quality router: " + str(exc))


if __name__ == "__main__":
    main()
