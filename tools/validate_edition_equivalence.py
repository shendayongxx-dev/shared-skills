from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOTS = {
    "Chinese": REPO / "skills" / "zh" / "ecommerce-poster-design",
    "English": REPO / "skills" / "en" / "ecommerce-poster-design",
}

CASES = [
    ("zh", "zh-CN", ["轻盈随行", "到手价129元", "立即选购"]),
    ("en", "en-US", ["Lightweight for every journey", "Now ¥129", "Shop now"]),
]

results = {}
for label, root in ROOTS.items():
    spec = spec_from_file_location(f"resolve_canvas_{label}", root / "scripts" / "resolve_canvas.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    out = []
    for case_id, language, protected_copy in CASES:
        request = {"canvas": {"aspect_ratio": "4:5", "orientation": None, "format": "PNG", "language": language, "width": None, "height": None, "platform_size": None}}
        resolved = module.resolve_request(request)
        assert resolved["canvas"]["language"] == language
        assert (resolved["canvas"]["width"], resolved["canvas"]["height"]) == (1080, 1350)
        out.append((case_id, resolved["canvas"].copy(), list(protected_copy)))
    results[label] = out

assert results["Chinese"] == results["English"], "language-flow results differ"

for root in ROOTS.values():
    consumer = (root / "modules/consumer-agent/scripts/score_evaluation.py").read_text(encoding="utf-8")
    aesthetic = (root / "modules/aesthetic-agent/scripts/score_evaluation.py").read_text(encoding="utf-8")
    final_contract = (root / "scripts/validate_final_quality_edit_contract.py").read_text(encoding="utf-8")
    assert 'deepcopy(context["protected_content"])' in consumer
    assert 'draft["protected_content"]!=context["protected_content"]' in consumer
    assert 'deepcopy(candidate["protected_content"])' in aesthetic
    assert 'contract["immutable_protected_content"] == candidate.get("protected_content")' in final_contract

print("PASS: Chinese and English instruction editions preserve identical Chinese-only and English-only poster behavior")
