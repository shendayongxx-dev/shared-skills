#!/usr/bin/env python3
"""Assemble an aesthetic-first wrapper without fabricating consumer results."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

PROTECTED_GROUPS = {
    "product_identity", "product_quantity", "brand_and_logo", "price_and_unit",
    "promotion_and_period", "selling_points", "cta", "legal_text",
}

def load(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value

def assemble(candidate):
    if candidate.get("schema_version") != "A-D-2.0":
        raise ValueError("candidate must use A-D-2.0")
    if not candidate.get("request_id") or not candidate.get("loop_state", {}).get("version_id"):
        raise ValueError("candidate request_id and version_id are required")
    protected = candidate.get("protected_content")
    if not isinstance(protected, dict) or set(protected) != PROTECTED_GROUPS:
        raise ValueError("candidate must contain the exact eight protected-content groups")
    return {
        "schema_version": "A-D-AESTHETIC-3.0-AF",
        "evaluation_phase": "pre_consumer",
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
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(assemble(load(args.candidate)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("aesthetic input assembler: " + str(exc))

if __name__ == "__main__":
    main()
