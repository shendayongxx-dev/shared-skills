#!/usr/bin/env python3
"""Static and behavioral checks for the rc.4 canvas resolver."""

import json
import sys
from pathlib import Path

from resolve_canvas import resolve_request


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        "SKILL.md",
        "assets/config/version.json",
        "references/contracts.md",
        "scripts/resolve_canvas.py",
        "scripts/test_canvas_normalization.py",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise SystemExit("missing canvas normalization files: " + ", ".join(missing))

    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    config = version.get("canvas_normalization", {})
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    contracts = (root / "references/contracts.md").read_text(encoding="utf-8")
    sample = resolve_request({
        "request_id": "REQ-CANVAS-VALIDATE",
        "canvas": {
            "aspect_ratio": "4:5",
            "format": "png",
            "language": "zh-CN",
        },
    })
    checks = {
        "skill_version": version.get("skill_version") == "3.1.0-rc.5",
        "pixels_optional": config.get("exact_pixel_dimensions_optional") is True,
        "short_edge": config.get("default_short_edge") == 1080,
        "derive_orientation": config.get("derive_orientation_from_aspect_ratio") is True,
        "platform_override": config.get("platform_requirements_override_defaults") is True,
        "notify_user": config.get("notify_user_before_generation") is True,
        "resolved_4_5": sample["canvas"]["width"] == 1080 and sample["canvas"]["height"] == 1350,
        "derived_vertical": sample["canvas_resolution"]["requested_orientation"] == "vertical",
        "skill_no_pixel_block": "不得仅因用户未提供绝对像素而返回 `blocked`" in skill,
        "contracts_define_algorithm": "最小整数倍" in contracts and "16:9 → 1920×1080" in contracts,
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"valid": not failed, "checks": checks, "missing": missing}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed canvas normalization checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
