#!/usr/bin/env python3
"""Static invariants for the 3.1 rc.3 aesthetic-first ablation package."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def require(ok,msg):
    if not ok: raise SystemExit("FAIL: "+msg)

version=json.loads((ROOT/"assets/config/version.json").read_text(encoding="utf-8"))
skill=(ROOT/"SKILL.md").read_text(encoding="utf-8")
assembler=(ROOT/"scripts/assemble_aesthetic_input.py").read_text(encoding="utf-8")
consumer_router=(ROOT/"scripts/route_consumer_result.py").read_text(encoding="utf-8")
require(version.get("skill_version")=="3.1.0-rc.3-ablation-aesthetic-first","wrong experiment version")
require(version.get("base_version")=="3.1.0-rc.3","wrong baseline")
require(version.get("release_channel")=="experiment" and version.get("production_ready") is False,"experiment must not claim stable production status")
require(version.get("evaluation_order")==["aesthetic_agent","consumer_agent"],"evaluation order drifted")
require(version.get("retry_policy",{}).get("max_redraw_attempts")==8,"rc.3 budget changed")
require("HC-01～HC-12 → 美学 Agent → 消费者 Agent → 最终质量仲裁" in skill,"main workflow order missing")
require("consumer_result" not in assembler,"aesthetic assembler still depends on consumer result")
require('"action":"invoke_final_quality_gate"' in consumer_router,"consumer pass does not route to final quality")
require("consumer-edit-lock/1.0-af" in consumer_router and "locked_aesthetic_dimensions" in consumer_router,"consumer retry lacks aesthetic lock")
print(json.dumps({"valid":True,"version":version["skill_version"],"evaluation_order":version["evaluation_order"],"max_redraw_attempts":8},ensure_ascii=False,indent=2))
