#!/usr/bin/env python3
"""Validate a no-consumer final-quality local-edit contract."""

import argparse
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_contract(routed, workflow, review):
    require(routed.get("action") == "regenerate_then_full_pipeline", "route does not authorize generation")
    contract = routed.get("generation_edit_contract")
    fields = {"contract_version", "generation_mode", "baseline_candidate", "authorized_defects", "editable_regions", "editable_objects", "protected_objects", "immutable_protected_content", "required_post_generation_checks", "ablation"}
    require(isinstance(contract, dict) and set(contract) == fields, "invalid no-consumer contract fields")
    require(contract["contract_version"] == "final-quality-edit-lock-no-consumer/1.0" and contract["generation_mode"] == "local_edit_only", "invalid contract version or mode")
    candidate = workflow["candidate"]
    baseline = {"request_id": candidate["request_id"], "version_id": candidate["loop_state"]["version_id"], "poster_image": candidate["poster_image"]}
    require(contract["baseline_candidate"] == baseline, "baseline mismatch")
    require(contract["authorized_defects"] == review["defects"], "authorized defects mismatch")
    require(contract["editable_regions"] == sorted({x["region"] for x in review["defects"]}), "editable region mismatch")
    require(contract["editable_objects"] == sorted({v for x in review["defects"] for v in x["editable_objects"]}), "editable object mismatch")
    require(contract["protected_objects"] == sorted({v for x in review["defects"] for v in x["protected_objects"]}), "protected object mismatch")
    require(contract["immutable_protected_content"] == candidate["protected_content"], "protected content mismatch")
    require(set(contract["required_post_generation_checks"]) == {"HC-01..HC-12", "aesthetic_agent_no_consumer", "final_quality_gate_no_consumer"}, "post-generation checks mismatch")
    require(contract["ablation"] == workflow["ablation"] == review["ablation"], "ablation identity mismatch")
    return contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("routed_result")
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--review", required=True)
    args = parser.parse_args()
    print(json.dumps(validate_contract(load(args.routed_result), load(args.workflow_input), load(args.review)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
