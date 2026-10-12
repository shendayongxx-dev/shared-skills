#!/usr/bin/env python3
"""Static checks for the no-aesthetic score-free final quality gate."""

import json
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        "SKILL.md", "ABLATION_MANIFEST.json", "assets/config/version.json",
        "assets/schemas/final-quality-review.schema.json", "references/final-quality-gate.md",
        "scripts/route_final_quality.py", "scripts/validate_final_quality_edit_contract.py",
        "scripts/test_final_quality_routing.py",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise SystemExit("missing final quality files: " + ", ".join(missing))
    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "assets/schemas/final-quality-review.schema.json").read_text(encoding="utf-8"))
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    gate_spec = (root / "references/final-quality-gate.md").read_text(encoding="utf-8")
    router = (root / "scripts/route_final_quality.py").read_text(encoding="utf-8")
    defect_codes = set(schema["properties"]["defects"]["items"]["properties"]["code"]["enum"])
    checks = {
        "version": version.get("skill_version") == "3.1.0-rc.3-ablation-no-aesthetic",
        "base": version.get("ablation", {}).get("base_version") == "3.1.0-rc.3",
        "experimental": version.get("production_ready") is False and version.get("release_channel") == "ablation-experiment",
        "flags": version.get("feature_flags") == {"consumer_agent": True, "aesthetic_agent": False, "final_quality_gate": True},
        "score_free": version.get("final_quality_gate", {}).get("mode") == "defect_based_no_score",
        "schema": schema.get("properties", {}).get("schema_version", {}).get("const") == "FINAL-QUALITY-3.1-ABLATION-NO-AESTHETIC",
        "schema_has_no_score": "score" not in schema.get("properties", {}),
        "consumer_only_audit": set(schema["properties"]["evidence_audit"]["properties"]) == {"consumer_evidence_supported", "contradictions", "generic_evidence_findings"},
        "mandatory_codes": {"TEXT_OVERLAP", "LOGO_FLOATING"} <= defect_codes,
        "mandatory_severity_documented": all(value in gate_spec for value in ("TEXT_OVERLAP", "LOGO_FLOATING", "至少为 `moderate`")),
        "router_rejects_minor_downgrade": "must be moderate or higher" in router,
        "skill_forbids_aesthetic_artifacts": "不调用、导入、读取或模拟美学 Agent" in skill,
        "router_has_no_aesthetic_inputs": all(value not in router for value in ("--aesthetic-result", "--aesthetic-details", "aesthetic_score")),
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"valid": not failed, "checks": checks, "missing": missing}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed final quality checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
