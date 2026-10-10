#!/usr/bin/env python3
"""Static integration checks for the rebuilt aesthetic rc.4 workflow."""

import json
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        "SKILL.md", "assets/config/version.json", "references/aesthetic-agent-integration.md",
        "scripts/assemble_aesthetic_input.py", "scripts/route_aesthetic_result.py",
        "scripts/validate_generation_edit_contract.py",
        "modules/aesthetic-agent/SKILL.md", "modules/aesthetic-agent/assets/rubric.json",
        "modules/aesthetic-agent/schemas/input.schema.json", "modules/aesthetic-agent/schemas/output.schema.json",
        "modules/aesthetic-agent/schemas/evaluation-draft.schema.json",
        "modules/aesthetic-agent/scripts/score_evaluation.py",
        "modules/aesthetic-agent/tests/test_score_evaluation.py",
    ]
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise SystemExit("missing integration files: " + ", ".join(missing))
    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    checks = {
        "skill_version": version.get("skill_version") == "3.0.0",
        "baseline": version.get("baseline_version") == "2.0.1",
        "aesthetic_version": version.get("aesthetic_agent_module", {}).get("version") == "3.0.0-rc.4",
        "interface": version.get("aesthetic_agent_module", {}).get("interface_version") == "A-D-AESTHETIC-3.0",
        "features": version.get("feature_flags") == {"consumer_agent": True, "aesthetic_agent": True},
        "unified_budget": version.get("retry_policy", {}).get("counter_scope") == "global_across_hard_compliance_consumer_and_aesthetic",
        "budget_eight": version.get("retry_policy", {}).get("max_redraw_attempts") == 8,
        "edit_contract": version.get("generation_edit_contract_version") == "aesthetic-edit-lock/1.0",
        "consumer_lock_enforcement": version.get("consumer_lock_enforcement") == "pre_generation_contract_and_post_generation_regression_rejection",
    }
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    checks["skill_three_gates"] = all(value in skill for value in ["HC-01～HC-12", "消费者 Agent", "美学 Agent"])
    checks["skill_requires_edit_contract"] = "validate_generation_edit_contract.py" in skill and "regressed_dimensions" in skill
    checks["legacy_not_active"] = version.get("aesthetic_agent_module", {}).get("version") != "2.4"
    output_schema = json.loads((root / "modules/aesthetic-agent/schemas/output.schema.json").read_text(encoding="utf-8"))
    dimensions = output_schema["properties"]["meta"]["properties"]["judge_dimensions"]
    checks["blocked_schema_allows_empty_dimensions"] = any(branch.get("maxItems") == 0 for branch in dimensions.get("oneOf", []))
    checks["blocked_schema_is_conditional"] = bool(output_schema.get("allOf"))
    failed = [name for name, passed in checks.items() if not passed]
    result = {"valid": not failed, "checks": checks, "missing": missing}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("failed integration checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
