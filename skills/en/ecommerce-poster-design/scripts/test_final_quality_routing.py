#!/usr/bin/env python3
"""Regression tests for the score-free 3.1 final quality gate."""

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


assembler = module("assemble_aesthetic_input_31", ROOT / "scripts/assemble_aesthetic_input.py")
router = module("route_final_quality", ROOT / "scripts/route_final_quality.py")
contract_validator = module("validate_final_quality_edit_contract", ROOT / "scripts/validate_final_quality_edit_contract.py")


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
    workflow = assembler.assemble(candidate, consumer)
    consumer_details = {
        "score": 88,
        "request_id": consumer["request_id"],
        "version_id": consumer["version_id"],
        "dimensions": {
            key: {"items": [{"level": 3} for _ in range(5)]}
            for key in assembler.CONSUMER_DIMENSIONS
        },
    }
    aesthetic = {
        "agent_name": "aesthetic_agent",
        "score": 88,
        "pass": True,
        "problem_list": [],
        "modify_suggestion": [],
        "protected_content": copy.deepcopy(consumer["protected_content"]),
        "meta": {
            "judge_dimensions": [
                "构图与视觉平衡", "视觉层级", "配色与对比", "字体与排版",
                "风格与场景适配", "材质光影与细节完成度",
            ],
            "confidence": 0.9,
        },
    }
    aesthetic_details = {
        "score": 88,
        "pass": True,
        "request_id": consumer["request_id"],
        "version_id": consumer["version_id"],
        "poster_image": candidate["poster_image"],
        "dimensions": {
            key: {"items": [{"level": 3} for _ in range(4)]}
            for key in ("composition", "hierarchy", "color", "typography", "consistency", "finish")
        },
    }
    return candidate, consumer, consumer_details, aesthetic, aesthetic_details, workflow


def defect(severity="moderate", code="TEXT_DENSITY_HIGH", region="左下卖点区"):
    return {
        "code": code,
        "category": "typography",
        "severity": severity,
        "region": region,
        "observation": "三行卖点在360px缩图下行距过紧，第二与第三行难以区分",
        "required_action": "只扩大卖点行距并降低次要行字号",
        "editable_objects": ["卖点区字号", "卖点区行距"],
        "protected_objects": ["卖点原文", "商品", "价格"],
    }


def review(candidate, mode="standard", defects=None, confidence=0.9):
    defects = defects or []
    return {
        "schema_version": "FINAL-QUALITY-3.2",
        "request_id": candidate["request_id"],
        "version_id": candidate["loop_state"]["version_id"],
        "poster_image": candidate["poster_image"],
        "review_mode": mode,
        "image_views": {"original": True, "thumbnail_360": True, "product_reference": True},
        "evidence_audit": {
            "consumer_evidence_supported": True,
            "aesthetic_evidence_supported": True,
            "contradictions": [],
            "generic_evidence_findings": [],
        },
        "defects": defects,
        "no_moderate_or_major_defect": not any(item["severity"] in {"critical", "severe", "moderate"} for item in defects),
        "confidence": confidence,
    }


