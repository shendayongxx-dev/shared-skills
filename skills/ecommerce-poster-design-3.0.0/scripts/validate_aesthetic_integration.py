#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(json.dumps({"valid": False, "error": message}, ensure_ascii=False, indent=2))
    raise SystemExit(1)


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
version_path = root / "assets" / "config" / "version.json"
if not version_path.is_file():
    fail(f"missing {version_path}")
version = json.loads(version_path.read_text(encoding="utf-8"))
module = version.get("aesthetic_agent_module", {})
flags = version.get("feature_flags", {})
retry = version.get("retry_policy", {})
if version.get("skill_version") != "3.0.0":
    fail("aesthetic integration must use skill_version 3.0.0")
if version.get("baseline_version") != "2.0.1":
    fail("Skill 3.0 must declare 2.0.1 as its independent baseline")
if flags.get("consumer_agent") is not True or flags.get("aesthetic_agent") is not True:
    fail("consumer_agent and aesthetic_agent must both be enabled")
if module.get("interface_version") != "2.0":
    fail("aesthetic interface must be 2.0")

aesthetic = root / module.get("path", "modules/aesthetic-agent")
required = [
    aesthetic / "SKILL.md",
    aesthetic / "agent-prompt.md",
    aesthetic / "config.json",
    aesthetic / "schemas" / "input.schema.json",
    aesthetic / "schemas" / "output.schema.json",
    aesthetic / "schemas" / "review.schema.json",
    aesthetic / "schemas" / "assessment.schema.json",
    aesthetic / "schemas" / "context.schema.json",
    aesthetic / "scripts" / "evaluate.mjs",
    aesthetic / "scripts" / "match-references.mjs",
    aesthetic / "scripts" / "match-quality-examples.mjs",
    root / "references" / "aesthetic-agent-integration.md",
    root / "scripts" / "assemble_aesthetic_input.py",
    root / "scripts" / "route_aesthetic_result.py",
    root / "scripts" / "test_aesthetic_integration.py",
]
missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
if missing:
    fail("missing aesthetic integration files: " + ", ".join(missing))

input_schema = json.loads((aesthetic / "schemas" / "input.schema.json").read_text(encoding="utf-8"))
output_schema = json.loads((aesthetic / "schemas" / "output.schema.json").read_text(encoding="utf-8"))
context_schema = json.loads((aesthetic / "schemas" / "context.schema.json").read_text(encoding="utf-8"))
if set(input_schema.get("required", [])) != {"poster_image", "product_input"}:
    fail("aesthetic input contract drifted")
if set(output_schema.get("required", [])) != {
    "agent_name", "score", "pass", "problem_list", "modify_suggestion", "protected_content", "meta"
}:
    fail("aesthetic output contract drifted")
if "protected_content" not in context_schema.get("properties", {}):
    fail("orchestrator context must carry the eight protected-content groups")
integrated_required = (
    context_schema.get("allOf", [{}])[0]
    .get("then", {})
    .get("required", [])
)
if not {"hard_check", "consumer", "protected_content"}.issubset(set(integrated_required)):
    fail("integrated context must require upstream gates and protected_content")

agent_config = json.loads((aesthetic / "config.json").read_text(encoding="utf-8"))
checks = {
    "max_generation_rounds": retry.get("aesthetic_max_generation_rounds") == agent_config.get("loop", {}).get("max_generation_rounds"),
    "pre_aesthetic_max_redraw_attempts": retry.get("max_redraw_attempts") == 3,
    "stagnation_rounds": retry.get("aesthetic_stagnation_rounds") == agent_config.get("loop", {}).get("stagnation_rounds"),
    "min_total_gain": retry.get("aesthetic_min_total_gain") == agent_config.get("loop", {}).get("min_total_gain"),
}
if not all(checks.values()):
    fail("host retry policy does not match aesthetic-agent config")

print(json.dumps({
    "valid": True,
    "skill_version": version["skill_version"],
    "workflow_version": version.get("workflow_version"),
    "aesthetic_agent": module,
    "feature_flags": flags,
    "retry_alignment": checks,
    "required_files": len(required),
}, ensure_ascii=False, indent=2))
