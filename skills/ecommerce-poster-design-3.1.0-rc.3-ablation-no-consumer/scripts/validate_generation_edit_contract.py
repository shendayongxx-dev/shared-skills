#!/usr/bin/env python3
"""Validate a no-consumer aesthetic local-edit contract."""

import argparse
import hashlib
import json
from pathlib import Path

AESTHETIC_DIMENSIONS = {"composition", "hierarchy", "color", "typography", "consistency", "finish"}
FORBIDDEN_CHANGES = ["八组 protected_content 的事实、数量、含义和可读性", "本轮未开放的美学维度"]


def workflow_hash(workflow):
    candidate = workflow["candidate"]
    payload = json.dumps({"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "poster_image": candidate["poster_image"], "protected_content": candidate["protected_content"], "ablation": workflow["ablation"]}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_contract(routed, workflow):
    if routed.get("action") != "regenerate_then_full_pipeline":
        raise ValueError("edit contract requires regenerate_then_full_pipeline")
    contract = routed.get("generation_edit_contract")
    required = {"contract_version", "generation_mode", "baseline_candidate", "editable_aesthetic_dimensions", "locked_aesthetic_dimensions", "immutable_protected_content", "advisory_instructions", "forbidden_changes", "required_post_generation_checks", "ablation"}
    if not isinstance(contract, dict) or set(contract) != required:
        raise ValueError("invalid no-consumer aesthetic edit contract fields")
    if contract["contract_version"] != "aesthetic-edit-lock-no-consumer/1.0" or contract["generation_mode"] != "local_edit_only":
        raise ValueError("invalid no-consumer aesthetic contract")
    candidate = workflow["candidate"]
    expected = {"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "poster_image": candidate["poster_image"], "context_hash": workflow_hash(workflow)}
    if contract["baseline_candidate"] != expected:
        raise ValueError("baseline mismatch")
    editable, locked = contract["editable_aesthetic_dimensions"], contract["locked_aesthetic_dimensions"]
    if not editable or set(editable) | set(locked) != AESTHETIC_DIMENSIONS or set(editable) & set(locked):
        raise ValueError("aesthetic dimensions must form exact editable/locked partition")
    if contract["immutable_protected_content"] != candidate["protected_content"]:
        raise ValueError("protected content mismatch")
    if contract["advisory_instructions"] != routed.get("modify_suggestion") or contract["forbidden_changes"] != FORBIDDEN_CHANGES:
        raise ValueError("instruction scope mismatch")
    if set(contract["required_post_generation_checks"]) != {"HC-01..HC-12", "aesthetic_agent_no_consumer", "final_quality_gate_no_consumer"}:
        raise ValueError("post-generation checks mismatch")
    if contract["ablation"] != workflow["ablation"]:
        raise ValueError("ablation identity mismatch")
    return contract


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routed_result")
    parser.add_argument("--workflow-input", required=True)
    args = parser.parse_args()
    print(json.dumps({"valid": True, "contract": validate_contract(load(args.routed_result), load(args.workflow_input))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
