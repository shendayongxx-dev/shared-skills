"""Shared deterministic helpers for Consumer Agent 1.1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIMENSIONS = (
    "product_recognition",
    "benefit_clarity",
    "offer_visibility",
    "population_scene_fit",
    "purchase_drive",
)

DIMENSION_LABELS = (
    "商品与品牌识别",
    "核心利益与卖点说服力",
    "价格促销与交易信息",
    "人群—动机—场景适配",
    "信任与行动驱动",
)


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, value: Any) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]
