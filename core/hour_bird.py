"""时禽与气将。"""

from __future__ import annotations

from core.qiyuan import build_yuan, hour_bird as _hour_bird, qi_jiang as _qi_jiang


def hour_bird(day_bird: str, hour_branch: str) -> str:
    return _hour_bird(day_bird, hour_branch)


def qi_jiang(day_ordinal: int) -> str:
    yuan = build_yuan(day_ordinal)
    return _qi_jiang(yuan.index, yuan.day_index)
