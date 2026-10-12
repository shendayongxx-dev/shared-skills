#!/usr/bin/env python3
"""Regression tests for the rc.3 no-aesthetic final quality gate."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = {"product_recognition", "benefit_clarity", "offer_visibility", "population_scene_fit", "purchase_drive"}
ABLATION = {"id": "no-aesthetic", "base_version": "3.1.0-rc.3", "aesthetic_artifacts_used": False}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


router = module("route_final_no_aesthetic", ROOT / "scripts/route_final_quality.py")
contract_validator = module("validate_final_no_aesthetic", ROOT / "scripts/validate_final_quality_edit_contract.py")


def fixtures():
    workflow = json.loads((ROOT / "modules/consumer-agent/examples/nori-input.json").read_text(encoding="utf-8"))
    consumer = json.loads((ROOT / "modules/consumer-agent/examples/consumer-output-pass.json").read_text(encoding="utf-8"))
    consumer["request_id"] = workflow["request_id"]
    consumer["version_id"] = workflow["loop_state"]["version_id"]
    consumer["protected_content"] = copy.deepcopy(workflow["protected_content"])
    consumer["score"] = 88
    consumer["pass"] = True
    consumer["dimension_scores"] = {name: 17 for name in DIMENSIONS}
    consumer["locked_dimensions"] = sorted(DIMENSIONS)
    consumer["regressed_dimensions"] = []
    consumer["hard_fail"] = False
    consumer["next_route"] = "aesthetic_agent"
    details = {
        "score": 88, "request_id": consumer["request_id"], "version_id": consumer["version_id"],
        "dimensions": {key: {"items": [{"level": 3} for _ in range(5)]} for key in DIMENSIONS},
    }
    return workflow, consumer, details


def defect(severity="moderate", code="TEXT_DENSITY_HIGH", region="左下卖点区"):
    return {
        "code": code, "category": "typography", "severity": severity, "region": region,
        "observation": "三行卖点在360px缩图下行距过紧", "required_action": "只扩大卖点行距",
        "editable_objects": ["卖点区行距"], "protected_objects": ["卖点原文", "商品", "价格"],
    }


def review(workflow, mode="standard", defects=None, confidence=0.9):
    defects = defects or []
    return {
        "schema_version": "FINAL-QUALITY-3.1-ABLATION-NO-AESTHETIC",
        "request_id": workflow["request_id"], "version_id": workflow["loop_state"]["version_id"],
        "poster_image": workflow["poster_image"], "review_mode": mode,
        "image_views": {"original": True, "thumbnail_360": True, "product_reference": True},
        "evidence_audit": {"consumer_evidence_supported": True, "contradictions": [], "generic_evidence_findings": []},
        "defects": defects,
        "no_moderate_or_major_defect": not any(item["severity"] in {"critical", "severe", "moderate"} for item in defects),
        "confidence": confidence, "ablation": ABLATION.copy(),
    }


class FinalQualityRoutingTests(unittest.TestCase):
    def setUp(self):
        self.workflow, self.consumer, self.details = fixtures()
        self.version = json.loads((ROOT / "assets/config/version.json").read_text(encoding="utf-8"))

    def route(self, value, attempts=0, history=None):
        return router.route_result(value, self.consumer, self.details, self.workflow, self.version, attempts, history or [])

    def test_clean_candidate_completes_without_aesthetic(self):
        routed = self.route(review(self.workflow))
        self.assertEqual((routed["status"], routed["action"], routed["final_pass"]), ("passed", "complete", True))
        self.assertNotIn("aesthetic_score", routed)

    def test_suspicious_consumer_score_invokes_adversarial_review(self):
        self.consumer["score"] = self.details["score"] = 98
        self.consumer["dimension_scores"] = {key: 19 for key in DIMENSIONS}
        routed = self.route(review(self.workflow), attempts=3)
        self.assertEqual(routed["action"], "invoke_adversarial_final_review")
        self.assertEqual(routed["global_redraw_attempts"], 3)

    def test_moderate_defect_creates_valid_local_edit_contract(self):
        value = review(self.workflow, defects=[defect()])
        routed = self.route(value, attempts=3)
        self.assertEqual(routed["action"], "regenerate_then_full_pipeline")
        self.assertEqual(routed["next_global_redraw_attempt"], 4)
        contract = routed["generation_edit_contract"]
        self.assertEqual(contract["contract_version"], "final-quality-edit-lock-no-aesthetic/1.0")
        self.assertNotIn("locked_aesthetic_dimensions", contract)
        self.assertEqual(contract_validator.validate_contract(routed, self.workflow, value), contract)

    def test_text_overlap_cannot_be_minor(self):
        with self.assertRaisesRegex(ValueError, "TEXT_OVERLAP must be moderate or higher"):
            self.route(review(self.workflow, defects=[defect("minor", "TEXT_OVERLAP", "标题区")]))

    def test_logo_floating_cannot_be_minor(self):
        item = defect("minor", "LOGO_FLOATING", "品牌区")
        item["category"] = "hierarchy"
        with self.assertRaisesRegex(ValueError, "LOGO_FLOATING must be moderate or higher"):
            self.route(review(self.workflow, defects=[item]))

    def test_three_minor_defects_require_revision(self):
        items = [defect("minor", region=value) for value in ("左上", "右下", "底部")]
        self.assertEqual(self.route(review(self.workflow, defects=items))["action"], "regenerate_then_full_pipeline")

    def test_unsupported_consumer_evidence_repeats_review(self):
        value = review(self.workflow)
        value["evidence_audit"]["generic_evidence_findings"] = ["证据没有画面位置"]
        self.assertEqual(self.route(value, attempts=5)["action"], "reevaluate_current_candidate")

    def test_budget_selection_uses_defects_then_consumer_score(self):
        history = [
            {"version_id": "v1", "hard_compliance_pass": True, "consumer_pass": True, "consumer_score": 90, "final_quality_pass": False, "final_quality_defects": [{"severity": "moderate"}]},
            {"version_id": "v2", "hard_compliance_pass": True, "consumer_pass": True, "consumer_score": 84, "final_quality_pass": False, "final_quality_defects": [{"severity": "minor"}]},
            {"version_id": "v3", "hard_compliance_pass": False, "consumer_pass": True, "consumer_score": 99, "final_quality_pass": True, "final_quality_defects": []},
        ]
        routed = self.route(review(self.workflow, defects=[defect()]), attempts=8, history=history)
        self.assertEqual(routed["best_candidate"]["version_id"], "v2")

    def test_cross_version_review_is_rejected(self):
        value = review(self.workflow)
        value["version_id"] = "stale"
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            self.route(value)


if __name__ == "__main__":
    unittest.main()
