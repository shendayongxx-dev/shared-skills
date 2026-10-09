import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aesthetic_adapter", ROOT / "scripts" / "aesthetic_adapter.py")
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(adapter)


def baseline_input(image_refs=None):
    return {
        "request_id": "REQ-TEST",
        "product": {
            "image_refs": image_refs or ["product.png"],
            "name": "测试商品",
            "category": "测试品类",
            "selling_points": ["卖点一", "卖点二"],
            "quantity": 1,
        },
        "brand": {"name": "品牌", "logo_ref": "logo.png", "required_elements": [], "forbidden_elements": []},
        "commerce": {
            "price_text": "到手价 ¥99",
            "promotion_text": "满减",
            "promotion_period": "10月",
            "legal_text": "以实际为准",
        },
        "marketing": {"goal": "新品转化", "channel": "电商", "usage_context": "首发", "cta": "立即购买"},
        "canvas": {"width": 1080, "height": 1440, "format": "png", "language": "zh-CN"},
    }


def style(tags=None):
    return {"tags": tags or {"audience_id": "P02", "motivation_id": "M03", "scenario_id": "S03"}}


def aesthetic(score=8.5, passed=True, confidence=0.8, problems=None, suggestions=None):
    return {
        "agent_name": "aesthetic_agent",
        "score": score,
        "pass": passed,
        "problem_list": problems or [],
        "modify_suggestion": suggestions or [],
        "protected_content": ["商品主体", "到手价 ¥99"],
        "meta": {"judge_dimensions": ["构图与视觉平衡"], "confidence": confidence},
    }


class AdapterTests(unittest.TestCase):
    def test_adapter_uses_combined_skill_version(self):
        self.assertEqual(adapter.ABLATION_VERSION, "1.0.0-imagegen-aesthetic-agent.1")

    def test_exact_mapping_and_ordered_scene_tags(self):
        result = adapter.build_aesthetic_input(baseline_input(), style(), "round-01.png")
        self.assertEqual(
            result,
            {
                "poster_image": "round-01.png",
                "product_input": {
                    "product_img": "product.png",
                    "selling_points": ["卖点一", "卖点二"],
                    "price_text": "到手价 ¥99",
                    "marketing_target": "新品转化",
                    "scene_tags": ["P02", "M03", "S03"],
                },
            },
        )

    def test_multiple_product_images_require_explicit_choice(self):
        data = baseline_input(["front.png", "back.png"])
        with self.assertRaises(adapter.AdapterError):
            adapter.build_aesthetic_input(data, style(), "poster.png")
        mapped = adapter.build_aesthetic_input(data, style(), "poster.png", "back.png")
        self.assertEqual(mapped["product_input"]["product_img"], "back.png")

    def test_all_null_scene_tags_are_not_invented(self):
        null_style = style({"audience_id": None, "motivation_id": None, "scenario_id": None})
        with self.assertRaises(adapter.AdapterError):
            adapter.build_aesthetic_input(baseline_input(), null_style, "poster.png")

    def test_high_aesthetic_score_cannot_override_hard_failure(self):
        baseline = {"status": "degraded", "hard_compliance": {"passed": False, "problem_list": []}}
        result = adapter.merge_results(baseline, aesthetic(score=9.5, passed=True))
        self.assertFalse(result["ablation_result"]["pass"])
        self.assertFalse(result["ablation_result"]["baseline_hard_pass"])
        self.assertEqual(result["ablation_result"]["status"], "revise")

    def test_combined_pass_requires_both_gates(self):
        baseline = {"status": "passed", "hard_compliance": {"passed": True, "problem_list": []}}
        result = adapter.merge_results(baseline, aesthetic())
        self.assertTrue(result["ablation_result"]["pass"])
        self.assertEqual(result["ablation_result"]["status"], "passed")
        self.assertFalse(result["ablation_result"]["consumer_agent_used"])
        self.assertEqual(result["ablation_result"]["max_redraw_attempts"], 3)

    def test_unavailable_zero_is_not_a_measured_score(self):
        baseline = {"status": "passed", "hard_compliance": {"passed": True, "problem_list": []}}
        missing = aesthetic(
            score=0,
            passed=False,
            confidence=0,
            problems=["无法评价：当前海报不可读取"],
            suggestions=["提供可读取海报"],
        )
        result = adapter.merge_results(baseline, missing)
        self.assertEqual(result["ablation_result"]["score_state"], "unavailable")
        self.assertEqual(result["ablation_result"]["status"], "aesthetic_unavailable")

    def test_consumer_output_is_rejected(self):
        baseline = {"status": "passed", "hard_compliance": {"passed": True, "problem_list": []}}
        wrong = aesthetic()
        wrong["agent_name"] = "consumer_agent"
        with self.assertRaises(adapter.AdapterError):
            adapter.merge_results(baseline, wrong)


if __name__ == "__main__":
    unittest.main()
