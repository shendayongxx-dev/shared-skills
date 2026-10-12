#!/usr/bin/env python3
"""Static validation for the rc.3 no-aesthetic ablation."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(path):
    lines = []
    for item in sorted(
        (
            value for value in path.rglob("*")
            if value.is_file()
            and "__pycache__" not in value.parts
            and value.suffix != ".pyc"
        ),
        key=lambda value: value.as_posix().lower(),
    ):
        lines.extend((item.relative_to(path).as_posix(), sha256(item)))
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def main():
    version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "ABLATION_MANIFEST.json").read_text(encoding="utf-8"))
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    preserved = manifest["preserved_snapshot"]
    forbidden_paths = [
        ROOT / "modules/aesthetic-agent", ROOT / "references/aesthetic-agent-integration.md",
        ROOT / "scripts/assemble_aesthetic_input.py", ROOT / "scripts/route_aesthetic_result.py",
        ROOT / "scripts/validate_aesthetic_integration.py", ROOT / "scripts/test_aesthetic_integration.py",
        ROOT / "scripts/validate_generation_edit_contract.py",
    ]
    production_files = [
        ROOT / "SKILL.md", ROOT / "assets/config/version.json", ROOT / "scripts/route_consumer_result.py",
        ROOT / "scripts/route_final_quality.py", ROOT / "scripts/validate_final_quality_edit_contract.py",
        ROOT / "modules/consumer-agent/scripts/score_evaluation.py",
    ]
    runtime_text = "\n".join(path.read_text(encoding="utf-8") for path in production_files[1:] if path.suffix in {".py", ".json"})
    checks = {
        "version_identity": version.get("skill_version") == "3.1.0-rc.3-ablation-no-aesthetic",
        "base_pinned": version.get("ablation", {}).get("base_version") == "3.1.0-rc.3" and manifest.get("base_commit") == "d36e9a3b855c6a473155f80070921afa6c61b960",
        "experimental_not_stable": version.get("production_ready") is False and version.get("release_channel") == "ablation-experiment" and manifest.get("release") is False,
        "flags": version.get("feature_flags") == {"consumer_agent": True, "aesthetic_agent": False, "final_quality_gate": True},
        "aesthetic_artifacts_forbidden": version.get("ablation", {}).get("aesthetic_artifacts_allowed") is False,
        "aesthetic_paths_absent": not any(path.exists() for path in forbidden_paths),
        "production_files_present": all(path.is_file() for path in production_files),
        "skill_declares_ablation": "3.1.0-rc.3-ablation-no-aesthetic" in skill and "不调用、导入、读取或模拟美学 Agent" in skill,
        "no_hidden_aesthetic_runtime": all(value not in runtime_text for value in ("A-D-AESTHETIC", "aesthetic_score", "locked_aesthetic_dimensions", "invoke_aesthetic_agent", "modules/aesthetic-agent")),
        "consumer_module_preserved": tree_sha256(ROOT / "modules/consumer-agent") == preserved["consumer_module_sha256_tree"],
        "consumer_rubric_preserved": sha256(ROOT / "modules/consumer-agent/assets/rubric.json") == preserved["consumer_rubric_sha256"],
        "classification_preserved": sha256(ROOT / "assets/classification/manifest.json") == preserved["classification_manifest_sha256"],
        "logo_scripts_preserved": sha256(ROOT / "scripts/prepare_logo_asset.mjs") == preserved["prepare_logo_asset_sha256"] and sha256(ROOT / "scripts/apply_logo_asset.mjs") == preserved["apply_logo_asset_sha256"],
        "budget_preserved": version.get("retry_policy", {}).get("max_redraw_attempts") == 8,
        "integrated_generation_preserved": version.get("generation_backend", {}).get("svg_logo_pipeline", {}).get("generation_strategy") == "integrated_full_poster_then_deterministic_logo_only" and "禁止先生成空背景" in skill,
    }
    failed = [key for key, value in checks.items() if not value]
    print(json.dumps({"valid": not failed, "checks": checks}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed no-aesthetic ablation checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
