import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ImageGenIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "assets" / "config" / "version.json").read_text(encoding="utf-8"))

    def test_imagegen_is_required_builtin_backend(self):
        backend = self.config["generation_backend"]
        self.assertEqual(backend["skill"], "imagegen")
        self.assertEqual(backend["tool"], "image_gen")
        self.assertEqual(backend["mode"], "builtin")
        self.assertTrue(backend["required"])
        self.assertTrue(backend["cli_fallback_requires_user_confirmation"])

    def test_aesthetic_on_consumer_off_and_baseline_budget_unchanged(self):
        self.assertTrue(self.config["feature_flags"]["aesthetic_agent"])
        self.assertFalse(self.config["feature_flags"]["consumer_agent"])
        self.assertEqual(self.config["retry_policy"]["max_redraw_attempts"], 3)
        self.assertEqual(self.config["aesthetic_agent"]["loop_owner"], "baseline_1.0")

    def test_c_library_remains_connected(self):
        c_library = self.config["c_library"]
        self.assertEqual(c_library["status"], "connected")
        self.assertEqual(c_library["official_asset_version"], "2.0.1-a.1")
        self.assertEqual(c_library["eligible_seed_cases"], 6)
        self.assertEqual(c_library["seed_scenario_coverage"], 6)

    def test_provided_imagegen_package_is_pinned(self):
        source = self.config["imagegen_integration_source"]
        self.assertEqual(source["declared_version"], "1.0.0-imagegen.1")
        self.assertEqual(len(source["skill_package_sha256"]), 64)
        self.assertEqual(len(source["zip_package_sha256"]), 64)
        self.assertTrue(source["classification_assets_reused"])
        self.assertTrue((ROOT / "references" / "imagegen-integration.md").is_file())


if __name__ == "__main__":
    unittest.main()

