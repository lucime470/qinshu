"""盘面聚合。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.birds import bird, bird_name
from core.calendar import build_calendar
from core.fan_dao import dao_jiang, fan_dao_alt, fan_qin, huo_yao
from core.hour_bird import hour_bird, qi_jiang
from core.qiyuan import build_yuan
from core.relations import build_relations, seasonal_strength, suo_bo_facts

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def _hour_branch(dt: datetime) -> str:
    # 23:00-00:59 为子时；过 23:00 后时柱已按次日计算。
    return BRANCHES[((dt.hour + 1) // 2) % 12]


def build_chart(dt: datetime, longitude: float | None = None) -> dict[str, Any]:
    cal = build_calendar(dt, longitude)
    yuan = build_yuan(cal.day_ordinal)
    hb = _hour_branch(cal.local_time)
    hour = hour_bird(yuan.day_bird, hb)
    qj = qi_jiang(cal.day_ordinal)
    fan = fan_qin(hb, qj, hour)
    dao = dao_jiang(hb, hour, fan)
    hy = huo_yao(hb, hour)
    alt_fan, alt_dao = fan_dao_alt(hb, qj, yuan.day_bird, hour)
    relations = build_relations(
        cal.four_pillars["day"][1], hb, fan, dao, yuan.day_bird, hour, qj, hy
    )
    relations["season"] = cal.month_branch
    relations["suo_bo_facts"] = suo_bo_facts(cal.four_pillars["day"][1], hb, {
        "day": yuan.day_bird,
        "hour": hour,
        "qi_jiang": qj,
        "fan_qin": fan,
        "dao_jiang": dao,
        "huo_yao": hy,
    })
    relations["strength"] = {
        name: seasonal_strength(name, cal.month_branch)
        for name in dict.fromkeys([yuan.day_bird, hour, qj, fan, dao, hy])
    }
    relations["self_label"] = "翻禽"
    relations["other_label"] = "倒将"
    warnings = []
    if fan == dao:
        warnings.append({
            "code": "self_equals_other",
            "message": "翻禽与倒将同宿，彼我同位；只作盘面事实，不自动断吉凶。",
            "source": "演禽正传 第14-15页",
        })
    if alt_fan != fan or alt_dao != dao:
        warnings.append({
            "code": "fan_dao_tradition_diff",
            "message": "《演禽正传》与《禽星易见》系辅助起法的番禽/到将结果不同；主盘采用《演禽正传》。",
            "source": "演禽正传 第14-15页；禽星易见 番禽到将",
        })
    return {
        "input": {
            "datetime": cal.local_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": "Asia/Shanghai",
            "longitude": longitude,
            "use_current_time": False,
        },
        "calendar": {
            "four_pillars": cal.four_pillars,
            "solar_term": cal.solar_term,
            "month_branch": cal.month_branch,
            "day_boundary": cal.day_boundary,
            "solar_time_variant": cal.solar_time_variant,
            "lunar_date": cal.lunar_date,
        },
        "yuan": {
            "index": yuan.index,
            "name": yuan.name,
            "leader_bird": yuan.leader_bird,
            "day_index": yuan.day_index,
        },
        "birds": {
            "day": yuan.day_bird,
            "hour": hour,
            "qi_jiang": qj,
            "fan_qin": fan,
            "dao_jiang": dao,
            "huo_yao": hy,
        },
        "relations": relations,
        "comparison": {
            "fan_qin_alt": alt_fan,
            "dao_jiang_alt": alt_dao,
            "source": "禽星易见系辅助起法" if (alt_fan != fan or alt_dao != dao) else None,
        },
        "evidence": [
            {"rule_id": "yz-yuan-001", "source_book": "演禽正传", "source_chapter": "起日禽", "source_page": "8-12", "original_text": "一元虚、二元奎、三元毕、四元鬼、五元翼、六元氐、七元箕。"},
            {"rule_id": "yz-hour-001", "source_book": "演禽正传", "source_chapter": "起时禽", "source_page": "13", "original_text": "日虚月鬼火从箕，水毕木氐金奎位，土宿还从翼上推。"},
            {"rule_id": "yz-qijiang-001", "source_book": "演禽正传", "source_chapter": "气将", "source_page": "14", "original_text": "每一元的第1天，第16天，第31天，第46天所对应的星宿。"},
            {"rule_id": "yz-fandao-001", "source_book": "演禽正传", "source_chapter": "起翻禽/起倒将", "source_page": "14-15", "original_text": "从当下时辰地支开始排气将，顺数地支，顺数二十八宿，数到时禽所在。"},
            {"rule_id": "yz-huoyao-001", "source_book": "演禽正传", "source_chapter": "活耀", "source_page": "15-16", "original_text": "日毕月尾金牛头，木虚水氐火奎流，土翼常将寅上转。"},
            {
                "rule_id": "yz-suobo-001",
                "source_book": "演禽正传",
                "source_chapter": "外锁泊",
                "source_page": "PDF第29-30页（印刷第21-22页）",
                "original_text": "山、水、田、园、井、刀、天、草、岸、风、汤火、月；木长生亥、火长生寅、金长生巳、日长生午、月长生未、水土长生申。外锁泊吉凶：山宫尾箕贵；房昴星吉；羊犬忌；壁轸亢凶。水宫角亢壁翼吉；飞禽忌；张尾虚、走兽凶。田宫星鬼胃昴牛娄吉；鼠獐鹿忌；余禽凶。园宫觜参室斗昴鬼娄吉；余禽俱凶。井宫诸禽忌。刀宫诸禽忌。天宫诸禽皆吉。草宫牛羊獐鹿马、奎室房吉；角亢壁凶。岸宫翼轸猪羊尾毕井心星吉。风宫诸禽俱凶。汤火宫诸禽忌，天禽不妨。月宫诸禽皆吉，惟角亢壁翼轸凶。",
            },
            {
                "rule_id": "yz-xinghai-001",
                "source_book": "演禽正传",
                "source_chapter": "锁泊刑害歌",
                "source_page": "PDF第29页（印刷第21页）",
                "original_text": "尾忌汤火及刀砧，轸水须忧丑未临。箕鬼氐房由忌子，心奎二宿百般寻。金狗从来未不宁，金牛角轸酉为刑。星张汤火忧寅上，危燕巳上莫相侵。觜参昴胃毕辰凶，井壁原来忌卯宫。",
            },
            {
                "rule_id": "qy-fuduan-001",
                "source_book": "禽星易见",
                "source_chapter": "伏断",
                "source_page": "伏断",
                "original_text": "子虚丑斗寅嫌室，卯女辰箕巳泊房。午角未张申忌鬼，酉觜戌胃亥壁当。",
            },
            {
                "rule_id": "yz-season-001",
                "source_book": "演禽正传",
                "source_chapter": "二十八宿四时旺衰歌",
                "source_page": "PDF第13页（印刷第5页）",
                "original_text": "春：蛟龙蚓雉燕鸡蛇，皆到春来福禄加。夏：兔獐鹿蝠狐貉羊，遇夏生时百事强。秋：虎犴猿猴马獬貐，秋天福禄自然殊。冬：狼狗乌猪鼠豹牛，若逢冬月更无忧。",
            },
            {
                "rule_id": "yz-dedi-001",
                "source_book": "演禽正传",
                "source_chapter": "外锁泊得地",
                "source_page": "PDF第29-30页（印刷第21-22页）",
                "original_text": "其法以本禽于长生位起山字，顺数至用时住，看彼我之禽，何者得地变化，遇吉则吉，遇凶则凶。外锁泊吉凶中，吉、贵、不妨记为得地，凶、忌记为不得地；该分类仅据原文标签，不另造五行旺衰公式。",
            },
        ],
        "warnings": warnings,
    }
