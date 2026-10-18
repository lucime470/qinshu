import json
import tempfile
import threading
import urllib.request
from urllib.parse import quote, urlencode
from pathlib import Path

import pytest

import storage.db as db
from core.chart import build_chart
from http.server import ThreadingHTTPServer
from datetime import datetime
from webapp.server import Handler, HOST


@pytest.fixture()
def live_server(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    server = ThreadingHTTPServer((HOST, 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{HOST}:{server.server_address[1]}"
    server.shutdown()


def _call(url, data=None, method=None):
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(request) as response:
        return response.status, json.loads(response.read())


def test_t14_health_and_page(live_server):
    with urllib.request.urlopen(live_server + "/api/health") as response:
        assert response.status == 200
    with urllib.request.urlopen(live_server + "/") as response:
        page = response.read().decode("utf-8")
    assert "禽枢" in page
    assert 'id="chart-table"' in page


def test_chart_table_gets_facts_from_chart(live_server):
    _, chart = _call(live_server + "/api/chart", {"datetime": "2022-05-22T17:30:00"})
    facts = chart["relations"]["suo_bo_facts"]["outer"]
    assert set(facts) == {"day", "hour", "qi_jiang", "fan_qin", "dao_jiang", "huo_yao"}
    for key, fact in facts.items():
        assert fact["de_di"]["status"] in {"得地", "不得地", "原文未定吉凶"}
        assert chart["relations"]["fei_fu"][fact["bird"]] in {"飞", "伏"}
    assert set(chart["relations"]["fei_fu"]) == {fact["bird"] for fact in facts.values()}
    assert chart["relations"]["suo_bo"]["inner"]["name"]


def test_bird_profile_exposes_suo_bo_dial(live_server):
    _, data = _call(live_server + "/api/birds/" + quote("箕水豹"))
    dial = data["suo_bo_dial"]
    assert dial["inner"]["子"] == "湖"
    assert dial["inner"]["寅"] == "山"
    assert dial["outer_columns"]["山"] == "申"
    assert dial["outer_columns"]["汤火"] == "午"
    assert dial["outer_columns"]["月"] == "未"
    assert dial["outer_start"] == "申"
    assert dial["outer_luminary"] == "水"


def test_t15_lesson_crud(live_server):
    _, chart = _call(live_server + "/api/chart", {"datetime": "2022-05-22T17:30:00"})
    _, created = _call(live_server + "/api/lessons", {"chart": chart, "judgement_text": "测试"}, method="POST")
    lesson_id = created["id"]
    _, listing = _call(live_server + "/api/lessons")
    assert any(item["id"] == lesson_id for item in listing["lessons"])
    _, detail = _call(live_server + f"/api/lessons/{lesson_id}")
    assert detail["judgement_text"] == "测试"
    _call(live_server + f"/api/lessons/{lesson_id}", {"judgement_text": "改后"}, method="PATCH")
    _, detail = _call(live_server + f"/api/lessons/{lesson_id}")
    assert detail["judgement_text"] == "改后"
    _call(live_server + f"/api/lessons/{lesson_id}", method="DELETE")
    with pytest.raises(urllib.error.HTTPError) as exc:
        _call(live_server + f"/api/lessons/{lesson_id}")
    assert exc.value.code == 404


def test_t16_reading_endpoint(live_server):
    _, chart = _call(live_server + "/api/chart", {"datetime": "2022-05-22T17:30:00"})
    _, reading = _call(live_server + "/api/reading", {"chart": chart, "category_code": "marriage"}, method="POST")
    assert reading["category_name"] == "婚姻"
    assert reading["role_map"]["roles"]
    assert reading["conflicts"]


def test_lesson_search_filters(live_server):
    _, chart = _call(live_server + "/api/chart", {"datetime": "2022-05-22T17:30:00"})
    first = _call(live_server + "/api/lessons", {
        "chart": chart, "category_code": "marriage", "judgement_text": "甲课", "notes": "求财备查",
    }, method="POST")[1]["id"]
    second = _call(live_server + "/api/lessons", {
        "chart": chart, "category_code": "wealth", "judgement_text": "乙课", "notes": "婚姻备查",
    }, method="POST")[1]["id"]

    def ids(query):
        _, data = _call(live_server + "/api/lessons?" + urlencode(dict(
            part.split("=", 1) for part in query.split("&")
        )))
        return {item["id"] for item in data["lessons"]}

    assert ids("q=甲课") == {first}
    assert ids("q=婚姻") == {first, second}
    assert ids("category_code=wealth") == {second}
    assert ids("from=2022-05-22&to=2022-05-22") == {first, second}
    assert ids("from=2022-05-23") == set()
    assert ids("q=备查&category_code=marriage") == {first}
    assert ids("q=备查&category_code=wealth") == {second}
    _call(live_server + f"/api/lessons/{first}", method="DELETE")
    _call(live_server + f"/api/lessons/{second}", method="DELETE")


def test_guide_endpoint_and_step_patch(live_server):
    _, chart = _call(live_server + "/api/chart", {"datetime": "2022-05-22T17:30:00"})
    _, guide = _call(live_server + "/api/guide", {"chart": chart}, method="POST")
    assert len(guide["steps"]) == 10
    assert guide["steps"][0]["step_code"] == "time"
    steps = [
        {
            "step_code": s["step_code"],
            "step_order": s["order"],
            "facts": s["facts"],
            "source_refs": s["source_refs"],
            "user_judgement": "已核" if s["step_code"] == "time" else "",
            "user_notes": "备注" if s["step_code"] == "suo_bo" else "",
        }
        for s in guide["steps"]
    ]
    _, created = _call(live_server + "/api/lessons", {"chart": chart, "steps": steps}, method="POST")
    lesson_id = created["id"]
    _, detail = _call(live_server + f"/api/lessons/{lesson_id}")
    assert len(detail["steps"]) == 10
    assert detail["steps"][0]["user_judgement"] == "已核"
    assert detail["steps"][7]["user_notes"] == "备注"
    _call(live_server + f"/api/lessons/{lesson_id}", {"steps": steps}, method="PATCH")
    _, detail = _call(live_server + f"/api/lessons/{lesson_id}")
    assert len(detail["steps"]) == 10
    assert detail["steps"][0]["step_code"] == "time"
    assert detail["steps"][0]["user_judgement"] == "已核"
    assert detail["steps"][7]["user_notes"] == "备注"
    _call(live_server + f"/api/lessons/{lesson_id}", method="DELETE")
