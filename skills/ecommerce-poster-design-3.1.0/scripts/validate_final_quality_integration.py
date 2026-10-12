#!/usr/bin/env python3
"""Static integration checks for the 3.1 score-free final quality gate."""

import json
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        "SKILL.md",
        "assets/config/version.json",
        "assets/schemas/final-quality-review.schema.json",
        "references/final-quality-gate.md",
        "scripts/route_final_quality.py",
        "scripts/validate_final_quality_edit_contract.py",
        "scripts/test_final_quality_routing.py",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise SystemExit("missing final quality integration files: " + ", ".join(missing))
    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    gate = version.get("final_quality_gate", {})
    schema = json.loads((root / "assets/schemas/final-quality-review.schema.json").read_text(encoding="utf-8"))
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    gate_spec = (root / "references/final-quality-gate.md").read_text(encoding="utf-8")
    router = (root / "scripts/route_final_quality.py").read_text(encoding="utf-8")
    defect_codes = set(schema["properties"]["defects"]["items"]["properties"]["code"]["enum"])
    checks = {
        "skill_version": version.get("skill_version") == "3.1.0-rc.4",
        "workflow_version": version.get("workflow_version") == "3.1",
        "baseline": version.get("baseline_version") == "3.0.0",
        "stable_release_channel": version.get("production_ready") is True and version.get("release_channel") == "stable",
        "feature_enabled": version.get("feature_flags", {}).get("final_quality_gate") is True,
        "score_free_mode": gate.get("mode") == "defect_based_no_score",
        "schema_version": schema.get("properties", {}).get("schema_version", {}).get("const") == "FINAL-QUALITY-3.1",
        "schema_has_no_score": "score" not in schema.get("properties", {}),
        "adversarial_review": gate.get("adversarial_review_on_suspicious_score") is True,
        "minor_limit": gate.get("max_minor_defects_for_pass") == 2,
        "skill_routes_to_gate": "route_final_quality.py" in skill and "最终质量仲裁" in skill,
        "skill_forbids_abstract_redraw": "抽象审美意见触发重画" in skill,
        "mandatory_defect_codes": {"TEXT_OVERLAP", "LOGO_FLOATING"} <= defect_codes,
        "skill_requires_moderate_text_and_logo_defects": all(value in skill for value in ("TEXT_OVERLAP", "LOGO_FLOATING", "至少为 `moderate`")),
        "gate_documents_mandatory_severity": all(value in gate_spec for value in ("TEXT_OVERLAP", "LOGO_FLOATING", "强制中度缺陷")),
        "router_rejects_minor_downgrade": "must be moderate or higher" in router,
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"valid": not failed, "checks": checks, "missing": missing}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed final quality checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
