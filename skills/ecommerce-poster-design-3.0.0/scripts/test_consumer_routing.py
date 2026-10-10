#!/usr/bin/env python3
import json
from pathlib import Path

from route_consumer_result import route_result


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "modules" / "consumer-agent" / "examples"
VERSION = json.loads((ROOT / "assets" / "config" / "version.json").read_text(encoding="utf-8"))


def load(name: str):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


passed = route_result(load("consumer-output-pass.json"), VERSION, 1)
assert passed["status"] == "in_progress" and passed["action"] == "invoke_aesthetic_agent"

iterate = route_result(load("consumer-output-iterate.json"), VERSION, 1)
assert iterate["action"] == "redraw_then_full_hard_check"
assert iterate["next_global_redraw_attempt"] == 2

exhausted = route_result(load("consumer-output-iterate.json"), VERSION, 8)
assert exhausted["status"] == "degraded" and exhausted["action"] == "stop_at_limit"

blocked = route_result(load("consumer-output-complete-input.json"), VERSION, 0)
assert blocked["status"] == "blocked" and blocked["action"] == "complete_input"

regression = route_result(load("consumer-output-regression.json"), VERSION, 2)
assert regression["action"] == "redraw_then_full_hard_check"
assert regression["regressed_dimensions"]

print("PASS: 5 consumer routing scenarios")
