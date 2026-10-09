"""End-to-end smoke test for prepare -> vendored evaluate -> merge."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "aesthetic_adapter.py"
AGENT = ROOT / "integrations" / "ecommerce-aesthetic-agent"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    node = shutil.which("node")
    if not node:
        raise SystemExit("node executable is required")

    with tempfile.TemporaryDirectory(prefix=".aesthetic-experiment-smoke-", dir=ROOT / "tests") as temporary:
        task = Path(temporary)
        baseline_input = {
            "request_id": "SMOKE-001",
            "product": {
                "image_refs": ["product.png"],
                "name": "测试商品",
                "category": "测试品类",
                "selling_points": ["卖点一", "卖点二"],
                "quantity": 1,
            },
            "brand": {"name": "测试品牌", "logo_ref": "logo.png", "required_elements": [], "forbidden_elements": []},
            "commerce": {
                "price_text": "到手价 ¥99",
                "promotion_text": "满减",
                "promotion_period": "10月",
                "legal_text": "以实际为准",
            },
            "marketing": {"goal": "新品转化", "channel": "电商", "usage_context": "首发", "cta": "立即购买"},
            "canvas": {"width": 1080, "height": 1440, "format": "png", "language": "zh-CN"},
        }
        style = {"tags": {"audience_id": "P02", "motivation_id": "M03", "scenario_id": "S03"}}
        protected = {
            "product_identity": ["测试商品"],
            "product_quantity": 1,
            "brand_and_logo": ["测试品牌", "logo.png"],
            "price_and_unit": ["到手价 ¥99"],
            "promotion_and_period": ["满减", "10月"],
            "selling_points": ["卖点一", "卖点二"],
            "cta": ["立即购买"],
            "legal_text": ["以实际为准"],
        }
        write_json(task / "baseline-input.json", baseline_input)
        write_json(task / "style-guide.json", style)
        write_json(task / "protected-content.json", protected)

        prepared = task / "aesthetic-round-01"
        subprocess.run(
            [
                sys.executable,
                str(ADAPTER),
                "prepare",
                "--baseline-input",
                str(task / "baseline-input.json"),
                "--style-guide",
                str(task / "style-guide.json"),
                "--protected-content",
                str(task / "protected-content.json"),
                "--poster-image",
                "poster.png",
                "--out",
                str(prepared),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        review = json.loads((AGENT / "examples" / "review-v2.demo.json").read_text(encoding="utf-8"))
        review["source_poster"] = "poster.png"
        review["source_product"] = "product.png"
        write_json(prepared / "review.json", review)

        scored = prepared / "result"
        subprocess.run(
            [
                node,
                str(AGENT / "scripts" / "evaluate.mjs"),
                "--input",
                str(prepared / "aesthetic-input.json"),
                "--review",
                str(prepared / "review.json"),
                "--config",
                str(AGENT / "config.json"),
                "--context",
                str(prepared / "context.json"),
                "--out",
                str(scored),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        baseline_result = {"status": "passed", "hard_compliance": {"passed": True, "problem_list": []}}
        write_json(task / "baseline-result.json", baseline_result)
        subprocess.run(
            [
                sys.executable,
                str(ADAPTER),
                "merge",
                "--baseline-result",
                str(task / "baseline-result.json"),
                "--aesthetic-result",
                str(scored / "agent-result.json"),
                "--out",
                str(task / "combined.json"),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        combined = json.loads((task / "combined.json").read_text(encoding="utf-8"))
        assert combined["baseline_result"] == baseline_result
        assert combined["aesthetic_agent_result"]["agent_name"] == "aesthetic_agent"
        assert combined["experiment_result"]["variant"] == "aesthetic_agent_added"
        assert combined["experiment_result"]["pass"] is False
        assert combined["experiment_result"]["consumer_agent_used"] is False
        assert combined["experiment_result"]["iteration_owner"] == "baseline_1.0"
        assert combined["experiment_result"]["max_redraw_attempts"] == 3
        print("smoke integration passed")


if __name__ == "__main__":
    main()
