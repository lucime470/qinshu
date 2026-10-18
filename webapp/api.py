"""盘面 API 的纯函数封装。"""

from __future__ import annotations

from datetime import datetime

from core.birds import bird, all_birds
from core.chart import build_chart
from core.guide import build_guide
from core.reading import build_reading, list_categories as _list_categories
from core.relations import ensure_relations
from storage import db

def chart_from_payload(payload: dict) -> dict:
    raw = payload.get("datetime")
    if not raw:
        raise ValueError("datetime 必填")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("datetime 格式应为 YYYY-MM-DDTHH:MM:SS") from exc
    longitude = payload.get("longitude")
    if longitude is not None:
        longitude = float(longitude)
    return build_chart(dt, longitude)


def bird_profile(code_or_name: str) -> dict:
    item = bird(code_or_name)
    from core.relations import inner_suo_bo, outer_suo_bo
    luminary = item["seven_luminary"]
    outer = outer_suo_bo(item["name"])
    return {
        "bird_code": item["bird_code"],
        "name": item["name"],
        "short": item["short"],
        "seven_luminary": item["seven_luminary"],
        "element": item["element"],
        "yinyang": item["yinyang"],
        "day_night": item["day_night"],
        "palace": item["palace"],
        "he": [x for x in _names(item["he"])],
        "chong": [x for x in _names(item["chong"])],
        "natures": item.get("natures", {}),
        "source": item.get("source", "演禽正传"),
        "suo_bo_dial": {
            "inner": {
                branch: inner_suo_bo(branch)["name"] for branch in "子丑寅卯辰巳午未申酉戌亥"
            },
            "outer_columns": outer["columns"],
            "outer_start": outer["columns"]["山"],
            "outer_luminary": luminary,
        },
    }


def _names(codes: list[str]) -> list[str]:
    from core.birds import bird_name
    return [bird_name(code) for code in codes]


def bird_list() -> dict:
    return {"birds": [bird_profile(item["bird_code"]) for item in all_birds()]}


def categories() -> dict:
    return {"categories": _list_categories()}


def guide_from_payload(payload: dict) -> dict:
    chart = payload.get("chart")
    if not chart:
        raise ValueError("chart 必填")
    return {"steps": build_guide(ensure_relations(chart))}


def reading_from_payload(payload: dict) -> dict:
    chart = payload.get("chart")
    category_code = payload.get("category_code")
    if not chart or not category_code:
        raise ValueError("chart 与 category_code 必填")
    return build_reading(ensure_relations(chart), category_code, payload.get("household", "unspecified"))


def lessons(query: dict) -> dict:
    return {"lessons": db.list_lessons(
        q=query.get("q", [""])[0],
        category_code=query.get("category_code", [""])[0],
        date_from=query.get("from", [""])[0],
        date_to=query.get("to", [""])[0],
    )}


def create_lesson(payload: dict) -> dict:
    chart = payload.get("chart")
    if not chart:
        raise ValueError("chart 必填")
    chart = ensure_relations(chart)
    lesson_id = db.save_lesson(
        chart,
        category_code=payload.get("category_code"),
        judgement_text=payload.get("judgement_text", ""),
        notes=payload.get("notes", ""),
        steps=payload.get("steps", []),
    )
    return {"id": lesson_id}


def get_lesson(lesson_id: int) -> dict:
    item = db.get_lesson(lesson_id)
    if item is None:
        raise KeyError("课例不存在")
    item["chart_snapshot"] = ensure_relations(item["chart_snapshot"])
    return item


def patch_lesson(lesson_id: int, payload: dict) -> dict:
    steps = payload.get("steps")
    if db.get_lesson(lesson_id) is None:
        raise KeyError("课例不存在")
    if steps is not None:
        if not db.replace_steps(lesson_id, steps):
            raise KeyError("课例不存在")
    if not db.update_lesson(
        lesson_id,
        judgement_text=payload.get("judgement_text"),
        notes=payload.get("notes"),
        category_code=payload.get("category_code"),
    ):
        if steps is not None:
            return {"ok": True}
        raise KeyError("课例不存在")
    return {"ok": True}


def remove_lesson(lesson_id: int) -> dict:
    if not db.delete_lesson(lesson_id):
        raise KeyError("课例不存在")
    return {"ok": True}
