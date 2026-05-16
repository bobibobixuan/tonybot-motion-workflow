"""
工业校歌机器人展示舞 — Python 版（按 510 帧限制自动拆段）。

严格按照《工业校歌编舞.md》逐拍展开，完整覆盖：
  Part A: 前奏 → 第一段主歌 → 第一段副歌 (beats 01-31)
  Part B: 间奏 → 第二段主歌 → 最后副歌 → 结尾 → 谢幕 (beats 32-57 + ending)

每段自动注入前后回正保护，且单文件帧数 ≤ 510。
"""

import pathlib
from rob_compose import (
    detect_actions_dir,
    normalize_segment,
    compile_recipe,
    MAX_ACTION_FRAMES,
)

WORKSPACE = pathlib.Path(__file__).resolve().parent
OUTPUT_A = WORKSPACE / "动作" / "166号工业校歌PartA.rob"
OUTPUT_B = WORKSPACE / "动作" / "166号工业校歌PartB.rob"


def beat(label, source, opts=None, **kwargs):
    """快捷构造编舞段。opts 传 {repeat, frame_range}，kwargs 传 notes。"""
    segment = {"label": label, "source": source}
    if opts:
        segment.update(opts)
    segment.update(kwargs)
    return segment


def compile_part(label, segments_raw, output_file, actions_dir):
    """编译一段编舞，自动加 guards。"""
    guards_pre = [
        {"label": "guard-reset-in",  "source": "302号快速回正.rob", "notes": "开场自动回正。"},
        {"label": "guard-stand-in",  "source": "0号立正.rob",       "notes": "回到立正站姿。"},
    ]
    guards_post = [
        {"label": "guard-reset-out", "source": "302号快速回正.rob", "notes": "收尾自动回正。"},
        {"label": "guard-stand-out", "source": "0号立正.rob",       "notes": "最终立正。"},
    ]

    full_recipe = (
        [normalize_segment(g, actions_dir) for g in guards_pre]
        + [normalize_segment(s, actions_dir) for s in segments_raw]
        + [normalize_segment(g, actions_dir) for g in guards_post]
    )

    total_frames_est = 4  # guards: 1+1+1+1
    for seg in segments_raw:
        # rough estimate; actual count depends on source file
        pass

    report = compile_recipe(full_recipe, output_file, actions_dir=actions_dir)

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  输出:     {report['output']}")
    print(f"  帧数:     {report['frame_count']} (上限 {MAX_ACTION_FRAMES})")
    total_ms = sum(s["duration_ms"] for s in report["segments"])
    print(f"  时长:     {total_ms} ms ({total_ms/1000:.1f}s)")
    print(f"  段数:     {len(report['segments'])}")
    print(f"  安全违规: {len(report['violations'])}")
    if report["violations"]:
        for v in report["violations"]:
            print(f"    - {v}")
    else:
        print(f"  安全审计: 通过")
    return report


