import json
from pathlib import Path


def _rules(name):
    return json.loads((Path(__file__).resolve().parent.parent / "data" / "rules" / name).read_text(encoding="utf-8"))


def test_birds_count_and_fields():
    birds = _rules("birds.json")["birds"]
    assert len(birds) == 28
    assert [b["bird_code"] for b in birds] == [f"B{i:02d}" for i in range(1, 29)]
    for b in birds:
        assert b["seven_luminary"] in {"日", "月", "金", "木", "水", "火", "土"}
        assert b["element"] in {"日", "月", "金", "木", "水", "火", "土"}
        assert b["day_night"] in {"昼", "夜"}


def test_qiyuan_shape():
    q = _rules("qiyuan.json")
    assert len(q["yuan_leaders"]) == 7
    assert len(q["qi_jiang_table"]) == 4
    assert all(len(row["birds"]) == 7 for row in q["qi_jiang_table"])
    assert len(q["day_bird_table"]) == 7
    assert all(len(y["birds"]) == 60 for y in q["day_bird_table"])
    assert q["hour_start_by_luminary"] == {"日":"B11","月":"B23","火":"B07","水":"B19","木":"B03","金":"B15","土":"B27"}


def test_outer_suo_bo_water_soil_same():
    q = _rules("qiyuan.json")
    assert q["suo_bo"]["outer_luminary_start"]["水"] == q["suo_bo"]["outer_luminary_start"]["土"]


def test_outer_suo_bo_judgement_shape():
    q = _rules("qiyuan.json")
    suo = q["suo_bo"]
    assert set(suo["outer_judgement"]["columns"]) == set(suo["outer_columns"])
    assert len(suo["xing_hai"]["entries"]) == 10
    assert all(day in suo["fuduan"]["by_day_branch"] for day in "子丑寅卯辰巳午未申酉戌亥")
    assert suo["outer_judgement"]["source_page"] == "PDF第30页（印刷第22页）"
