from core.relations import (
    relation, sanhe, fei_fu, inner_suo_bo, outer_suo_bo, outer_at_hour,
    suo_bo_judgement, de_di, xing_hai, fuduan, seasonal_strength, ensure_relations,
)
from core.birds import bird, bird_name


def test_he_chong_symmetry():
    assert bird_name("B01") == "角木蛟"
    assert "昴日鸡" in [bird_name(x) for x in bird("角木蛟")["he"]]
    assert "奎木狼" in [bird_name(x) for x in bird("角木蛟")["chong"]]
    assert "井木犴" in [bird_name(x) for x in bird("星日马")["he"]]
    assert "星日马" in [bird_name(x) for x in bird("虚日鼠")["chong"]]


def test_sheng_ke():
    assert relation("角木蛟", "尾火虎") == "我生"
    assert relation("尾火虎", "角木蛟") == "生我"
    assert relation("角木蛟", "胃土雉") == "我克"
    assert relation("胃土雉", "角木蛟") == "克我"


def test_fei_fu_day_night():
    assert fei_fu("辰", "角木蛟")["角木蛟"] == "飞"
    assert fei_fu("子", "角木蛟")["角木蛟"] == "伏"


def test_suo_bo():
    assert inner_suo_bo("寅")["name"] == "山"
    outer = outer_suo_bo("角木蛟")
    assert outer["columns"]["山"] == "亥"
    assert outer_suo_bo("虚日鼠")["columns"]["山"] == "午"
    assert outer_suo_bo("箕水豹")["columns"]["山"] == "申"
    assert outer_suo_bo("氐土貉")["columns"]["山"] == "申"


def test_t8_fei_fu_day_night_semantics():
    day = fei_fu("辰", "角木蛟", "氐土貉")
    night = fei_fu("子", "角木蛟", "氐土貉")
    assert day == {"角木蛟":"飞", "氐土貉":"伏"}
    assert night == {"角木蛟":"伏", "氐土貉":"飞"}


def test_t9_specific_he_chong():
    assert "昴日鸡" in [bird_name(x) for x in bird("角木蛟")["he"]]
    assert "奎木狼" in [bird_name(x) for x in bird("角木蛟")["chong"]]
    assert "井木犴" in [bird_name(x) for x in bird("星日马")["he"]]
    assert "星日马" in [bird_name(x) for x in bird("虚日鼠")["chong"]]


def test_t10_suo_bo_three_entries():
    assert inner_suo_bo("寅")["name"] == "山"
    assert inner_suo_bo("午")["name"] == "火"
    assert inner_suo_bo("亥")["name"] == "江"
    assert outer_suo_bo("角木蛟")["columns"]["山"] == "亥"
    assert outer_suo_bo("尾火虎")["columns"]["山"] == "寅"
    assert outer_suo_bo("箕水豹")["columns"]["山"] == "申"


def test_outer_suo_bo_uses_hour_branch():
    # 原书示例：井木犴长生亥，巳时为天宫；张月鹿长生未，巳时为汤火宫。
    assert outer_at_hour("井木犴", "巳")["column"] == "天"
    assert outer_at_hour("张月鹿", "巳")["column"] == "汤火"
    assert outer_at_hour("角木蛟", "亥")["column"] == "山"


