import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("score_evaluation", ROOT / "scripts/score_evaluation.py")
score_evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score_evaluation)


def protected():
    return {
        "product_identity": ["NORI 600 mL 不锈钢保温杯"],
        "product_quantity": 1,
        "brand_and_logo": ["NORI"],
        "price_and_unit": ["129元"],
        "promotion_and_period": ["2026年10月1日至10月15日"],
        "selling_points": ["316不锈钢内胆", "12小时保温保冷", "一键锁扣 防漏随行"],
        "cta": ["立即选购"],
        "legal_text": [],
    }


def workflow():
    pc = protected()
    candidate = {
        "schema_version": "A-D-2.0",
        "request_id": "test-001",
        "poster_image": "candidate-v1.png",
        "protected_content": copy.deepcopy(pc),
        "loop_state": {"version_id": "v1"},
    }
    consumer = {
        "schema_version": "A-D-2.0",
        "request_id": "test-001",
        "version_id": "v1",
        "agent_name": "consumer_agent",
        "score": 88,
        "pass": True,
        "protected_content": copy.deepcopy(pc),
        "locked_dimensions": sorted(score_evaluation.CONSUMER_DIMENSIONS),
        "hard_fail": False,
        "next_route": "aesthetic_agent",
    }
    return {"schema_version": "A-D-AESTHETIC-3.0", "candidate": candidate, "consumer_result": consumer}


def draft(level=3):
    rubric = json.loads((ROOT / "assets/rubric.json").read_text(encoding="utf-8"))
    ids = [item_id for dimension in rubric["dimensions"].values() for item_id, _, _ in dimension["items"]]
    items = {item_id: {"level": level, "evidence": "synthetic test evidence for " + item_id,
                       "enhancement_evidence": "specific synthetic enhancement " + item_id if level == 4 else "",
                       "root_issue_id": None} for item_id in ids}
    return {"evaluation_blocked": None, "subcriteria": items, "critical_issues": [],
            "problem_list": [], "modify_suggestion": [], "confidence": 0.8}


def failed_feedback(value):
    value["problem_list"] = ["测试中的未达标维度"]
    value["modify_suggestion"] = ["允许编辑：失败区域；禁止编辑：保护内容；消费者功能锁：五维功能；验收：缩图和原图均达标"]
    return value


class ScoringTests(unittest.TestCase):
    def test_all_level_three_is_75_and_fails(self):
        result, audit = score_evaluation.calculate(workflow(), failed_feedback(draft(3)))
        self.assertEqual(result["score"], 75)
        self.assertFalse(result["pass"])
        self.assertEqual(audit["dimension_scores"], {"composition": 15, "hierarchy": 15, "color": 11, "typography": 15, "consistency": 11, "finish": 8})

    def test_exact_dimension_floors_total_80_pass(self):
        value = draft(3)
        for item_id in ["A1_1", "A2_1", "A3_1", "A4_1", "A5_1"]:
            value["subcriteria"][item_id].update(level=4, enhancement_evidence="specific independent enhancement " + item_id)
        result, audit = score_evaluation.calculate(workflow(), value)
        self.assertEqual(result["score"], 80)
        self.assertTrue(result["pass"])
        self.assertEqual(audit["dimension_scores"], {"composition": 16, "hierarchy": 16, "color": 12, "typography": 16, "consistency": 12, "finish": 8})

    def test_total_cannot_hide_low_dimension(self):
        value = draft(3)
        for item_id in ["A2_1", "A3_1", "A4_1", "A5_1", "A6_1", "A6_2"]:
            value["subcriteria"][item_id].update(level=4, enhancement_evidence="specific independent enhancement " + item_id)
        result, _ = score_evaluation.calculate(workflow(), failed_feedback(value))
        self.assertGreaterEqual(result["score"], 80)
        self.assertFalse(result["pass"])

    def test_hard_issue_blocks_100(self):
        value = draft(4)
        value["critical_issues"] = ["商品结构明显错误"]
        value["problem_list"] = ["商品结构明显错误"]
        value["modify_suggestion"] = ["允许编辑：商品错误区域；禁止编辑：准确文案；消费者功能锁：五维功能；验收：对照原商品恢复"]
        result, _ = score_evaluation.calculate(workflow(), value)
        self.assertEqual(result["score"], 100)
        self.assertFalse(result["pass"])

    def test_level_four_requires_enhancement_evidence(self):
        value = draft(4)
        value["subcriteria"]["A1_1"]["enhancement_evidence"] = ""
        with self.assertRaisesRegex(ValueError, "level 4"):
            score_evaluation.calculate(workflow(), value)

    def test_consumer_must_pass_and_protected_content_must_match(self):
        broken = workflow()
        broken["consumer_result"]["pass"] = False
        with self.assertRaisesRegex(ValueError, "consumer must pass"):
            score_evaluation.calculate(broken, draft(4))
        broken = workflow()
        broken["consumer_result"]["protected_content"]["cta"] = ["changed"]
        with self.assertRaisesRegex(ValueError, "protected content changed"):
            score_evaluation.calculate(broken, draft(4))

    def test_blocked_observation_returns_null(self):
        value = {"evaluation_blocked": "原商品图不可读取", "critical_issues": [],
                 "problem_list": [], "modify_suggestion": [], "confidence": 0}
        result, audit = score_evaluation.calculate(workflow(), value)
        self.assertIsNone(result["score"])
        self.assertFalse(result["pass"])
        self.assertEqual(audit["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
