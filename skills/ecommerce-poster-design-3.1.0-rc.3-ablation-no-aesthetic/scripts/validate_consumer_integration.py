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
flags = version.get("feature_flags", {})
module = version.get("consumer_agent_module", {})
generation = version.get("generation_backend", {})

if version.get("skill_version") != "3.1.0-rc.3-ablation-no-aesthetic":
    fail("this validator requires Skill 3.1.0-rc.3-ablation-no-aesthetic")
if flags.get("consumer_agent") is not True:
    fail("consumer_agent must be enabled")
if flags.get("aesthetic_agent") is not False or flags.get("final_quality_gate") is not True:
    fail("no-aesthetic ablation requires aesthetic_agent=false and final_quality_gate=true")
if version.get("ablation", {}).get("id") != "no-aesthetic" or version.get("ablation", {}).get("base_version") != "3.1.0-rc.3":
    fail("invalid no-aesthetic ablation identity")
if module.get("interface_version") != "A-D-2.0":
    fail("consumer interface must be A-D-2.0")
if generation.get("skill") != "imagegen" or generation.get("tool") != "image_gen":
    fail("generation backend must use the Codex imagegen skill and image_gen tool")
if generation.get("mode") != "builtin" or generation.get("required") is not True:
    fail("ImageGen built-in mode must be required")

consumer = root / module.get("path", "modules/consumer-agent")
required = [
    consumer / "SKILL.md",
    consumer / "assets" / "rubric.json",
    consumer / "assets" / "schemas" / "input.schema.json",
    consumer / "assets" / "schemas" / "output.schema.json",
    consumer / "scripts" / "assemble_input.py",
    consumer / "scripts" / "validate_input.py",
    consumer / "scripts" / "score_evaluation.py",
    consumer / "scripts" / "run_evals.py",
    root / "references" / "consumer-agent-integration.md",
    root / "references" / "imagegen-integration.md",
    root / "scripts" / "route_consumer_result.py",
    root / "scripts" / "test_consumer_routing.py",
]
missing = [str(path.relative_to(root)) for path in required if not path.is_file()]
if missing:
    fail("missing integration files: " + ", ".join(missing))

input_schema = json.loads(required[2].read_text(encoding="utf-8"))
output_schema = json.loads(required[3].read_text(encoding="utf-8"))
if input_schema.get("properties", {}).get("schema_version", {}).get("const") != "A-D-2.0":
    fail("input schema version mismatch")
if output_schema.get("properties", {}).get("schema_version", {}).get("const") != "A-D-2.0":
    fail("output schema version mismatch")

result = {
    "valid": True,
    "skill_version": version["skill_version"],
    "workflow_version": version.get("workflow_version"),
    "consumer_agent": module,
    "generation_backend": generation,
    "feature_flags": flags,
    "required_files": len(required),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
