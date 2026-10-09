#!/usr/bin/env python3
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from assemble_aesthetic_input import assemble  # noqa: E402
from route_aesthetic_result import AESTHETIC_DIMENSIONS, flatten_protected, route_result  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def assert_value_error(callable_, message):
    try:
        callable_()
        raise AssertionError(message)
    except ValueError:
        pass


examples = ROOT / "modules" / "consumer-agent" / "examples"
consumer_input = load(examples / "nori-input.json")
consumer_result = load(examples / "consumer-output-pass.json")
version = load(ROOT / "assets" / "config" / "version.json")

aesthetic_input, context = assemble(
    consumer_input,
    consumer_result,
    "runs/v01/hard-check.json",
    "runs/v01/consumer-result.json",
)
assert set(aesthetic_input) == {"poster_image", "product_input"}
assert aesthetic_input["poster_image"] == consumer_input["poster_image"]
assert aesthetic_input["product_input"]["product_img"] == consumer_input["evaluation_context"]["product_img"]
assert aesthetic_input["product_input"]["marketing_target"] == consumer_input["source_input"]["marketing"]["goal"]
assert context["protected_content"] == consumer_result["protected_content"]
assert context["hard_check"]["status"] == context["consumer"]["status"] == "pass"

drifted_consumer = deepcopy(consumer_result)
drifted_consumer["protected_content"]["cta"] = ["立即下单"]
assert_value_error(
    lambda: assemble(consumer_input, drifted_consumer, "hard.json", "consumer.json"),
    "consumer protected-content drift should fail",
)
mismatched_version = deepcopy(consumer_result)
mismatched_version["version_id"] = "v02"
assert_value_error(
    lambda: assemble(consumer_input, mismatched_version, "hard.json", "consumer.json"),
    "consumer version mismatch should fail",
)
mismatched_product = deepcopy(consumer_input)
mismatched_product["evaluation_context"]["product_img"] = "another-product.png"
assert_value_error(
    lambda: assemble(mismatched_product, consumer_result, "hard.json", "consumer.json"),
    "primary product image mismatch should fail",
)
malformed_protected_input = deepcopy(consumer_input)
malformed_protected_result = deepcopy(consumer_result)
del malformed_protected_input["protected_content"]["legal_text"]
del malformed_protected_result["protected_content"]["legal_text"]
assert_value_error(
    lambda: assemble(malformed_protected_input, malformed_protected_result, "hard.json", "consumer.json"),
    "missing protected-content group should fail",
)

flat = flatten_protected(consumer_result["protected_content"])
base = {
    "agent_name": "aesthetic_agent",
    "score": 7.5,
    "pass": False,
    "problem_list": ["层级不足"],
    "modify_suggestion": ["重建信息层级"],
    "protected_content": flat,
    "meta": {"judge_dimensions": AESTHETIC_DIMENSIONS, "confidence": 0.8},
}


def passing_assessment(score=8.6):
    return {
        "schema_version": "2.0",
        "status": "pass",
        "score_unrounded": score,
        "threshold": 8.5,
        "dimensions": [
            {
                "key": key,
                "label": label,
                "score": score,
                "threshold": 8,
                "gap": score - 8,
                "pass": True,
                "evidence": "synthetic passing evidence",
                "confidence": 0.9,
            }
            for key, label in zip(
                ["composition", "hierarchy", "color", "typography", "consistency", "finish"],
                AESTHETIC_DIMENSIONS,
            )
        ],
        "below_threshold": [],
        "config_snapshot": {
            "total_threshold": 8.5,
            "loop": {"max_generation_rounds": 8},
        },
        "design_plan": None,
        "generation_assets_ready": True,
        "overall_qualified": True,
        "run_binding": {
            "poster_image": aesthetic_input["poster_image"],
            "product_img": aesthetic_input["product_input"]["product_img"],
            "context_version": consumer_result["version_id"],
        },
    }

routed = route_result(base, consumer_result, version, 0, [])
assert routed["status"] == "in_progress"
assert routed["action"] == "regenerate_then_full_pipeline"
assert routed["next_generation_round"] == 1
assert routed["next_stagnation_count"] == 0
assert routed["protected_content"] == consumer_result["protected_content"]

stagnated = deepcopy(base)
stagnated["score"] = 8.15
routed = route_result(stagnated, consumer_result, version, 3, [8.0, 8.1], 1)
assert routed["action"] == "change_design_direction_then_regenerate"
assert routed["next_stagnation_count"] == 0

after_direction_change = deepcopy(base)
after_direction_change["score"] = 8.16
routed = route_result(after_direction_change, consumer_result, version, 4, [8.0, 8.1, 8.15], 0)
assert routed["action"] == "regenerate_then_full_pipeline"
assert routed["next_stagnation_count"] == 1

