from datetime import datetime

from core.chart import build_chart


def test_t1_2021_05_23_chi_you():
    chart = build_chart(datetime(2021, 5, 23, 1, 30))
    assert chart["calendar"]["four_pillars"] == {"year":"辛丑","month":"癸巳","day":"辛未","hour":"己丑"}
    assert chart["yuan"]["name"] == "一元"
    assert chart["birds"]["day"] == "昴日鸡"
    assert chart["birds"]["hour"] == "危月燕"
    assert chart["birds"]["qi_jiang"] == "虚日鼠"
    # T1 来源为《演禽起课仅供参考》，其翻禽按“顺数到日禽”起，属《禽星易见》系辅助体系。
    assert chart["comparison"]["fan_qin_alt"] == "星日马"
    assert chart["comparison"]["dao_jiang_alt"] == "女土蝠"
    # 主盘仍按《演禽正传》“顺数到时禽”，与书页 T2/T3 一致。
    assert chart["birds"]["fan_qin"] == "室火猪"


def test_t2_2022_05_22_you():
    chart = build_chart(datetime(2022, 5, 22, 17, 30))
    assert chart["calendar"]["four_pillars"] == {"year":"壬寅","month":"乙巳","day":"乙亥","hour":"乙酉"}
    assert chart["yuan"]["name"] == "七元"
    assert chart["birds"]["day"] == "昴日鸡"
    assert chart["birds"]["hour"] == "觜火猴"
    assert chart["birds"]["qi_jiang"] == "箕水豹"
    assert chart["birds"]["fan_qin"] == "心月狐"
    assert chart["birds"]["dao_jiang"] == "昴日鸡"


def test_t3_2022_05_24_si():
    chart = build_chart(datetime(2022, 5, 24, 9, 30))
    assert chart["calendar"]["four_pillars"] == {"year":"壬寅","month":"乙巳","day":"丁丑","hour":"乙巳"}
    assert chart["birds"]["day"] == "觜火猴"
    assert chart["birds"]["hour"] == "危月燕"
    assert chart["birds"]["qi_jiang"] == "箕水豹"
    assert chart["birds"]["fan_qin"] == "胃土雉"
    assert chart["birds"]["huo_yao"] == "参水猿"
