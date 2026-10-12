#!/usr/bin/env python3
"""Validate the Skill 3.1 SVG logo preprocessing and deterministic application contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    backend = version.get("generation_backend", {})
    pipeline = backend.get("svg_logo_pipeline", {})
    required = [
        root / "scripts/prepare_logo_asset.mjs",
        root / "scripts/apply_logo_asset.mjs",
        root / "scripts/test_logo_asset_pipeline.mjs",
        root / "references/imagegen-integration.md",
        root / "references/hard-compliance.md",
    ]
    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    imagegen_text = (root / "references/imagegen-integration.md").read_text(encoding="utf-8")
    hard_text = (root / "references/hard-compliance.md").read_text(encoding="utf-8")
    checks = {
        "skill_version": version.get("skill_version") == "3.1.0-rc.3-ablation-no-aesthetic" and version.get("ablation", {}).get("base_version") == "3.1.0-rc.3",
        "pipeline_enabled": pipeline.get("enabled") is True,
        "source_preserved": pipeline.get("authoritative_source_preserved") is True,
        "preflight_schema": pipeline.get("preflight_schema") == "logo-asset-preflight/1.0",
        "application_schema": pipeline.get("application_schema") == "logo-application/1.0",
        "raster_size": pipeline.get("default_raster_long_edge", 0) >= 2048,
        "integrated_poster_then_logo_only": pipeline.get("generation_strategy") == "integrated_full_poster_then_deterministic_logo_only",
        "required_files": all(item.is_file() for item in required),
        "skill_requires_svg_preflight": "prepare_logo_asset.mjs" in skill_text and "apply_logo_asset.mjs" in skill_text,
        "imagegen_does_not_redraw_logo": "不得要求模型重画 Logo" in imagegen_text,
        "logo_is_only_post_composite": "只允许应用官方 Logo" in imagegen_text and "禁止只生成空背景后再贴商品" in imagegen_text,
        "hc05_requires_manifests": "logo-asset-preflight/1.0" in hard_text and "logo-application/1.0" in hard_text,
    }
    result = {"valid": all(checks.values()), "checks": checks, "missing": [str(p) for p in required if not p.is_file()]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
