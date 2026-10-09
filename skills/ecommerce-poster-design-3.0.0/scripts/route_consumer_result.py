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


def route_result(
    result: Dict[str, Any],
    version: Dict[str, Any],
    redraw_attempts: int,
    phase: str = "pre_aesthetic",
    aesthetic_generation_round: int = 0,
) -> Dict[str, Any]:
    if result.get("schema_version") != "A-D-2.0" or result.get("agent_name") != "consumer_agent":
        raise ValueError("expected an A-D-2.0 consumer_agent result")
    if type(redraw_attempts) is not int or redraw_attempts < 0:
        raise ValueError("redraw_attempts cannot be negative")
    if phase not in {"pre_aesthetic", "aesthetic_recheck"}:
        raise ValueError("phase must be pre_aesthetic or aesthetic_recheck")
    if type(aesthetic_generation_round) is not int or aesthetic_generation_round < 0:
        raise ValueError("aesthetic_generation_round cannot be negative")

    flags = version.get("feature_flags", {})
    if flags.get("consumer_agent") is not True:
        raise ValueError("consumer_agent feature flag is not enabled")
    max_attempts = version.get("retry_policy", {}).get("max_redraw_attempts")
    aesthetic_max_rounds = version.get("retry_policy", {}).get("aesthetic_max_generation_rounds")
    if type(max_attempts) is not int or max_attempts < 0:
        raise ValueError("invalid max_redraw_attempts")
    if type(aesthetic_max_rounds) is not int or aesthetic_max_rounds < 1:
        raise ValueError("invalid aesthetic_max_generation_rounds")
    if redraw_attempts > max_attempts:
        raise ValueError("redraw_attempts exceeds the pre-aesthetic limit")
    if phase == "pre_aesthetic" and aesthetic_generation_round != 0:
        raise ValueError("pre_aesthetic phase cannot carry an aesthetic generation round")
    if phase == "aesthetic_recheck" and not 1 <= aesthetic_generation_round <= aesthetic_max_rounds:
        raise ValueError("aesthetic_recheck requires a generation round within the configured budget")

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
        "pre_aesthetic_redraw_attempts": redraw_attempts,
        "max_pre_aesthetic_redraw_attempts": max_attempts,
        "phase": phase,
        "aesthetic_generation_round": aesthetic_generation_round,
        "aesthetic_max_generation_rounds": aesthetic_max_rounds,
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
            type(result.get("score")) is int
            and result["score"] >= 80
            and set(scores) == DIMENSIONS
            and all(type(scores[name]) is int and scores[name] >= 14 for name in DIMENSIONS)
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
            "reason": "consumer passed and aesthetic_agent is disabled by configuration",
        }

    if route != "poster_generation_skill":
        raise ValueError("a normal failed evaluation must route to poster_generation_skill")
    if phase == "aesthetic_recheck":
        if aesthetic_generation_round >= aesthetic_max_rounds:
            return {
                **common,
                "status": "degraded",
                "action": "stop_at_aesthetic_limit",
                "reason": "aesthetic generation budget exhausted during consumer recheck",
                "unresolved_problems": result.get("problem_list", []),
            }
        return {
            **common,
            "status": "in_progress",
            "action": "regenerate_for_aesthetic_then_full_hard_check",
            "next_aesthetic_generation_round": aesthetic_generation_round + 1,
            "problem_list": result.get("problem_list", []),
            "modify_suggestion": result.get("modify_suggestion", []),
        }
    if redraw_attempts >= max_attempts:
        return {
            **common,
            "status": "degraded",
            "action": "stop_at_limit",
            "reason": "pre-aesthetic redraw limit exhausted",
            "unresolved_problems": result.get("problem_list", []),
        }
    return {
        **common,
        "status": "in_progress",
        "action": "redraw_then_full_hard_check",
        "next_pre_aesthetic_redraw_attempt": redraw_attempts + 1,
        "problem_list": result.get("problem_list", []),
        "modify_suggestion": result.get("modify_suggestion", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--config", default="assets/config/version.json")
    parser.add_argument("--redraw-attempts", type=int, required=True)
    parser.add_argument("--phase", choices=["pre_aesthetic", "aesthetic_recheck"], default="pre_aesthetic")
    parser.add_argument("--aesthetic-generation-round", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    version = json.loads(Path(args.config).read_text(encoding="utf-8"))
    rendered = json.dumps(
        route_result(result, version, args.redraw_attempts, args.phase, args.aesthetic_generation_round),
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
