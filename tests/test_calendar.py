from datetime import datetime, timedelta

from core.calendar import build_calendar, equation_of_time_minutes


def test_book_pillars_2022_05_22_you():
    cal = build_calendar(datetime(2022, 5, 22, 17, 30))
    assert cal.four_pillars == {"year": "壬寅", "month": "乙巳", "day": "乙亥", "hour": "乙酉"}


def test_book_pillars_2022_05_24_si():
    cal = build_calendar(datetime(2022, 5, 24, 9, 30))
    assert cal.four_pillars == {"year": "壬寅", "month": "乙巳", "day": "丁丑", "hour": "乙巳"}


def test_zi_chu_day_boundary():
    assert build_calendar(datetime(2022, 5, 22, 22, 59)).four_pillars["day"] == "乙亥"
    assert build_calendar(datetime(2022, 5, 22, 23, 0)).four_pillars["day"] == "丙子"


def test_solar_time_variant_does_not_change_main_chart():
    main = build_calendar(datetime(2022, 5, 22, 17, 30))
    variant = build_calendar(datetime(2022, 5, 22, 17, 30), longitude=87)
    assert main.four_pillars == variant.four_pillars
    assert variant.solar_time_variant is not None


def test_solar_term_month_switch():
    before = build_calendar(datetime(2022, 5, 21, 9, 0))
    after = build_calendar(datetime(2022, 5, 21, 12, 0))
    assert before.four_pillars["month"] == "乙巳"
    assert after.four_pillars["month"] == "乙巳"
    # 立春前后年柱切换
    lichun_before = build_calendar(datetime(2022, 2, 3, 23, 0))
    lichun_after = build_calendar(datetime(2022, 2, 4, 12, 0))
    assert lichun_before.four_pillars["year"] == "辛丑"
    assert lichun_after.four_pillars["year"] == "壬寅"
    assert lichun_before.four_pillars["day"] == lichun_after.four_pillars["day"]


def test_leap_month_and_year_boundary():
    # 2020 闰四月；只校验四柱连续、无异常
    for dt in (datetime(2020, 5, 23, 12), datetime(2020, 6, 21, 12), datetime(2021, 12, 31, 22), datetime(2021, 12, 31, 23)):
        cal = build_calendar(dt)
        assert len(cal.four_pillars["year"]) == 2
        assert cal.day_index in range(60)


def test_solar_variant_marks_hour_difference():
    main = build_calendar(datetime(2022, 5, 22, 0, 30))
    west = build_calendar(datetime(2022, 5, 22, 0, 30), longitude=87)
    assert main.four_pillars == west.four_pillars
    assert west.solar_time_variant["four_pillars"]["hour"] != main.four_pillars["hour"] or west.solar_time_variant["local_time"] != "2022-05-22 00:30:00"


def test_equation_of_time_in_reference_range():
    # 年内极值约在 2 月中旬 -14 分钟、11 月初 +16 分钟。
    feb = equation_of_time_minutes(datetime(2022, 2, 11, 12))
    nov = equation_of_time_minutes(datetime(2022, 11, 3, 12))
    may = equation_of_time_minutes(datetime(2022, 5, 14, 12))
    assert -15 <= feb <= -13
    assert 15 <= nov <= 17
    assert abs(may) < 4


def test_solar_variant_includes_equation_of_time():
    at_120 = build_calendar(datetime(2022, 5, 22, 17, 30), longitude=120).solar_time_variant
    assert at_120["longitude_minutes"] == 0
    assert at_120["equation_minutes"] == round(equation_of_time_minutes(datetime(2022, 5, 22, 17, 30)), 2)
    expected = datetime(2022, 5, 22, 17, 30) + timedelta(minutes=at_120["equation_minutes"])
    assert at_120["local_time"] == expected.strftime("%Y-%m-%d %H:%M:%S")


def test_solar_variant_uses_longitude_plus_equation():
    variant = build_calendar(datetime(2022, 5, 22, 17, 30), longitude=87).solar_time_variant
    assert variant["longitude_minutes"] == -132.0
    total = variant["longitude_minutes"] + variant["equation_minutes"]
    expected = datetime(2022, 5, 22, 17, 30) + timedelta(minutes=total)
    assert variant["local_time"] == expected.strftime("%Y-%m-%d %H:%M:%S")
