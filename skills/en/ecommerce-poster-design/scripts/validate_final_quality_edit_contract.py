#!/usr/bin/env python3
"""Validate a final-quality-edit-lock/1.0 contract before ImageGen is called."""

import argparse
import json
from pathlib import Path


CONSUMER_DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}
CONTRACT_FIELDS = {
    "contract_version", "generation_mode", "baseline_candidate", "authorized_defects",
    "editable_regions", "editable_objects", "protected_objects", "locked_consumer_dimensions",
    "immutable_protected_content", "required_post_generation_checks", "on_consumer_regression",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_contract(routed, workflow, review):
    require(routed.get("action") == "regenerate_then_full_pipeline", "route does not authorize generation")
    contract = routed.get("generation_edit_contract")
    require(isinstance(contract, dict) and set(contract) == CONTRACT_FIELDS, "invalid final quality edit contract fields")
    require(contract["contract_version"] == "final-quality-edit-lock/1.0", "unsupported final quality edit contract")
    require(contract["generation_mode"] == "local_edit_only", "final quality retry must use local edit only")
    candidate = workflow.get("candidate") or {}
    consumer = workflow.get("consumer_result") or {}
    expected_baseline = {
        "request_id": candidate.get("request_id"),
        "version_id": candidate.get("loop_state", {}).get("version_id"),
        "poster_image": candidate.get("poster_image"),
    }
    require(contract["baseline_candidate"] == expected_baseline, "contract baseline does not match the current candidate")
    require(review.get("request_id") == expected_baseline["request_id"], "review request does not match baseline")
    require(review.get("version_id") == expected_baseline["version_id"], "review version does not match baseline")
    require(review.get("poster_image") == expected_baseline["poster_image"], "review poster does not match baseline")
    require(contract["authorized_defects"] == review.get("defects"), "contract defects differ from the reviewed defects")
    expected_regions = sorted({item["region"] for item in review["defects"]})
    expected_editable = sorted({value for item in review["defects"] for value in item["editable_objects"]})
    expected_protected = sorted({value for item in review["defects"] for value in item["protected_objects"]})
    require(contract["editable_regions"] == expected_regions, "editable regions exceed or omit reviewed regions")
    require(contract["editable_objects"] == expected_editable, "editable objects exceed or omit reviewed objects")
    require(contract["protected_objects"] == expected_protected, "protected objects do not match the review")
    require(set(contract["locked_consumer_dimensions"]) == CONSUMER_DIMENSIONS, "all five consumer functions must remain locked")
    require(contract["locked_consumer_dimensions"] == consumer.get("dimension_scores"), "consumer lock scores changed")
    require(contract["immutable_protected_content"] == candidate.get("protected_content"), "protected content changed")
    required_checks = {
        "HC-01..HC-12", "consumer_agent_with_previous_result_and_all_five_locks",
        "reject_if_regressed_dimensions_nonempty", "aesthetic_agent", "final_quality_gate",
    }
    require(set(contract["required_post_generation_checks"]) == required_checks, "post-generation checks are incomplete")
    require(contract["on_consumer_regression"] == "reject_candidate_and_restore_baseline_candidate", "invalid regression action")
    return contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routed_result")
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--review", required=True)
    args = parser.parse_args()
    try:
        result = validate_contract(load(args.routed_result), load(args.workflow_input), load(args.review))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("final quality edit contract: " + str(exc))


if __name__ == "__main__":
    main()
