"""七元甲子与日禽。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.birds import bird, bird_code, bird_name

ROOT = Path(__file__).resolve().parent.parent
QIYUAN_PATH = ROOT / "data" / "rules" / "qiyuan.json"

# 锚点：2021-05-23 辛未日，一元第 8 天，日禽昴日鸡。
# 七元表以甲子日为每元起点。辛未日 = 甲子日起第 8 天。
ANCHOR_GANZHI_INDEX = 7  # 辛未
ANCHOR_YUAN = 1
ANCHOR_YUAN_DAY = 8
ANCHOR_ORDINAL = (date(2021, 5, 23) - date(1984, 2, 2)).days


@lru_cache(maxsize=1)
def load_qiyuan() -> dict[str, Any]:
    return json.loads(QIYUAN_PATH.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class YuanResult:
    index: int
    name: str
    leader_bird: str
    day_index: int
    day_bird: str


def yuan_from_day_ordinal(day_ordinal: int) -> tuple[int, int]:
    """返回 (元序号 1-7, 元内日序 1-60)。

    元按连续 60 日推进；日柱序号只用于查该元内的日禽。
    """
    offset = day_ordinal - ANCHOR_ORDINAL + (ANCHOR_YUAN - 1) * 60 + (ANCHOR_YUAN_DAY - 1)
    return offset // 60 % 7 + 1, offset % 60 + 1


def build_yuan(day_ordinal: int) -> YuanResult:
    data = load_qiyuan()
    yuan_index, yuan_day = yuan_from_day_ordinal(day_ordinal)
    table = data["day_bird_table"][yuan_index - 1]
    code = table["birds"][yuan_day - 1]
    return YuanResult(
        index=yuan_index,
        name=table["name"],
        leader_bird=bird_name(table["leader"]),
        day_index=yuan_day,
        day_bird=bird_name(code),
    )


def qi_jiang(yuan_index: int, yuan_day: int) -> str:
    data = load_qiyuan()
    segment = min((yuan_day - 1) // 15, 3)
    code = data["qi_jiang_table"][segment]["birds"][yuan_index - 1]
    return bird_name(code)


def hour_start_bird(day_bird: str) -> str:
    data = load_qiyuan()
    lum = bird(day_bird)["seven_luminary"]
    return bird_name(data["hour_start_by_luminary"][lum])


def hour_bird(day_bird: str, hour_branch: str) -> str:
    from core.birds import bird_name, next_bird

    start = hour_start_bird(day_bird)
    return bird_name(next_bird(start, "子丑寅卯辰巳午未申酉戌亥".index(hour_branch)))
