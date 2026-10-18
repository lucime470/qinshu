"""占类用神替换与条件匹配。

只输出盘面事实、命中条件与原文，不自动下吉凶结论。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_PATH = ROOT / "data" / "rules" / "categories.json"

ROLE_KEYS = {
    "番禽": "fan_qin",
    "翻禽": "fan_qin",
    "倒将": "dao_jiang",
    "到将": "dao_jiang",
    "时禽": "hour",
    "日禽": "day",
    "气将": "qi_jiang",
    "活曜": "huo_yao",
}


@lru_cache(maxsize=1)
def load_categories() -> dict[str, Any]:
    return json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))


def list_categories() -> list[dict[str, str]]:
    return [
        {"code": item["code"], "name": item["name"], "source_page": item["source_page"]}
        for item in load_categories()["categories"]
    ]


def _resolve_role(chart: dict, role: str) -> str | None:
    if role in ("我禽", "我"):
        return chart["birds"]["fan_qin"]
    if role in ("他禽", "他"):
        return chart["birds"]["dao_jiang"]
    if role in ROLE_KEYS:
        return chart["birds"][ROLE_KEYS[role]]
    return None


def _fmt_roles(chart: dict, roles: list[dict]) -> list[dict]:
    return [
        {"role": item["role"], "bird_key": item["bird"], "bird": _resolve_role(chart, item["bird"]), "note": item.get("note", "")}
        for item in roles
    ]


def _rel(a: str, b: str) -> str:
    from core.relations import relation
    return relation(a, b)


def _resolve(chart: dict, key: str) -> str:
    return {
        "fan": chart["birds"]["fan_qin"],
        "dao": chart["birds"]["dao_jiang"],
        "day": chart["birds"]["day"],
        "hour": chart["birds"]["hour"],
        "qijiang": chart["birds"]["qi_jiang"],
        "huoyao": chart["birds"]["huo_yao"],
    }[key]


def _yang_yin(chart: dict, bird_yinyang: str, palace_yinyang: str) -> bool:
    """孕产“阳禽泊阳宫/阴禽泊阴宫”。

    禽的阴阳取本命字段；宫取该禽实际外锁泊落宫，其阴阳按十二支
    （子寅辰午申戌为阳）判定。
    《禽星易见》原文另列一份阴阳宿名，和本命字段有异文，见 RULES.md。
    """
    from core.birds import bird as _bird
    from core.relations import YANG_BRANCHES, ensure_relations

    # 《禽星易见》原文以“阳禽/阴禽”配对“阳宫/阴宫”作二选一判断，
    # 这里按原文用当日时禽（地禽）的阴阳与所泊宫位判定。
    chart = ensure_relations(chart)
    name = chart["birds"]["hour"]
    profile = _bird(name)
    palace = chart["relations"]["suo_bo_facts"]["outer"]["hour"]["branch"]
    return profile["yinyang"] == bird_yinyang and (palace in YANG_BRANCHES) == (palace_yinyang == "阳")


def _condition_matches(condition_id: str, chart: dict) -> bool:
    """按条件 id 做结构化判定，不再从原文模糊匹配。"""
    from core.relations import ensure_relations

    chart = ensure_relations(chart)
    fan, dao, day, hour = (_resolve(chart, k) for k in ("fan", "dao", "day", "hour"))
    rel = chart["relations"]["sheng_ke"]
    outer = chart["relations"]["suo_bo_facts"]["outer"]
    de_di = chart["relations"]["suo_bo_facts"]["de_di"]
    strength = chart["relations"].get("strength", {})
    four_lessons = list(dict.fromkeys([day, hour, fan, chart["birds"]["huo_yao"]]))

    def is_strong(name: str) -> bool:
        return strength.get(name, {}).get("status") == "旺"

    def is_de_di(key: str) -> bool:
        return bool(de_di[key]["matched"])

    def is_not_de_di(key: str) -> bool:
        return de_di[key]["status"] == "不得地"

    fact_key = {"self": "fan_qin", "other": "dao_jiang"}

    def favorable(key: str) -> bool:
        return outer[fact_key[key]]["judgement"]["label"] in ("吉", "贵", "不妨")

    def harmful(key: str) -> bool:
        facts = chart["relations"]["suo_bo_facts"]["xing_hai"]
        def is_hit(items: list[dict]) -> bool:
            return any(item.get("target_type") != "general_hint" for item in items)
        return is_hit(facts.get(fact_key[key]) or []) or is_hit(chart["relations"]["xing_hai"].get(key) or [])

    def no_element(element: str) -> bool:
        from core.birds import bird as _bird
        from core.relations import ELEMENT_OF
        return all(ELEMENT_OF[_bird(name)["seven_luminary"]] != element for name in four_lessons)

    def all_four_element(element: str) -> bool:
        from core.birds import bird as _bird
        from core.relations import ELEMENT_OF
        return all(ELEMENT_OF[_bird(name)["seven_luminary"]] == element for name in four_lessons)

    mapping = {
        # 婚姻
        "partner_sheng_self": lambda: _rel(dao, fan) == "我生",
        "partner_ke_self": lambda: _rel(dao, fan) == "我克",
        "self_ke_partner": lambda: _rel(fan, dao) == "我克",
        "bihe": lambda: _rel(fan, dao) == "比和",
        "day_ke_self": lambda: _rel(day, fan) == "我克",
        "day_sheng_self": lambda: _rel(day, fan) == "我生",
        "sanhe": lambda: bool(chart["relations"]["sanhe_with_day"]),
        # 孕产
        "mother_ke_child": lambda: _rel(fan, dao) == "我克",
        "child_ke_mother": lambda: _rel(dao, fan) == "我克",
        "yang_yang": lambda: _yang_yin(chart, "阳", "阳"),
        "yin_yin": lambda: _yang_yin(chart, "阴", "阴"),
        # 求财 / 交易
        "open_hand": lambda: _rel(fan, hour) == "我克",
        "partner_ke": lambda: _rel(dao, fan) == "我克",
        "hour_weak": lambda: not is_strong(hour),
        "hour_fuduan": lambda: bool(chart["relations"]["fuduan"]["matched"]) and _rel(day, hour) == "我克",
        # 疾病
        "patient_ke_disease": lambda: _rel(hour, fan) == "我克",
        "disease_ke_patient": lambda: _rel(fan, hour) == "我克",
        "day_sheng_patient": lambda: _rel(day, hour) == "我生",
        "day_ke_patient": lambda: _rel(day, hour) == "我克",
        "killer_of_hour": lambda: _rel(day, hour) == "我克" or _rel(fan, hour) == "我克",
        # 天时
        "fan_ke_hour": lambda: _rel(fan, hour) == "我克",
        "bihe_weather": lambda: _rel(fan, hour) == "比和",
        "all_fire": lambda: all_four_element("火"),
        "all_water": lambda: all_four_element("水"),
        "all_wood": lambda: all_four_element("木"),
        "all_earth": lambda: all_four_element("土"),
        # 家宅
        "huoyao_sheng_hour": lambda: _rel(chart["birds"]["huo_yao"], hour) == "我生",
        "huoyao_ke_hour": lambda: _rel(chart["birds"]["huo_yao"], hour) == "我克",
        "hour_ke_huoyao": lambda: _rel(hour, chart["birds"]["huo_yao"]) == "我克",
        "hour_sheng_huoyao": lambda: _rel(hour, chart["birds"]["huo_yao"]) == "我生",
        # 失物
        "day_sheng_lost": lambda: _rel(day, fan) == "我生",
        "hour_ke_lost": lambda: _rel(hour, fan) == "我克",
        "day_ke_lost": lambda: _rel(day, fan) == "我克",
        # 谒见 / 逃难 / 捕捉 / 行人 / 官讼 / 出战 / 渔猎
        "other_sheng_self": lambda: _rel(dao, fan) == "我生",
        "self_ke_other": lambda: _rel(fan, dao) == "我克",
        "other_ke_self": lambda: _rel(dao, fan) == "我克",
        "others_sheng_other": lambda: _rel(hour, dao) == "我生",
        "day_other_sheng_self": lambda: _rel(day, fan) == "我生" or _rel(dao, fan) == "我生",
        "self_too_high": lambda: _rel(fan, dao) == "我克" and chart["relations"]["fei_fu"].get(fan) == "飞",
        "self_strong": lambda: rel["self_vs_other"] == "我克" and favorable("self") and is_strong(fan),
        "other_weak": lambda: (not is_strong(dao) or harmful("other") or not favorable("other")),
        "day_ke_other": lambda: _rel(day, dao) == "我克",
        "three_harmony": lambda: bool(chart["relations"]["day_time_sanhe"]),
        # 饮食
        "he_host": lambda: _rel(day, hour) == "比和",
        "no_he_host": lambda: _rel(day, hour) != "比和",
        "fan_strong": lambda: is_strong(fan),
        # 年岁
        "no_earth": lambda: no_element("土"),
        "no_water": lambda: no_element("水"),
        "no_wood": lambda: no_element("木"),
        "no_metal": lambda: no_element("金"),
        # 求官
        "hour_flying": lambda: chart["relations"]["fei_fu"].get(hour) == "飞" and is_de_di("hour"),
        "hour_hidden": lambda: chart["relations"]["fei_fu"].get(hour) == "伏" and not is_de_di("hour"),
        "hour_strong": lambda: is_strong(hour),
        # 擒捕 / 声息
        "self_high_other_low": lambda: is_de_di("fan_qin") and is_not_de_di("dao_jiang"),
        "self_strong_de_di": lambda: is_strong(fan) and is_de_di("fan_qin"),
        "hour_fuduan_void": lambda: bool(chart["relations"]["fuduan"]["matched"]),
        "birds_bihe": lambda: _rel(fan, dao) == "比和",
    }
    fn = mapping.get(condition_id)
    return bool(fn()) if fn else False


def build_reading(chart: dict, category_code: str, household: str = "unspecified") -> dict[str, Any]:
    from core.relations import ensure_relations

    chart = ensure_relations(chart)
    item = next((c for c in load_categories()["categories"] if c["code"] == category_code), None)
    if item is None:
        raise KeyError("未知占类")
    roles_y = _fmt_roles(chart, item["roles_y"])
    roles_q = _fmt_roles(chart, item["roles_q"])
    if category_code == "marriage" and household in ("male", "female"):
        roles_y = _marriage_roles(chart, household)
    matched = []
    all_rules = []
    for cond in item.get("conditions", []):
        record = {
            "id": cond["id"],
            "condition": cond["text"],
            "meaning": cond["meaning"],
            "matched": _condition_matches(cond["id"], chart),
        }
        all_rules.append(record)
        if record["matched"]:
            matched.append(record)
    conflicts = []
    if item["original_y"] and item["original_q"]:
        conflicts.append({
            "conflict_group": item["conflict_group"],
            "primary": "演禽正传",
            "difference": "两书用神名与取象不同；主判断区以《演禽正传》为主，另列《禽星易见》原文。",
            "role_comparison": [
                {
                    "primary": primary["role"],
                    "primary_bird": primary["bird"],
                    "secondary": secondary["role"],
                    "secondary_bird": secondary["bird"],
                }
                for primary, secondary in zip(roles_y, roles_q)
            ],
        })
    return {
        "category_code": item["code"],
        "category_name": item["name"],
        "source_page": item["source_page"],
        "household": household,
        "role_map": {
            "primary_book": "演禽正传",
            "roles": roles_y,
            "secondary_book": "禽星易见",
            "secondary_roles": roles_q,
        },
        "matched_rules": matched,
        "all_rules": all_rules,
        "conflicts": conflicts,
        "original": {
            "primary": {"book": "演禽正传", "text": item["original_y"], "page": item["source_page"]},
            "secondary": {"book": "禽星易见", "text": item["original_q"], "page": "禽星易见·" + item["name"]},
        },
    }


def _marriage_roles(chart: dict, household: str) -> list[dict]:
    if household == "male":
        # 男家问婚：时禽为男，番禽为女。
        return [
            {"role": "男", "bird_key": "时禽", "bird": chart["birds"]["hour"], "note": "男家问婚"},
            {"role": "女", "bird_key": "番禽", "bird": chart["birds"]["fan_qin"], "note": "男家问婚"},
            {"role": "媒人", "bird_key": "日禽", "bird": chart["birds"]["day"], "note": ""},
        ]
    # 女家问婚：番禽为男，时禽为女。
    return [
        {"role": "男", "bird_key": "番禽", "bird": chart["birds"]["fan_qin"], "note": "女家问婚"},
        {"role": "女", "bird_key": "时禽", "bird": chart["birds"]["hour"], "note": "女家问婚"},
        {"role": "媒人", "bird_key": "日禽", "bird": chart["birds"]["day"], "note": ""},
    ]
