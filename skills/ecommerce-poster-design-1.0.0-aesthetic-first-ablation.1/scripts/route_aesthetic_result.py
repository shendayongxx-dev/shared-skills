#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict

from assemble_aesthetic_input import flatten_protected_content


def _expected_flattened(value: Any):
    if isinstance(value, dict) and "groups" in value and "aesthetic_flattened" in value:
        return value["aesthetic_flattened"]
    if isinstance(value, dict):
        return flatten_protected_content(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError("expected protected content must be the eight-group object, adapter snapshot, or string array")


def route_result(
    result: Dict[str, Any],
    version: Dict[str, Any],
    redraw_attempts: int,
    expected_protected: Any,
    assessment: Any = None,
) -> Dict[str, Any]:
    if result.get("agent_name") != "aesthetic_agent":
        raise ValueError("expected an aesthetic_agent result")
    if redraw_attempts < 0:
        raise ValueError("redraw_attempts cannot be negative")
    flags = version.get("feature_flags", {})
    if flags.get("aesthetic_agent") is not True or flags.get("consumer_agent") is not True:
        raise ValueError("both Agent feature flags must be enabled")
    if version.get("agent_order") != ["aesthetic_agent", "consumer_agent"]:
        raise ValueError("agent_order must be aesthetic_agent then consumer_agent")
    max_attempts = version.get("retry_policy", {}).get("max_redraw_attempts")
    if not isinstance(max_attempts, int) or max_attempts < 0:
        raise ValueError("invalid max_redraw_attempts")
    expected = _expected_flattened(expected_protected)
    common = {
        "aesthetic_score": result.get("score"),
        "global_redraw_attempts": redraw_attempts,
        "max_redraw_attempts": max_attempts,
        "protected_content": expected,
    }
    actual_protected = result.get("protected_content")
    canonical_suffix_ok = (
        isinstance(actual_protected, list)
        and len(actual_protected) >= len(expected)
        and actual_protected[-len(expected):] == expected
    )
    if not canonical_suffix_ok:
        return {
            **common,
            "status": "blocked",
            "action": "resolve_protected_content_mismatch",
            "reason": "aesthetic Agent did not return the canonical flattened protected content unchanged as its ordered suffix",
        }
    score = result.get("score")
    confidence = (result.get("meta") or {}).get("confidence")
    problems = result.get("problem_list") or []
    unevaluated = score == 0 and confidence == 0 and problems and str(problems[0]).startswith("无法评价")
    if unevaluated:
        return {**common, "status": "blocked", "action": "resolve_aesthetic_input", "reason": problems[0]}
    if result.get("pass") is True:
        if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 8.5:
            raise ValueError("aesthetic pass=true contradicts the total-score threshold")
        if not isinstance(assessment, dict):
            return {
                **common,
                "status": "blocked",
                "action": "provide_aesthetic_assessment",
                "reason": "assessment-internal.json is required to verify all six dimensions",
            }
        dimensions = assessment.get("dimensions")
        score_unrounded = assessment.get("score_unrounded")
        valid_dimensions = (
            assessment.get("status") == "pass"
            and isinstance(score_unrounded, (int, float))
            and not isinstance(score_unrounded, bool)
            and score_unrounded >= 8.5
            and isinstance(dimensions, list)
            and len(dimensions) == 6
            and all(
                isinstance(item, dict)
                and item.get("pass") is True
                and isinstance(item.get("score"), (int, float))
                and not isinstance(item.get("score"), bool)
                and item["score"] >= 8
                for item in dimensions
            )
            and assessment.get("below_threshold") == []
        )
        if not valid_dimensions:
            raise ValueError("public aesthetic pass contradicts assessment-internal dimension gates")
        return {**common, "status": "in_progress", "action": "invoke_consumer_agent"}
    if redraw_attempts >= max_attempts:
        return {
            **common,
            "status": "degraded",
            "action": "stop_at_limit",
            "reason": "global redraw limit exhausted before aesthetic pass",
            "unresolved_problems": problems,
        }
    return {
        **common,
        "status": "in_progress",
        "action": "redraw_then_full_hard_check_then_aesthetic",
        "triggered_by": "aesthetic_agent",
        "next_global_redraw_attempt": redraw_attempts + 1,
        "problem_list": problems,
        "modify_suggestion": result.get("modify_suggestion") or [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--expected-protected", required=True)
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    version = json.loads(Path(args.config).read_text(encoding="utf-8"))
    expected = json.loads(Path(args.expected_protected).read_text(encoding="utf-8"))
    assessment = json.loads(Path(args.assessment).read_text(encoding="utf-8"))
    rendered = json.dumps(route_result(result, version, args.redraw_attempts, expected, assessment), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
