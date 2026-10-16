#!/usr/bin/env python3
"""Resolve an aspect-ratio canvas request into exact downstream dimensions."""

import argparse
import json
from copy import deepcopy
from math import ceil, gcd
from pathlib import Path


ORIENTATION_ALIASES = {
    "vertical": "vertical",
    "portrait": "vertical",
    "竖版": "vertical",
    "竖向": "vertical",
    "horizontal": "horizontal",
    "landscape": "horizontal",
    "横版": "horizontal",
    "横向": "horizontal",
    "square": "square",
    "方形": "square",
}


def _positive_int(value, field):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _parse_ratio(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("canvas.aspect_ratio is required")
    normalized = value.strip().replace("：", ":").replace("/", ":")
    parts = [part.strip() for part in normalized.split(":")]
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("canvas.aspect_ratio must use width:height")
    width_part, height_part = (int(part) for part in parts)
    if width_part <= 0 or height_part <= 0:
        raise ValueError("canvas.aspect_ratio values must be positive")
    divisor = gcd(width_part, height_part)
    return width_part // divisor, height_part // divisor


def _orientation(width, height):
    return "vertical" if height > width else "horizontal" if width > height else "square"


def _normalize_orientation(value, derived):
    if value is None or (isinstance(value, str) and not value.strip()):
        return derived
    if not isinstance(value, str):
        raise ValueError("canvas.orientation must be a string")
    normalized = ORIENTATION_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise ValueError("canvas.orientation must be vertical, horizontal, or square")
    if normalized != derived:
        raise ValueError("canvas.orientation conflicts with canvas.aspect_ratio")
    return normalized


def _dimensions_for_ratio(width_part, height_part, short_edge=1080):
    multiplier = ceil(short_edge / min(width_part, height_part))
    return width_part * multiplier, height_part * multiplier


def resolve_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    result = deepcopy(request)
    canvas = result.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError("canvas must be a JSON object")

    ratio_width, ratio_height = _parse_ratio(canvas.get("aspect_ratio"))
    requested_ratio = f"{ratio_width}:{ratio_height}"
    requested_orientation = _normalize_orientation(
        canvas.get("orientation"), _orientation(ratio_width, ratio_height)
    )
    output_format = canvas.get("format")
    if not isinstance(output_format, str) or not output_format.strip():
        raise ValueError("canvas.format is required")
    output_format = output_format.strip().lower()
    language = canvas.get("language")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("canvas.language is required")

    width = canvas.get("width")
    height = canvas.get("height")
    if (width is None) != (height is None):
        raise ValueError("canvas.width and canvas.height must be provided together")

    platform_size = canvas.get("platform_size")
    platform_override = platform_size is not None
    if platform_override:
        if not isinstance(platform_size, dict):
            raise ValueError("canvas.platform_size must be an object")
        resolved_width = _positive_int(platform_size.get("width"), "canvas.platform_size.width")
        resolved_height = _positive_int(platform_size.get("height"), "canvas.platform_size.height")
        method = "platform_requirement"
    elif width is not None:
        resolved_width = _positive_int(width, "canvas.width")
        resolved_height = _positive_int(height, "canvas.height")
        divisor = gcd(resolved_width, resolved_height)
        if (resolved_width // divisor, resolved_height // divisor) != (ratio_width, ratio_height):
            raise ValueError("exact canvas dimensions conflict with canvas.aspect_ratio")
        method = "explicit_pixels"
    else:
        resolved_width, resolved_height = _dimensions_for_ratio(ratio_width, ratio_height)
        method = "ratio_default_short_edge_1080"

    resolved_divisor = gcd(resolved_width, resolved_height)
    resolved_ratio = f"{resolved_width // resolved_divisor}:{resolved_height // resolved_divisor}"
    resolved_orientation = _orientation(resolved_width, resolved_height)
    result["canvas"] = {
        "width": resolved_width,
        "height": resolved_height,
        "format": output_format,
        "language": language.strip(),
    }
    result["canvas_resolution"] = {
        "requested_aspect_ratio": requested_ratio,
        "requested_orientation": requested_orientation,
        "resolved_aspect_ratio": resolved_ratio,
        "resolved_orientation": resolved_orientation,
        "resolution_method": method,
        "platform_override": platform_override,
        "notice": f"将按 {resolved_width}×{resolved_height} px（{resolved_ratio}，{output_format.upper()}）生成。",
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.input).read_text(encoding="utf-8"))
    resolved = resolve_request(request)
    Path(args.output).write_text(
        json.dumps(resolved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
