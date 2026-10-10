#!/usr/bin/env python3
"""Validate the consumer-frozen edit contract before an aesthetic ImageGen retry."""

import argparse
import hashlib
import json
from pathlib import Path


CONSUMER_DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}
AESTHETIC_DIMENSIONS = {"composition", "hierarchy", "color", "typography", "consistency", "finish"}
FORBIDDEN_CHANGES = [
    "商品与品牌识别关系",
    "卖点及核心利益的表达与可理解性",
    "价格促销、交易信息和CTA的可发现性",
    "已通过的人群—动机—场景联系",
    "已通过的信任与购买行动驱动力",
    "八组protected_content的文字、数量、含义、位置关系与可读性",
    "本轮editable_aesthetic_dimensions之外的构图、层级、配色、排版、风格场景或材质功能",
]


def workflow_hash(workflow):
    candidate = workflow["candidate"]
    payload = json.dumps({
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "protected_content": candidate["protected_content"],
        "consumer_score": workflow["consumer_result"]["score"],
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_contract(routed, workflow):
    if routed.get("action") != "regenerate_then_full_pipeline":
        raise ValueError("edit contract is valid only for regenerate_then_full_pipeline")
    contract = routed.get("generation_edit_contract")
    if not isinstance(contract, dict):
        raise ValueError("generation_edit_contract is required")
    required = {
        "contract_version", "generation_mode", "baseline_candidate",
        "editable_aesthetic_dimensions", "locked_aesthetic_dimensions",
        "locked_consumer_dimensions", "immutable_protected_content",
        "advisory_instructions", "forbidden_changes",
        "required_post_generation_checks", "on_consumer_regression",
    }
    if set(contract) != required:
        raise ValueError("generation edit contract fields are incomplete or unexpected")
    if contract["contract_version"] != "aesthetic-edit-lock/1.0" or contract["generation_mode"] != "local_edit_only":
        raise ValueError("only the local-edit consumer-lock contract is supported")
    candidate = workflow["candidate"]
    baseline = contract["baseline_candidate"]
    expected_baseline = {
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "context_hash": workflow_hash(workflow),
    }
    if baseline != expected_baseline:
        raise ValueError("edit baseline does not match the consumer-passed candidate")
    editable = contract["editable_aesthetic_dimensions"]
    locked = contract["locked_aesthetic_dimensions"]
    if not isinstance(editable, list) or not editable or len(editable) != len(set(editable)):
        raise ValueError("at least one unique editable aesthetic dimension is required")
    if not isinstance(locked, list) or len(locked) != len(set(locked)):
        raise ValueError("locked aesthetic dimensions must be unique")
    if set(editable) | set(locked) != AESTHETIC_DIMENSIONS or set(editable) & set(locked):
        raise ValueError("editable and locked aesthetic dimensions must form an exact partition")
    consumer_locks = contract["locked_consumer_dimensions"]
    if not isinstance(consumer_locks, dict) or set(consumer_locks) != CONSUMER_DIMENSIONS:
        raise ValueError("all five consumer dimensions must be frozen")
    for key, lock in consumer_locks.items():
        if lock.get("score") != workflow["consumer_result"]["dimension_scores"][key] or lock.get("score", 0) < 14:
            raise ValueError("consumer lock score does not match the passing result")
        if lock.get("policy") != "freeze_function_and_visual_relationship":
            raise ValueError("consumer lock policy is missing")
    if contract["immutable_protected_content"] != candidate["protected_content"]:
        raise ValueError("protected content is not immutable or belongs to another candidate")
    if not isinstance(contract["advisory_instructions"], list) or not contract["advisory_instructions"]:
        raise ValueError("advisory local edit instructions are required")
    if contract["advisory_instructions"] != routed.get("modify_suggestion"):
        raise ValueError("advisory instructions do not match the routed aesthetic result")
    if contract["forbidden_changes"] != FORBIDDEN_CHANGES:
        raise ValueError("consumer-function and non-target aesthetic prohibitions are incomplete")
    required_checks = set(contract["required_post_generation_checks"])
    if "consumer_agent_with_previous_result_and_all_five_locks" not in required_checks or "reject_if_regressed_dimensions_nonempty" not in required_checks:
        raise ValueError("post-generation consumer regression checks are required")
    if contract["on_consumer_regression"] != "reject_candidate_and_restore_baseline_candidate":
        raise ValueError("consumer regression must restore the baseline candidate")
    return contract


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routed_result")
    parser.add_argument("--workflow-input", required=True)
    args = parser.parse_args()
    try:
        contract = validate_contract(load(args.routed_result), load(args.workflow_input))
        print(json.dumps({"valid": True, "contract": contract}, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("generation edit contract: " + str(exc))


if __name__ == "__main__":
    main()