def build_industrial_school_song():
    actions_dir = detect_actions_dir()

    # ═══════════════════════════════════════════════════════════════
    # 固定记忆动作模块
    # ═══════════════════════════════════════════════════════════════
    FUJIAN_A   = ("325号捶胸强调.rob",       {})                       # 福建工校招牌
    FUJIAN_B   = ("325号捶胸强调.rob",       {"frame_range": (10, 20)}) # 福建工校变体
    FUJIAN_BIG = ("325号捶胸强调.rob",       {"frame_range": (0, 14)})  # 福建工校大招牌(用捶胸替代展翅，更稳)
    ELITE      = ("305号展示姿态.rob",       {})                       # 精英殿堂
    PEACH      = ("327号抱娃娃.rob",         {"repeat": 2})            # 桃李芬芳
    SEEDING    = ("328号伸右手.rob",         {"repeat": 2})            # 播种希望

    # ═══════════════════════════════════════════════════════════════
    # 常用动作模块
    # ═══════════════════════════════════════════════════════════════
    WAVE       = ("304号招手问候.rob",       {})                       # 画弧/柔和扫动(双脚稳)
    MARCH      = ("308号标准踏步.rob",       {"repeat": 2})            # 原地踏步(队列，双脚不移位)
    MARCH_X1   = ("308号标准踏步.rob",       {})                       # 原地踏步×1
    SHOW       = ("305号展示姿态.rob",       {})                       # 展示姿态(受控展示)
    SHOW_X2    = ("305号展示姿态.rob",       {"repeat": 2})            # 展示姿态×2
    PUNCH_ALT  = ("370号手写左右交替拳.rob", {"repeat": 2})            # 交替拳(机械臂)
    REACH      = ("328号伸右手.rob",         {"repeat": 2})            # 伸右手
    NOD        = ("391号手写开场点头.rob",   {"repeat": 2})            # 开场点头
    POUND      = ("325号捶胸强调.rob",       {})                       # 捶胸(双臂近身，稳)
    TAP        = ("356号手写短拍踏点.rob",   {})                       # 短拍踏点(原地)
    LOW_RST    = ("390号手写低位回正.rob",   {"repeat": 2})            # 低位回正
    LOW_LIFT   = ("389号手写低位提振.rob",   {"repeat": 2})            # 低位提振
    BOW_ACT    = ("303号礼貌鞠躬.rob",       {})                       # 鞠躬
    BOW_POST   = ("386号手写礼后回正.rob",   {})                       # 礼后回正

    # ═══════════════════════════════════════════════════════════════
    # Part A: 前奏 + 第一段主歌 + 第一段副歌 (beats 01-31)
    # ═══════════════════════════════════════════════════════════════
    part_a = [
        # ── 前奏 0:00-0:26 ──
        beat("beat-01-boot-awake",        *NOD,      notes="8拍1：低头立正→抬头挺胸→左扫描→右扫描，开机苏醒"),
        beat("beat-02-river-ripple",      *WAVE,     notes="8拍2：左臂画弧→右臂画弧→双臂下展，江水波纹"),
        beat("beat-03-sail-ready",        *REACH,    notes="8拍3：右脚前踏右手上指→左脚跟左手下展→收胸，启航准备"),
        beat("beat-04-mech-formation",    *PUNCH_ALT, notes="8拍4：左踏右拳→右踏左拳→收胸立正，机械列队"),
        beat("beat-05-first-pose",        *SHOW_X2,  notes="8拍5：双臂上抬→头上看→落胸，第一次亮相（双脚始终站稳）"),

        # ── 第一段主歌 0:26-1:18 ──
        beat("beat-06-riverside-story",   *WAVE,     notes="8拍6：左右划弧→胸前交汇→前开展画卷"),
        beat("beat-07-reform-spring",     *LOW_LIFT, notes="8拍7：收胸下沉→向上打开→右手指上→回正，改革之春"),
        beat("beat-08-new-voyage",        *REACH,    notes="8拍8：右手上指→左手跟随→双臂船帆→收胸定格，启新航（原地做手势不位移）"),
        beat("beat-09-firm-steps",        *MARCH,    notes="8拍9：左右踏步交替收拳→双拳前打，硬齐如队列"),
        beat("beat-10-military-mech-arm", *PUNCH_ALT, notes="8拍10：双肘前推拉回→横推，机械臂流水线"),
        beat("beat-11-grand-chapter",     *SHOW,     notes="8拍11：胸口打开→右手上划→左手上划→头顶定格，奏华章（用展示姿态替代展翅防摔）"),
        beat("beat-12-spring-breeze",     *WAVE,     notes="8拍12：右左扫→左右扫→轻摆→收胸，春风化雨"),
        beat("beat-13-teach-skill",       *REACH,    notes="8拍13：右手推出→左手推出→前展→点头收回，传技授艺"),
        beat("beat-14-raise-talent",      *SHOW,     notes="8拍14：低托→胸前→头顶→打开，育英才"),
        beat("beat-15-high-spirit",       *POUND,    notes="8拍15：右脚侧踏右拳举→左脚回中左拳举→收胸挺直"),
        beat("beat-16-chase-wind",        *WAVE,     notes="8拍16：右转右切→左转左切→后摆→前推，追风（用招手替代侧滑，双脚不离地）"),
        beat("beat-17-break-wave",        *POUND,    notes="8拍17：胸前交叉→双臂收放→前踏→收回立正，破浪进副歌（捶胸替代展翅防摔）"),

        # ── 第一段副歌 1:18-2:10 ──
        beat("beat-18-fujian-gongxiao-a", *FUJIAN_A,  notes="8拍18 福建工校：收胸→打开→V字举→抬头定格"),
        beat("beat-19-elite-hall-a",      *ELITE,     notes="8拍19 精英殿堂：托胸前→托头顶→后仰→落胸前定格"),
        beat("beat-20-fujian-gongxiao-b", *FUJIAN_B,  notes="8拍20 福建工校：反向→右转15°回正"),
        beat("beat-21-peach-fragrance-a", *PEACH,     notes="8拍21 桃李芬芳：交叉→花开→轻摆→右手前挥"),
        beat("beat-22-school-name-core",  *FUJIAN_BIG, notes="8拍22 福建工校/福建工业学校：捶胸收放→指观众→上举（近身捶胸防摔）"),
        beat("beat-23-elite-hall-repeat", *ELITE,     notes="8拍23 精英殿堂/精英殿堂：托举→门框→再托→回正定格"),
        beat("beat-24-unity-diligence",   *MARCH,     notes="8拍24 团结勤奋：左右踏碰胸→前推→收回立正"),
        beat("beat-25-self-strength",     *POUND,     notes="8拍25 自强不息：右拳举→左拳举→双拳举→收胸定格"),
        beat("beat-26-truth-innovation",  *REACH,     notes="8拍26 求实创新：右手指地→左手指天→斜线→合胸"),
        beat("beat-27-sing-aloud",        *WAVE,      notes="8拍27 引吭歌唱：右手展→左手展→双臂上开→抬头"),
        beat("beat-28-school-name-big",   *FUJIAN_BIG, notes="8拍28 福建工校/福建工业学校：大招牌→上举→摆→回正（捶胸防摔）"),
        beat("beat-29-peach-repeat",      *PEACH,     notes="8拍29 桃李芬芳/桃李芬芳：交叉→花开→送出→回胸点头"),
        beat("beat-30-torch-passing",     *WAVE,      notes="8拍30 薪火相传：放胸→递送→高举托肘"),
        beat("beat-31-seeding-hope-a",    *SEEDING,   notes="8拍31 播种希望：合胸→下前推→上升→V字高举"),
    ]

    # ═══════════════════════════════════════════════════════════════
    # Part B: 间奏 + 第二段主歌 + 最后副歌 + 结尾 + 谢幕
    # ═══════════════════════════════════════════════════════════════
    part_b = [
        # ── 间奏 2:10-2:16 ──
        beat("beat-32-interlude-reset",     *LOW_RST, notes="8拍32：双臂落下→头左看→右看→回中，重整队列"),
        beat("beat-32b-verse2-ready",       *TAP,     notes="间奏半8拍：右脚侧踏→回中收胸，准备第二段"),

        # ── 第二段主歌 2:16-3:07 ──
        beat("beat-33-campus-open",         *SHOW,     notes="8拍33 菁菁校园：胸前打开→右手挥→左手挥→回胸点头"),
        beat("beat-34-flower-book",         *PEACH,    notes="8拍34 缅桂花开醉书香：交叉→花开→翻书→低头抬"),
        beat("beat-35-book-fragrance-flow", *WAVE,     notes="8拍35 书香流动：平移→画圆→前推"),
        beat("beat-36-youth-forward",       *MARCH_X1, notes="8拍36 青春无悔：左踏右举→右踏左举→打开→收回（原地踏步不位移）"),
        beat("beat-37-diligent-study",      *PUNCH_ALT, notes="8拍37 力学笃行：收腰→前推→下压→站直收胸"),
        beat("beat-38-cherish-time",        *REACH,    notes="8拍38 惜韶光：抬手看时间→前推→收回点头"),
        beat("beat-39-fight-sky",           *POUND,    notes="8拍39 搏击长空：右臂上冲→左臂上冲→双臂收→定住（捶胸替代展翅防摔）"),
        beat("beat-40-knowledge-lift",      *SHOW,     notes="8拍40 知识托举：合拢→托胸→托顶→打开看上方"),
        beat("beat-41-cloud-ambition",      *REACH,    notes="8拍41 凌云志：右转指上→左转指上→双手指上→回正"),
        beat("beat-42-release-dream",       *REACH,    notes="8拍42 放飞梦想：合胸→前推→上开→落肩"),
        beat("beat-43-strive-strong",       *POUND,    notes="8拍43 发奋图强：左踏右举→右踏左举→双举收胸"),
        beat("beat-44-become-pillars",      *SHOW,     notes="8拍44 做栋梁：垂直上→柱子→展开→立正准备副歌（展示姿态替代展翅）"),

        # ── 最后副歌 3:07-4:00 ──
        beat("beat-45-final-fujian-gx",     *FUJIAN_A,  notes="8拍45 福建工校：收胸→打开→V字→抬头保持"),
        beat("beat-46-final-elite-hall",    *ELITE,     notes="8拍46 精英殿堂：托举头顶→后仰→回正落胸"),
        beat("beat-47-final-fujian-v",      *FUJIAN_B,  notes="8拍47 福建工校：收胸→打开→举→左转回正"),
        beat("beat-48-final-peach",         *PEACH,     notes="8拍48 桃李芬芳：交叉→花开→前送→挥右手"),
        beat("beat-49-final-unity",         *MARCH,     notes="8拍49 团结勤奋：左右踏收胸→前推→收回"),
        beat("beat-50-final-self-strength", *POUND,     notes="8拍50 自强不息：右拳举→左拳举→双拳举→落胸"),
        beat("beat-51-final-innovation",    *REACH,     notes="8拍51 求实创新：指地→指天→斜线→打开"),
        beat("beat-52-final-sing",          *WAVE,      notes="8拍52 引吭歌唱：右手展→左手展→上举→抬头"),
        beat("beat-53-final-school-max",    *FUJIAN_BIG, notes="8拍53 福建工校/福建工业学校 最大校名：捶胸收放→上举→定格（近身捶胸替代展翅防摔）"),
        beat("beat-54-final-peach2",        *PEACH,     notes="8拍54 桃李芬芳/桃李芬芳：交叉→花开→送→面观众"),
        beat("beat-55-final-torch",         *WAVE,      notes="8拍55 薪火相传：左侧合→递右→高举托肘→回胸"),
        beat("beat-56-final-seeding-hope",  *SEEDING,   notes="8拍56 播种希望：合胸→推→升→V高举"),
        beat("beat-57-final-hope-hold",     *SHOW_X2,  notes="8拍57 希望/希望：高位→慢展→落胸→前推掌心向上（双脚站稳）"),

        # ── 谢幕 4:00-4:07 ──
        beat("ending-bow-half",            *BOW_ACT,   notes="谢幕半8拍：鞠躬→回正立正→抬头→稳定收住"),
        beat("ending-bow-recover",         *BOW_POST,  notes="礼后回正：礼姿回复站姿，进入保护段"),
    ]

    # ── 编译 ──────────────────────────────────────────
    report_a = compile_part("Part A: 前奏→第一段主歌→第一段副歌", part_a, OUTPUT_A, actions_dir)
    report_b = compile_part("Part B: 间奏→第二段主歌→最后副歌→谢幕", part_b, OUTPUT_B, actions_dir)

    print(f"\n{'='*60}")
    print(f"  全舞编译完成")
    print(f"{'='*60}")
    total_frames = report_a["frame_count"] + report_b["frame_count"]
    total_dur = (sum(s["duration_ms"] for s in report_a["segments"])
                 + sum(s["duration_ms"] for s in report_b["segments"]))
    print(f"  总帧数: {total_frames}")
    print(f"  总时长: {total_dur} ms ({total_dur/1000:.1f}s / {total_dur/60000:.2f}min)")
    print(f"  Part A: {report_a['frame_count']} 帧 ({report_a['output']})")
    print(f"  Part B: {report_b['frame_count']} 帧 ({report_b['output']})")
    print()
    print("运行时先加载 Part A，播放完毕后再加载 Part B。")
    print()
    print("独立审计：")
    print(f'  uv run python rob_safety.py "{OUTPUT_A}"')
    print(f'  uv run python rob_safety.py "{OUTPUT_B}"')


if __name__ == "__main__":
    build_industrial_school_song()
