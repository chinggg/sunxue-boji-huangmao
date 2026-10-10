#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sunxue.py —— 孙学 · 薄肌 · 黄毛 个人操作系统 CLI

零第三方依赖，纯标准库，Python 3.8+。

    python3 sunxue.py diag     三维诊断
    python3 sunxue.py roi      ROI 计算器（看评价成本吃掉多少）
    python3 sunxue.py body     薄肌进度估算
    python3 sunxue.py 37       37% 参照系决策计算器
    python3 sunxue.py today    生成今日 Markdown 记录模板
    python3 sunxue.py quote    随机一条系统格言

测试/非交互：任何命令都可加 --answers "a,b,c" 顺序喂入答案。
"""

import argparse
import datetime
import os
import random
import sys

# --------------------------------------------------------------------------
# 基础设施
# --------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

ANSI = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "cyan": "\033[36m", "gray": "\033[90m",
}


def c(text, *styles):
    if not USE_COLOR:
        return text
    return "".join(ANSI[s] for s in styles if s in ANSI) + text + ANSI["reset"]


def rule(char="─", width=52):
    return char * width


def header(title):
    print()
    print(c(rule(), "gray"))
    print(c("  " + title, "bold"))
    print(c(rule(), "gray"))


class Feeder:
    """非交互答案供给器，用于测试与 CI。"""

    def __init__(self, raw):
        self.items = [x.strip() for x in raw.split(",")] if raw else []
        self.i = 0

    def next(self):
        if self.i < len(self.items):
            v = self.items[self.i]
            self.i += 1
            return v
        return None


FEEDER = None


def ask(prompt, default=None, cast=str, validate=None):
    """向用户提问。--answers 有存货时直接取用。"""
    tail = " [{}]".format(default) if default is not None else ""
    while True:
        if FEEDER is not None:
            got = FEEDER.next()
            if got is None or got == "":
                raw = str(default) if default is not None else ""
            else:
                raw = got
            print("{}{}: {}".format(prompt, tail, raw))
        else:
            try:
                raw = input("{}{}: ".format(prompt, tail)).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if raw == "":
                raw = str(default) if default is not None else ""
        try:
            value = cast(raw)
        except (TypeError, ValueError):
            print(c("  输入无效，请重试。", "yellow"))
            if FEEDER is not None:
                sys.exit(1)
            continue
        if validate and not validate(value):
            print(c("  超出范围，请重试。", "yellow"))
            if FEEDER is not None:
                sys.exit(1)
            continue
        return value


def ask_choice(prompt, options, default=1):
    """选项式提问。options = [(说明, 分值), ...]"""
    print()
    print(c(prompt, "bold"))
    for i, (label, _score) in enumerate(options, 1):
        print("  {}) {}".format(i, label))
    idx = ask("选择", default, int, lambda v: 1 <= v <= len(options))
    return options[idx - 1][1]


def bar(score, total=10, width=20, ch="█"):
    filled = int(round(score / float(total) * width))
    filled = max(0, min(width, filled))
    return ch * filled + "·" * (width - filled)


def grade(pct):
    if pct >= 80:
        return c("🟢 已成型", "green")
    if pct >= 60:
        return c("🟡 建设中", "yellow")
    if pct >= 40:
        return c("🟠 半成品", "yellow")
    return c("🔴 未安装", "red")


# --------------------------------------------------------------------------
# diag —— 三维诊断
# --------------------------------------------------------------------------

SUNXUE_Q = [
    ("你能说出未来 10 年确定增长的行业吗？", [
        ("一个都说不出来", 0),
        ("能说 1 个，但没验证过", 3),
        ("能说 3 个，有基本判断依据", 7),
        ("有完整的 100 个赛道推演表 / Benchmark", 10),
    ]),
    ("你的收入里，有多少来自「可复制、可放大」的系统？", [
        ("100% 来自出售时间（工资/计件）", 0),
        ("大部分卖时间，有一点点副业", 3),
        ("有一份时间多次变现的产品或内容", 7),
        ("主要收入来自系统/资产/网络效应", 10),
    ]),
    ("过去 90 天，你有没有推翻过一次自己的核心认知？", [
        ("没有，我一直是对的", 0),
        ("有动摇，但没改", 4),
        ("有，改了一个小认知", 7),
        ("有，做过 180 度转向并写了补丁日志", 10),
    ]),
]

BOJI_Q = [
    ("你每周做几次抗阻训练（深蹲/硬拉等复合动作）？", [
        ("0 次", 0),
        ("1 次，或只有有氧", 3),
        ("2–3 次", 7),
        ("4 次以上，且有渐进超载记录", 10),
    ]),
    ("你的睡眠 / 体脂 / 力量数据，存在哪里？", [
        ("哪儿都没有，凭感觉", 0),
        ("某个 App 里（SaaS 孤岛）", 4),
        ("本地 Markdown / 表格，有历史曲线", 8),
        ("本地 Markdown + AI 自动出日报", 10),
    ]),
    ("过去 12 个月，你做过一次无症状的深度体检吗？", [
        ("没有，只在有症状时去医院", 0),
        ("做过常规体检", 5),
        ("做过，且覆盖了血脂/血糖/肝功等核心项", 8),
        ("做过，且是 AI 建议驱动、有趋势对比", 10),
    ]),
]

HUANGMAO_Q = [
    ("过去 30 天，你有没有因为「别人怎么看」放弃一个正确的决定？", [
        ("有，而且不止一次", 0),
        ("有过一次，事后后悔", 3),
        ("犹豫过，但还是做了", 7),
        ("完全没有，这项不计入我的成本表", 10),
    ]),
    ("你做过「面子过不去但正确」的事吗？", [
        ("没有，我一直在等体面的出场时机", 0),
        ("想过，没做", 3),
        ("做过一件", 7),
        ("做过，并记录了情绪成本从 6 降到 2", 10),
    ]),
    ("遭遇嘲讽或质疑时，你的执行链路会中断吗？", [
        ("会，我会停下来解释和自证", 0),
        ("会慢下来，需要几天恢复", 4),
        ("基本不受影响", 7),
        ("完全不中断，我只信数据与 AI 的推演", 10),
    ]),
]

COMBOS = {
    (1, 1, 1): ("✅ 三体齐备", "你已进入护甲压力测试期：高认知+好体魄的人极易被质疑，这正是黄毛发挥作用的时候。"),
    (1, 1, 0): ("被舆论劝退者", "全看懂了，但不敢做。先别再读书了——本周做一件小事，把黄毛装上。"),
    (1, 0, 1): ("碳基服务器宕机", "认知跑太快，身体先崩。立刻停掉熬夜，从每天 30 分钟抗阻训练开始。"),
    (1, 0, 0): ("观众席常客", "想明白了，但上不了场。先装薄肌：它是唯一 7–14 天就能给你正反馈的模块。"),
    (0, 1, 1): ("健身房打工人", "执行力强、体格好，但方向为零。立刻补孙学：做一次 100 赛道全图插眼。"),
    (0, 1, 0): ("镜子里的努力", "练了很久，还是为观众服务。问自己一句：这块肌肉是为自己长的，还是为别人看的？"),
    (0, 0, 1): ("纯莽夫", "冲劲十足，无方向无续航。先开图（孙学），再建仓（薄肌）。"),
    (0, 0, 0): ("增量遗民", "还在用增量时代的会计准则，记存量时代的账。从 docs/01 开始通读。"),
}

PRESCRIPTION = {
    "孙学": "读 docs/02 与 docs/06，跑一次 `sunxue.py 37`，用 AI 推演 100 个赛道建立 Benchmark。",
    "薄肌": "每天 30 分钟抗阻复合动作，数据写进本地 Markdown。见 templates/health-data.md。",
    "黄毛": "本周做一件「面子过不去但正确」的事，并写进黄毛日志，记录情绪成本。",
}


def cmd_diag(args):
    header("三维诊断 · 孙学 / 薄肌 / 黄毛")
    print(c("  诚实打分。这不是考试，是体检。", "gray"))

    scores = {}
    for name, questions, color in (
        ("孙学", SUNXUE_Q, "yellow"),
        ("薄肌", BOJI_Q, "red"),
        ("黄毛", HUANGMAO_Q, "green"),
    ):
        print()
        print(c("  ── {} ──".format(name), color, "bold"))
        total = 0
        for prompt, options in questions:
            total += ask_choice(prompt, options)
        scores[name] = total

    print()
    print(c(rule("═"), "gray"))
    print(c("  诊断结果", "bold"))
    print(c(rule("═"), "gray"))
    print()

    flags = {}
    for name in ("孙学", "薄肌", "黄毛"):
        raw = scores[name]
        pct = raw / 30.0 * 100
        flags[name] = 1 if pct >= 60 else 0
        print("  {:<4} {} {:>5.1f} / 100   {}".format(
            name, c(bar(raw, 30), "cyan"), pct, grade(pct)))

    product = (scores["孙学"] / 30.0) * (scores["薄肌"] / 30.0) * (scores["黄毛"] / 30.0)
    print()
    print("  耦合产出  ≈ 孙学 × 薄肌 × 黄毛 = {}".format(c("{:.3f}".format(product), "bold")))
    print("  {}".format(c("乘法系统：任何一项趋近 0，整体趋近 0。", "gray")))

    key = (flags["孙学"], flags["薄肌"], flags["黄毛"])
    title, advice = COMBOS[key]
    print()
    print("  {}".format(c("【" + title + "】", "bold")))
    print("  {}".format(advice))

    weak = sorted(scores.items(), key=lambda kv: kv[1])
    print()
    print(c("  下一步处方（按短板排序）", "bold"))
    for name, _s in weak[:2]:
        print("  · {}：{}".format(name, PRESCRIPTION[name]))

    print()
    print(c("  完整理论见 docs/05-三体耦合模型.md", "gray"))
    print()


# --------------------------------------------------------------------------
# roi —— ROI 计算器
# --------------------------------------------------------------------------

def roi_level(v):
    if v >= 0.50:
        return c("🟢 值得出手", "green")
    if v >= 0.25:
        return c("🟡 可以试试", "yellow")
    if v >= 0.10:
        return c("🟠 偏薄", "yellow")
    return c("🔴 被成本压死", "red")


def cmd_roi(args):
    header("孙学 ROI 计算器")
    print(c("  ROI = (结果收益 R × 实现概率 P) / (直接成本 C + 评价成本 E + 切换成本 S)", "gray"))
    print(c("  0 = 无 / 10 = 极大", "gray"))

    action = ask("动作描述", "换一个更有前景的赛道")
    R = ask("结果收益 R", 5, float, lambda v: 0 <= v <= 10)
    P = ask("实现概率 P", 0.5, float, lambda v: 0.0 < v <= 1.0)
    C = ask("直接成本 C", 5, float, lambda v: 0 <= v <= 10)
    E = ask("评价成本 E（父母/同事/同学怎么看）", 5, float, lambda v: 0 <= v <= 10)
    S = ask("切换成本 S（房子/车子/沉没投入）", 5, float, lambda v: 0 <= v <= 10)

    denom = C + E + S
    before = (R * P) / denom if denom > 0 else 0.0

    e2 = E * 0.0
    s2 = S * 0.3
    denom2 = C + e2 + s2
    after = (R * P) / denom2 if denom2 > 0 else 0.0

    print()
    print(c(rule("═"), "gray"))
    print("  动作：{}".format(c(action, "bold")))
    print(c(rule("═"), "gray"))
    print()
    print(c("  ── 当前 ──", "bold"))
    print("    ROI = ({:.1f} × {:.2f}) / ({:.1f} + {:.1f} + {:.1f}) = {}".format(
        R, P, C, E, S, c("{:.3f}".format(before), "bold")))
    print("    评级：{}".format(roi_level(before)))
    if denom > 0 and E + S > 0:
        print("    成本结构：直接 {:.0f}% · 评价 {:.0f}% · 切换 {:.0f}%".format(
            C / denom * 100, E / denom * 100, S / denom * 100))

    print()
    print(c("  ── 孙学优化后 ──", "bold"))
    print("    {}  E: {:.1f} → {:.1f}".format(c("黄毛清零评价成本", "green"), E, e2))
    print("    {}  S: {:.1f} → {:.1f}".format(c("轻资产压切换成本", "blue"), S, s2))
    print("    ROI = ({:.1f} × {:.2f}) / ({:.1f} + {:.1f} + {:.1f}) = {}".format(
        R, P, C, e2, s2, c("{:.3f}".format(after), "bold")))
    print("    评级：{}".format(roi_level(after)))
    if before > 0:
        print("    {}  ↑ 提升 {:.0f}%".format(
            c("同样的能力，不同的成本表。", "gray"), (after / before - 1) * 100))

    print()
    print(c("  公理：C(action) = C(task) + C(face) + C(permission)，黄毛令后两项归零。", "gray"))
    print()


# --------------------------------------------------------------------------
# body —— 薄肌进度
# --------------------------------------------------------------------------

def bmi_tag(bmi):
    if bmi < 18.5:
        return "偏瘦区间"
    if bmi < 24.0:
        return "正常区间"
    if bmi < 28.0:
        return "超重区间"
    return "肥胖区间"


def cmd_body(args):
    header("薄肌进度估算")
    print(c("  肌肉是身体的美金存量。先看你的资产负债表。", "gray"))

    w = ask("体重（kg）", 70, float, lambda v: 20 <= v <= 300)
    bf = ask("体脂率（%）", 20, float, lambda v: 3 <= v <= 70)
    h = ask("身高（cm）", 172, float, lambda v: 100 <= v <= 250)
    goal = ask("目标体脂率（%）", 15, float, lambda v: 3 <= v <= 70)

    fat = w * bf / 100.0
    lean = w - fat
    bmi = w / ((h / 100.0) ** 2)

    print()
    print(c(rule("═"), "gray"))
    print(c("  身体成分", "bold"))
    print(c(rule("═"), "gray"))
    print("    去脂体重（肌肉+骨+水）：{:.2f} kg   {}".format(lean, c("← 你的现金储备", "green")))
    print("    脂肪质量：              {:.2f} kg   {}".format(fat, c("← 不良负债", "red")))
    print("    BMI：{:.1f}（{}）".format(bmi, bmi_tag(bmi)))
    print("    蛋白质目标：{:.0f}–{:.0f} g/日   {}".format(
        w * 1.6, w * 2.2, c("← 1.6–2.2 g/kg", "gray")))

    print()
    print(c("  薄肌路径", "bold"))
    print(c(rule("─"), "gray"))
    if goal >= bf:
        print("    {}".format(c("目标体脂 ≥ 当前体脂，无需减脂。重点是维持抗阻训练、保住去脂体重。", "yellow")))
    else:
        target_w = lean / (1 - goal / 100.0)
        lose = w - target_w
        weeks = lose / 0.5
        print("    保持去脂体重时的目标体重：{:.1f} kg".format(target_w))
        print("    需减脂肪：{:.1f} kg".format(lose))
        print("    健康速率（0.5 kg/周）：约 {:.0f} 周 ≈ {} 个月".format(
            weeks, "{:.1f}".format(weeks / 4.35)))
        print()
        print("    {}".format(c("顺序不能反：先用抗阻训练把「现金储备」建起来，再谈热量缺口。", "bold")))
        print("    {}".format(c("顺序反了，减的是资产不是负债。", "gray")))

    print()
    print(c("  ⚠️ 司美格鲁肽等药物在减脂同时大幅削减肌肉：", "yellow"))
    print(c("     越打药 → 代谢断崖 → 停药反弹 → 肌肉更少 → 晚年肌无力。", "gray"))
    print(c("  完整模型见 docs/07-肌肉资产负债表.md", "gray"))
    print()


# --------------------------------------------------------------------------
# 37 —— 37% 参照系决策
# --------------------------------------------------------------------------

def cmd_37(args):
    header("37% 参照系决策计算器")
    print(c("  面对 N 个选项：前 37% 只建 Benchmark，之后遇超参照系最优解立刻出手。", "gray"))

    n = ask("选项总数", 100, int, lambda v: v >= 2)
    seen = ask("已考察数量", int(n * 0.37) or 1, int, lambda v: 0 <= v <= n)

    gate = int(round(n * 0.368)) or 1
    pct = seen / float(n) * 100

    print()
    print(c(rule("═"), "gray"))
    print(c("  诊断", "bold"))
    print(c(rule("═"), "gray"))
    print()
    print("  参照系门槛：{} 个（{} × 37%）".format(gate, n))
    print("  当前进度：  {} / {}   {}".format(seen, n, bar(min(seen, n), n, 24)))
    print("  完成度：    {:.1f}%".format(pct))
    print()

    if seen < gate:
        print("  状态：{}".format(c("⏳ 仍在参照系建设期 —— 只看不定", "yellow")))
        print("  还差 {} 个样本才能建立 Benchmark。".format(gate - seen))
        print("  {}".format(c("现在下单 = 盲定。你还没见过「好」，认不出「最好」。", "gray")))
    else:
        print("  状态：{}".format(c("✅ 参照系已建立，进入决策区", "green")))
        print("  从下一个起，遇到综合指标超过 Benchmark 的，{}".format(c("立刻出手。", "bold")))
        print("  {}".format(c("看满全部 = 瘫痪。最优解通常早就过去了。", "gray")))

    print()
    print(c("  两种失败模式：盲定（参照系缺失） / 瘫痪（选择过载）", "gray"))
    print(c("  详见 docs/06-全图插眼与37%参照系.md", "gray"))
    print()


# --------------------------------------------------------------------------
# today —— 今日模板
# --------------------------------------------------------------------------

TODAY_TEMPLATE = """# {date} · 孙学薄肌黄毛日报

