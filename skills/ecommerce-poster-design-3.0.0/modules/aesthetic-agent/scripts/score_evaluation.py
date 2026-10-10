"""Deterministic scorer for ecommerce-aesthetic-agent 3.0.0-rc.4."""

from argparse import ArgumentParser
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONSUMER_DIMENSIONS = {
    "product_recognition",
    "benefit_clarity",
    "offer_visibility",
    "population_scene_fit",
    "purchase_drive",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def context_hash(workflow):
    payload = json.dumps(
        {
            "request_id": workflow["candidate"]["request_id"],
            "version_id": workflow["candidate"]["loop_state"]["version_id"],
            "poster_image": workflow["candidate"]["poster_image"],
            "protected_content": workflow["candidate"]["protected_content"],
            "consumer_score": workflow["consumer_result"]["score"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_upstream(workflow):
    require(isinstance(workflow, dict) and set(workflow) == {"schema_version", "candidate", "consumer_result"}, "exact workflow input fields required")
    require(workflow["schema_version"] == "A-D-AESTHETIC-3.0", "unsupported workflow schema")
    candidate = workflow["candidate"]
    consumer = workflow["consumer_result"]
    require(candidate.get("schema_version") == "A-D-2.0", "candidate must use A-D-2.0")
    require(consumer.get("schema_version") == "A-D-2.0" and consumer.get("agent_name") == "consumer_agent", "formal consumer result required")
    require(candidate.get("request_id") == consumer.get("request_id"), "consumer result belongs to another request")
    require(candidate.get("loop_state", {}).get("version_id") == consumer.get("version_id"), "consumer result belongs to another image version")
    require(candidate.get("protected_content") == consumer.get("protected_content"), "protected content changed between agents")
    require(consumer.get("pass") is True and consumer.get("hard_fail") is False, "consumer must pass before aesthetic evaluation")
    require(isinstance(consumer.get("score"), int) and consumer["score"] >= 80, "invalid consumer pass score")
    require(consumer.get("next_route") == "aesthetic_agent", "consumer route must target aesthetic_agent")
    require(set(consumer.get("locked_dimensions", [])) == CONSUMER_DIMENSIONS, "all five passed consumer functions must be locked")
    return candidate, consumer


def blocked_result(candidate, draft, reason):
    problems = draft.get("problem_list") or ["无法完成美学评价：" + reason]
    suggestions = draft.get("modify_suggestion") or ["补齐缺失输入或提供可读取图像；保持八组保护对象和当前消费者锁，不盲目重画"]
    require(len(problems) == len(suggestions) and 1 <= len(problems) <= 3, "blocked feedback must be paired, maximum three")
    return {
        "agent_name": "aesthetic_agent",
        "score": None,
        "pass": False,
        "problem_list": problems,
        "modify_suggestion": suggestions,
        "protected_content": deepcopy(candidate["protected_content"]),
        "meta": {"judge_dimensions": [], "confidence": 0},
    }


def calculate(workflow, draft, rubric=None):
    candidate, consumer = validate_upstream(workflow)
    require(isinstance(draft, dict), "draft object required")
    blocked = draft.get("evaluation_blocked")
    if blocked is not None:
        require(text(blocked), "evaluation_blocked must be null or a reason")
        return blocked_result(candidate, draft, blocked), {
            "rubric_version": "3.0.0-rc.4",
            "score": None,
            "status": "blocked",
            "reason": blocked,
            "context_hash": context_hash(workflow),
        }

    rubric = rubric or load(ROOT / "assets/rubric.json")
    groups = rubric["dimensions"]
    expected = {item_id for dimension in groups.values() for item_id, _, _ in dimension["items"]}
    items = draft.get("subcriteria")
    require(isinstance(items, dict) and set(items) == expected, "exactly the 25 rubric subcriteria are required")
    details = {}
    scores = {}
    for key, dimension in groups.items():
        raw = Decimal(0)
        rows = []
        for item_id, label, weight in dimension["items"]:
            item = items[item_id]
            require(isinstance(item, dict) and set(item) == {"level", "evidence", "enhancement_evidence", "root_issue_id"}, item_id + ": exact observation fields required")
            level = item["level"]
            require(type(level) is int and 0 <= level <= 4, item_id + ": level must be integer 0..4")
            require(text(item["evidence"]), item_id + ": visible evidence required")
            if level == 4:
                require(text(item["enhancement_evidence"]), item_id + ": level 4 needs concrete enhancement evidence")
            else:
                require(item["enhancement_evidence"] == "", item_id + ": enhancement evidence is reserved for level 4")
            require(item["root_issue_id"] is None or text(item["root_issue_id"]), item_id + ": invalid root issue ID")
            contribution = Decimal(weight) * level / 4
            raw += contribution
            rows.append({
                "id": item_id,
                "label": label,
                "weight": weight,
                "level": level,
                "contribution": float(contribution),
                "evidence": item["evidence"],
                "enhancement_evidence": item["enhancement_evidence"],
                "root_issue_id": item["root_issue_id"],
            })
        score = int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        scores[key] = score
        details[key] = {"label": dimension["label"], "raw_score": float(raw), "score": score, "minimum": dimension["minimum"], "items": rows}

    problems = draft.get("problem_list")
    suggestions = draft.get("modify_suggestion")
    require(isinstance(problems, list) and isinstance(suggestions, list) and len(problems) == len(suggestions) and len(problems) <= 3, "paired feedback, maximum three")
    require(all(text(x) for x in problems + suggestions), "feedback must contain nonempty strings")
    critical = draft.get("critical_issues")
    require(isinstance(critical, list) and len(set(critical)) == len(critical) and all(text(x) for x in critical), "critical_issues must be unique nonempty strings")
    require(set(critical).issubset(set(problems)), "critical issues must also appear in problem_list")
    confidence = draft.get("confidence")
    require(type(confidence) in (int, float) and not isinstance(confidence, bool) and 0 <= confidence <= 1, "confidence must be 0..1")

    total = sum(scores.values())
    dimension_pass = all(scores[key] >= groups[key]["minimum"] for key in groups)
    passed = total >= rubric["pass_rules"]["minimum_score"] and dimension_pass and not critical
    if not passed:
        require(bool(problems), "failed evaluation needs actionable feedback")
        markers = ["允许编辑：", "禁止编辑：", "消费者功能锁：", "验收："]
        for suggestion in suggestions:
            require(all(marker in suggestion for marker in markers), "each failed suggestion needs edit scope, prohibition, consumer lock and acceptance criteria")

    labels = [groups[key]["label"] for key in groups]
    result = {
        "agent_name": "aesthetic_agent",
        "score": total,
        "pass": bool(passed),
        "problem_list": problems,
        "modify_suggestion": suggestions,
        "protected_content": deepcopy(candidate["protected_content"]),
        "meta": {"judge_dimensions": labels, "confidence": confidence},
    }
    audit = {
        "rubric_version": rubric["version"],
        "score": total,
        "pass": bool(passed),
        "dimension_scores": scores,
        "dimensions": details,
        "critical_issues": critical,
        "consumer_lock": sorted(consumer["locked_dimensions"]),
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "context_hash": context_hash(workflow),
    }
    return result, audit


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-input", required=True)
    parser.add_argument("--draft", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--details", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    details = Path(args.details)
    require(not output.exists() and not details.exists(), "refusing to overwrite existing result files")
    result, audit = calculate(load(args.workflow_input), load(args.draft))
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    details.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit("aesthetic scorer: " + str(exc))
