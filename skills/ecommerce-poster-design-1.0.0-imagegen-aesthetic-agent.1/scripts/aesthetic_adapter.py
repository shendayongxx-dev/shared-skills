#!/usr/bin/env python3
"""Deterministic adapter between frozen poster baseline 1.0 and aesthetic agent.

This module does not inspect images, score aesthetics, run a consumer agent, or
generate posters. It only maps frozen baseline fields, writes sidecars, and
merges two already-produced results without changing either result's meaning.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPERIMENT_VERSION = "1.0.0-imagegen-aesthetic-agent.1"
BASELINE_VERSION = "1.0.0-imagegen.1"
MAX_REDRAW_ATTEMPTS = 3

BASELINE_INPUT_KEYS = {"request_id", "product", "brand", "commerce", "marketing", "canvas"}
PROTECTED_KEYS = {
    "product_identity",
    "product_quantity",
    "brand_and_logo",
    "price_and_unit",
    "promotion_and_period",
    "selling_points",
    "cta",
    "legal_text",
}
AESTHETIC_KEYS = {
    "agent_name",
    "score",
    "pass",
    "problem_list",
    "modify_suggestion",
    "protected_content",
    "meta",
}


class AdapterError(ValueError):
    """Raised when a mapping would be lossy, ambiguous, or semantically unsafe."""


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be a JSON object")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterError(f"{label} must be a non-empty string")
    return value


def require_string_list(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise AdapterError(f"{label} must contain at least {min_items} item(s)")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise AdapterError(f"{label} must contain only non-empty strings")
    return value


def choose_product_image(image_refs: Any, explicit: str | None) -> str:
    refs = require_string_list(image_refs, "product.image_refs", min_items=1)
    if explicit is not None:
        require_string(explicit, "--product-image")
        if explicit not in refs:
            raise AdapterError("--product-image must exactly match one baseline product.image_refs entry")
        return explicit
    if len(refs) != 1:
        raise AdapterError("multiple product.image_refs require explicit --product-image; refusing silent first-image selection")
    return refs[0]


def map_scene_tags(style_guide: dict[str, Any]) -> list[str]:
    tags = require_object(style_guide.get("tags"), "style_guide.tags")
    ordered = []
    for key in ("audience_id", "motivation_id", "scenario_id"):
        value = tags.get(key)
        if value is None:
            continue
        ordered.append(require_string(value, f"style_guide.tags.{key}"))
    if not ordered:
        raise AdapterError("all C tags are null; aesthetic scene_tags cannot be invented")
    return ordered


def build_aesthetic_input(
    baseline_input: dict[str, Any],
    style_guide: dict[str, Any],
    poster_image: str,
    product_image: str | None = None,
) -> dict[str, Any]:
    missing = BASELINE_INPUT_KEYS - set(baseline_input)
    if missing:
        raise AdapterError(f"baseline input missing keys: {sorted(missing)}")

    product = require_object(baseline_input["product"], "product")
    commerce = require_object(baseline_input["commerce"], "commerce")
    marketing = require_object(baseline_input["marketing"], "marketing")

    return {
        "poster_image": require_string(poster_image, "poster_image"),
        "product_input": {
            "product_img": choose_product_image(product.get("image_refs"), product_image),
            "selling_points": require_string_list(product.get("selling_points"), "product.selling_points", min_items=1),
            "price_text": require_string(commerce.get("price_text"), "commerce.price_text"),
            "marketing_target": require_string(marketing.get("goal"), "marketing.goal"),
            "scene_tags": map_scene_tags(style_guide),
        },
    }


def validate_protected_content(value: Any) -> dict[str, Any]:
    protected = require_object(value, "protected_content")
    missing = PROTECTED_KEYS - set(protected)
    if missing:
        raise AdapterError(f"protected_content missing keys: {sorted(missing)}")
    return protected


def write_new_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    baseline_input = require_object(load_json(args.baseline_input), "baseline input")
    style_guide = require_object(load_json(args.style_guide), "style guide")
    protected = validate_protected_content(load_json(args.protected_content))
    aesthetic_input = build_aesthetic_input(
        baseline_input,
        style_guide,
        args.poster_image,
        args.product_image,
    )

    canvas = require_object(baseline_input["canvas"], "canvas")
    context = {
        "mode": "standalone",
        "version": EXPERIMENT_VERSION,
        "canvas": {
            "width": canvas.get("width"),
            "height": canvas.get("height"),
            "format": canvas.get("format"),
        },
    }
    if not isinstance(context["canvas"]["width"], int) or context["canvas"]["width"] <= 0:
        raise AdapterError("canvas.width must be a positive integer")
    if not isinstance(context["canvas"]["height"], int) or context["canvas"]["height"] <= 0:
        raise AdapterError("canvas.height must be a positive integer")
    require_string(context["canvas"]["format"], "canvas.format")

    sidecar = {
        "schema_version": "1.0",
        "source": "baseline_1.0_protected_content",
        "protected_content": protected,
        "unmapped_baseline_fields": {
            "product_name": baseline_input["product"].get("name"),
            "product_category": baseline_input["product"].get("category"),
            "brand": baseline_input["brand"],
            "promotion_text": baseline_input["commerce"].get("promotion_text"),
            "promotion_period": baseline_input["commerce"].get("promotion_period"),
            "legal_text": baseline_input["commerce"].get("legal_text"),
            "cta": baseline_input["marketing"].get("cta"),
        },
    }
    manifest = {
        "adapter_version": EXPERIMENT_VERSION,
        "baseline_version": BASELINE_VERSION,
        "consumer_agent_used": False,
        "aesthetic_context_mode": "standalone",
        "iteration_owner": "baseline_1.0",
        "max_redraw_attempts": MAX_REDRAW_ATTEMPTS,
        "mapping": {
            "poster_image": "explicit current candidate",
            "product_img": "product.image_refs explicit selection",
            "selling_points": "product.selling_points",
            "price_text": "commerce.price_text",
            "marketing_target": "marketing.goal",
            "scene_tags": "style_guide.tags non-null IDs",
        },
    }

    output = Path(args.out)
    files = {
        "aesthetic-input.json": aesthetic_input,
        "protected-content-sidecar.json": sidecar,
        "context.json": context,
        "adapter-manifest.json": manifest,
    }
    for name in files:
        if output.joinpath(name).exists():
            raise AdapterError(f"refusing overwrite: {output / name}")
    for name, value in files.items():
        write_new_json(output / name, value)
    return manifest


def validate_aesthetic_result(value: Any) -> dict[str, Any]:
    result = require_object(value, "aesthetic result")
    if set(result) != AESTHETIC_KEYS:
        raise AdapterError(f"aesthetic result fields must be exactly {sorted(AESTHETIC_KEYS)}")
    if result.get("agent_name") != "aesthetic_agent":
        raise AdapterError("agent_name must be aesthetic_agent; consumer output is forbidden")
    score = result.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10:
        raise AdapterError("aesthetic score must be a number from 0 to 10")
    if not isinstance(result.get("pass"), bool):
        raise AdapterError("aesthetic pass must be boolean")
    problems = require_string_list(result.get("problem_list"), "problem_list")
    suggestions = require_string_list(result.get("modify_suggestion"), "modify_suggestion")
    if len(problems) != len(suggestions):
        raise AdapterError("problem_list and modify_suggestion must have equal length")
    require_string_list(result.get("protected_content"), "protected_content", min_items=1)
    meta = require_object(result.get("meta"), "meta")
    if set(meta) != {"judge_dimensions", "confidence"}:
        raise AdapterError("aesthetic meta fields must be judge_dimensions and confidence")
    require_string_list(meta.get("judge_dimensions"), "meta.judge_dimensions", min_items=1)
    confidence = meta.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise AdapterError("meta.confidence must be a number from 0 to 1")
    return result


def is_unavailable_score(result: dict[str, Any]) -> bool:
    problems = result["problem_list"]
    return (
        result["score"] == 0
        and result["meta"]["confidence"] == 0
        and bool(problems)
        and problems[0].startswith("无法评价")
    )


def merge_results(baseline_result: dict[str, Any], aesthetic_result: dict[str, Any]) -> dict[str, Any]:
    status = baseline_result.get("status")
    if status not in {"passed", "degraded", "blocked"}:
        raise AdapterError("baseline result status must be passed, degraded, or blocked")
    hard = require_object(baseline_result.get("hard_compliance"), "baseline_result.hard_compliance")
    hard_pass = hard.get("passed")
    if not isinstance(hard_pass, bool):
        raise AdapterError("baseline_result.hard_compliance.passed must be boolean")

    aesthetic = validate_aesthetic_result(aesthetic_result)
    unavailable = is_unavailable_score(aesthetic)
    combined_pass = status == "passed" and hard_pass and aesthetic["pass"] and not unavailable

    if combined_pass:
        combined_status = "passed"
    elif status == "blocked":
        combined_status = "baseline_blocked"
    elif unavailable:
        combined_status = "aesthetic_unavailable"
    else:
        combined_status = "revise"

    return {
        "baseline_result": baseline_result,
        "aesthetic_agent_result": aesthetic,
        "experiment_result": {
            "variant": "aesthetic_agent_added",
            "pass": combined_pass,
            "status": combined_status,
            "baseline_hard_pass": hard_pass,
            "aesthetic_pass": aesthetic["pass"],
            "aesthetic_score": aesthetic["score"],
            "score_state": "unavailable" if unavailable else "measured",
            "consumer_agent_used": False,
            "iteration_owner": "baseline_1.0",
            "max_redraw_attempts": MAX_REDRAW_ATTEMPTS,
        },
    }


def merge(args: argparse.Namespace) -> dict[str, Any]:
    baseline = require_object(load_json(args.baseline_result), "baseline result")
    aesthetic = require_object(load_json(args.aesthetic_result), "aesthetic result")
    combined = merge_results(baseline, aesthetic)
    write_new_json(Path(args.out), combined)
    return combined["experiment_result"]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="map frozen baseline files to aesthetic input and sidecars")
    prep.add_argument("--baseline-input", required=True)
    prep.add_argument("--style-guide", required=True)
    prep.add_argument("--protected-content", required=True)
    prep.add_argument("--poster-image", required=True)
    prep.add_argument("--product-image")
    prep.add_argument("--out", required=True)
    prep.set_defaults(handler=prepare)

    combine = sub.add_parser("merge", help="combine results while preserving both pass semantics")
    combine.add_argument("--baseline-result", required=True)
    combine.add_argument("--aesthetic-result", required=True)
    combine.add_argument("--out", required=True)
    combine.set_defaults(handler=merge)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        summary = args.handler(args)
    except (AdapterError, FileExistsError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"aesthetic adapter error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