def test_outer_suo_bo_judgement_examples():
    assert suo_bo_judgement("尾火虎", "山")["label"] == "贵"
    assert suo_bo_judgement("房日兔", "山")["label"] == "吉"
    assert suo_bo_judgement("鬼金羊", "山")["label"] == "忌"
    assert suo_bo_judgement("壁水貐", "山")["label"] == "凶"
    assert suo_bo_judgement("角木蛟", "水")["label"] == "吉"
    assert suo_bo_judgement("毕月乌", "水")["matched_by"] == "category"
    assert suo_bo_judgement("鬼金羊", "田")["label"] == "吉"
    assert suo_bo_judgement("柳土獐", "田")["label"] == "忌"
    assert suo_bo_judgement("角木蛟", "井")["label"] == "忌"
    assert suo_bo_judgement("尾火虎", "天")["label"] == "吉"
    assert suo_bo_judgement("牛金牛", "草")["label"] == "吉"
    assert suo_bo_judgement("角木蛟", "草")["label"] == "凶"
    assert suo_bo_judgement("觜火猴", "草")["text"] == "余禽有得失"
    assert suo_bo_judgement("觜火猴", "草")["label"] is None
    assert suo_bo_judgement("角木蛟", "风")["label"] == "凶"
    assert suo_bo_judgement("毕月乌", "汤火")["label"] == "不妨"
    assert suo_bo_judgement("角木蛟", "汤火")["label"] == "忌"
    assert suo_bo_judgement("角木蛟", "月")["label"] == "凶"
    assert suo_bo_judgement("房日兔", "月")["label"] == "吉"


def test_de_di_follows_suo_bo_judgement():
    assert de_di(suo_bo_judgement("尾火虎", "山"))["status"] == "得地"
    assert de_di(suo_bo_judgement("鬼金羊", "山"))["status"] == "不得地"
    assert de_di(suo_bo_judgement("毕月乌", "汤火"))["status"] == "得地"
    assert de_di(suo_bo_judgement("角木蛟", "风"))["status"] == "不得地"
    assert de_di({"column": "未详", "label": None, "text": "该宫此禽未见明条。"})["status"] == "原文未定吉凶"


def test_outer_at_hour_exposes_de_di():
    fact = outer_at_hour("井木犴", "巳")
    assert fact["column"] == "天"
    assert fact["de_di"]["status"] == "得地"
    assert outer_at_hour("张月鹿", "巳")["de_di"]["status"] == "不得地"


def test_xing_hai_uses_branch_palace_and_suo_bo_palace():
    assert xing_hai("轸水蚓", "井", "丑")[0]["text"] == "轸水须忧丑未临"
    assert xing_hai("尾火虎", "汤火", "酉")[0]["text"] == "尾忌汤火及刀砧"
    assert xing_hai("井木犴", "汤火", "卯")[0]["text"] == "井壁原来忌卯宫"
    assert xing_hai("角木蛟", "山", "亥") == []


def test_fuduan_is_not_fei_fu():
    assert fuduan("子", "虚日鼠")["matched"] is True
    assert fuduan("子", "危月燕")["matched"] is False
    assert fuduan("亥", "壁水貐")["target"] == "壁"
    assert fuduan("亥", "觜火猴")["matched"] is False


def test_seasonal_strength_from_book_song():
    assert seasonal_strength("角木蛟", "寅")["status"] == "旺"
    assert seasonal_strength("房日兔", "巳")["status"] == "旺"
    assert seasonal_strength("尾火虎", "申")["status"] == "旺"
    assert seasonal_strength("奎木狼", "亥")["status"] == "旺"
    assert seasonal_strength("昴日鸡", "巳")["status"] == "衰"


def test_xing_hai_heart_que_is_hint_not_hit():
    hits = xing_hai("心月狐", "天", "巳")
    assert hits and hits[0]["target_type"] == "general_hint"
    assert hits[0]["matched_target"] is None


def test_ensure_relations_backfills_old_snapshot():
    old = {
        "calendar": {"four_pillars": {"day": "乙亥", "hour": "乙酉", "month": "乙巳"}},
        "birds": {"day": "昴日鸡", "hour": "觜火猴", "fan_qin": "心月狐", "dao_jiang": "昴日鸡"},
        "relations": {"self": "心月狐", "other": "昴日鸡"},
    }
    ensure_relations(old)
    assert old["relations"]["suo_bo_facts"]["outer"]["hour"]["column"] == "草"
    assert old["relations"]["suo_bo_facts"]["fuduan"]["matched"] is False
    assert old["relations"]["strength"]["昴日鸡"]["status"] == "衰"
    assert "self_vs_other" in old["relations"]["sheng_ke"]
