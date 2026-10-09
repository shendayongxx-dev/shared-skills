#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        "SKILL.md", "references/contracts.md", "references/hard-compliance.md",
        "references/aesthetic-first-ablation.md", "scripts/assemble_aesthetic_input.py",
        "scripts/route_aesthetic_result.py", "scripts/route_consumer_result.py",
        "modules/aesthetic-agent/SKILL.md", "modules/aesthetic-agent/config.json",
        "modules/aesthetic-agent/scripts/evaluate.mjs",
        "modules/aesthetic-agent/schemas/input.schema.json",
        "modules/aesthetic-agent/schemas/output.schema.json",
        "modules/consumer-agent/SKILL.md",
        "modules/consumer-agent/scripts/assemble_input.py",
        "modules/consumer-agent/scripts/score_evaluation.py",
        "modules/consumer-agent/assets/schemas/input.schema.json",
        "modules/consumer-agent/assets/schemas/output.schema.json",
    ]
    missing = [relative for relative in required if not (root / relative).is_file()]
    if missing:
        raise SystemExit(f"missing required files: {missing}")
    version = json.loads((root / "assets/config/version.json").read_text(encoding="utf-8"))
    assert version["skill_version"] == "1.0.0-aesthetic-first-ablation.1"
    assert version["git_branch"] == "experiment/ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1"
    assert version["git_tag"] == "ecommerce-poster-design-v1.0.0-aesthetic-first-ablation.1"
    assert version["baseline"]["skill_version"] == "1.0.0"
    assert version["production_ready"] is False
    assert version["feature_flags"] == {"aesthetic_agent": True, "consumer_agent": True}
    assert version["agent_order"] == ["aesthetic_agent", "consumer_agent"]
    assert version["retry_policy"]["max_redraw_attempts"] == 3
    assert version["retry_policy"]["shared_across_stages"] is True
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    for phrase in ["美学 Agent → 消费者 Agent", "redraw_then_full_hard_check_then_aesthetic", "全局最多重画 3 次"]:
        assert phrase in skill, f"missing integration rule in SKILL.md: {phrase}"
    print("PASS: aesthetic-first ablation structure, flags, order, shared budget and modules")


if __name__ == "__main__":
    main()
