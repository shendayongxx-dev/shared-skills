#!/usr/bin/env python3
"""Assemble the exact A-D-AESTHETIC-3.0 wrapper from A-D-2.0 artifacts."""

import argparse
import json
from copy import deepcopy
from pathlib import Path


CONSUMER_DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}
PROTECTED_GROUPS = {
    "product_identity", "product_quantity", "brand_and_logo", "price_and_unit",
    "promotion_and_period", "selling_points", "cta", "legal_text",
}


def load(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate(candidate, consumer):
    if candidate.get("schema_version") != "A-D-2.0":
        raise ValueError("candidate must use A-D-2.0")
    if consumer.get("schema_version") != "A-D-2.0" or consumer.get("agent_name") != "consumer_agent":
        raise ValueError("formal A-D-2.0 consumer result required")
    if candidate.get("request_id") != consumer.get("request_id"):
        raise ValueError("consumer result belongs to another request")
    if candidate.get("loop_state", {}).get("version_id") != consumer.get("version_id"):
        raise ValueError("consumer result belongs to another image version")
    protected = candidate.get("protected_content")
    if not isinstance(protected, dict) or set(protected) != PROTECTED_GROUPS:
        raise ValueError("candidate must contain the exact eight protected-content groups")
    if protected != consumer.get("protected_content"):
        raise ValueError("protected content changed between candidate and consumer result")
    scores = consumer.get("dimension_scores")
    valid_pass = (
        consumer.get("pass") is True
        and consumer.get("hard_fail") is False
        and consumer.get("next_route") == "aesthetic_agent"
        and not consumer.get("regressed_dimensions")
        and type(consumer.get("score")) is int and consumer["score"] >= 80
        and isinstance(scores, dict) and set(scores) == CONSUMER_DIMENSIONS
        and all(type(scores[name]) is int and scores[name] >= 14 for name in CONSUMER_DIMENSIONS)
        and set(consumer.get("locked_dimensions", [])) == CONSUMER_DIMENSIONS
    )
    if not valid_pass:
        raise ValueError("aesthetic Agent requires a passing consumer result with all five dimensions locked")


def assemble(candidate, consumer):
    validate(candidate, consumer)
    return {"schema_version": "A-D-AESTHETIC-3.0", "candidate": deepcopy(candidate), "consumer_result": deepcopy(consumer)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit("aesthetic input assembler: refusing to overwrite existing output")
    try:
        workflow = assemble(load(args.candidate), load(args.consumer_result))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("aesthetic input assembler: " + str(exc))


if __name__ == "__main__":
    main()
