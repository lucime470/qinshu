"""合冲、三合、生克、飞伏、锁泊。"""

from __future__ import annotations

import json
from typing import Any

from core.birds import bird, bird_name
from core.qiyuan import load_qiyuan

ELEMENT_CYCLE = ["木", "火", "土", "金", "水"]
# 日同火、月同水（《演禽正传》第 4 页禽星属性）
ELEMENT_OF = {"木":"木","火":"火","土":"土","金":"金","水":"水","日":"火","月":"水"}
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
SANHE = {"申子辰":"水", "亥卯未":"木", "寅午戌":"火", "巳酉丑":"金"}
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
YANG_BRANCHES = set("子寅辰午申戌")
SEASON_BY_MONTH_BRANCH = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}
# 《演禽正传》第13页（印刷第5页）“二十八宿四时旺衰歌”
SEASON_BIRDS = {
    "春": {"角", "亢", "轸", "胃", "危", "昴", "翼"},
    "夏": {"房", "柳", "张", "女", "心", "氐", "鬼"},
    "秋": {"尾", "井", "参", "觜", "星", "斗", "壁"},
    "冬": {"奎", "娄", "毕", "室", "虚", "箕", "牛"},
}
FAVORABLE_LABELS = {"吉", "贵", "不妨"}
UNFAVORABLE_LABELS = {"凶", "忌"}
DE_DI_LABELS = {"吉", "贵", "不妨"}


def relation(a: str, b: str) -> str:
    """返回 a 对 b 的关系（以 a 为我）。"""
    ea, eb = ELEMENT_OF[bird(a)["seven_luminary"]], ELEMENT_OF[bird(b)["seven_luminary"]]
    if ea == eb:
        return "比和"
    if SHENG[ea] == eb:
        return "我生"
    if SHENG[eb] == ea:
        return "生我"
    if KE[ea] == eb:
        return "我克"
    if KE[eb] == ea:
        return "克我"
    return "无直接生克"


def sanhe(a: str, b: str, c: str | None = None) -> bool:
    ba, bb = bird(a)["palace"], bird(b)["palace"]
    if not ba or not bb or ba == bb:
        return False
    groups = ["申子辰", "亥卯未", "寅午戌", "巳酉丑"]
    if c is None:
        return any(ba in g and bb in g for g in groups)
    bc = bird(c)["palace"]
    return bool(bc) and any(ba in g and bb in g and bc in g for g in groups)


def fei_fu(hour_branch: str, *birds: str) -> dict[str, str]:
    is_day = hour_branch in "辰巳午未申酉戌"
    result = {}
    for name in birds:
        flying = (bird(name)["day_night"] == "昼") == is_day
        result[name] = "飞" if flying else "伏"
    return result


def season_of_month(month_branch: str) -> str:
    return SEASON_BY_MONTH_BRANCH[month_branch]


def seasonal_strength(bird_name_: str, month_branch: str) -> dict[str, Any]:
    """按四时旺衰歌判定该禽当令与否，只给出“旺/衰”事实。"""
    season = season_of_month(month_branch)
    short = bird(bird_name_)["short"]
    strong = short in SEASON_BIRDS[season]
    return {
        "bird": bird_name_,
        "season": season,
        "month_branch": month_branch,
        "status": "旺" if strong else "衰",
        "matched": strong,
        "source": "演禽正传 第13页（印刷第5页）·二十八宿四时旺衰歌",
    }


def inner_suo_bo(day_branch: str) -> dict[str, str]:
    inner = load_qiyuan()["suo_bo"]["inner"]
    return {"name": inner[day_branch], "day_branch": day_branch, "source": "演禽正传 PDF第28页（印刷第20页）"}


