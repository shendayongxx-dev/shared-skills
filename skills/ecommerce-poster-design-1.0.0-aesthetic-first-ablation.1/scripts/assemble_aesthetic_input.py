#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


PROTECTED_GROUPS = [
    "product_identity", "product_quantity", "brand_and_logo", "price_and_unit",
    "promotion_and_period", "selling_points", "cta", "legal_text",
]


def load_json(path: str) -> Dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def flatten_protected_content(value: Dict[str, Any]) -> List[str]:
    if set(value) != set(PROTECTED_GROUPS):
        missing = [name for name in PROTECTED_GROUPS if name not in value]
        extra = [name for name in value if name not in PROTECTED_GROUPS]
        raise ValueError(f"invalid protected_content groups; missing={missing}, extra={extra}")
    flattened: List[str] = []
    for group in PROTECTED_GROUPS:
        item = value[group]
        if group == "product_quantity":
            if item is not None:
                if not isinstance(item, int) or isinstance(item, bool) or item < 1:
                    raise ValueError("product_quantity must be a positive integer or null")
                flattened.append(f"{group}: {item}")
            continue
        if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item):
            raise ValueError(f"{group} must be an array of strings")
        flattened.extend(f"{group}: {entry}" for entry in item)
    if not flattened:
        raise ValueError("protected_content cannot flatten to an empty array")
    return flattened


def assemble(source: Dict[str, Any], style: Dict[str, Any], protected: Dict[str, Any], poster: str) -> Dict[str, Any]:
    product = source.get("product") or {}
    commerce = source.get("commerce") or {}
    marketing = source.get("marketing") or {}
    image_refs = product.get("image_refs")
    selling_points = product.get("selling_points")
    if not isinstance(image_refs, list) or not image_refs or not isinstance(image_refs[0], str) or not image_refs[0]:
        raise ValueError("source_input.product.image_refs[0] is required")
    if not isinstance(selling_points, list) or not selling_points or any(not isinstance(x, str) or not x for x in selling_points):
        raise ValueError("source_input.product.selling_points must be a non-empty string array")
    price_text = commerce.get("price_text")
    marketing_target = marketing.get("goal")
    if not isinstance(price_text, str) or not price_text:
        raise ValueError("source_input.commerce.price_text is required by the aesthetic contract")
    if not isinstance(marketing_target, str) or not marketing_target:
        raise ValueError("source_input.marketing.goal is required")
    tags = style.get("tags") or {}
    scene_tags = [tags.get("audience_id"), tags.get("motivation_id"), tags.get("scenario_id")]
    normalized_tags = ["null" if value is None else value for value in scene_tags]
    if any(not isinstance(value, str) or not value for value in normalized_tags):
        raise ValueError("style_guide.tags must contain audience_id, motivation_id and scenario_id as strings or null")
    flatten_protected_content(protected)
    if not isinstance(poster, str) or not poster:
        raise ValueError("poster path is required")
    return {
        "poster_image": poster,
        "product_input": {
            "product_img": image_refs[0],
            "selling_points": selling_points,
            "price_text": price_text,
            "marketing_target": marketing_target,
            "scene_tags": normalized_tags,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--style", required=True)
    parser.add_argument("--protected", required=True)
    parser.add_argument("--poster", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--protected-output")
    args = parser.parse_args()
    source = load_json(args.source)
    style = load_json(args.style)
    protected = load_json(args.protected)
    payload = assemble(source, style, protected, args.poster)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.protected_output:
        snapshot = {"groups": protected, "aesthetic_flattened": flatten_protected_content(protected)}
        Path(args.protected_output).write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
