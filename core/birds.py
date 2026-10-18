"""二十八宿、七曜与关系基础数据。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BIRDS_PATH = ROOT / "data" / "rules" / "birds.json"


@lru_cache(maxsize=1)
def load_birds() -> dict[str, Any]:
    data = json.loads(BIRDS_PATH.read_text(encoding="utf-8"))
    birds = data["birds"]
    return {
        "by_code": {bird["bird_code"]: bird for bird in birds},
        "by_name": {bird["name"]: bird for bird in birds},
        "ordered": birds,
        "data": data,
    }


def all_birds() -> list[dict[str, Any]]:
    return load_birds()["ordered"]


def bird(code_or_name: str) -> dict[str, Any]:
    data = load_birds()
    if code_or_name in data["by_code"]:
        return data["by_code"][code_or_name]
    if code_or_name in data["by_name"]:
        return data["by_name"][code_or_name]
    raise KeyError(f"未知禽星：{code_or_name}")


def bird_name(code_or_name: str) -> str:
    return bird(code_or_name)["name"]


def bird_code(code_or_name: str) -> str:
    return bird(code_or_name)["bird_code"]


def seven_luminary(code_or_name: str) -> str:
    return bird(code_or_name)["seven_luminary"]


def next_bird(code_or_name: str, steps: int = 1) -> str:
    ordered = load_birds()["ordered"]
    codes = [item["bird_code"] for item in ordered]
    return codes[(codes.index(bird_code(code_or_name)) + steps) % len(codes)]


def element(code_or_name: str) -> str:
    return bird(code_or_name)["element"]


def is_day_bird(code_or_name: str) -> bool:
    return bird(code_or_name)["day_night"] == "昼"


def he_partner(code_or_name: str) -> list[str]:
    return list(bird(code_or_name)["he"])


def chong_partner(code_or_name: str) -> list[str]:
    return list(bird(code_or_name)["chong"])