def outer_suo_bo(bird_name_: str) -> dict[str, Any]:
    data = load_qiyuan()["suo_bo"]
    lum = bird(bird_name_)["seven_luminary"]
    start = data["outer_luminary_start"][lum]
    branches = "子丑寅卯辰巳午未申酉戌亥"
    start_i = branches.index(start)
    result = {}
    for offset, column in enumerate(data["outer_columns"]):
        result[column] = branches[(start_i + offset) % 12]
    return {"bird": bird_name_, "luminary": lum, "columns": result, "source": "演禽正传 PDF第29页（印刷第21页）"}


def outer_at_hour(bird_name_: str, hour_branch: str) -> dict[str, Any]:
    """按“长生位起山、顺数到用时”求该禽此刻实际所泊的宫。

    原书示例：井木犴长生亥，已时顺数至巳为天宫；张月鹿长生未，
    顺数至巳为汤火宫。返回落宫、正数序列和该宫吉凶标签。
    """
    data = load_qiyuan()["suo_bo"]
    lum = bird(bird_name_)["seven_luminary"]
    start = data["outer_luminary_start"][lum]
    start_i = BRANCHES.index(start)
    hour_i = BRANCHES.index(hour_branch)
    last_column = data["outer_columns"][(hour_i - start_i) % 12]
    path = []
    for offset, column in enumerate(data["outer_columns"]):
        branch = BRANCHES[(start_i + offset) % 12]
        path.append({"branch": branch, "column": column})
    judgement = suo_bo_judgement(bird_name_, last_column)
    return {
        "bird": bird_name_,
        "luminary": lum,
        "start_branch": start,
        "hour_branch": hour_branch,
        "branch": hour_branch,
        "column": last_column,
        "path": path,
        "judgement": judgement,
        "de_di": de_di(judgement),
        "source": "演禽正传 PDF第29页（印刷第21页）",
    }


def _category_member(short: str, category: str, categories: dict[str, list[str]]) -> bool:
    return short in categories.get(category, [])


def suo_bo_judgement(bird_name_: str, column_name: str) -> dict[str, Any]:
    """按《演禽正传》外锁泊吉凶表返回该禽落该宫的原文标签。

    先匹配具体禽名，再匹配古禽类别，最后取该宫的“余禽/诸禽”通例。
    """
    data = load_qiyuan()["suo_bo"]
    judgement = data["outer_judgement"]
    short = bird(bird_name_)["short"]
    categories = data["outer_categories"]
    rules = judgement["columns"].get(column_name, [])
    fallback = None
    for rule in rules:
        if rule.get("default"):
            fallback = rule
            continue
        if short in rule.get("birds", []) or short in rule.get("aliases", []):
            return {
                "column": column_name,
                "label": rule["label"],
                "text": rule["text"],
                "matched_by": "bird",
                "source_page": judgement["source_page"],
            }
        category = rule.get("category")
        if category and _category_member(short, category, categories):
            return {
                "column": column_name,
                "label": rule["label"],
                "text": rule["text"],
                "matched_by": "category",
                "category": category,
                "source_page": judgement["source_page"],
            }
    if fallback:
        return {
            "column": column_name,
            "label": fallback["label"],
            "text": fallback["text"],
            "matched_by": "default",
            "source_page": judgement["source_page"],
        }
    return {
        "column": column_name,
        "label": None,
        "text": "该宫此禽未见明条。",
        "matched_by": "none",
        "source_page": judgement["source_page"],
    }


def de_di(judgement: dict[str, Any]) -> dict[str, Any]:
    """把外锁泊吉凶标签转成“得地/不得地”的盘面事实。

    书中只说“得地/不得地”，没有另列五行旺衰公式。这里采用可追溯
    的保守口径：外锁泊吉凶为吉、贵、不妨者记“得地”，凶、忌者记
    “不得地”，未列明条则记“未见明条”。该字段不替代原文，也不自动
    合成断语。
    """
    label = judgement.get("label")
    if label in DE_DI_LABELS:
        status = "得地"
        matched = True
    elif label in UNFAVORABLE_LABELS:
        status = "不得地"
        matched = False
    else:
        status = "原文未定吉凶"
        matched = False
    return {
        "status": status,
        "matched": matched,
        "label": label,
        "column": judgement.get("column"),
        "text": judgement.get("text"),
        "source_page": judgement.get("source_page"),
    }


