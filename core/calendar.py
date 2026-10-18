"""历法与四柱。

口径：
- 输入按北京时间解释。
- 子初 23:00 换日，用 lunar_python 的八字节 Sect=1。
- 节气定月、立春换年。
- 真太阳时只生成对照结果，不改变主盘。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from lunar_python import Solar

BEIJING = ZoneInfo("Asia/Shanghai")
JIE_QI_NAMES = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


@dataclass(frozen=True)
class CalendarResult:
    local_time: datetime
    four_pillars: dict[str, str]
    solar_term: str
    month_branch: str
    day_boundary: str
    day_index: int
    day_ganzhi_index: int
    day_ordinal: int
    lunar_date: str
    solar_time_variant: dict | None = None


def _solar(dt: datetime) -> Solar:
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def _jieqi(dt: datetime) -> str:
    lunar = _solar(dt).getLunar()
    # 当天正好交节时，优先取当天交节的名称。
    today = dt.strftime("%Y-%m-%d")
    for name, value in lunar.getJieQiTable().items():
        if name in JIE_QI_NAMES and value.toYmd() == today:
            return name
    prev = lunar.getPrevJieQi(True)
    return prev.getName() if prev else ""


def _day_index(day_pillar: str) -> int:
    return next(i for i in range(60) if GAN[i % 10] + ZHI[i % 12] == day_pillar)


def equation_of_time_minutes(dt: datetime) -> float:
    """均时差近似值（分钟）。

    采用 NOAA Solar Calculator 的常用近似：真太阳时 = 平太阳时 + 均时差。
    结果以分钟计，正值表示真太阳时快于平太阳时。近似误差约 1 分钟，
    只用于对照盘。
    """
    day_of_year = dt.timetuple().tm_yday
    hour = dt.hour + dt.minute / 60 + dt.second / 3600
    gamma = 2 * math.pi / 365 * (day_of_year - 1 + (hour - 12) / 24)
    return 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )


def _local_solar_time(dt: datetime, longitude: float) -> tuple[datetime, float, float]:
    # 北京时间以东经 120° 为基准；每 1° 相差 4 分钟，再叠加均时差。
    longitude_minutes = (longitude - 120.0) * 4.0
    equation_minutes = equation_of_time_minutes(dt)
    return dt + timedelta(minutes=longitude_minutes + equation_minutes), longitude_minutes, equation_minutes


def _effective_date(dt: datetime) -> date:
    """子初 23:00 换日后的日期。"""
    return dt.date() + timedelta(days=1 if dt.hour >= 23 else 0)


def _pillars_at(dt: datetime) -> dict[str, str]:
    eight = _solar(dt).getLunar().getEightChar()
    eight.setSect(1)
    return {
        "year": eight.getYear(),
        "month": eight.getMonth(),
        "day": eight.getDay(),
        "hour": eight.getTime(),
    }


def build_calendar(dt: datetime, longitude: float | None = None) -> CalendarResult:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING)
    dt = dt.astimezone(BEIJING)
    pillars = _pillars_at(dt)
    lunar = _solar(dt).getLunar()
    variant = None
    if longitude is not None:
        local_dt, longitude_minutes, equation_minutes = _local_solar_time(dt, longitude)
        variant = {
            "longitude": f"{longitude:g}",
            "local_time": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "four_pillars": _pillars_at(local_dt),
            "longitude_minutes": round(longitude_minutes, 2),
            "equation_minutes": round(equation_minutes, 2),
            "note": "按经度差加均时差换算；仅作对照，不参与主盘，断课仍用北京时间主盘。",
        }
    return CalendarResult(
        local_time=dt,
        four_pillars=pillars,
        solar_term=_jieqi(dt),
        month_branch=pillars["month"][1],
        day_boundary="23:00",
        day_index=_day_index(pillars["day"]),
        day_ganzhi_index=_day_index(pillars["day"]),
        day_ordinal=(_effective_date(dt) - date(1984, 2, 2)).days,
        lunar_date=lunar.getYearInChinese() + "年" + lunar.getMonthInChinese() + "月" + lunar.getDayInChinese(),
        solar_time_variant=variant,
    )
