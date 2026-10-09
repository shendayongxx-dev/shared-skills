#!/usr/bin/env python3
import json
from copy import deepcopy
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
assert iterate["next_pre_aesthetic_redraw_attempt"] == 2

exhausted = route_result(load("consumer-output-iterate.json"), VERSION, 3)
assert exhausted["status"] == "degraded" and exhausted["action"] == "stop_at_limit"

blocked = route_result(load("consumer-output-complete-input.json"), VERSION, 0)
assert blocked["status"] == "blocked" and blocked["action"] == "complete_input"

regression = route_result(load("consumer-output-regression.json"), VERSION, 2)
assert regression["action"] == "redraw_then_full_hard_check"
assert regression["regressed_dimensions"]

boolean_score = deepcopy(load("consumer-output-pass.json"))
boolean_score["score"] = True
try:
    route_result(boolean_score, VERSION, 1)
    raise AssertionError("boolean score must not pass as an integer score")
except ValueError:
    pass

try:
    route_result(load("consumer-output-pass.json"), VERSION, True)
    raise AssertionError("boolean redraw_attempts must not pass as an integer counter")
except ValueError:
    pass

aesthetic_retry = route_result(
    load("consumer-output-iterate.json"), VERSION, 3, "aesthetic_recheck", 4
)
assert aesthetic_retry["action"] == "regenerate_for_aesthetic_then_full_hard_check"
assert aesthetic_retry["next_aesthetic_generation_round"] == 5

aesthetic_exhausted = route_result(
    load("consumer-output-iterate.json"), VERSION, 3, "aesthetic_recheck", 8
)
assert aesthetic_exhausted["status"] == "degraded"
assert aesthetic_exhausted["action"] == "stop_at_aesthetic_limit"

aesthetic_pass = route_result(
    load("consumer-output-pass.json"), VERSION, 3, "aesthetic_recheck", 4
)
assert aesthetic_pass["action"] == "invoke_aesthetic_agent"
assert aesthetic_pass["aesthetic_generation_round"] == 4

try:
    route_result(load("consumer-output-pass.json"), VERSION, 0, "aesthetic_recheck", 0)
    raise AssertionError("aesthetic recheck round 0 must fail")
except ValueError:
    pass

try:
    route_result(load("consumer-output-pass.json"), VERSION, 0, "pre_aesthetic", 1)
    raise AssertionError("pre-aesthetic phase must not carry an aesthetic round")
except ValueError:
    pass

print("PASS: 12 consumer routing scenarios")