def xing_hai(bird_name_: str, outer_column: str, outer_branch: str) -> list[dict[str, Any]]:
    """返回锁泊刑害歌中与该禽、其外锁泊宫或落宫地支有关的条目。

    “刑害歌”原文混用十二支宫（子丑等）与十二锁泊宫（汤火、刀），
    这里只按该禽实际所泊的两项事实匹配，不把两者强行换算。
    """
    data = load_qiyuan()["suo_bo"]["xing_hai"]
    short = bird(bird_name_)["short"]
    matched = []
    for entry in data["entries"]:
        if short not in entry["birds"]:
            continue
        if not entry["targets"]:
            # “心奎二宿百般寻”没有给出具体宫位，只能作为原文提示，
            # 不能当作已命中的刑害事实。
            matched.append({**entry, "matched_target": None, "target_type": "general_hint",
                            "source_page": data["source_page"]})
            continue
        for target in entry["targets"]:
            if target == outer_branch:
                matched.append({**entry, "matched_target": target, "target_type": "branch_palace",
                                "source_page": data["source_page"]})
            elif target == outer_column:
                matched.append({**entry, "matched_target": target, "target_type": "suo_bo_palace",
                                "source_page": data["source_page"]})
    return matched


def suo_bo_facts(day_branch: str, hour_branch: str, birds: dict[str, str]) -> dict[str, Any]:
    """汇总盘面禽星的内外锁泊、吉凶、刑害与伏断。"""
    roles = dict(birds)
    outer = {key: outer_at_hour(name, hour_branch) for key, name in roles.items()}
    return {
        "inner": inner_suo_bo(day_branch),
        "outer": outer,
        "de_di": {key: fact["de_di"] for key, fact in outer.items()},
        "xing_hai": {
            key: xing_hai(name, outer[key]["column"], outer[key]["branch"])
            for key, name in roles.items()
        },
        "fuduan": fuduan(day_branch, birds["hour"]),
    }


def fuduan(day_branch: str, hour_bird_: str) -> dict[str, Any]:
    data = load_qiyuan()["suo_bo"]["fuduan"]
    target = data["by_day_branch"][day_branch]
    short = bird(hour_bird_)["short"]
    return {
        "day_branch": day_branch,
        "target": target,
        "hour_bird": hour_bird_,
        "matched": short == target,
        "source_book": data["source_book"],
        "source_page": data["source_page"],
        "original_text": data["source_text"],
    }


