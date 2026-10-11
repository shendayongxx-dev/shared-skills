#!/usr/bin/env python3
"""Static validation for the rc.3 no-consumer ablation."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "ABLATION_MANIFEST.json").read_text(encoding="utf-8"))
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    base = ROOT.parent / "ecommerce-poster-design-3.1.0"
    sha256 = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    forbidden_paths = [ROOT / "modules/consumer-agent", ROOT / "scripts/route_consumer_result.py", ROOT / "references/consumer-agent-integration.md"]
    production_files = [ROOT / "SKILL.md", ROOT / "assets/config/version.json", ROOT / "scripts/assemble_aesthetic_input.py", ROOT / "scripts/route_aesthetic_result.py", ROOT / "scripts/route_final_quality.py", ROOT / "scripts/validate_generation_edit_contract.py", ROOT / "scripts/validate_final_quality_edit_contract.py", ROOT / "modules/aesthetic-agent/scripts/score_evaluation.py", ROOT / "modules/aesthetic-agent/schemas/input.schema.json"]
    checks = {
        "version_identity": version.get("skill_version") == "3.1.0-rc.3-ablation-no-consumer",
        "base_pinned": version.get("ablation", {}).get("base_version") == "3.1.0-rc.3",
        "consumer_disabled": version.get("feature_flags", {}).get("consumer_agent") is False,
        "consumer_artifacts_forbidden": version.get("ablation", {}).get("consumer_artifacts_allowed") is False,
        "consumer_paths_absent": not any(path.exists() for path in forbidden_paths),
        "production_files_present": all(path.is_file() for path in production_files),
        "skill_declares_ablation": "3.1.0-rc.3-ablation-no-consumer" in skill and "不生成伪消费者结果" in skill,
        "no_hidden_consumer_result_key": all('workflow["consumer_result"]' not in path.read_text(encoding="utf-8") for path in production_files if path.suffix in {".py", ".md"}),
        "base_skill_snapshot_unchanged": sha256(base / "SKILL.md") == manifest["base_snapshot"]["skill_md_sha256"],
        "base_version_snapshot_unchanged": sha256(base / "assets/config/version.json") == manifest["base_snapshot"]["version_json_sha256"],
        "aesthetic_rubric_preserved": sha256(ROOT / "modules/aesthetic-agent/assets/rubric.json") == manifest["base_snapshot"]["aesthetic_rubric_sha256"],
        "classification_manifest_preserved": sha256(ROOT / "assets/classification/manifest.json") == manifest["base_snapshot"]["classification_manifest_sha256"],
    }
    failed = [key for key, value in checks.items() if not value]
    print(json.dumps({"valid": not failed, "checks": checks}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed ablation checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
