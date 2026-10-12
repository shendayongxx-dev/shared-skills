#!/usr/bin/env python3
import json
from pathlib import Path

from route_consumer_result import route_result

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "modules" / "consumer-agent" / "examples"
VERSION = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


passed = route_result(load("consumer-output-pass.json"), VERSION, 1)
assert passed["status"] == "in_progress" and passed["action"] == "invoke_final_quality_gate"
assert passed["compatibility_route_received"] == "aesthetic_agent"
assert passed["ablation"]["aesthetic_artifacts_used"] is False

iterate = route_result(load("consumer-output-iterate.json"), VERSION, 1)
assert iterate["action"] == "redraw_then_full_hard_check" and iterate["next_global_redraw_attempt"] == 2

exhausted = route_result(load("consumer-output-iterate.json"), VERSION, 8)
assert exhausted["status"] == "degraded" and exhausted["action"] == "stop_at_limit"

blocked = route_result(load("consumer-output-complete-input.json"), VERSION, 0)
assert blocked["status"] == "blocked" and blocked["action"] == "complete_input"

regression = route_result(load("consumer-output-regression.json"), VERSION, 2)
assert regression["action"] == "redraw_from_last_consumer_pass_then_full_hard_check"
assert regression["candidate_disposition"] == "reject" and regression["restore_last_consumer_pass"] is True

print("PASS: 5 no-aesthetic consumer routing scenarios")
