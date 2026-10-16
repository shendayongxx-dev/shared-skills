#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


DIMENSIONS = {
    "product_recognition",
    "benefit_clarity",
    "offer_visibility",
    "population_scene_fit",
    "purchase_drive",
}


def route_result(result: Dict[str, Any], version: Dict[str, Any], redraw_attempts: int) -> Dict[str, Any]:
    if result.get("schema_version") != "A-D-2.0" or result.get("agent_name") != "consumer_agent":
        raise ValueError("expected an A-D-2.0 consumer_agent result")
    if redraw_attempts < 0:
        raise ValueError("redraw_attempts cannot be negative")

    flags = version.get("feature_flags", {})
    if flags.get("consumer_agent") is not True:
        raise ValueError("consumer_agent feature flag is not enabled")
    max_attempts = version.get("retry_policy", {}).get("max_redraw_attempts")
    if not isinstance(max_attempts, int) or max_attempts < 0:
        raise ValueError("invalid max_redraw_attempts")

    route = result.get("next_route")
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
            raise ValueError("a passing consumer result must route to aesthetic_agent")
        if flags.get("aesthetic_agent") is True:
            return {**common, "status": "in_progress", "action": "invoke_aesthetic_agent"}
        return {
            **common,
            "status": "passed",
            "action": "complete_v2",
            "reason": "consumer passed and aesthetic_agent is disabled in Skill 2.0",
        }

    if route != "poster_generation_skill":
        raise ValueError("a normal failed evaluation must route to poster_generation_skill")
    if redraw_attempts >= max_attempts:
        return {
            **common,
            "status": "degraded",
            "action": "stop_at_limit",
            "reason": "global redraw limit exhausted",
            "unresolved_problems": result.get("problem_list", []),
            "candidate_disposition": "reject" if regressed else "retain_for_comparison",
            "restore_last_consumer_pass": bool(regressed),
        }
    if regressed:
        return {
            **common,
            "status": "in_progress",
            "action": "redraw_from_last_consumer_pass_then_full_hard_check",
            "reason": "aesthetic retry regressed one or more frozen consumer dimensions",
            "candidate_disposition": "reject",
            "restore_last_consumer_pass": True,
            "next_global_redraw_attempt": redraw_attempts + 1,
            "problem_list": result.get("problem_list", []),
            "modify_suggestion": result.get("modify_suggestion", []),
        }
    return {
        **common,
        "status": "in_progress",
        "action": "redraw_then_full_hard_check",
        "next_global_redraw_attempt": redraw_attempts + 1,
        "problem_list": result.get("problem_list", []),
        "modify_suggestion": result.get("modify_suggestion", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    version = json.loads(Path(args.config).read_text(encoding="utf-8"))
    rendered = json.dumps(route_result(result, version, args.redraw_attempts), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