passed = deepcopy(base)
passed.update({"score": 8.6, "pass": True, "problem_list": [], "modify_suggestion": []})
routed = route_result(
    passed,
    consumer_result,
    version,
    2,
    [7.5, 8.0],
    assessment=passing_assessment(),
    aesthetic_input=aesthetic_input,
)
assert routed["status"] == "passed" and routed["action"] == "complete"
assert routed["assessment_verified"] is True
assert_value_error(
    lambda: route_result(passed, consumer_result, version, 2, [7.5, 8.0]),
    "pass=true without internal assessment should fail",
)
assert_value_error(
    lambda: route_result(
        passed,
        consumer_result,
        version,
        2,
        [7.5, 8.0],
        assessment=passing_assessment(),
    ),
    "pass=true without the bound aesthetic input should fail",
)
failed_dimension_assessment = passing_assessment()
failed_dimension_assessment["dimensions"][-1].update({"score": 7.5, "pass": False})
assert_value_error(
    lambda: route_result(
        passed,
        consumer_result,
        version,
        2,
        [7.5, 8.0],
        assessment=failed_dimension_assessment,
        aesthetic_input=aesthetic_input,
    ),
    "pass=true with a failed internal dimension should fail",
)
score_mismatch_assessment = passing_assessment(9.0)
assert_value_error(
    lambda: route_result(
        passed,
        consumer_result,
        version,
        2,
        [7.5, 8.0],
        assessment=score_mismatch_assessment,
        aesthetic_input=aesthetic_input,
    ),
    "public and internal score mismatch should fail",
)
cross_candidate_assessment = passing_assessment()
cross_candidate_assessment["run_binding"]["poster_image"] = "another-poster.png"
assert_value_error(
    lambda: route_result(
        passed,
        consumer_result,
        version,
        2,
        [7.5, 8.0],
        assessment=cross_candidate_assessment,
        aesthetic_input=aesthetic_input,
    ),
    "assessment from another candidate should fail",
)

incomplete = deepcopy(base)
incomplete.update({"score": 0, "meta": {"judge_dimensions": base["meta"]["judge_dimensions"], "confidence": 0}})
routed = route_result(incomplete, consumer_result, version, 0, [])
assert routed["status"] == "blocked"

exhausted = deepcopy(base)
routed = route_result(exhausted, consumer_result, version, 8, [7.0, 7.8, 8.1])
assert routed["status"] == "degraded" and routed["action"] == "return_best_candidate"

drifted = deepcopy(base)
drifted["protected_content"] = flat[:-1]
try:
    route_result(drifted, consumer_result, version, 0, [])
    raise AssertionError("protected-content drift should fail")
except ValueError as exc:
    assert "protected content" in str(exc)

with_additional_protection = deepcopy(base)
with_additional_protection["protected_content"].append("额外保护：已确认活动角标")
assert route_result(with_additional_protection, consumer_result, version, 0, [])["status"] == "in_progress"
duplicated_upstream = deepcopy(consumer_result)
duplicated_upstream["protected_content"]["cta"] = ["立即选购", "立即选购"]
duplicated_upstream_result = deepcopy(base)
duplicated_upstream_result["protected_content"] = flatten_protected(duplicated_upstream["protected_content"])
assert route_result(duplicated_upstream_result, duplicated_upstream, version, 0, [])["status"] == "in_progress"
duplicated_additional = deepcopy(with_additional_protection)
duplicated_additional["protected_content"].append("额外保护：已确认活动角标")
assert_value_error(
    lambda: route_result(duplicated_additional, consumer_result, version, 0, []),
    "duplicate additional protection should fail",
)

boolean_score = deepcopy(base)
boolean_score["score"] = True
assert_value_error(
    lambda: route_result(boolean_score, consumer_result, version, 0, []),
    "boolean aesthetic score should fail",
)
wrong_dimensions = deepcopy(base)
wrong_dimensions["meta"]["judge_dimensions"] = list(reversed(AESTHETIC_DIMENSIONS))
assert_value_error(
    lambda: route_result(wrong_dimensions, consumer_result, version, 0, []),
    "non-canonical aesthetic dimensions should fail",
)
boolean_consumer_score = deepcopy(consumer_result)
boolean_consumer_score["score"] = True
assert_value_error(
    lambda: route_result(base, boolean_consumer_score, version, 0, []),
    "boolean consumer score should fail",
)
assert_value_error(
    lambda: route_result(base, consumer_result, version, 0, [], True),
    "boolean stagnation counter should fail",
)
assert_value_error(
    lambda: route_result(base, consumer_result, version, 0, [7.0]),
    "round zero cannot have previous aesthetic scores",
)
assert_value_error(
    lambda: route_result(base, consumer_result, version, 2, [7.0], 2),
    "stagnation counter must already be reset at the threshold",
)

print(json.dumps({"valid": True, "tests": 37}, ensure_ascii=False))