def ensure_relations(chart: dict[str, Any]) -> dict[str, Any]:
    """补齐旧课例快照缺少的关系字段。

    旧快照只保存了最初的合冲、生克与内外锁泊；外锁泊实落宫、刑害、
    伏断和四时旺衰是后来新增的。这里按快照中的四柱与禽星重新计算，
    只补缺失字段，不覆盖已有的新快照值。
    """
    calendar = chart.get("calendar") or {}
    four = calendar.get("four_pillars") or {}
    day_branch = (four.get("day") or "")[1:2]
    hour_branch = (four.get("hour") or "")[1:2]
    birds = chart.get("birds") or {}
    if not day_branch or not hour_branch or not all(
        birds.get(key) for key in ("day", "hour", "fan_qin", "dao_jiang")
    ):
        return chart

    relations = chart.setdefault("relations", {})
    base = build_relations(
        day_branch, hour_branch, birds["fan_qin"], birds["dao_jiang"], birds["day"], birds["hour"],
        birds.get("qi_jiang"), birds.get("huo_yao"),
    )
    for key, value in base.items():
        relations.setdefault(key, value)
    if isinstance(relations.get("sheng_ke"), dict):
        for key, value in base["sheng_ke"].items():
            relations["sheng_ke"].setdefault(key, value)
    if isinstance(relations.get("fei_fu"), dict):
        for key, value in base["fei_fu"].items():
            relations["fei_fu"].setdefault(key, value)
    if isinstance(relations.get("suo_bo"), dict):
        for key, value in base["suo_bo"].items():
            relations["suo_bo"].setdefault(key, value)

    all_birds = {
        key: name
        for key, name in birds.items()
        if key in {"day", "hour", "qi_jiang", "fan_qin", "dao_jiang", "huo_yao"} and name
    }
    facts = suo_bo_facts(day_branch, hour_branch, all_birds)
    existing = relations.get("suo_bo_facts")
    if not isinstance(existing, dict):
        relations["suo_bo_facts"] = facts
    else:
        for key, value in facts.items():
            existing.setdefault(key, value)
        if isinstance(existing.get("outer"), dict):
            for key, value in facts["outer"].items():
                existing["outer"].setdefault(key, value)
        if isinstance(existing.get("xing_hai"), dict):
            for key, value in facts["xing_hai"].items():
                existing["xing_hai"].setdefault(key, value)

    month_branch = calendar.get("month_branch") or four.get("month", "")[1:2]
    if month_branch:
        relations["season"] = month_branch
        strength = relations.get("strength")
        if not isinstance(strength, dict):
            strength = {}
            relations["strength"] = strength
        for name in dict.fromkeys(all_birds.values()):
            strength.setdefault(name, seasonal_strength(name, month_branch))

    relations.setdefault("self_label", "翻禽")
    relations.setdefault("other_label", "倒将")
    return chart


def build_relations(day_branch: str, hour_branch: str, self_bird: str, other_bird: str, day_bird: str, hour_bird_: str,
                    qi_jiang: str | None = None, huo_yao: str | None = None) -> dict[str, Any]:
    he = [bird_name(code) for code in bird(self_bird)["he"]]
    chong = [bird_name(code) for code in bird(self_bird)["chong"]]
    fei_fu_birds = list(dict.fromkeys(
        [day_bird, hour_bird_, self_bird, other_bird]
        + [name for name in (qi_jiang, huo_yao) if name]
    ))
    outer_self = outer_at_hour(self_bird, hour_branch)
    outer_other = outer_at_hour(other_bird, hour_branch)
    outer_day = outer_at_hour(day_bird, hour_branch)
    outer_hour = outer_at_hour(hour_bird_, hour_branch)
    return {
        "self": self_bird,
        "other": other_bird,
        "same_bird": self_bird == other_bird,
        "sheng_ke": {
            "self_vs_other": relation(self_bird, other_bird),
            "other_vs_self": relation(other_bird, self_bird),
            "self_vs_day": relation(self_bird, day_bird),
            "other_vs_day": relation(other_bird, day_bird),
        },
        "he": he,
        "chong": chong,
        "sanhe": sanhe(self_bird, other_bird),
        "sanhe_with_day": sanhe(self_bird, other_bird, day_bird),
        "day_time_sanhe": sanhe(day_bird, hour_bird_, self_bird),
        "fei_fu": fei_fu(hour_branch, *fei_fu_birds),
        "xing_hai": {
            "self": xing_hai(self_bird, outer_self["column"], outer_self["branch"]),
            "other": xing_hai(other_bird, outer_other["column"], outer_other["branch"]),
            "day": xing_hai(day_bird, outer_day["column"], outer_day["branch"]),
            "hour": xing_hai(hour_bird_, outer_hour["column"], outer_hour["branch"]),
        },
        "fuduan": fuduan(day_branch, hour_bird_),
        "outer_hour": outer_hour,
        "suo_bo": {
            "inner": inner_suo_bo(day_branch),
            "outer_self": outer_self,
            "outer_other": outer_other,
            "outer_day": outer_day,
            "outer_hour": outer_hour,
        },
    }