## 一、薄肌　Body OS
- [ ] 抗阻训练 30 分钟（深蹲 / 硬拉 / 卧推 / 划船 / 推举）
- 主项动作与重量：
- 组数 × 次数：
- 是否达成渐进超载：是 / 否（本周 → 下周 +2.5kg 或 +1 次）
- 蛋白质摄入：___ g（目标 {protein} g）
- 睡眠：___ 小时（可穿戴数据）

## 二、孙学　Kernel
- 今日认知补丁（我以前错在哪）：
- 今日开图动作（推演了哪个赛道 / 建立了哪个 Benchmark）：
- 今日是否做了「一份时间多次变现」的事：是 / 否

## 三、黄毛　Shield OS
- 今日做了什么「面子过不去但正确」的事：
- 事前预估情绪成本（0–10）：
- 事后实际情绪成本（0–10）：
- 是否因外界评价中断执行：是 / 否

## 四、数据守护进程
- 今日记录已写入本地 Markdown：是 / 否
- 餐前/餐后照片已交给 AI 核算：是 / 否
- 本周是否换过模型对比结论：是 / 否

---
> 结果产出 ≈ 孙学 × 薄肌 × 黄毛 —— 乘法，任何一项趋近 0，整体趋近 0。
"""


def cmd_today(args):
    today = datetime.date.today().isoformat()
    w = args.weight if args.weight else 70.0
    text = TODAY_TEMPLATE.format(
        date=today,
        protein="{:.0f}–{:.0f}".format(w * 1.6, w * 2.2),
    )
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("已写入 {}".format(args.out))
    else:
        sys.stdout.write(text)


# --------------------------------------------------------------------------
# quote —— 格言
# --------------------------------------------------------------------------

QUOTES = [
    "高富帅是把资源花在「让人羡慕」上——那是消费。孙学是把资源花在「最后站着的是我」上——那是投资。",
    "肌肉就是你身上的美金存量。大病来临时，代谢会优先扣除它去修复器官。",
    "黄毛不是一种发型，是把「他人评价」从成本项里彻底划掉的结算方式。",
    "孙学、黄毛、薄肌没有一样要求先天条件。它们把「能不能」换成「愿不愿意」。",
    "高富帅只有张凌赫能当，黄毛只要愿意，谁都能当。",
    "大肌肉是展示型资产，薄肌是功能型资产。同样是身体，一个为观众服务，一个为自己服务。",
    "如果在 AI 时代，你的知识没有被形式化并上传网络，那么它在下一纪元等同于未曾发生。",
    "财富自由不是赚很多钱，是不再为钱出售自己的时间、注意力、尊严和情绪。",
    "先自由，后财富。自由是认知的解绑定与机动性，财富只是套利之后的伴生品。",
    "一代版本一代神。阻碍你的从来不是能力短板，是你舍不得卸下的那套旧出装。",
    "越成功，Ego 越大，最终沦为旧版本的殉道者。",
    "先造侦察兵去插眼，再派主力出击。大部分人的问题是闭着眼睛在战争迷雾里冲。",
    "决策失败只有两种：第一套就盲目下定，或者看满 100 套选择瘫痪。",
    "你可以砍掉虚荣，别砍掉信用。可以少买 logo，别少攒本事。",
    "虚荣是最大的负债，生存才是唯一的硬通货。",
    "别信人，信数据。",
    "阻碍个体演进的往往不是能力的短板，而是过去成功带来的巨大 Ego。",
    "环境不好时，活到春天的往往不是最壮的，是最省油的。",
]


def cmd_quote(args):
    print()
    print(c("  " + random.choice(QUOTES), "bold"))
    print()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="sunxue",
        description="孙学 · 薄肌 · 黄毛 —— 低成本个人操作系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="零第三方依赖。完整理论见 docs/。",
    )
    p.add_argument(
        "--answers",
        help="以逗号分隔预填答案，用于非交互执行（须写在子命令之前）",
    )
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("diag", help="三维诊断：孙学 / 薄肌 / 黄毛")
    d.add_argument("--quick", action="store_true", help="使用默认答案快速预览")
    d.set_defaults(func=cmd_diag)

    r = sub.add_parser("roi", help="ROI 计算器：看评价成本吃掉多少")
    r.set_defaults(func=cmd_roi)

    b = sub.add_parser("body", help="薄肌进度与蛋白质目标估算")
    b.set_defaults(func=cmd_body)

    s = sub.add_parser("37", help="37%% 参照系决策计算器")
    s.set_defaults(func=cmd_37)

    t = sub.add_parser("today", help="生成今日 Markdown 记录模板")
    t.add_argument("--weight", type=float, help="体重 kg，用于计算蛋白质目标")
    t.add_argument("--out", help="写入文件而不是标准输出")
    t.set_defaults(func=cmd_today)

    q = sub.add_parser("quote", help="随机一条系统格言")
    q.set_defaults(func=cmd_quote)
    return p


def main(argv=None):
    global FEEDER
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0

    if args.answers:
        FEEDER = Feeder(args.answers)

    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
