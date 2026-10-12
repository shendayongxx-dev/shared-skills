#!/usr/bin/env python3
"""Cross-component invariants for the no-aesthetic ablation."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))

assert version["feature_flags"] == {"consumer_agent": True, "aesthetic_agent": False, "final_quality_gate": True}
assert version["ablation"]["base_version"] == "3.1.0-rc.3"
assert version["retry_policy"]["max_redraw_attempts"] == 8
assert version["generation_backend"]["svg_logo_pipeline"]["generation_strategy"] == "integrated_full_poster_then_deterministic_logo_only"
assert (ROOT / "modules/consumer-agent").is_dir()
assert not (ROOT / "modules/aesthetic-agent").exists()
for name in ("assemble_aesthetic_input.py", "route_aesthetic_result.py", "validate_generation_edit_contract.py"):
    assert not (ROOT / "scripts" / name).exists()
router = (ROOT / "scripts/route_consumer_result.py").read_text(encoding="utf-8")
assert '"action": "invoke_final_quality_gate"' in router
assert '"compatibility_route_received": "aesthetic_agent"' in router
final_router = (ROOT / "scripts/route_final_quality.py").read_text(encoding="utf-8")
for forbidden in ("--aesthetic-result", "--aesthetic-details", "aesthetic_score", "locked_aesthetic_dimensions"):
    assert forbidden not in final_router
skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
imagegen_contract = (ROOT / "references/imagegen-integration.md").read_text(encoding="utf-8")
assert "禁止先生成空背景" in skill_text
assert "不得只生成空场景" in skill_text
assert "只允许应用官方 Logo" in imagegen_contract
print("PASS: no-aesthetic ablation invariants")
