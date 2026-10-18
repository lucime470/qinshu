from datetime import datetime

from core.chart import build_chart
from core.guide import build_guide


def _chart():
    return build_chart(datetime(2022, 5, 22, 17, 30))


def test_guide_has_ten_ordered_steps():
    steps = build_guide(_chart())
    assert [s["order"] for s in steps] == list(range(1, 11))
    assert [s["step_code"] for s in steps] == [
        "time", "yuan_day", "hour_qijiang", "fan_dao_huoyao", "sheng_ke",
        "fei_fu", "he_chong", "suo_bo", "category", "judgement",
    ]
    assert all(s["title"] and s["question"] and isinstance(s["source_refs"], list) for s in steps)


def test_guide_facts_come_from_chart():
    chart = _chart()
    steps = {s["step_code"]: s for s in build_guide(chart)}
    assert steps["time"]["facts"]["four_pillars"] == chart["calendar"]["four_pillars"]
    assert steps["yuan_day"]["facts"]["day_bird"] == chart["birds"]["day"]
    assert steps["hour_qijiang"]["facts"]["hour_bird"] == chart["birds"]["hour"]
    assert steps["fan_dao_huoyao"]["facts"]["fan_qin"] == chart["birds"]["fan_qin"]
    assert steps["suo_bo"]["facts"]["fuduan"]["hour_bird"] == chart["birds"]["hour"]
    assert steps["suo_bo"]["facts"]["season"] == chart["calendar"]["month_branch"]


def test_guide_marks_uncertain_de_di_without_guessing():
    chart = _chart()
    steps = {s["step_code"]: s for s in build_guide(chart)}
    hour = chart["birds"]["hour"]
    assert steps["sheng_ke"]["facts"]["de_di"]["hour"]["status"] in {"得地", "不得地", "原文未定吉凶"}
