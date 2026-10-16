#!/usr/bin/env python3
"""Bind the final poster candidate to the authoritative logo application chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify(candidate: Path, preflight: dict, application: dict) -> dict:
    require(preflight.get("schema_version") == "logo-asset-preflight/1.1", "invalid logo preflight schema")
    require(application.get("schema_version") == "logo-application/1.0", "invalid logo application schema")

    source = preflight.get("authoritative_source") or {}
    prepared = preflight.get("generation_asset") or {}
    applied_logo = application.get("prepared_logo") or {}
    base = application.get("base_poster") or {}
    output = application.get("output") or {}
    for record, label in ((source, "authoritative source"), (prepared, "prepared logo"),
                          (applied_logo, "applied logo"), (base, "base poster"), (output, "application output")):
        require(record.get("path") and record.get("sha256"), f"{label} path and hash are required")
        path = Path(record["path"])
        require(path.is_file(), f"{label} file is missing")
        require(digest(path) == record["sha256"], f"{label} hash mismatch")

    require(prepared["sha256"] == applied_logo["sha256"], "application did not use the prepared logo")
    candidate_hash = digest(candidate)
    require(candidate_hash == output["sha256"], "final candidate is not the logo-composited output")
    require(candidate_hash != base["sha256"], "final candidate still points to the logo-free base poster")
    transformation = application.get("transformation") or {}
    require(transformation.get("rotation") == 0, "logo rotation is not allowed")
    require(transformation.get("recolor") is False, "logo recoloring is not allowed")
    require(transformation.get("crop") is False, "logo cropping is not allowed")
    require(transformation.get("aspect_ratio_preserved") is True, "logo aspect ratio must be preserved")

    transparency = prepared.get("transparency_class", "unknown")
    return {
        "schema_version": "logo-verification/1.0",
        "passed": True,
        "candidate": {"path": str(candidate.resolve()), "sha256": candidate_hash},
        "authoritative_source_sha256": source["sha256"],
        "prepared_logo_sha256": prepared["sha256"],
        "base_poster_sha256": base["sha256"],
        "application_output_sha256": output["sha256"],
        "placement": application.get("placement"),
        "transparency_class": transparency,
        "visual_checks_required": [
            "logo_presence_and_uniqueness",
            "authoritative_logo_correctness",
            "unexpected_rectangular_background_or_border",
            "white_black_edge_or_alpha_halo",
            "scale_alignment_contrast_grouping_and_integration",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--application", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(Path(args.candidate), load(Path(args.preflight)), load(Path(args.application)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
