import ast
import json
import re
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "en"
    / "ecommerce-poster-design"
)

skill_files = [ROOT / "SKILL.md", *sorted((ROOT / "modules").glob("*/SKILL.md"))]
for path in skill_files:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        raise SystemExit(f"invalid front matter: {path}")
    front = match.group(1)
    if not re.search(r"^name:\s*[a-z0-9-]+\s*$", front, re.M):
        raise SystemExit(f"invalid name: {path}")
    if not re.search(r'^description:\s*(?:".+"|[^\r\n]+)\s*$', front, re.M):
        raise SystemExit(f"invalid description: {path}")

for path in ROOT.rglob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))

for path in ROOT.rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

missing = []
link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
for path in ROOT.rglob("*.md"):
    for target in link_pattern.findall(path.read_text(encoding="utf-8")):
        target = target.split("#", 1)[0]
        if not target or re.match(r"^[a-z]+://", target, re.I):
            continue
        if not (path.parent / target).resolve().exists():
            missing.append(f"{path.relative_to(ROOT)} -> {target}")
if missing:
    raise SystemExit("missing markdown links:\n" + "\n".join(missing))

main = (ROOT / "SKILL.md").read_text(encoding="utf-8")
contracts = (ROOT / "references" / "contracts.md").read_text(encoding="utf-8")
for phrase in ["Chinese-only", "English-only", "bilingual mode is not supported", "must not translate"]:
    if phrase not in main:
        raise SystemExit(f"missing multilingual rule in SKILL.md: {phrase}")
for phrase in ["Chinese-only", "English-only", "bilingual output is not supported", "Do not translate"]:
    if phrase not in contracts:
        raise SystemExit(f"missing multilingual contract rule: {phrase}")

print(f"PASS: {len(skill_files)} SKILL front matters, JSON, Python AST, markdown links, and multilingual English contracts")
