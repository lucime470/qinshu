"""固定十步引导。

每一步只输出盘面事实、规则出处和待用户判断的问题；不生成吉凶结论。
前端按本模块返回的步骤顺序渲染，课例按 step_code 保存逐步判断。
"""

from __future__ import annotations

from typing import Any

from core.birds import bird
from core.relations import ensure_relations


def _bird_facts(chart: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    name = chart["birds"][key]
    profile = bird(name)
    relations = chart["relations"]
    outer = relations["suo_bo_facts"]["outer"].get(key) or {}
    return {
        "label": label,
        "bird": name,
        "palace": profile["palace"],
        "seven_luminary": profile["seven_luminary"],
        "day_night": profile["day_night"],
        "outer": outer.get("column"),
        "outer_branch": outer.get("branch"),
        "de_di": (outer.get("de_di") or {}).get("status"),
        "strength": relations.get("strength", {}).get(name, {}).get("status"),
    }


def build_guide(chart: dict[str, Any]) -> list[dict[str, Any]]:
    chart = ensure_relations(chart)
    cal = chart["calendar"]
    four = cal["four_pillars"]
    yuan = chart["yuan"]
    birds = chart["birds"]
    rel = chart["relations"]
    facts = rel["suo_bo_facts"]

    time_facts = {
        "datetime": chart["input"]["datetime"],
        "timezone": chart["input"].get("timezone"),
        "four_pillars": four,
        "solar_term": cal.get("solar_term"),
        "month_branch": cal.get("month_branch"),
        "day_boundary": cal.get("day_boundary"),
    }
    yuan_facts = {
        "yuan": yuan["name"],
        "yuan_index": yuan["index"],
        "day_index": yuan["day_index"],
        "leader_bird": yuan["leader_bird"],
        "day_bird": birds["day"],
        "day_palace": bird(birds["day"])["palace"],
    }
    hour_facts = {
        "hour_bird": birds["hour"],
        "hour_palace": bird(birds["hour"])["palace"],
        "qi_jiang": birds["qi_jiang"],
        "qi_jiang_palace": bird(birds["qi_jiang"])["palace"],
    }
    fan_dao_facts = {
        "fan_qin": birds["fan_qin"],
        "dao_jiang": birds["dao_jiang"],
        "huo_yao": birds["huo_yao"],
        "fan_palace": bird(birds["fan_qin"])["palace"],
        "dao_palace": bird(birds["dao_jiang"])["palace"],
        "huo_yao_palace": bird(birds["huo_yao"])["palace"],
        "comparison": chart.get("comparison") or {},
    }
    sheng_ke_facts = {
        "self": rel.get("self_label", "翻禽"),
        "other": rel.get("other_label", "倒将"),
        "self_bird": birds["fan_qin"],
        "other_bird": birds["dao_jiang"],
        "sheng_ke": rel.get("sheng_ke"),
        "same_bird": rel.get("same_bird"),
        "de_di": facts.get("de_di"),
        "strength": rel.get("strength"),
    }
    fei_fu_facts = {
        "fei_fu": rel.get("fei_fu"),
        "day_night": {
            key: bird(name)["day_night"]
            for key, name in birds.items()
            if key in {"day", "hour", "qi_jiang", "fan_qin", "dao_jiang", "huo_yao"}
        },
        "hour_branch": four["hour"][1],
    }
    he_chong_facts = {
        "he": rel.get("he"),
        "chong": rel.get("chong"),
        "sanhe": rel.get("sanhe"),
        "sanhe_with_day": rel.get("sanhe_with_day"),
        "day_time_sanhe": rel.get("day_time_sanhe"),
    }
    suo_bo_facts = {
        "inner": facts.get("inner"),
        "outer_hour": facts.get("outer", {}).get("hour"),
        "outer_day": facts.get("outer", {}).get("day"),
        "xing_hai_hour": facts.get("xing_hai", {}).get("hour"),
        "fuduan": facts.get("fuduan"),
        "season": rel.get("season"),
        "strongest": {
            key: value.get("status")
            for key, value in (rel.get("strength") or {}).items()
        },
    }

    return [
        {
            "step_code": "time",
            "order": 1,
            "title": "时间与四柱核对",
            "question": "四柱、节气月建、子初换日是否符合当前时间？",
            "facts": time_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "四柱与节气", "page": "6–7"},
                {"book": "项目口径", "chapter": "子初换日", "page": "23:00"},
            ],
        },
        {
            "step_code": "yuan_day",
            "order": 2,
            "title": "七元与日禽核对",
            "question": "元序、元内日序和日禽是否与七元甲子表一致？",
            "facts": yuan_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "起日禽", "page": "8–12"},
            ],
        },
        {
            "step_code": "hour_qijiang",
            "order": 3,
            "title": "时禽与气将核对",
            "question": "时禽是否按日禽七曜起子时顺推？气将是否取元内第 1/16/31/46 天？",
            "facts": hour_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "起时禽", "page": "13"},
                {"book": "演禽正传", "chapter": "气将", "page": "14"},
            ],
        },
        {
            "step_code": "fan_dao_huoyao",
            "order": 4,
            "title": "翻禽、倒将、活曜核对",
            "question": "翻禽、倒将与活曜是否与书中步进一致？是否采用《演禽正传》主盘？",
            "facts": fan_dao_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "起翻禽/起倒将", "page": "14–15"},
                {"book": "演禽正传", "chapter": "活耀", "page": "15–16"},
            ],
        },
        {
            "step_code": "sheng_ke",
            "order": 5,
            "title": "彼我强弱与生克",
            "question": "翻禽与倒将谁生谁克？双方是否得地、旺衰如何？",
            "facts": sheng_ke_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "生克得地", "page": "28–30"},
            ],
        },
        {
            "step_code": "fei_fu",
            "order": 6,
            "title": "飞伏与昼夜",
            "question": "各禽当前为飞还是伏？是否与昼夜属性一致？",
            "facts": fei_fu_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "昼夜飞伏", "page": "7"},
            ],
        },
        {
            "step_code": "he_chong",
            "order": 7,
            "title": "合、冲、三合",
            "question": "我禽的合冲对象是谁？日、时、翻禽是否同临三合？",
            "facts": he_chong_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "合冲三合", "page": "28"},
            ],
        },
        {
            "step_code": "suo_bo",
            "order": 8,
            "title": "锁泊与宫位",
            "question": "内外锁泊落在何宫？是否得地、刑害或逢伏断？",
            "facts": suo_bo_facts,
            "source_refs": [
                {"book": "演禽正传", "chapter": "内锁泊", "page": "PDF第28页（印刷第20页）"},
                {"book": "演禽正传", "chapter": "外锁泊", "page": "PDF第29页（印刷第21页）"},
                {"book": "演禽正传", "chapter": "外锁泊吉凶", "page": "PDF第30页（印刷第22页）"},
                {"book": "禽星易见", "chapter": "伏断", "page": "伏断"},
            ],
        },
        {
            "step_code": "category",
            "order": 9,
            "title": "选择占类",
            "question": "按所问之事选择占类，核对用神分配、命中的条件和两书差异。",
            "facts": {"category_options": "见下方占类对照"},
            "source_refs": [
                {"book": "演禽正传", "chapter": "分类占法", "page": "62–67"},
                {"book": "禽星易见", "chapter": "分类占法", "page": "占婚姻至占声息"},
            ],
        },
        {
            "step_code": "judgement",
            "order": 10,
            "title": "填写判断、依据与备注",
            "question": "综合以上盘面事实，写下自己的判断、依据和保留意见。",
            "facts": {},
            "source_refs": [
                {"book": "项目口径", "chapter": "人作最终判断", "page": "PROJECT.md"},
            ],
        },
    ]
