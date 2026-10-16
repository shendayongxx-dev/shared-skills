#!/usr/bin/env python3
"""Regression tests for rc.4 canvas normalization."""

import unittest

from resolve_canvas import resolve_request


def request_for(ratio, orientation=None, **canvas_updates):
    canvas = {
        "aspect_ratio": ratio,
        "format": "png",
        "language": "zh-CN",
    }
    if orientation is not None:
        canvas["orientation"] = orientation
    canvas.update(canvas_updates)
    return {"request_id": "REQ-CANVAS", "canvas": canvas}


class CanvasNormalizationTests(unittest.TestCase):
    def test_common_ratio_defaults(self):
        cases = {
            "1:1": (1080, 1080),
            "4:5": (1080, 1350),
            "3:4": (1080, 1440),
            "9:16": (1080, 1920),
            "16:9": (1920, 1080),
        }
        for ratio, expected in cases.items():
            with self.subTest(ratio=ratio):
                result = resolve_request(request_for(ratio))
                self.assertEqual((result["canvas"]["width"], result["canvas"]["height"]), expected)
                self.assertEqual(result["canvas_resolution"]["resolution_method"], "ratio_default_short_edge_1080")

    def test_chinese_colon_and_derived_orientation(self):
        result = resolve_request(request_for("4：5"))
        self.assertEqual(result["canvas_resolution"]["requested_orientation"], "vertical")
        self.assertIn("1080×1350", result["canvas_resolution"]["notice"])

    def test_explicit_pixels_are_preserved(self):
        result = resolve_request(request_for("4:5", width=1200, height=1500))
        self.assertEqual((result["canvas"]["width"], result["canvas"]["height"]), (1200, 1500))
        self.assertEqual(result["canvas_resolution"]["resolution_method"], "explicit_pixels")

    def test_platform_requirement_overrides_default(self):
        result = resolve_request(
            request_for("4:5", platform_size={"width": 1200, "height": 1600})
        )
        self.assertEqual((result["canvas"]["width"], result["canvas"]["height"]), (1200, 1600))
        self.assertTrue(result["canvas_resolution"]["platform_override"])

    def test_conflicting_explicit_orientation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "orientation conflicts"):
            resolve_request(request_for("4:5", "horizontal"))

    def test_conflicting_exact_pixels_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "dimensions conflict"):
            resolve_request(request_for("4:5", width=1080, height=1920))

    def test_format_remains_required(self):
        request = request_for("4:5")
        request["canvas"]["format"] = ""
        with self.assertRaisesRegex(ValueError, "format is required"):
            resolve_request(request)


if __name__ == "__main__":
    unittest.main()
