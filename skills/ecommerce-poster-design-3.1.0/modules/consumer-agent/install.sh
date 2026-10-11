#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET_ROOT=${CODEX_HOME:-"$HOME/.codex"}
TARGET_DIR="$TARGET_ROOT/skills/02-consumer-agent-skill"

mkdir -p "$TARGET_ROOT/skills"
if [ -e "$TARGET_DIR" ]; then
  echo "Target already exists: $TARGET_DIR" >&2
  exit 1
fi
cp -R "$SOURCE_DIR" "$TARGET_DIR"
echo "Installed to $TARGET_DIR"
