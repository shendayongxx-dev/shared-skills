#!/usr/bin/env python3
"""Bridge the A-D-2.0 consumer contract to aesthetic-agent v2.

The aesthetic business input remains exactly its published two-field shape.
Upstream proof and the eight protected-content groups travel in orchestrator
context, so interface adaptation never drops data or invents user facts.
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Tuple


DIMENSIONS = {
    "product_recognition",
    "benefit_clarity",
    "offer_visibility",
    "population_scene_fit",
    "purchase_drive",
}
PROTECTED_GROUPS = {
    "product_identity",
    "product_quantity",
    "brand_and_logo",
    "price_and_unit",
    "promotion_and_period",
    "selling_points",
    "cta",
    "legal_text",
}


def load(path: str) -> Dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write(path: str, value: Dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _non_empty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _validate_protected(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != PROTECTED_GROUPS:
        raise ValueError("protected_content must contain exactly the eight A-D-2.0 groups")
    quantity = value["product_quantity"]
    if quantity is not None and (type(quantity) is not int or quantity < 1):
        raise ValueError("protected_content.product_quantity must be null or a positive integer")
    for name in PROTECTED_GROUPS - {"product_quantity"}:
        items = value[name]
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise ValueError(f"protected_content.{name} must be a string list")


def assemble(
    consumer_input: Dict[str, Any],
    consumer_result: Dict[str, Any],
    hard_check_report: str,
    consumer_report: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if consumer_input.get("schema_version") != "A-D-2.0":
        raise ValueError("consumer input must use A-D-2.0")
    if consumer_result.get("schema_version") != "A-D-2.0":
        raise ValueError("consumer result must use A-D-2.0")
    if consumer_result.get("agent_name") != "consumer_agent":
        raise ValueError("expected consumer_agent result")
    if consumer_result.get("request_id") != consumer_input.get("request_id"):
        raise ValueError("consumer request_id does not match its input")
    if (consumer_input.get("source_input") or {}).get("request_id") != consumer_input.get("request_id"):
        raise ValueError("consumer source_input.request_id does not match its envelope")
    if (consumer_input.get("loop_state") or {}).get("version_id") != consumer_result.get("version_id"):
        raise ValueError("consumer version_id does not match its input loop state")
    scores = consumer_result.get("dimension_scores") or {}
    valid_pass = (
        consumer_result.get("pass") is True
        and consumer_result.get("next_route") == "aesthetic_agent"
        and consumer_result.get("hard_fail") is False
        and not consumer_result.get("regressed_dimensions")
        and type(consumer_result.get("score")) is int
        and consumer_result["score"] >= 80
        and set(scores) == DIMENSIONS
        and all(type(scores[name]) is int and scores[name] >= 14 for name in DIMENSIONS)
    )
    if not valid_pass:
        raise ValueError("aesthetic Agent requires a current, passing A-D-2.0 consumer result")

    source = consumer_input.get("source_input") or {}
    product = source.get("product") or {}
    commerce = source.get("commerce") or {}
    marketing = source.get("marketing") or {}
    evaluation = consumer_input.get("evaluation_context") or {}
    canvas = source.get("canvas") or {}
    protected = deepcopy(consumer_result.get("protected_content"))
    _validate_protected(protected)
    if protected != consumer_input.get("protected_content"):
        raise ValueError("consumer result changed or dropped input protected_content")

    selling_points = product.get("selling_points")
    if not isinstance(selling_points, list) or not selling_points or not all(
        isinstance(item, str) and item.strip() for item in selling_points
    ):
        raise ValueError("source product.selling_points must be a non-empty string list")
    scene_tags = evaluation.get("scene_tags")
    if not isinstance(scene_tags, list) or not scene_tags or not all(
        isinstance(item, str) and item.strip() for item in scene_tags
    ):
        raise ValueError("evaluation_context.scene_tags must be a non-empty string list")
    image_refs = product.get("image_refs")
    if not isinstance(image_refs, list) or not image_refs or evaluation.get("product_img") != image_refs[0]:
        raise ValueError("evaluation_context.product_img must match the primary source product image")

    aesthetic_input = {
        "poster_image": _non_empty_string(consumer_input.get("poster_image"), "poster_image"),
        "product_input": {
            "product_img": _non_empty_string(evaluation.get("product_img"), "product_img"),
            "selling_points": list(selling_points),
            "price_text": _non_empty_string(commerce.get("price_text"), "price_text"),
            "marketing_target": _non_empty_string(marketing.get("goal"), "marketing.goal"),
            "scene_tags": list(scene_tags),
        },
    }
    version_id = _non_empty_string(consumer_result.get("version_id"), "version_id")
    context = {
        "mode": "integrated",
        "version": version_id,
        "hard_check": {
            "version": version_id,
            "status": "pass",
            "report_ref": _non_empty_string(hard_check_report, "hard_check_report"),
        },
        "consumer": {
            "version": version_id,
            "status": "pass",
            "report_ref": _non_empty_string(consumer_report, "consumer_report"),
        },
        "canvas": {
            "width": canvas.get("width"),
            "height": canvas.get("height"),
            "format": canvas.get("format"),
        },
        "protected_content": protected,
    }
    if type(context["canvas"]["width"]) is not int or context["canvas"]["width"] < 1:
        raise ValueError("canvas.width must be a positive integer")
    if type(context["canvas"]["height"]) is not int or context["canvas"]["height"] < 1:
        raise ValueError("canvas.height must be a positive integer")
    _non_empty_string(context["canvas"]["format"], "canvas.format")
    return aesthetic_input, context


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consumer-input", required=True)
    parser.add_argument("--consumer-result", required=True)
    parser.add_argument("--hard-check-report", required=True)
    parser.add_argument("--consumer-report", required=True)
    parser.add_argument("--input-output", required=True)
    parser.add_argument("--context-output", required=True)
    args = parser.parse_args()
    aesthetic_input, context = assemble(
        load(args.consumer_input),
        load(args.consumer_result),
        args.hard_check_report,
        args.consumer_report,
    )
    write(args.input_output, aesthetic_input)
    write(args.context_output, context)


if __name__ == "__main__":
    main()
