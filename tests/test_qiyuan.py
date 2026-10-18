from datetime import date, timedelta

from core.calendar import build_calendar
from core.qiyuan import build_yuan


def _chart_day(day):
    from datetime import datetime
    return build_calendar(datetime(day.year, day.month, day.day, 12, 0)).day_ordinal


def test_anchor_examples():
    assert build_yuan(_chart_day(date(2021, 5, 23))).name == "一元"
    assert build_yuan(_chart_day(date(2021, 5, 23))).day_bird == "昴日鸡"
    assert build_yuan(_chart_day(date(2022, 5, 22))).name == "七元"
    assert build_yuan(_chart_day(date(2022, 5, 22))).day_bird == "昴日鸡"


def test_420_days_no_jump():
    start = date(2021, 5, 23)
    prev = None
    for offset in range(420):
        yuan = build_yuan(_chart_day(start + timedelta(days=offset)))
        if prev is None:
            assert yuan.day_index == 8
        else:
            assert yuan.day_index == prev.day_index % 60 + 1
            assert yuan.index == (prev.index % 7 + 1 if prev.day_index == 60 else prev.index)
        prev = yuan
