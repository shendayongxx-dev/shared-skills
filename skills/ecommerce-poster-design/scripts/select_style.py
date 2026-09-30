from __future__ import annotations

import argparse
import json
from pathlib import Path


LEVELS = {3: "exact", 2: "two_dimension", 1: "single_dimension", 0: "global"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a style rule from C classification assets")
    parser.add_argument("asset_dir", type=Path)
    parser.add_argument("audience_id")
    parser.add_argument("motivation_id")
    parser.add_argument("scenario_id")
    parser.add_argument("--request-id", default="REQ-UNSPECIFIED")
    args = parser.parse_args()

    base = args.asset_dir.resolve()
    taxonomy = json.loads((base / "taxonomy.json").read_text(encoding="utf-8"))
    rules_doc = json.loads((base / "rules.json").read_text(encoding="utf-8"))

    allowed = {
        "audience_id": {
            item["id"] for item in taxonomy["audiences"] if item.get("status") == "active"
        },
        "motivation_id": {
            item["id"]
            for item in taxonomy["purchase_motivations"]
            if item.get("status") == "active"
        },
        "scenario_id": {
            item["id"] for item in taxonomy["scenarios"] if item.get("status") == "active"
        },
    }
    requested = {
        "audience_id": args.audience_id,
        "motivation_id": args.motivation_id,
        "scenario_id": args.scenario_id,
    }
    unknown = [key for key, value in requested.items() if value not in allowed[key]]
    if unknown:
        raise SystemExit("unknown taxonomy id(s): " + ", ".join(unknown))

    candidates = []
    for rule in rules_doc["rules"]:
        if rule.get("status") != "active":
            continue
        match = rule["match"]
        if not all(match[key] == "*" or match[key] == requested[key] for key in requested):
            continue
        specificity = sum(match[key] != "*" for key in requested)
        candidates.append((specificity, int(rule["priority"]), rule["rule_id"], rule))

    if not candidates:
        raise SystemExit("no compatible rule and no default rule")
    specificity, _, _, selected = max(candidates, key=lambda item: (item[0], item[1], item[2]))
    style = selected["style"]
    warnings = []
    if taxonomy.get("asset_status") == "demo_only":
        warnings.append("C classification assets are demo-only and must not be cited as market evidence")

    result = {
        "schema_version": "1.0",
        "taxonomy_version": taxonomy["taxonomy_version"],
        "asset_version": rules_doc["rules_version"],
        "request_id": args.request_id,
        "tags": requested,
        "classification_evidence": [],
        "confidence": {"audience": None, "motivation": None, "scenario": None},
        "source_rule_ids": [selected["rule_id"]],
        "source_case_ids": selected.get("recommended_case_ids", []),
        "fallback_level": LEVELS[specificity],
        "palette": style["palette"],
        "typography": {
            "headline_character": style["headline_character"],
            "body_character": style["body_character"],
        },
        "layout": {
            "composition": style["composition"],
            "product_ratio": style["product_ratio"],
            "information_hierarchy": style["information_hierarchy"],
        },
        "info_density": style["info_density"],
        "promotion_intensity": style["promotion_intensity"],
        "cta_guidance": style["cta_guidance"],
        "prohibited_styles": style["prohibited_styles"],
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
