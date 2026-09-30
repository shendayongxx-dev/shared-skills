from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
VALID_STATUS = {"active", "draft", "deprecated", "demo_only"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(errors, f"missing file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        fail(errors, f"invalid JSON: {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        fail(errors, f"top-level JSON must be an object: {path}")
        return {}
    return value


def collect_ids(items: object, label: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        fail(errors, f"{label} must be an array")
        return set()
    result: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            fail(errors, f"{label}[{index}] must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail(errors, f"{label}[{index}] has no valid id")
            continue
        if item_id in result:
            fail(errors, f"duplicate id {item_id} in {label}")
        result.add(item_id)
        if item.get("status") not in VALID_STATUS:
            fail(errors, f"invalid status for {item_id}")
    return result


def main() -> int:
    base = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent / "assets" / "classification"
    )
    errors: list[str] = []
    warnings: list[str] = []

    taxonomy = load_json(base / "taxonomy.json", errors)
    rules_doc = load_json(base / "rules.json", errors)

    if taxonomy.get("schema_version") != "1.0":
        fail(errors, "taxonomy schema_version must be 1.0")
    if rules_doc.get("schema_version") != "1.0":
        fail(errors, "rules schema_version must be 1.0")
    if taxonomy.get("taxonomy_version") != rules_doc.get("taxonomy_version"):
        fail(errors, "taxonomy_version mismatch between taxonomy.json and rules.json")

    audiences = collect_ids(taxonomy.get("audiences"), "audiences", errors)
    motivations = collect_ids(
        taxonomy.get("purchase_motivations"), "purchase_motivations", errors
    )
    scenarios = collect_ids(taxonomy.get("scenarios"), "scenarios", errors)

    rules = rules_doc.get("rules")
    if not isinstance(rules, list):
        fail(errors, "rules must be an array")
        rules = []

    rule_ids: set[str] = set()
    referenced_case_ids: set[str] = set()
    default_count = 0
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(errors, f"rules[{index}] must be an object")
            continue
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            fail(errors, f"rules[{index}] has no valid rule_id")
            continue
        if rule_id in rule_ids:
            fail(errors, f"duplicate rule_id {rule_id}")
        rule_ids.add(rule_id)
        if rule.get("status") not in VALID_STATUS:
            fail(errors, f"invalid status for rule {rule_id}")
        if not isinstance(rule.get("priority"), int):
            fail(errors, f"priority must be an integer for rule {rule_id}")

        match = rule.get("match")
        if not isinstance(match, dict):
            fail(errors, f"missing match object for rule {rule_id}")
            continue
        checks = [
            ("audience_id", audiences),
            ("motivation_id", motivations),
            ("scenario_id", scenarios),
        ]
        for key, allowed in checks:
            value = match.get(key)
            if value != "*" and value not in allowed:
                fail(errors, f"unknown {key}={value!r} in rule {rule_id}")
        if all(match.get(key) == "*" for key, _ in checks):
            default_count += 1
            if rule_id != "R-DEFAULT":
                fail(errors, "the all-wildcard rule must be named R-DEFAULT")

        style = rule.get("style")
        if not isinstance(style, dict):
            fail(errors, f"missing style object for rule {rule_id}")
            continue
        ratio = style.get("product_ratio")
        if not isinstance(ratio, (int, float)) or not 0 <= ratio <= 1:
            fail(errors, f"product_ratio must be 0..1 for rule {rule_id}")
        for field in ("info_density", "promotion_intensity"):
            value = style.get(field)
            if not isinstance(value, int) or not 1 <= value <= 5:
                fail(errors, f"{field} must be an integer 1..5 for rule {rule_id}")
        palette = style.get("palette", [])
        if not isinstance(palette, list):
            fail(errors, f"palette must be an array for rule {rule_id}")
        else:
            for color in palette:
                if not isinstance(color, dict) or not HEX.match(str(color.get("hex", ""))):
                    fail(errors, f"invalid palette hex in rule {rule_id}")
        case_ids = rule.get("recommended_case_ids", [])
        if not isinstance(case_ids, list):
            fail(errors, f"recommended_case_ids must be an array for rule {rule_id}")
        else:
            referenced_case_ids.update(str(value) for value in case_ids)

    if default_count != 1:
        fail(errors, f"expected exactly one global default rule, found {default_count}")

    index_path = base / "case-index.csv"
    index_rows: list[dict[str, str]] = []
    try:
        with index_path.open("r", encoding="utf-8-sig", newline="") as handle:
            index_rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        fail(errors, f"missing file: {index_path}")

    case_ids: set[str] = set()
    for row_number, row in enumerate(index_rows, 2):
        case_id = row.get("case_id", "")
        if not case_id:
            fail(errors, f"case-index row {row_number} has no case_id")
            continue
        if case_id in case_ids:
            fail(errors, f"duplicate case_id {case_id}")
        case_ids.add(case_id)
        for key, allowed in (
            ("audience_id", audiences),
            ("motivation_id", motivations),
            ("scenario_id", scenarios),
        ):
            if row.get(key) not in allowed:
                fail(errors, f"unknown {key} in case {case_id}")
        for rid in filter(None, row.get("rule_ids", "").split(";")):
            if rid not in rule_ids:
                fail(errors, f"unknown rule_id {rid} in case {case_id}")
        metadata_path = base / row.get("metadata_path", "")
        if not metadata_path.is_file():
            fail(errors, f"missing metadata for case {case_id}: {metadata_path}")
        if row.get("storage_type") == "local":
            asset_path = base / row.get("asset_location", "")
            if not asset_path.is_file():
                fail(errors, f"missing local asset for case {case_id}: {asset_path}")

    for case_id in sorted(referenced_case_ids - case_ids):
        fail(errors, f"rule references unknown case_id {case_id}")

    if taxonomy.get("asset_status") == "demo_only":
        warnings.append("classification assets are demo-only and not market evidence")

    result = {
        "valid": not errors,
        "base": str(base),
        "counts": {
            "audiences": len(audiences),
            "purchase_motivations": len(motivations),
            "scenarios": len(scenarios),
            "rules": len(rule_ids),
            "cases": len(case_ids),
        },
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
