#!/usr/bin/env python3
"""Fail CI when main's release pointers drift from the authoritative Skill."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
CURRENT = MANIFEST["current"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


version_path = ROOT / CURRENT["directory"] / "assets" / "config" / "version.json"
version = json.loads(version_path.read_text(encoding="utf-8"))

require(MANIFEST["latest_version"] == "3.1.0-rc.3", "latest_version drifted")
require(CURRENT["version"] == MANIFEST["latest_version"], "current.version drifted")
require(version["skill_version"] == CURRENT["version"], "Skill version disagrees with manifest")
require(CURRENT["status"] == "stable", "current release channel is not stable")
require(version["release_channel"] == "stable", "Skill release channel is not stable")
require(version["production_ready"] is True, "Skill is not production_ready")
require((ROOT / CURRENT["directory"] / "SKILL.md").is_file(), "current Skill is missing")
require((ROOT / CURRENT["tests"]).is_dir(), "current tests are missing")
require(CURRENT["tag"] == "ecommerce-poster-design-v3.1.0-rc.3", "current Tag drifted")

main_skill_dirs = sorted(path.parent.name for path in (ROOT / "skills").glob("ecommerce-poster-design-*/SKILL.md") if path.is_file())
require(main_skill_dirs == ["ecommerce-poster-design-3.1.0"], f"main contains unexpected Skill directories: {main_skill_dirs}")
require(not (ROOT / "skills" / "ecommerce-poster-design-3.1.0-rc.3-ablation-no-consumer" / "SKILL.md").exists(), "ablation experiment leaked into main")

for experiment in MANIFEST.get("experiments", []):
    require(experiment.get("present_on_main") is False, "experiment must be absent from main")
    require(str(experiment.get("branch", "")).startswith("experiment/"), "experiment branch is missing")

print(json.dumps({"valid": True, "latest_version": MANIFEST["latest_version"], "skill_directory": CURRENT["directory"], "main_skill_dirs": main_skill_dirs}, ensure_ascii=False, indent=2))
