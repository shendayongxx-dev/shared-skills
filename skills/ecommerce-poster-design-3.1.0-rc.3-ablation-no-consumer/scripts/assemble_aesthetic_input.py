#!/usr/bin/env python3
"""Assemble the no-consumer aesthetic workflow input."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

PROTECTED_GROUPS = {
    "product_identity", "product_quantity", "brand_and_logo", "price_and_unit",
    "promotion_and_period", "selling_points", "cta", "legal_text",
}
SCHEMA = "A-D-AESTHETIC-3.1-ABLATION-NO-CONSUMER"


def load(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate(candidate):
    if candidate.get("schema_version") != "A-D-2.0":
        raise ValueError("candidate must use A-D-2.0")
    protected = candidate.get("protected_content")
    if not isinstance(protected, dict) or set(protected) != PROTECTED_GROUPS:
        raise ValueError("candidate must contain the exact eight protected-content groups")
    loop = candidate.get("loop_state") or {}
    if not candidate.get("request_id") or not candidate.get("poster_image") or not loop.get("version_id"):
        raise ValueError("candidate requires request_id, poster_image and version_id")


def assemble(candidate):
    validate(candidate)
    return {
        "schema_version": SCHEMA,
        "ablation": {
            "id": "no-consumer",
            "base_version": "3.1.0-rc.3",
            "consumer_artifacts_used": False,
        },
        "candidate": deepcopy(candidate),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit("aesthetic input assembler: refusing to overwrite existing output")
    try:
        workflow = assemble(load(args.candidate))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("aesthetic input assembler: " + str(exc))


if __name__ == "__main__":
    main()
