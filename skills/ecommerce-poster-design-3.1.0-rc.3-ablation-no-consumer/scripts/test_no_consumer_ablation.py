#!/usr/bin/env python3

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


assembler = module("assemble_no_consumer", ROOT / "scripts/assemble_aesthetic_input.py")
scorer = module("score_no_consumer", ROOT / "modules/aesthetic-agent/scripts/score_evaluation.py")
aesthetic_router = module("route_aesthetic_no_consumer", ROOT / "scripts/route_aesthetic_result.py")
aesthetic_contract = module("validate_aesthetic_no_consumer", ROOT / "scripts/validate_generation_edit_contract.py")
final_router = module("route_final_no_consumer", ROOT / "scripts/route_final_quality.py")
final_contract = module("validate_final_no_consumer", ROOT / "scripts/validate_final_quality_edit_contract.py")


def candidate():
    return {
        "schema_version": "A-D-2.0", "request_id": "REQ-ABLATION-1", "poster_image": "candidate.png",
        "loop_state": {"version_id": "v1"},
        "protected_content": {
            "product_identity": ["NORI保温杯"], "product_quantity": 1, "brand_and_logo": ["NORI"],
            "price_and_unit": ["¥129/个"], "promotion_and_period": [], "selling_points": ["长效保温"],
            "cta": ["立即购买"], "legal_text": [],
        },
    }


def draft(level):
    rubric = json.loads((ROOT / "modules/aesthetic-agent/assets/rubric.json").read_text(encoding="utf-8"))
    ids = [item[0] for dimension in rubric["dimensions"].values() for item in dimension["items"]]
    failed = level < 4
    return {
        "evaluation_blocked": None,
        "subcriteria": {item: {"level": level, "evidence": f"{item} 当前候选可见证据", "enhancement_evidence": "多对象关系形成明确增强" if level == 4 else "", "root_issue_id": "root-1" if failed else None} for item in ids},
        "problem_list": ["排版与层级未达到门槛"] if failed else [],
        "modify_suggestion": ["允许编辑：未达标美学维度；禁止编辑：商品与事实；保护范围：八组保护内容；验收：原图和360px缩图均清楚"] if failed else [],
        "critical_issues": [], "confidence": 0.9,
    }


def defect(code="TEXT_OVERLAP", severity="moderate"):
    return {"code": code, "category": "typography" if code == "TEXT_OVERLAP" else "hierarchy", "severity": severity, "region": "顶部标题区", "observation": "可见缺陷", "required_action": "局部调整", "editable_objects": ["标题间距"], "protected_objects": ["商品", "文案原文"]}


def review(workflow, defects=None, mode="standard"):
    value = defects or []
    candidate_value = workflow["candidate"]
    return {
        "schema_version": "FINAL-QUALITY-3.1-ABLATION-NO-CONSUMER", "request_id": candidate_value["request_id"],
        "version_id": candidate_value["loop_state"]["version_id"], "poster_image": candidate_value["poster_image"],
        "review_mode": mode, "image_views": {"original": True, "thumbnail_360": True, "product_reference": True},
        "evidence_audit": {"aesthetic_evidence_supported": True, "contradictions": [], "generic_evidence_findings": []},
        "defects": value, "no_moderate_or_major_defect": not any(x["severity"] in {"critical", "severe", "moderate"} for x in value),
        "confidence": 0.9, "ablation": copy.deepcopy(workflow["ablation"]),
    }


class NoConsumerAblationTests(unittest.TestCase):
    def setUp(self):
        self.candidate = candidate()
        self.workflow = assembler.assemble(self.candidate)
        self.version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))

    def test_workflow_has_no_consumer_result(self):
        self.assertEqual(set(self.workflow), {"schema_version", "ablation", "candidate"})
        self.assertNotIn("consumer_result", self.workflow)
        self.assertFalse(self.workflow["ablation"]["consumer_artifacts_used"])

    def test_aesthetic_pass_routes_to_final_gate_without_consumer(self):
        result, details = scorer.calculate(self.workflow, draft(4))
        routed = aesthetic_router.route_result(result, details, self.workflow, self.version, 0)
        self.assertTrue(result["pass"])
        self.assertEqual(routed["action"], "invoke_final_quality_gate")
        self.assertNotIn("consumer_dimension_scores", routed)

    def test_aesthetic_failure_contract_has_no_consumer_locks(self):
        result, details = scorer.calculate(self.workflow, draft(3))
        routed = aesthetic_router.route_result(result, details, self.workflow, self.version, 2)
        contract = routed["generation_edit_contract"]
        self.assertEqual(contract["contract_version"], "aesthetic-edit-lock-no-consumer/1.0")
        self.assertNotIn("locked_consumer_dimensions", contract)
        self.assertEqual(aesthetic_contract.validate_contract(routed, self.workflow), contract)

    def test_clean_final_review_passes(self):
        aesthetic, details = scorer.calculate(self.workflow, draft(4))
        routed = final_router.route_result(review(self.workflow, mode="adversarial"), aesthetic, details, self.workflow, self.version, 0)
        self.assertEqual((routed["status"], routed["action"], routed["final_pass"]), ("passed", "complete", True))

    def test_text_overlap_cannot_be_minor(self):
        aesthetic, details = scorer.calculate(self.workflow, draft(4))
        with self.assertRaisesRegex(ValueError, "TEXT_OVERLAP must be moderate or higher"):
            final_router.route_result(review(self.workflow, [defect(severity="minor")], mode="adversarial"), aesthetic, details, self.workflow, self.version, 0)

    def test_logo_floating_triggers_valid_local_edit(self):
        aesthetic, details = scorer.calculate(self.workflow, draft(4))
        value = review(self.workflow, [defect("LOGO_FLOATING")], mode="adversarial")
        routed = final_router.route_result(value, aesthetic, details, self.workflow, self.version, 1)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(final_contract.validate_contract(routed, self.workflow, value), routed["generation_edit_contract"])

    def test_consumer_module_and_routes_are_absent(self):
        self.assertFalse((ROOT / "modules/consumer-agent").exists())
        for name in ("route_consumer_result.py", "validate_consumer_integration.py", "test_consumer_routing.py"):
            self.assertFalse((ROOT / "scripts" / name).exists())


if __name__ == "__main__":
    unittest.main()