class FinalQualityRoutingTests(unittest.TestCase):
    def setUp(self):
        values = fixtures()
        self.candidate, self.consumer, self.consumer_details, self.aesthetic, self.aesthetic_details, self.workflow = values
        self.version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))

    def route(self, value, attempts=0, history=None):
        return router.route_result(
            value, self.consumer, self.consumer_details, self.aesthetic, self.aesthetic_details,
            self.workflow, self.version, attempts, history or [],
        )

    def test_clean_normal_scores_complete(self):
        routed = self.route(review(self.candidate))
        self.assertEqual((routed["status"], routed["action"]), ("passed", "complete"))
        self.assertTrue(routed["final_pass"])

    def test_suspicious_score_invokes_adversarial_review_without_redraw(self):
        self.consumer["score"] = self.consumer_details["score"] = 98
        self.consumer["dimension_scores"] = {key: 19 for key in assembler.CONSUMER_DIMENSIONS}
        self.workflow["consumer_result"] = copy.deepcopy(self.consumer)
        routed = self.route(review(self.candidate), attempts=3)
        self.assertEqual(routed["action"], "invoke_adversarial_final_review")
        self.assertEqual(routed["global_redraw_attempts"], 3)
        self.assertIn("consumer_total", routed["suspicious_score_reasons"])

    def test_clean_adversarial_review_can_complete_suspicious_candidate(self):
        self.aesthetic["score"] = self.aesthetic_details["score"] = 95
        routed = self.route(review(self.candidate, mode="adversarial"), attempts=2)
        self.assertEqual((routed["status"], routed["action"]), ("passed", "complete"))

    def test_moderate_defect_creates_local_edit_contract(self):
        routed = self.route(review(self.candidate, defects=[defect()]), attempts=3)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(routed["next_global_redraw_attempt"], 4)
        contract = routed["generation_edit_contract"]
        self.assertEqual(contract["contract_version"], "final-quality-edit-lock/1.0")
        self.assertEqual(contract["generation_mode"], "local_edit_only")
        self.assertEqual(contract["editable_regions"], ["左下卖点区"])
        validated = contract_validator.validate_contract(routed, self.workflow, review(self.candidate, defects=[defect()]))
        self.assertEqual(validated, contract)

    def test_text_overlap_cannot_be_downgraded_to_minor(self):
        with self.assertRaisesRegex(ValueError, "TEXT_OVERLAP must be moderate or higher"):
            self.route(review(self.candidate, defects=[defect("minor", code="TEXT_OVERLAP", region="左上标题区")]))

    def test_logo_floating_creates_local_edit_contract(self):
        item = defect("moderate", code="LOGO_FLOATING", region="顶部品牌区")
        item["category"] = "hierarchy"
        item["observation"] = "Logo 与标题之间存在明显孤立大空隙，未形成品牌信息组"
        item["required_action"] = "仅调整 Logo 尺寸与垂直位置，使其与标题形成清晰分组"
        item["editable_objects"] = ["Logo 尺寸", "Logo 垂直位置", "Logo 与标题间距"]
        routed = self.route(review(self.candidate, defects=[item]), attempts=1)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(routed["generation_edit_contract"]["editable_regions"], ["顶部品牌区"])

    def test_logo_floating_cannot_be_downgraded_to_minor(self):
        item = defect("minor", code="LOGO_FLOATING", region="顶部品牌区")
        item["category"] = "hierarchy"
        with self.assertRaisesRegex(ValueError, "LOGO_FLOATING must be moderate or higher"):
            self.route(review(self.candidate, defects=[item]))

    def test_logo_background_artifact_requires_moderate_or_higher(self):
        item = defect("minor", code="LOGO_BACKGROUND_ARTIFACT", region="顶部品牌区")
        item["category"] = "brand"
        with self.assertRaisesRegex(ValueError, "LOGO_BACKGROUND_ARTIFACT must be moderate or higher"):
            self.route(review(self.candidate, defects=[item]))

    def test_product_scene_composite_artifact_requires_moderate_or_higher(self):
        item = defect("minor", code="PRODUCT_SCENE_COMPOSITE_ARTIFACT", region="商品底部与台面接触区")
        item["category"] = "finish"
        item["observation"] = "商品底部没有接触阴影，边缘色温与背景相反，呈现可定位的后贴断层"
        item["required_action"] = "以原商品图为参考局部重建接触阴影、环境色和边缘融合"
        item["editable_objects"] = ["商品边缘融合", "接触阴影", "局部环境反射"]
        with self.assertRaisesRegex(ValueError, "PRODUCT_SCENE_COMPOSITE_ARTIFACT must be moderate or higher"):
            self.route(review(self.candidate, defects=[item]))

    def test_product_scene_composite_artifact_creates_local_edit_contract(self):
        item = defect("moderate", code="PRODUCT_SCENE_COMPOSITE_ARTIFACT", region="商品底部与台面接触区")
        item["category"] = "finish"
        item["observation"] = "商品底部没有接触阴影，边缘色温与背景相反，呈现可定位的后贴断层"
        item["required_action"] = "以原商品图为参考局部重建接触阴影、环境色和边缘融合"
        item["editable_objects"] = ["商品边缘融合", "接触阴影", "局部环境反射"]
        routed = self.route(review(self.candidate, defects=[item]), attempts=1)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(routed["generation_edit_contract"]["editable_regions"], ["商品底部与台面接触区"])

    def test_missing_logo_must_be_critical(self):
        item = defect("severe", code="LOGO_MISSING", region="顶部品牌区")
        item["category"] = "brand"
        with self.assertRaisesRegex(ValueError, "LOGO_MISSING must be critical"):
            self.route(review(self.candidate, defects=[item]))

    def test_incorrect_logo_critical_creates_revision_contract(self):
        item = defect("critical", code="LOGO_INCORRECT", region="顶部品牌区")
        item["category"] = "brand"
        routed = self.route(review(self.candidate, defects=[item]), attempts=1)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")

    def test_three_minor_defects_require_revision(self):
        defects = [defect("minor", region=value) for value in ["左上", "右下", "底部"]]
        routed = self.route(review(self.candidate, defects=defects))
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")

    def test_two_minor_defects_can_pass(self):
        defects = [defect("minor", region=value) for value in ["左上", "右下"]]
        routed = self.route(review(self.candidate, defects=defects))
        self.assertEqual(routed["action"], "complete")
        self.assertEqual(routed["minor_defect_count"], 2)

    def test_unsupported_evidence_repeats_evaluation_without_redraw(self):
        value = review(self.candidate)
        value["evidence_audit"]["generic_evidence_findings"] = ["美学证据仅写配色协调，没有画面位置"]
        routed = self.route(value, attempts=5)
        self.assertEqual(routed["action"], "reevaluate_current_candidate")
        self.assertEqual(routed["global_redraw_attempts"], 5)

    def test_low_confidence_blocks_without_redraw(self):
        routed = self.route(review(self.candidate, confidence=0.4), attempts=4)
        self.assertEqual((routed["status"], routed["action"]), ("blocked", "complete_final_quality_input"))
        self.assertEqual(routed["global_redraw_attempts"], 4)

    def test_budget_exhaustion_returns_best_eligible_candidate(self):
        history = [
            {"version_id": "v1", "hard_compliance_pass": True, "consumer_pass": True, "aesthetic_pass": True, "aesthetic_score": 86},
            {"version_id": "v2", "hard_compliance_pass": False, "consumer_pass": True, "aesthetic_pass": True, "aesthetic_score": 99},
        ]
        routed = self.route(review(self.candidate, defects=[defect()]), attempts=8, history=history)
        self.assertEqual(routed["action"], "return_best_candidate")
        self.assertEqual(routed["best_candidate"]["version_id"], "v1")

    def test_cross_version_review_is_rejected(self):
        value = review(self.candidate)
        value["version_id"] = "stale"
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            self.route(value)


if __name__ == "__main__":
    unittest.main()
