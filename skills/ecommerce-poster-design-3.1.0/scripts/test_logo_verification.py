#!/usr/bin/env python3
"""Regression tests for final candidate/logo application binding."""

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_logo_application", ROOT / "scripts/verify_logo_application.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LogoVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        root = Path(self.temp.name)
        self.source = root / "logo.svg"
        self.prepared = root / "logo.png"
        self.base = root / "base.png"
        self.final = root / "final.png"
        self.source.write_text("<svg/>", encoding="utf-8")
        self.prepared.write_bytes(b"prepared-logo")
        self.base.write_bytes(b"base-poster")
        self.final.write_bytes(b"base-poster-with-logo")
        self.preflight = {
            "schema_version": "logo-asset-preflight/1.1",
            "authoritative_source": {"path": str(self.source), "sha256": sha(self.source)},
            "generation_asset": {
                "path": str(self.prepared), "sha256": sha(self.prepared),
                "transparency_class": "has_transparent_pixels",
            },
        }
        self.application = {
            "schema_version": "logo-application/1.0",
            "prepared_logo": {"path": str(self.prepared), "sha256": sha(self.prepared)},
            "base_poster": {"path": str(self.base), "sha256": sha(self.base)},
            "output": {"path": str(self.final), "sha256": sha(self.final)},
            "placement": {"left": 20, "top": 20, "width": 200, "height": 50},
            "transformation": {"rotation": 0, "recolor": False, "crop": False, "aspect_ratio_preserved": True},
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_composited_candidate_passes(self):
        result = MODULE.verify(self.final, self.preflight, self.application)
        self.assertTrue(result["passed"])
        self.assertEqual(result["schema_version"], "logo-verification/1.0")

    def test_logo_free_base_cannot_be_final_candidate(self):
        with self.assertRaisesRegex(ValueError, "not the logo-composited output"):
            MODULE.verify(self.base, self.preflight, self.application)

    def test_tampered_prepared_logo_is_rejected(self):
        self.prepared.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "prepared logo hash mismatch"):
            MODULE.verify(self.final, self.preflight, self.application)


if __name__ == "__main__":
    unittest.main()
