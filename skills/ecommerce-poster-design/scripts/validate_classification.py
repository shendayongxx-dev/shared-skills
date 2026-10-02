from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
VALID_STATUS = {"active", "draft", "deprecated", "demo_only"}
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.0-rc.1", "2.0.0-rc.1"}
PROVISIONAL_SCHEMA_VERSIONS = {"1.0-rc.1", "2.0.0-rc.1"}
APPROVED_RIGHTS = {
    "owned",
    "licensed",
    "permission_granted",
    "public_domain",
    "internal_authorized",
}
REQUIRED_PALETTE_ROLES = {"background", "support", "accent", "text"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def warn(warnings: list[str], blockers: set[str], code: str, message: str) -> None:
    warnings.append(f"{code}: {message}")
    blockers.add(code)


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
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


def deep_merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Merge objects recursively; child scalars and arrays replace parent values."""
    merged = dict(parent)
    for key, value in child.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_style(
    rule_id: str,
    rules_by_id: dict[str, dict[str, Any]],
    errors: list[str],
    resolving: tuple[str, ...] = (),
) -> dict[str, Any]:
    if rule_id in resolving:
        fail(errors, "inheritance cycle: " + " -> ".join((*resolving, rule_id)))
        return {}
    rule = rules_by_id.get(rule_id)
    if not rule:
        fail(errors, f"missing inherited rule: {rule_id}")
        return {}
    style = rule.get("style")
    if not isinstance(style, dict):
        fail(errors, f"missing style object for rule {rule_id}")
        style = {}
    parent_id = rule.get("extends_rule_id")
    if not parent_id:
        return dict(style)
    if not isinstance(parent_id, str):
        fail(errors, f"extends_rule_id must be a string for rule {rule_id}")
        return dict(style)
    parent = rules_by_id.get(parent_id)
    if parent is not None and rule.get("status") == "active" and parent.get("status") != "active":
        fail(errors, f"active rule {rule_id} inherits non-active rule {parent_id}")
    parent_style = resolve_style(parent_id, rules_by_id, errors, (*resolving, rule_id))
    return deep_merge(parent_style, style)


def validate_palette_sets(rule_id: str, palette_sets: object, errors: list[str]) -> None:
    if not isinstance(palette_sets, list) or not palette_sets:
        fail(errors, f"palette_sets must be a non-empty array for rule {rule_id}")
        return
    palette_ids: set[str] = set()
    for index, palette_set in enumerate(palette_sets):
        if not isinstance(palette_set, dict):
            fail(errors, f"palette_sets[{index}] must be an object for rule {rule_id}")
            continue
        palette_id = palette_set.get("palette_id")
        if not isinstance(palette_id, str) or not palette_id:
            fail(errors, f"palette_sets[{index}] has no palette_id for rule {rule_id}")
        elif palette_id in palette_ids:
            fail(errors, f"duplicate palette_id {palette_id} in rule {rule_id}")
        else:
            palette_ids.add(palette_id)
        colors = palette_set.get("colors")
        if not isinstance(colors, list) or not 4 <= len(colors) <= 6:
            fail(errors, f"palette {palette_id!r} must contain 4..6 colors for rule {rule_id}")
            continue
        roles: set[str] = set()
        for color in colors:
            if not isinstance(color, dict) or not HEX.match(str(color.get("hex", ""))):
                fail(errors, f"invalid palette hex in rule {rule_id}, palette {palette_id!r}")
                continue
            role = color.get("role")
            if isinstance(role, str):
                roles.add(role)
        missing = sorted(REQUIRED_PALETTE_ROLES - roles)
        if missing:
            fail(errors, f"palette {palette_id!r} in rule {rule_id} misses roles: {', '.join(missing)}")


def validate_legacy_palette(rule_id: str, palette: object, errors: list[str]) -> None:
    if not isinstance(palette, list) or not palette:
        fail(errors, f"palette must be a non-empty array for rule {rule_id}")
        return
    for color in palette:
        if not isinstance(color, dict) or not HEX.match(str(color.get("hex", ""))):
            fail(errors, f"invalid palette hex in rule {rule_id}")


def find_case_index(base: Path, errors: list[str], warnings: list[str]) -> Path | None:
    nested = base / "cases" / "case-index.csv"
    legacy = base / "case-index.csv"
    if nested.is_file():
        if legacy.is_file():
            warnings.append("DUPLICATE_CASE_INDEX: using cases/case-index.csv and ignoring root case-index.csv")
        return nested
    if legacy.is_file():
        return legacy
    fail(errors, f"missing file: expected {nested} or {legacy}")
    return None


def validate_manifest(base: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    files = manifest.get("files")
    if not isinstance(files, list):
        fail(errors, "manifest files must be an array")
        return
    listed: set[str] = set()
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            fail(errors, f"manifest files[{index}] must be an object")
            continue
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            fail(errors, f"manifest files[{index}] has no path")
            continue
        if rel in listed:
            fail(errors, f"duplicate manifest path: {rel}")
        listed.add(rel)
        path = (base / rel).resolve()
        try:
            path.relative_to(base.resolve())
        except ValueError:
            fail(errors, f"manifest path escapes package: {rel}")
            continue
        if not path.is_file():
            fail(errors, f"manifest file missing: {rel}")
            continue
        if item.get("bytes") != path.stat().st_size:
            fail(errors, f"manifest byte count mismatch: {rel}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if item.get("sha256") != actual_hash:
            fail(errors, f"manifest sha256 mismatch: {rel}")
    actual = {
        path.relative_to(base).as_posix()
        for path in base.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    for rel in sorted(actual - listed):
        fail(errors, f"file not listed in manifest: {rel}")
    for rel in sorted(listed - actual):
        fail(errors, f"manifest lists missing file: {rel}")


def main() -> int:
    base = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent / "assets" / "classification"
    )
    errors: list[str] = []
    warnings: list[str] = []
    production_blockers: set[str] = set()

    taxonomy = load_json(base / "taxonomy.json", errors)
    rules_doc = load_json(base / "rules.json", errors)
    manifest_path = base / "manifest.json"
    manifest = load_json(manifest_path, errors) if manifest_path.is_file() else {}
    if manifest:
        validate_manifest(base, manifest, errors)

    taxonomy_schema = taxonomy.get("schema_version")
    rules_schema = rules_doc.get("schema_version")
    for label, value in (("taxonomy", taxonomy_schema), ("rules", rules_schema)):
        if value not in SUPPORTED_SCHEMA_VERSIONS:
            fail(errors, f"unsupported {label} schema_version: {value!r}")
    if taxonomy_schema != rules_schema:
        fail(errors, "schema_version mismatch between taxonomy.json and rules.json")
    if taxonomy_schema in PROVISIONAL_SCHEMA_VERSIONS:
        warn(
            warnings,
            production_blockers,
            "PROVISIONAL_SCHEMA",
            f"schema {taxonomy_schema} is accepted for integration testing but not frozen",
        )
    if taxonomy.get("taxonomy_version") != rules_doc.get("taxonomy_version"):
        fail(errors, "taxonomy_version mismatch between taxonomy.json and rules.json")

    audiences = collect_ids(taxonomy.get("audiences"), "audiences", errors)
    motivations = collect_ids(
        taxonomy.get("purchase_motivations"), "purchase_motivations", errors
    )
    scenarios = collect_ids(taxonomy.get("scenarios"), "scenarios", errors)

    rules_value = rules_doc.get("rules")
    if not isinstance(rules_value, list):
        fail(errors, "rules must be an array")
        rules_value = []
    rules = [rule for rule in rules_value if isinstance(rule, dict)]
    if len(rules) != len(rules_value):
        fail(errors, "every rule must be an object")

    rules_by_id: dict[str, dict[str, Any]] = {}
    for index, rule in enumerate(rules):
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            fail(errors, f"rules[{index}] has no valid rule_id")
            continue
        if rule_id in rules_by_id:
            fail(errors, f"duplicate rule_id {rule_id}")
        rules_by_id[rule_id] = rule

    referenced_case_ids: set[str] = set()
    default_count = 0
    for rule_id, rule in rules_by_id.items():
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

        resolved_style = resolve_style(rule_id, rules_by_id, errors)
        ratio = resolved_style.get("product_ratio")
        if not isinstance(ratio, (int, float)) or not 0 <= ratio <= 1:
            fail(errors, f"product_ratio must be 0..1 for rule {rule_id}")
        for field in ("info_density", "promotion_intensity"):
            value = resolved_style.get(field)
            if not isinstance(value, int) or not 1 <= value <= 5:
                fail(errors, f"{field} must be an integer 1..5 for rule {rule_id}")
        if "palette_sets" in resolved_style:
            validate_palette_sets(rule_id, resolved_style.get("palette_sets"), errors)
        else:
            validate_legacy_palette(rule_id, resolved_style.get("palette"), errors)

        case_ids = rule.get("recommended_case_ids", [])
        if not isinstance(case_ids, list):
            fail(errors, f"recommended_case_ids must be an array for rule {rule_id}")
        else:
            referenced_case_ids.update(str(value) for value in case_ids)

    if default_count != 1:
        fail(errors, f"expected exactly one global default rule, found {default_count}")

    index_path = find_case_index(base, errors, warnings)
    index_rows: list[dict[str, str]] = []
    if index_path is not None:
        try:
            with index_path.open("r", encoding="utf-8-sig", newline="") as handle:
                index_rows = list(csv.DictReader(handle))
        except (OSError, csv.Error) as exc:
            fail(errors, f"cannot read case index {index_path}: {exc}")

    case_ids: set[str] = set()
    approved_cases = 0
    eligible_seed_cases = 0
    draft_marked_seed = 0
    case_status_by_id: dict[str, str] = {}
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
            if rid not in rules_by_id:
                fail(errors, f"unknown rule_id {rid} in case {case_id}")

        metadata_rel = row.get("metadata_path", "")
        metadata_path = base / metadata_rel
        metadata = load_json(metadata_path, errors) if metadata_rel else {}
        if metadata and metadata.get("case_id") != case_id:
            fail(errors, f"metadata case_id mismatch for case {case_id}")
        if row.get("storage_type") == "local":
            asset_path = base / row.get("asset_location", "")
            if not asset_path.is_file():
                fail(errors, f"missing local asset for case {case_id}: {asset_path}")

        review_status = (
            row.get("review_status")
            or metadata.get("review_status")
            or row.get("status")
            or metadata.get("case_status")
            or "unknown"
        )
        case_status_by_id[case_id] = review_status
        is_seed = str(row.get("is_seed", "")).lower() == "true"
        rights = metadata.get("rights") if isinstance(metadata.get("rights"), dict) else {}
        source = metadata.get("source") if isinstance(metadata.get("source"), dict) else {}
        rights_status = row.get("rights_status") or rights.get("rights_status", "")
        usage_status = row.get("usage_status") or source.get("usage_status", "")
        if review_status == "approved":
            approved_cases += 1
        elif is_seed and review_status != "demo_only":
            draft_marked_seed += 1
        if (
            review_status == "approved"
            and is_seed
            and rights_status in APPROVED_RIGHTS
            and usage_status != "research_reference_only"
        ):
            eligible_seed_cases += 1

    for case_id in sorted(referenced_case_ids - case_ids):
        fail(errors, f"rule references unknown case_id {case_id}")

    draft_references = sum(
        1 for case_id in referenced_case_ids if case_status_by_id.get(case_id) == "draft"
    )
    if draft_marked_seed:
        warn(
            warnings,
            production_blockers,
            "DRAFT_MARKED_SEED",
            f"{draft_marked_seed} draft cases are marked is_seed=true",
        )
    if draft_references:
        warnings.append(
            f"DRAFT_CASE_REFERENCES: rules reference {draft_references} draft cases; selectors must filter them"
        )
    if approved_cases == 0 and taxonomy.get("asset_status") != "demo_only":
        warn(
            warnings,
            production_blockers,
            "NO_APPROVED_CASES",
            "the package has no approved cases",
        )
    if taxonomy.get("asset_status") == "demo_only" or rules_doc.get("asset_status") == "demo_only":
        warn(
            warnings,
            production_blockers,
            "DEMO_ONLY",
            "classification assets are demo-only and not market evidence",
        )
    if manifest and manifest.get("formal_release") is not True:
        warn(
            warnings,
            production_blockers,
            "PACKAGE_NOT_FORMAL",
            "manifest marks this package as non-formal",
        )

    result = {
        "valid": not errors,
        "production_ready": not errors and not production_blockers and eligible_seed_cases > 0,
        "base": str(base),
        "case_index": str(index_path) if index_path else None,
        "schema_version": taxonomy_schema,
        "counts": {
            "audiences": len(audiences),
            "purchase_motivations": len(motivations),
            "scenarios": len(scenarios),
            "rules": len(rules_by_id),
            "cases": len(case_ids),
            "approved_cases": approved_cases,
            "eligible_seed_cases": eligible_seed_cases,
        },
        "production_blockers": sorted(production_blockers),
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
