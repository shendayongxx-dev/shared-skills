#!/usr/bin/env python3
"""Regression tests for the 2.0.1 -> aesthetic rc.4 orchestration boundary."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


assembler = module("assemble_aesthetic_input", ROOT / "scripts/assemble_aesthetic_input.py")
router = module("route_aesthetic_result", ROOT / "scripts/route_aesthetic_result.py")
contract_validator = module("validate_generation_edit_contract", ROOT / "scripts/validate_generation_edit_contract.py")
scorer = module("score_evaluation_rc4", ROOT / "modules/aesthetic-agent/scripts/score_evaluation.py")


def fixtures():
    candidate = json.loads((ROOT / "modules/consumer-agent/examples/nori-input.json").read_text(encoding="utf-8"))
    consumer = json.loads((ROOT / "modules/consumer-agent/examples/consumer-output-pass.json").read_text(encoding="utf-8"))
    consumer["request_id"] = candidate["request_id"]
    consumer["version_id"] = candidate["loop_state"]["version_id"]
    consumer["protected_content"] = copy.deepcopy(candidate["protected_content"])
    consumer["score"] = 88
    consumer["pass"] = True
    consumer["dimension_scores"] = {name: 17 for name in assembler.CONSUMER_DIMENSIONS}
    consumer["locked_dimensions"] = sorted(assembler.CONSUMER_DIMENSIONS)
    consumer["regressed_dimensions"] = []
    consumer["hard_fail"] = False
    consumer["next_route"] = "aesthetic_agent"
    return candidate, consumer


def draft(level=4):
    rubric = json.loads((ROOT / "modules/aesthetic-agent/assets/rubric.json").read_text(encoding="utf-8"))
    ids = [item_id for group in rubric["dimensions"].values() for item_id, _, _ in group["items"]]
    return {
        "evaluation_blocked": None,
        "subcriteria": {item_id: {"level": level, "evidence": "visible " + item_id,
                                     "enhancement_evidence": "enhanced " + item_id if level == 4 else "",
                                     "root_issue_id": None} for item_id in ids},
        "critical_issues": [], "problem_list": [], "modify_suggestion": [], "confidence": 0.9,
    }


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.candidate, self.consumer = fixtures()
        self.workflow = assembler.assemble(self.candidate, self.consumer)
        self.version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))

    def test_assembler_emits_exact_wrapper(self):
        self.assertEqual(set(self.workflow), {"schema_version", "candidate", "consumer_result"})
        self.assertEqual(self.workflow["schema_version"], "A-D-AESTHETIC-3.0")

    def test_assembler_rejects_missing_consumer_lock(self):
        broken = copy.deepcopy(self.consumer)
        broken["locked_dimensions"].pop()
        with self.assertRaisesRegex(ValueError, "five dimensions locked"):
            assembler.assemble(self.candidate, broken)

    def test_scored_pass_routes_complete_with_binding(self):
        result, details = scorer.calculate(self.workflow, draft(4))
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 3)
        self.assertEqual((routed["status"], routed["action"]), ("passed", "complete"))
        self.assertTrue(routed["details_verified"])

    def test_cross_version_details_are_rejected(self):
        result, details = scorer.calculate(self.workflow, draft(4))
        details["version_id"] = "stale-version"
        with self.assertRaisesRegex(ValueError, "version_id"):
            router.route_result(result, self.consumer, details, self.workflow, self.version, 3)

    def test_failed_score_uses_global_counter(self):
        failed = draft(3)
        failed["problem_list"] = ["排版节奏未达标"]
        failed["modify_suggestion"] = ["允许编辑：文字间距；禁止编辑：商品和交易文案；消费者功能锁：五维功能；验收：原图与360px缩图层级清楚"]
        result, details = scorer.calculate(self.workflow, failed)
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 3)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(routed["next_global_redraw_attempt"], 4)
        contract = contract_validator.validate_contract(routed, self.workflow)
        self.assertEqual(contract["generation_mode"], "local_edit_only")
        self.assertEqual(set(contract["locked_consumer_dimensions"]), assembler.CONSUMER_DIMENSIONS)
        self.assertEqual(set(contract["editable_aesthetic_dimensions"]), {"composition", "hierarchy", "color", "typography", "consistency"})
        self.assertEqual(contract["locked_aesthetic_dimensions"], ["finish"])

    def test_tampered_consumer_lock_contract_is_rejected(self):
        failed = draft(3)
        failed["problem_list"] = ["层级未达标"]
        failed["modify_suggestion"] = ["允许编辑：层级区域；禁止编辑：消费者通过区域；消费者功能锁：五维功能；验收：缩图层级清楚"]
        result, details = scorer.calculate(self.workflow, failed)
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 1)
        routed["generation_edit_contract"]["locked_consumer_dimensions"].pop("purchase_drive")
        with self.assertRaisesRegex(ValueError, "five consumer dimensions"):
            contract_validator.validate_contract(routed, self.workflow)

    def test_only_failed_aesthetic_dimensions_are_editable(self):
        value = draft(4)
        for item_id in ["A3_1", "A3_2", "A3_3", "A3_4", "A4_1", "A4_2", "A4_3", "A4_4"]:
            value["subcriteria"][item_id].update(level=2, enhancement_evidence="")
        value["problem_list"] = ["配色与排版未达标"]
        value["modify_suggestion"] = ["允许编辑：颜色和文字间距；禁止编辑：商品、利益、交易、场景和CTA功能；消费者功能锁：五维功能；验收：原图和缩图均保持消费者功能"]
        result, details = scorer.calculate(self.workflow, value)
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 2)
        contract = contract_validator.validate_contract(routed, self.workflow)
        self.assertEqual(set(contract["editable_aesthetic_dimensions"]), {"color", "typography"})
        self.assertEqual(set(contract["locked_aesthetic_dimensions"]), {"composition", "hierarchy", "consistency", "finish"})
        self.assertEqual(set(contract["locked_consumer_dimensions"]), assembler.CONSUMER_DIMENSIONS)

    def test_critical_only_failure_requires_scope_review(self):
        value = draft(4)
        value["critical_issues"] = ["未绑定维度的关键视觉问题"]
        value["problem_list"] = ["未绑定维度的关键视觉问题"]
        value["modify_suggestion"] = ["允许编辑：待确认；禁止编辑：全部消费者通过区域；消费者功能锁：五维功能；验收：人工确认范围"]
        result, details = scorer.calculate(self.workflow, value)
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 1)
        self.assertEqual((routed["status"], routed["action"]), ("blocked", "complete_aesthetic_scope"))
        self.assertNotIn("generation_edit_contract", routed)

    def test_blocked_does_not_increment_counter(self):
        blocked = {"evaluation_blocked": "poster unreadable", "critical_issues": [],
                   "problem_list": [], "modify_suggestion": [], "confidence": 0}
        result, details = scorer.calculate(self.workflow, blocked)
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 6)
        self.assertEqual((routed["status"], routed["action"]), ("blocked", "complete_aesthetic_input"))
        self.assertEqual(routed["global_redraw_attempts"], 6)

    def test_budget_exhaustion_returns_best_eligible_candidate(self):
        failed = draft(3)
        failed["problem_list"] = ["完成度未达标"]
        failed["modify_suggestion"] = ["允许编辑：局部边缘；禁止编辑：商品文字；消费者功能锁：五维功能；验收：边缘自然"]
        result, details = scorer.calculate(self.workflow, failed)
        history = [
            {"version_id": "v00", "aesthetic_score": 79, "hard_compliance_pass": True, "consumer_pass": True},
            {"version_id": "bad", "aesthetic_score": 99, "hard_compliance_pass": False, "consumer_pass": True},
        ]
        routed = router.route_result(result, self.consumer, details, self.workflow, self.version, 8, history)
        self.assertEqual(routed["action"], "return_best_candidate")
        self.assertEqual(routed["best_candidate"]["version_id"], "v00")


if __name__ == "__main__":
    unittest.main()
