#!/usr/bin/env python3
"""Validate rc.4 release pointers and the canonical Skill tree hash."""

import argparse
import hashlib
import json
from pathlib import Path


VERSION = "3.1.0-rc.4"
TAG = "ecommerce-poster-design-v3.1.0-rc.4"
SKILL_DIRECTORY = "skills/ecommerce-poster-design-3.1.0"
TEST_DIRECTORY = "tests/ecommerce-poster-design-3.1.0"


def tree_digest(root):
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    lines = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{relative}\t{digest}\n")
    tree_hash = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return len(files), tree_hash


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--installed")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "RELEASE_LOCK.json").read_text(encoding="utf-8"))
    skill_root = root / SKILL_DIRECTORY
    skill_version = json.loads(
        (skill_root / "assets/config/version.json").read_text(encoding="utf-8")
    )

    require(manifest.get("latest_version") == VERSION, "latest_version drifted")
    current = manifest.get("current", {})
    require(current.get("version") == VERSION, "current.version drifted")
    require(current.get("tag") == TAG, "current.tag drifted")
    require(current.get("directory") == SKILL_DIRECTORY, "current.directory drifted")
    require(current.get("tests") == TEST_DIRECTORY, "current.tests drifted")
    require(skill_version.get("skill_version") == VERSION, "Skill version drifted")
    require(lock.get("release_version") == VERSION, "release lock version drifted")
    require(lock.get("release_tag") == TAG, "release lock tag drifted")
    require(lock.get("canonical_skill_directory") == SKILL_DIRECTORY, "release lock directory drifted")

    file_count, tree_hash = tree_digest(skill_root)
    require(lock.get("skill_file_count") == file_count, "Skill file count drifted")
    require(lock.get("skill_tree_sha256") == tree_hash, "Skill tree hash drifted")

    pointer_files = [
        "README.md",
        "INSTALL.md",
        "PROJECT_STATUS.md",
        "VERSIONS.md",
        "RELEASE_NOTES_3.1.0-rc.4.md",
    ]
    for name in pointer_files:
        text = (root / name).read_text(encoding="utf-8")
        require(VERSION in text, f"{name} does not point to {VERSION}")

    installed_result = None
    if args.installed:
        installed = Path(args.installed).resolve()
        installed_count, installed_hash = tree_digest(installed)
        require(installed_count == file_count, "installed Skill file count differs from release")
        require(installed_hash == tree_hash, "installed Skill tree differs from release")
        installed_result = {"path": str(installed), "file_count": installed_count, "tree_sha256": installed_hash}

    print(json.dumps({
        "valid": True,
        "version": VERSION,
        "tag": TAG,
        "skill_directory": SKILL_DIRECTORY,
        "skill_file_count": file_count,
        "skill_tree_sha256": tree_hash,
        "installed": installed_result,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
