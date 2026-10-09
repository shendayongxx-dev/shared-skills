#!/usr/bin/env python3
import copy
import json
from pathlib import Path

from assemble_aesthetic_input import flatten_protected_content
from route_aesthetic_result import route_result as route_aesthetic
from route_consumer_result import route_result as route_consumer


ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))
EXAMPLES = ROOT / "modules" / "consumer-agent" / "examples"


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


protected = load("consumer-output-pass.json")["protected_content"]
flattened = flatten_protected_content(protected)
aesthetic_pass = {
    "agent_name": "aesthetic_agent", "score": 8.7, "pass": True,
    "problem_list": [], "modify_suggestion": [],
    "protected_content": ["商品主体：模块通用保护说明", "价格文案：模块通用保护说明"] + flattened,
    "meta": {"judge_dimensions": ["构图与视觉平衡"], "confidence": 0.9},
}
aesthetic_assessment = {
    "status": "pass", "score_unrounded": 8.7, "below_threshold": [],
    "dimensions": [{"score": 8.5, "pass": True} for _ in range(6)],
}
assert route_aesthetic(aesthetic_pass, VERSION, 0, protected, aesthetic_assessment)["action"] == "invoke_consumer_agent"
assert route_aesthetic(aesthetic_pass, VERSION, 0, protected)["action"] == "provide_aesthetic_assessment"

aesthetic_fail = copy.deepcopy(aesthetic_pass)
aesthetic_fail.update({"score": 7.2, "pass": False, "problem_list": ["层级不足"], "modify_suggestion": ["重排层级"]})
retry_aesthetic = route_aesthetic(aesthetic_fail, VERSION, 1, protected, None)
assert retry_aesthetic["action"] == "redraw_then_full_hard_check_then_aesthetic"
assert retry_aesthetic["next_global_redraw_attempt"] == 2
assert route_aesthetic(aesthetic_fail, VERSION, 3, protected, None)["status"] == "degraded"

mismatched_aesthetic = copy.deepcopy(aesthetic_pass)
mismatched_aesthetic["protected_content"] = ["changed"]
assert route_aesthetic(mismatched_aesthetic, VERSION, 0, protected, aesthetic_assessment)["status"] == "blocked"

unevaluated = copy.deepcopy(aesthetic_fail)
unevaluated.update({"score": 0, "problem_list": ["无法评价：缺少海报"], "meta": {"judge_dimensions": ["构图"], "confidence": 0}})
assert route_aesthetic(unevaluated, VERSION, 0, protected, None)["status"] == "blocked"

consumer_pass = load("consumer-output-pass.json")
completed = route_consumer(consumer_pass, VERSION, 1, protected)
assert completed["status"] == "passed" and completed["action"] == "complete_ablation"

consumer_iterate = load("consumer-output-iterate.json")
retry_consumer = route_consumer(consumer_iterate, VERSION, 1, consumer_iterate["protected_content"])
assert retry_consumer["action"] == "redraw_then_full_hard_check_then_aesthetic"
assert retry_consumer["next_global_redraw_attempt"] == 2
assert route_consumer(consumer_iterate, VERSION, 3, consumer_iterate["protected_content"])["status"] == "degraded"

consumer_blocked = load("consumer-output-complete-input.json")
blocked = route_consumer(consumer_blocked, VERSION, 0, consumer_blocked["protected_content"])
assert blocked["status"] == "blocked" and blocked["action"] == "complete_input"

consumer_mismatch = route_consumer(consumer_pass, VERSION, 0, {**protected, "cta": ["changed"]})
assert consumer_mismatch["status"] == "blocked"

bad_assessment = copy.deepcopy(aesthetic_assessment)
bad_assessment["dimensions"][0] = {"score": 7.5, "pass": False}
try:
    route_aesthetic(aesthetic_pass, VERSION, 0, protected, bad_assessment)
except ValueError:
    pass
else:
    raise AssertionError("public pass must not bypass a failed aesthetic dimension")

print("PASS: 12 aesthetic-first and consumer routing scenarios")
