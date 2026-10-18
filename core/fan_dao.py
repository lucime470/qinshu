"""翻禽、倒将、活曜。

主算法取《演禽正传》：
- 翻禽：时辰起气将，顺数到时禽；逆数地支、顺数星宿回到时辰。
- 倒将：时辰起时禽，顺数到翻禽；逆数地支、顺数星宿回到时辰。
- 活曜：按时禽七曜起宿，从寅起，逆数到时辰，再顺数到时辰。

《禽星易见》系辅助起法把“顺数到时禽”换成“顺数到日禽”，
结果不同；这里只作对照，不覆盖主盘。
"""

from __future__ import annotations

from core.birds import bird, bird_code, bird_name

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
HUO_YAO_START = {"日":"毕月乌","月":"尾火虎","金":"牛金牛","木":"虚日鼠","水":"氐土貉","火":"奎木狼","土":"翼火蛇"}


def _codes() -> list[str]:
    from core.birds import all_birds
    return [item["bird_code"] for item in all_birds()]


def _idx(code_or_name: str) -> int:
    return _codes().index(bird_code(code_or_name))


def _bid(index: int) -> str:
    return bird_name(_codes()[index % 28])


def _walk(start_bird: str, start_branch: str, target_bird: str, branch_forward: bool = True) -> tuple[str, int]:
    """从 (起点宿, 起点地支) 按地支与宿序同步走，直到宿名等于 target_bird。

    返回命中地支与“地支步数”；回推时用同一个地支步数，而不是循环项数。
    """
    b = _idx(start_bird)
    br = BRANCHES.index(start_branch)
    steps = 0
    for _ in range(28 * 12 + 1):
        if _bid(b) == target_bird:
            return BRANCHES[br], steps
        br = (br + (1 if branch_forward else -1)) % 12
        b = (b + 1) % 28
        steps += 1
    raise ValueError("目标禽星不在同步序列中")


def _return_from(bird_at_target: str, steps: int) -> str:
    """逆数相同步数，顺数宿序。"""
    return _bid(_idx(bird_at_target) + steps)


def fan_qin(hour_branch: str, qi_jiang: str, hour_bird: str) -> str:
    branch_at_target, steps = _walk(qi_jiang, hour_branch, hour_bird)
    return _return_from(hour_bird, steps)


def dao_jiang(hour_branch: str, hour_bird: str, fan: str) -> str:
    branch_at_target, steps = _walk(hour_bird, hour_branch, fan)
    return _return_from(fan, steps)


def huo_yao(hour_branch: str, hour_bird: str) -> str:
    lum = bird(hour_bird)["seven_luminary"]
    start = HUO_YAO_START[lum]
    # 从寅逆数地支、顺数二十八宿到时禽；再顺数到时辰地支。
    steps_to_bird = (_idx(hour_bird) - _idx(start)) % 28
    meeting_branch = (2 - steps_to_bird) % 12
    steps_back = (BRANCHES.index(hour_branch) - meeting_branch) % 12
    return _bid(_idx(hour_bird) + steps_back)


def fan_dao_alt(hour_branch: str, qi_jiang: str, day_bird: str, hour_bird: str) -> tuple[str, str]:
    """《禽星易见》系辅助起法：顺数到日禽，推出番禽；再从时禽顺数到番禽，推出到将。"""
    _, steps = _walk(qi_jiang, hour_branch, day_bird)
    alt_fan = _return_from(day_bird, steps)
    _, steps2 = _walk(hour_bird, hour_branch, alt_fan)
    alt_dao = _return_from(alt_fan, steps2)
    return alt_fan, alt_dao
