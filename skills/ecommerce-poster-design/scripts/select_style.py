from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


LEVELS = {3: "exact", 2: "two_dimension", 1: "single_dimension", 0: "global"}
NULL_TOKENS = {"null", "none", "-"}
APPROVED_RIGHTS = {
    "owned",
    "licensed",
    "permission_granted",
    "public_domain",
    "internal_authorized",
    "internal_reference_authorized",
}
HIERARCHY_LABELS = {
    "product": "商品主体",
    "core_benefit": "核心卖点",
    "proof_or_price": "已提供的证明、价格或活动信息",
    "cta_if_provided": "已提供的行动提示",
}


def parse_id(value: str) -> str | None:
    return None if value.lower() in NULL_TOKENS else value


def deep_merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Objects merge recursively; child scalars and arrays replace parent values."""
    merged = dict(parent)
    for key, value in child.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def compile_style(
    rule_id: str,
    rules_by_id: dict[str, dict[str, Any]],
    resolving: tuple[str, ...] = (),
) -> tuple[dict[str, Any], list[str]]:
    if rule_id in resolving:
        raise SystemExit("inheritance cycle: " + " -> ".join((*resolving, rule_id)))
    rule = rules_by_id.get(rule_id)
    if not rule:
        raise SystemExit(f"missing inherited rule: {rule_id}")
    style = rule.get("style")
    if not isinstance(style, dict):
        raise SystemExit(f"missing style object for rule {rule_id}")
    parent_id = rule.get("extends_rule_id")
    if not parent_id:
        return dict(style), [rule_id]
    parent = rules_by_id.get(parent_id)
    if not parent:
        raise SystemExit(f"missing inherited rule: {parent_id}")
    if rule.get("status") == "active" and parent.get("status") != "active":
        raise SystemExit(f"active rule {rule_id} inherits non-active rule {parent_id}")
    parent_style, chain = compile_style(parent_id, rules_by_id, (*resolving, rule_id))
    return deep_merge(parent_style, style), [*chain, rule_id]


def choose_palette(
    style: dict[str, Any], rule_id: str, requested_palette_id: str | None
) -> dict[str, Any]:
    palette_sets = style.get("palette_sets")
    if isinstance(palette_sets, list) and palette_sets:
        if requested_palette_id:
            selected = next(
                (item for item in palette_sets if item.get("palette_id") == requested_palette_id),
                None,
            )
            if selected is None:
                raise SystemExit(f"unknown palette_id for compiled rule {rule_id}: {requested_palette_id}")
            return selected
        return palette_sets[0]
    palette = style.get("palette")
    if isinstance(palette, list) and palette:
        if requested_palette_id and requested_palette_id != f"legacy:{rule_id}":
            raise SystemExit(f"legacy rule {rule_id} only supports palette_id legacy:{rule_id}")
        return {"palette_id": f"legacy:{rule_id}", "colors": palette}
    raise SystemExit(f"compiled rule {rule_id} has no usable palette")


def information_hierarchy(style: dict[str, Any]) -> list[str]:
    legacy = style.get("information_hierarchy")
    if isinstance(legacy, list) and legacy:
        return [str(value) for value in legacy]
    preference = style.get("hierarchy_preference")
    if isinstance(preference, list) and preference:
        return [HIERARCHY_LABELS.get(str(value), str(value)) for value in preference]
    return ["商品主体", "核心卖点", "已提供的价格或活动信息", "已提供的行动提示"]


def load_case_rows(base: Path) -> dict[str, dict[str, str]]:
    nested = base / "cases" / "case-index.csv"
    legacy = base / "case-index.csv"
    path = nested if nested.is_file() else legacy
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("case_id", ""): row for row in csv.DictReader(handle) if row.get("case_id")}


def filter_cases(
    case_ids: list[str],
    case_rows: dict[str, dict[str, str]],
    demo_mode: bool,
    requested: dict[str, str | None],
) -> tuple[list[str], list[dict[str, str]], list[dict[str, Any]], int]:
    eligible: list[str] = []
    statuses: list[dict[str, str]] = []
    references: list[dict[str, Any]] = []
    filtered = 0
    for case_id in case_ids:
        row = case_rows.get(case_id)
        if row is None:
            filtered += 1
            continue
        review_status = row.get("review_status") or row.get("status") or "unknown"
        statuses.append(
            {
                "case_id": case_id,
                "review_status": review_status,
                "rights_status": row.get("rights_status", ""),
                "usage_status": row.get("usage_status", ""),
            }
        )
        if demo_mode and review_status == "demo_only":
            eligible.append(case_id)
            continue
        is_seed = str(row.get("is_seed", "")).lower() == "true"
        rights_status = row.get("rights_status", "")
        usage_status = row.get("usage_status", "")
        if (
            review_status == "approved"
            and is_seed
            and rights_status in APPROVED_RIGHTS
            and usage_status != "research_reference_only"
        ):
            eligible.append(case_id)
            references.append(
                {
                    "case_id": case_id,
                    "title": row.get("title", ""),
                    "external_image_url": row.get("external_image_url", ""),
                    "source_url": row.get("source_url", ""),
                    "checksum_sha256": row.get("checksum_sha256", ""),
                    "tags": {
                        "audience_id": row.get("audience_id", ""),
                        "motivation_id": row.get("motivation_id", ""),
                        "scenario_id": row.get("scenario_id", ""),
                    },
                    "usage_scope": "internal_reference_only",
                    "public_repository_allowed": False,
                    "_match_score": sum(
                        value is not None and row.get(key) == value
                        for key, value in requested.items()
                    ),
                }
            )
        else:
            filtered += 1
    if references:
        best_score = max(item["_match_score"] for item in references)
        best_ids = {
            item["case_id"] for item in references if item["_match_score"] == best_score
        }
        eligible = [case_id for case_id in eligible if case_id in best_ids]
        references = [item for item in references if item["case_id"] in best_ids]
        for item in references:
            item.pop("_match_score", None)
    return eligible, statuses, references, filtered


def main() -> int:
    parser = argparse.ArgumentParser(description="Select and compile a style rule from C classification assets")
    parser.add_argument("asset_dir", type=Path)
    parser.add_argument("audience_id", help="taxonomy ID, or null/none/- when evidence is absent")
    parser.add_argument("motivation_id", help="taxonomy ID, or null/none/- when evidence is absent")
    parser.add_argument("scenario_id", help="taxonomy ID, or null/none/- when evidence is absent")
    parser.add_argument("--request-id", default="REQ-UNSPECIFIED")
    parser.add_argument("--palette-id", default=None)
    args = parser.parse_args()

    base = args.asset_dir.resolve()
    taxonomy = json.loads((base / "taxonomy.json").read_text(encoding="utf-8"))
    rules_doc = json.loads((base / "rules.json").read_text(encoding="utf-8"))
    manifest_path = base / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}

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
        "audience_id": parse_id(args.audience_id),
        "motivation_id": parse_id(args.motivation_id),
        "scenario_id": parse_id(args.scenario_id),
    }
    unknown = [
        key
        for key, value in requested.items()
        if value is not None and value not in allowed[key]
    ]
    if unknown:
        raise SystemExit("unknown taxonomy id(s): " + ", ".join(unknown))

    active_rules = [rule for rule in rules_doc["rules"] if rule.get("status") == "active"]
    rules_by_id = {rule["rule_id"]: rule for rule in rules_doc["rules"]}
    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for rule in active_rules:
        match = rule["match"]
        compatible = True
        for key, value in requested.items():
            if value is None:
                compatible = compatible and match[key] == "*"
            else:
                compatible = compatible and (match[key] == "*" or match[key] == value)
        if not compatible:
            continue
        specificity = sum(match[key] != "*" for key in requested)
        candidates.append((specificity, int(rule["priority"]), rule["rule_id"], rule))

    if not candidates:
        raise SystemExit("no compatible active rule and no default rule")
    specificity, _, _, selected = sorted(
        candidates, key=lambda item: (-item[0], -item[1], item[2])
    )[0]
    style, inheritance_chain = compile_style(selected["rule_id"], rules_by_id)
    selected_palette = choose_palette(style, selected["rule_id"], args.palette_id)

    warnings: list[str] = []
    demo_mode = taxonomy.get("asset_status") == "demo_only" or rules_doc.get("asset_status") == "demo_only"
    if demo_mode:
        warnings.append("C classification assets are demo-only and must not be cited as market evidence")
    if manifest and manifest.get("formal_release") is not True:
        warnings.append("C package is an integration candidate, not a formal release")
    if any(value is None for value in requested.values()):
        warnings.append("One or more classification dimensions lack evidence; human review is required")

    raw_case_ids = [str(value) for value in selected.get("recommended_case_ids", [])]
    source_case_ids, source_case_statuses, source_case_references, filtered_count = filter_cases(
        raw_case_ids, load_case_rows(base), demo_mode, requested
    )
    if filtered_count:
        warnings.append(
            f"Filtered {filtered_count} case reference(s) that are not approved, rights-cleared seeds"
        )

    result = {
        "schema_version": "1.0",
        "source_schema_version": taxonomy.get("schema_version"),
        "taxonomy_version": taxonomy["taxonomy_version"],
        "asset_version": rules_doc["rules_version"],
        "request_id": args.request_id,
        "tags": requested,
        "classification_evidence": [],
        "confidence": {"audience": None, "motivation": None, "scenario": None},
        "needs_human_review": any(value is None for value in requested.values()),
        "source_rule_ids": [selected["rule_id"]],
        "inheritance_chain": inheritance_chain,
        "source_case_ids": source_case_ids,
        "source_case_statuses": source_case_statuses,
        "source_case_references": source_case_references,
        "fallback_level": LEVELS[specificity],
        "selected_palette_set": selected_palette,
        "palette": selected_palette["colors"],
        "typography": {
            "headline_character": style["headline_character"],
            "body_character": style["body_character"],
        },
        "layout": {
            "composition": style["composition"],
            "product_ratio": style["product_ratio"],
            "information_hierarchy": information_hierarchy(style),
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
