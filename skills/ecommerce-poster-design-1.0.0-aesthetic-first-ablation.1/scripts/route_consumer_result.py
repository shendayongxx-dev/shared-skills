#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional


DIMENSIONS = {
    "product_recognition", "benefit_clarity", "offer_visibility",
    "population_scene_fit", "purchase_drive",
}


def route_result(
    result: Dict[str, Any],
    version: Dict[str, Any],
    redraw_attempts: int,
    expected_protected: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if result.get("schema_version") != "A-D-2.0" or result.get("agent_name") != "consumer_agent":
        raise ValueError("expected an A-D-2.0 consumer_agent result")
    if redraw_attempts < 0:
        raise ValueError("redraw_attempts cannot be negative")
    flags = version.get("feature_flags", {})
    if flags.get("consumer_agent") is not True or flags.get("aesthetic_agent") is not True:
        raise ValueError("both Agent feature flags must be enabled")
    if version.get("agent_order") != ["aesthetic_agent", "consumer_agent"]:
        raise ValueError("agent_order must be aesthetic_agent then consumer_agent")
    max_attempts = version.get("retry_policy", {}).get("max_redraw_attempts")
    if not isinstance(max_attempts, int) or max_attempts < 0:
        raise ValueError("invalid max_redraw_attempts")
    regressed = result.get("regressed_dimensions") or []
    common = {
        "request_id": result.get("request_id"),
        "version_id": result.get("version_id"),
        "consumer_score": result.get("score"),
        "dimension_scores": result.get("dimension_scores"),
        "locked_dimensions": result.get("locked_dimensions") or [],
        "regressed_dimensions": regressed,
        "protected_content": result.get("protected_content"),
        "global_redraw_attempts": redraw_attempts,
        "max_redraw_attempts": max_attempts,
    }
    if expected_protected is not None and result.get("protected_content") != expected_protected:
        return {
            **common,
            "status": "blocked",
            "action": "resolve_protected_content_mismatch",
            "reason": "consumer Agent did not return the canonical eight-group protected content unchanged",
        }
    route = result.get("next_route")
    if route == "complete_input":
        return {
            **common,
            "status": "blocked",
            "action": "complete_input",
            "reason": "consumer evaluation could not be completed",
            "input_errors": result.get("meta", {}).get("input_errors", []),
        }
    if result.get("pass") is True:
        scores = result.get("dimension_scores") or {}
        valid_pass = (
            isinstance(result.get("score"), int)
            and result["score"] >= 80
            and set(scores) == DIMENSIONS
            and all(isinstance(scores[name], int) and scores[name] >= 14 for name in DIMENSIONS)
            and result.get("hard_fail") is False
            and not regressed
        )
        if not valid_pass:
            raise ValueError("pass=true contradicts A-D-2.0 thresholds or regression state")
        if route != "aesthetic_agent":
            raise ValueError("a passing consumer result must retain the A-D-2.0 aesthetic_agent route value")
        return {
            **common,
            "status": "passed",
            "action": "complete_ablation",
            "reason": "the same candidate passed aesthetic first and then consumer evaluation",
        }
    if route != "poster_generation_skill":
        raise ValueError("a normal failed evaluation must route to poster_generation_skill")
    if redraw_attempts >= max_attempts:
        return {
            **common,
            "status": "degraded",
            "action": "stop_at_limit",
            "reason": "global redraw limit exhausted before consumer pass",
            "unresolved_problems": result.get("problem_list", []),
        }
    return {
        **common,
        "status": "in_progress",
        "action": "redraw_then_full_hard_check_then_aesthetic",
        "triggered_by": "consumer_agent",
        "next_global_redraw_attempt": redraw_attempts + 1,
        "problem_list": result.get("problem_list", []),
        "modify_suggestion": result.get("modify_suggestion", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--expected-protected")
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    version = json.loads(Path(args.config).read_text(encoding="utf-8"))
    expected = json.loads(Path(args.expected_protected).read_text(encoding="utf-8")) if args.expected_protected else None
    rendered = json.dumps(route_result(result, version, args.redraw_attempts, expected), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
