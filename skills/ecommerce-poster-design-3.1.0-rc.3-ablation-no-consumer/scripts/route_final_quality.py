#!/usr/bin/env python3
"""Route the score-free final quality gate for the no-consumer ablation."""

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path

SCHEMA = "FINAL-QUALITY-3.1-ABLATION-NO-CONSUMER"
SEVERITIES = {"critical", "severe", "moderate", "minor"}
MAJOR = {"critical", "severe", "moderate"}
ALLOWED_CODES = {"COMPETING_FOCAL_POINTS", "PRODUCT_TOO_SMALL", "PRODUCT_OCCLUDED", "PRODUCT_FLOATING", "PRODUCT_DISTORTED", "QUANTITY_AMBIGUOUS", "TEXT_DENSITY_HIGH", "ALIGNMENT_INCONSISTENT", "TEXT_OVERLAP", "LOGO_FLOATING", "TYPE_STYLE_CONFLICT", "PRICE_HIERARCHY_WEAK", "CTA_HIERARCHY_WEAK", "SAFE_MARGIN_WEAK", "COLOR_CONTRAST_LOW", "DECORATION_OVERLOAD", "SCENE_PRODUCT_MISMATCH", "GENERIC_TEMPLATE_LOOK", "LIGHTING_CONFLICT", "MATERIAL_ARTIFICIAL", "AI_ARTIFACT", "OTHER_VISIBLE_DEFECT"}
ALLOWED_CATEGORIES = {"product", "hierarchy", "typography", "color_scene", "finish"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def count_level4(details):
    return sum(item.get("level") == 4 for dimension in (details.get("dimensions") or {}).values() for item in dimension.get("items", []))


def validate_upstream(aesthetic, details, workflow):
    require(workflow.get("schema_version") == "A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER", "no-consumer workflow required")
    require(workflow.get("ablation") == {"id": "no-consumer", "base_version": "3.1.0-rc.3", "consumer_artifacts_used": False}, "invalid ablation identity")
    candidate = workflow.get("candidate") or {}
    require(aesthetic.get("agent_name") == "aesthetic_agent" and aesthetic.get("pass") is True and type(aesthetic.get("score")) is int and aesthetic["score"] >= 80, "passing aesthetic result required")
    require(aesthetic.get("protected_content") == candidate.get("protected_content"), "protected content mismatch")
    require(details.get("request_id") == candidate.get("request_id") and details.get("version_id") == candidate.get("loop_state", {}).get("version_id"), "aesthetic details candidate mismatch")
    require(details.get("poster_image") == candidate.get("poster_image") and details.get("score") == aesthetic.get("score") and details.get("pass") is True, "aesthetic details result mismatch")
    require(details.get("ablation") == workflow["ablation"], "aesthetic details missing ablation identity")
    return candidate


def validate_review(review, candidate, ablation):
    required = {"schema_version", "request_id", "version_id", "poster_image", "review_mode", "image_views", "evidence_audit", "defects", "no_moderate_or_major_defect", "confidence", "ablation"}
    require(isinstance(review, dict) and set(review) == required, "exact no-consumer final review fields required")
    require(review["schema_version"] == SCHEMA and review["ablation"] == ablation, "invalid review schema or ablation")
    require(review["request_id"] == candidate.get("request_id") and review["version_id"] == candidate.get("loop_state", {}).get("version_id") and review["poster_image"] == candidate.get("poster_image"), "review candidate mismatch")
    require(review["review_mode"] in {"standard", "adversarial"}, "invalid review mode")
    require(review["image_views"] == {"original": True, "thumbnail_360": True, "product_reference": True}, "all image views required")
    audit = review["evidence_audit"]
    require(isinstance(audit, dict) and set(audit) == {"aesthetic_evidence_supported", "contradictions", "generic_evidence_findings"}, "consumer-free evidence audit required")
    require(type(audit["aesthetic_evidence_supported"]) is bool, "aesthetic evidence flag must be boolean")
    for key in ("contradictions", "generic_evidence_findings"):
        require(isinstance(audit[key], list) and len(audit[key]) == len(set(audit[key])) and all(nonempty(x) for x in audit[key]), "invalid evidence list")
    defects = review["defects"]
    require(isinstance(defects, list) and len(defects) <= 6, "at most six defects allowed")
    for defect in defects:
        require(defect.get("code") in ALLOWED_CODES and defect.get("category") in ALLOWED_CATEGORIES and defect.get("severity") in SEVERITIES, "invalid defect taxonomy")
        require(defect["code"] not in {"TEXT_OVERLAP", "LOGO_FLOATING"} or defect["severity"] in MAJOR, f'{defect["code"]} must be moderate or higher')
        require(all(nonempty(defect.get(k)) for k in ("region", "observation", "required_action")), "localized defect evidence required")
        require(all(isinstance(defect.get(k), list) and defect[k] for k in ("editable_objects", "protected_objects")), "defect object scopes required")
    has_major = any(x["severity"] in MAJOR for x in defects)
    require(review["no_moderate_or_major_defect"] is (not has_major), "severity summary mismatch")
    require(type(review["confidence"]) in (int, float) and not isinstance(review["confidence"], bool) and math.isfinite(review["confidence"]) and 0 <= review["confidence"] <= 1, "invalid confidence")


def build_contract(review, candidate):
    return {
        "contract_version": "final-quality-edit-lock-no-consumer/1.0",
        "generation_mode": "local_edit_only",
        "baseline_candidate": {"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "poster_image": candidate["poster_image"]},
        "authorized_defects": deepcopy(review["defects"]),
        "editable_regions": sorted({x["region"] for x in review["defects"]}),
        "editable_objects": sorted({v for x in review["defects"] for v in x["editable_objects"]}),
        "protected_objects": sorted({v for x in review["defects"] for v in x["protected_objects"]}),
        "immutable_protected_content": deepcopy(candidate["protected_content"]),
        "required_post_generation_checks": ["HC-01..HC-12", "aesthetic_agent_no_consumer", "final_quality_gate_no_consumer"],
        "ablation": deepcopy(review["ablation"]),
    }


def select_best(history):
    eligible = [x for x in history if isinstance(x, dict) and x.get("hard_compliance_pass") is True and type(x.get("aesthetic_score")) is int]
    return max(eligible, key=lambda x: (x.get("final_quality_pass") is True, x["aesthetic_score"])) if eligible else None


def route_result(review, aesthetic, aesthetic_details, workflow, version, redraw_attempts, history=None):
    require(type(redraw_attempts) is int and redraw_attempts >= 0, "invalid redraw count")
    require(version.get("skill_version") == "3.1.0-rc.3-ablation-no-consumer", "wrong skill version")
    require(version.get("feature_flags") == {"consumer_agent": False, "aesthetic_agent": True, "final_quality_gate": True}, "consumer must be disabled")
    candidate = validate_upstream(aesthetic, aesthetic_details, workflow)
    validate_review(review, candidate, workflow["ablation"])
    gate = version["final_quality_gate"]
    common = {"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "final_quality_schema": SCHEMA, "global_redraw_attempts": redraw_attempts, "max_redraw_attempts": version["retry_policy"]["max_redraw_attempts"], "defects": deepcopy(review["defects"]), "ablation": deepcopy(workflow["ablation"])}
    if review["confidence"] < gate["minimum_review_confidence"]:
        return {**common, "status": "blocked", "action": "complete_final_quality_input", "final_pass": False}
    if not review["evidence_audit"]["aesthetic_evidence_supported"] or review["evidence_audit"]["contradictions"] or review["evidence_audit"]["generic_evidence_findings"]:
        return {**common, "status": "in_progress", "action": "reevaluate_current_candidate", "final_pass": False}
    suspicious = aesthetic["score"] >= gate["suspicious_score"]["aesthetic_total_at_least"] or count_level4(aesthetic_details) >= gate["suspicious_score"]["aesthetic_level4_count_at_least"]
    if suspicious and review["review_mode"] == "standard":
        return {**common, "status": "in_progress", "action": "invoke_adversarial_final_review", "final_pass": False}
    moderate_or_worse = [x for x in review["defects"] if x["severity"] in MAJOR]
    minor = [x for x in review["defects"] if x["severity"] == "minor"]
    needs_revision = bool(moderate_or_worse) or len(minor) > gate["max_minor_defects_for_pass"]
    maximum = version["retry_policy"]["max_redraw_attempts"]
    if needs_revision and redraw_attempts >= maximum:
        return {**common, "status": "degraded", "action": "return_best_candidate", "final_pass": False, "best_candidate": select_best(history or [])}
    if needs_revision:
        return {**common, "status": "in_progress", "action": "regenerate_then_full_pipeline", "final_pass": False, "next_global_redraw_attempt": redraw_attempts + 1, "generation_edit_contract": build_contract(review, candidate)}
    return {**common, "status": "passed", "action": "complete", "final_pass": True, "minor_defect_count": len(minor)}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review")
    parser.add_argument("--aesthetic-result", required=True)
    parser.add_argument("--aesthetic-details", required=True)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--history")
    parser.add_argument("--output")
    args = parser.parse_args()
    routed = route_result(load(args.review), load(args.aesthetic_result), load(args.aesthetic_details), load(args.workflow_input), load(args.config), args.redraw_attempts, load(args.history) if args.history else [])
    rendered = json.dumps(routed, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
