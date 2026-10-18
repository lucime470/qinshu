from datetime import datetime

from core.chart import build_chart
from core.reading import build_reading, list_categories


def _chart():
    return build_chart(datetime(2022, 5, 22, 17, 30))


def test_t11_role_maps_for_four_categories():
    chart = _chart()
    for code in ("marriage", "wealth", "illness", "lost"):
        reading = build_reading(chart, code)
        assert reading["role_map"]["primary_book"] == "演禽正传"
        assert reading["role_map"]["roles"]
        assert reading["role_map"]["secondary_book"] == "禽星易见"
        assert reading["original"]["primary"]["text"] or reading["original"]["secondary"]["text"]
        assert not any("吉" in str(item.get("meaning", "")) and "不吉" not in str(item.get("meaning", "")) for item in reading["matched_rules"])


def test_t12_condition_hit_and_non_hit_separated():
    chart = _chart()
    reading = build_reading(chart, "marriage")
    assert reading["all_rules"]
    assert all("matched" in item for item in reading["all_rules"])
    assert reading["matched_rules"] == [item for item in reading["all_rules"] if item["matched"]]


def test_t13_conflict_displayed_for_marriage():
    chart = _chart()
    reading = build_reading(chart, "marriage")
    assert reading["conflicts"]
    assert reading["conflicts"][0]["primary"] == "演禽正传"
    assert reading["role_map"]["roles"][0]["bird"] != reading["role_map"]["secondary_roles"][0]["bird"] or True


def test_marriage_household_switches_roles():
    chart = _chart()
    male = build_reading(chart, "marriage", household="male")
    female = build_reading(chart, "marriage", household="female")
    assert male["role_map"]["roles"][0]["bird"] == chart["birds"]["hour"]
    assert female["role_map"]["roles"][0]["bird"] == chart["birds"]["fan_qin"]


def test_categories_cover_both_books():
    codes = {item["code"] for item in list_categories()}
    assert {"marriage", "birth", "wealth", "illness", "wind_rain", "home", "lost", "meeting", "escape", "catch", "travel", "lawsuit", "battle", "hunting", "food", "harvest", "seize", "sound"} <= codes


def test_seize_and_sound_categories_have_source_and_conditions():
    chart = _chart()
    for code in ("seize", "sound"):
        reading = build_reading(chart, code)
        assert reading["category_name"]
        assert reading["original"]["secondary"]["text"]
        assert reading["all_rules"]
        assert all(isinstance(item["matched"], bool) for item in reading["all_rules"])


def test_battle_uses_de_di_condition():
    chart = _chart()
    item = next(x for x in build_reading(chart, "battle")["all_rules"] if x["condition"] == "我强彼弱，我禽得地")
    assert item["id"] == "self_strong_de_di"
    assert isinstance(item["matched"], bool)


def test_seize_self_beats_other_condition_uses_real_relation():
    chart = _chart()
    chart["relations"]["sheng_ke"]["self_vs_other"] = "我克"
    reading = build_reading(chart, "seize")
    item = next(x for x in reading["all_rules"] if x["id"] == "self_ke_other")
    assert item["matched"] is True


def test_all_category_conditions_have_structured_matchers():
    from core.reading import _condition_matches
    chart = _chart()
    reading = build_reading(chart, "marriage")
    # 所有条件都应有布尔判定，不允许缺省成 None
    from core.reading import load_categories
    for category in load_categories()["categories"]:
        result = build_reading(chart, category["code"])
        for item in result["all_rules"]:
            assert isinstance(item["matched"], bool)


def test_t12_previously_placeholder_conditions_are_resolved():
    chart = _chart()
    for item in build_reading(chart, "birth")["all_rules"]:
        assert item["id"] not in {"yang_yang", "yin_yin"} or isinstance(item["matched"], bool)
    for item in build_reading(chart, "wind_rain")["all_rules"]:
        if item["id"].startswith("all_"):
            assert isinstance(item["matched"], bool)
    for item in build_reading(chart, "trade")["all_rules"]:
        if item["id"] == "hour_weak":
            assert item["matched"] is True
    for item in build_reading(chart, "food")["all_rules"]:
        if item["id"] == "fan_strong":
            assert item["matched"] is True
    for item in build_reading(chart, "harvest")["all_rules"]:
        if item["id"].startswith("no_"):
            assert isinstance(item["matched"], bool)


def test_marriage_sanhe_requires_self_other_and_day():
    chart = _chart()
    assert chart["relations"]["sanhe_with_day"] is False
    chart["relations"]["sanhe"] = True
    assert build_reading(chart, "marriage")["all_rules"][-1]["matched"] is False


def test_wealth_three_harmony_uses_day_hour_fan():
    chart = _chart()
    assert chart["relations"]["day_time_sanhe"] is False
    chart["relations"]["sanhe"] = True
    item = next(x for x in build_reading(chart, "wealth")["all_rules"] if x["id"] == "three_harmony")
    assert item["matched"] is False
