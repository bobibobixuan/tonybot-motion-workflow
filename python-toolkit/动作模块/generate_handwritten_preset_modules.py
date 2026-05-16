import json
import pathlib


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_DIR = WORKSPACE_ROOT / "动作模块"


def mix(left, right, ratio):
    return [int(round(a + (b - a) * ratio)) for a, b in zip(left, right)]


ANCHORS = {
    "stand": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
    "step": [540, 330, 568, 612, 505, 575, 800, 724, 530, 612, 500, 406, 500, 425, 200, 275],
    "slide_left": [500, 395, 489, 594, 500, 575, 800, 725, 519, 605, 511, 406, 444, 425, 200, 275],
    "slide_right": [481, 395, 489, 594, 556, 575, 800, 725, 500, 605, 511, 406, 500, 425, 200, 275],
    "twist_left": [560, 368, 528, 608, 612, 237, 537, 724, 526, 578, 584, 455, 575, 762, 462, 275],
    "twist_right": [473, 421, 415, 545, 425, 237, 537, 724, 440, 631, 471, 391, 387, 762, 462, 275],
    "guard": [500, 395, 500, 593, 500, 575, 800, 724, 500, 605, 500, 406, 500, 425, 200, 275],
    "punch_left": [600, 395, 500, 593, 544, 681, 826, 288, 447, 713, 372, 406, 431, 425, 310, 275],
    "punch_right": [576, 395, 500, 593, 528, 575, 544, 724, 479, 705, 336, 359, 447, 423, 125, 711],
    "kick_left": [593, 387, 500, 593, 575, 500, 800, 724, 556, 612, 500, 406, 500, 500, 200, 275],
    "kick_right": [443, 387, 500, 593, 500, 500, 800, 724, 406, 612, 500, 406, 425, 500, 200, 275],
    "squat": [500, 200, 838, 744, 500, 575, 800, 725, 500, 800, 162, 256, 500, 425, 200, 275],
    "bow_open": [500, 500, 303, 500, 500, 500, 800, 724, 500, 500, 696, 500, 500, 500, 200, 275],
    "bow_deep": [500, 500, 433, 758, 500, 800, 790, 325, 500, 500, 566, 241, 500, 200, 210, 674],
}

ANCHORS["weight_left"] = mix(ANCHORS["stand"], ANCHORS["slide_left"], 0.5)
ANCHORS["weight_right"] = mix(ANCHORS["stand"], ANCHORS["slide_right"], 0.5)
ANCHORS["step_mid"] = mix(ANCHORS["stand"], ANCHORS["step"], 0.5)
ANCHORS["twist_left_mid"] = mix(ANCHORS["stand"], ANCHORS["twist_left"], 0.5)
ANCHORS["twist_right_mid"] = mix(ANCHORS["stand"], ANCHORS["twist_right"], 0.5)
ANCHORS["punch_left_mid"] = mix(ANCHORS["guard"], ANCHORS["punch_left"], 0.5)
ANCHORS["punch_right_mid"] = mix(ANCHORS["guard"], ANCHORS["punch_right"], 0.5)
ANCHORS["kick_left_mid"] = mix(ANCHORS["stand"], ANCHORS["kick_left"], 0.5)
ANCHORS["kick_right_mid"] = mix(ANCHORS["stand"], ANCHORS["kick_right"], 0.5)
ANCHORS["squat_mid"] = mix(ANCHORS["stand"], ANCHORS["squat"], 0.5)
ANCHORS["squat_left"] = mix(ANCHORS["squat"], ANCHORS["slide_left"], 0.5)
ANCHORS["squat_right"] = mix(ANCHORS["squat"], ANCHORS["slide_right"], 0.5)
ANCHORS["bow_mid"] = mix(ANCHORS["stand"], ANCHORS["bow_open"], 0.5)
ANCHORS["bow_deep_mid"] = mix(ANCHORS["bow_open"], ANCHORS["bow_deep"], 0.5)
ANCHORS["guard_left"] = mix(ANCHORS["guard"], ANCHORS["weight_left"], 0.5)
ANCHORS["guard_right"] = mix(ANCHORS["guard"], ANCHORS["weight_right"], 0.5)


def frames(*items):
    return [{"duration": duration, "pose": ANCHORS[anchor]} for duration, anchor in items]


MODULES = [
    (351, "手写左侧预摆", "左侧轻摆预备模块", "从中立重心轻压到左侧，再回到中位。", frames((160, "stand"), (120, "weight_left"), (120, "slide_left"), (160, "stand"))),
    (352, "手写右侧预摆", "右侧轻摆预备模块", "从中立重心轻压到右侧，再回到中位。", frames((160, "stand"), (120, "weight_right"), (120, "slide_right"), (160, "stand"))),
    (353, "手写左右对摆", "左右对摆模块", "先左后右地切换重心，适合开场找拍。", frames((140, "stand"), (110, "weight_left"), (110, "stand"), (110, "weight_right"), (140, "stand"))),
    (354, "手写左入右收", "左入右收模块", "先向左进入动作，再从右侧收回中心。", frames((140, "stand"), (100, "weight_left"), (120, "slide_left"), (100, "weight_right"), (140, "stand"))),
    (355, "手写右入左收", "右入左收模块", "先向右进入动作，再从左侧收回中心。", frames((140, "stand"), (100, "weight_right"), (120, "slide_right"), (100, "weight_left"), (140, "stand"))),
    (356, "手写短拍踏点", "短拍踏点模块", "用较短的踏点建立拍感。", frames((120, "stand"), (100, "step_mid"), (120, "step"), (100, "step_mid"), (140, "stand"))),
    (357, "手写双拍踏点", "双拍踏点模块", "连续两次踏点，适合铺设节奏前奏。", frames((120, "stand"), (90, "step_mid"), (110, "step"), (90, "stand"), (90, "step_mid"), (110, "step"), (140, "stand"))),
    (358, "手写左滑锁拍", "左滑锁拍模块", "向左滑入并在左侧短暂停住。", frames((140, "stand"), (100, "weight_left"), (120, "slide_left"), (100, "weight_left"), (140, "stand"))),
    (359, "手写右滑锁拍", "右滑锁拍模块", "向右滑入并在右侧短暂停住。", frames((140, "stand"), (100, "weight_right"), (120, "slide_right"), (100, "weight_right"), (140, "stand"))),
    (360, "手写左右滑步锁点", "左右滑步锁点模块", "一组完整的左右滑步锁点。", frames((120, "stand"), (100, "weight_left"), (100, "slide_left"), (100, "stand"), (100, "weight_right"), (100, "slide_right"), (140, "stand"))),
    (361, "手写左扭腰入拍", "左扭腰入拍模块", "通过左扭腰制造明显节拍落点。", frames((140, "stand"), (100, "twist_left_mid"), (140, "twist_left"), (100, "twist_left_mid"), (140, "stand"))),
    (362, "手写右扭腰入拍", "右扭腰入拍模块", "通过右扭腰制造明显节拍落点。", frames((140, "stand"), (100, "twist_right_mid"), (140, "twist_right"), (100, "twist_right_mid"), (140, "stand"))),
    (363, "手写左右扭腰往返", "左右扭腰往返模块", "左右各做一次扭腰，形成完整摆动。", frames((120, "stand"), (90, "twist_left_mid"), (120, "twist_left"), (90, "stand"), (90, "twist_right_mid"), (120, "twist_right"), (140, "stand"))),
    (364, "手写左扭腰双击", "左扭腰双击模块", "在左侧扭腰位置做两次重拍。", frames((120, "stand"), (90, "twist_left_mid"), (120, "twist_left"), (90, "twist_left_mid"), (120, "twist_left"), (140, "stand"))),
    (365, "手写右扭腰双击", "右扭腰双击模块", "在右侧扭腰位置做两次重拍。", frames((120, "stand"), (90, "twist_right_mid"), (120, "twist_right"), (90, "twist_right_mid"), (120, "twist_right"), (140, "stand"))),
    (366, "手写左拳预压", "左拳预压模块", "左拳出击前先做一次短预压。", frames((120, "guard"), (90, "punch_left_mid"), (120, "punch_left"), (90, "punch_left_mid"), (140, "guard"))),
    (367, "手写右拳预压", "右拳预压模块", "右拳出击前先做一次短预压。", frames((120, "guard"), (90, "punch_right_mid"), (120, "punch_right"), (90, "punch_right_mid"), (140, "guard"))),
    (368, "手写左拳双击", "左拳双击模块", "左拳连续双击，适合强调节奏。", frames((120, "guard"), (80, "punch_left_mid"), (110, "punch_left"), (80, "guard"), (80, "punch_left_mid"), (110, "punch_left"), (140, "guard"))),
    (369, "手写右拳双击", "右拳双击模块", "右拳连续双击，适合强调节奏。", frames((120, "guard"), (80, "punch_right_mid"), (110, "punch_right"), (80, "guard"), (80, "punch_right_mid"), (110, "punch_right"), (140, "guard"))),
    (370, "手写左右交替拳", "左右交替拳模块", "左右拳交替打出，形成一组连击。", frames((120, "guard"), (80, "punch_left_mid"), (100, "punch_left"), (80, "guard"), (80, "punch_right_mid"), (100, "punch_right"), (140, "guard"))),
    (371, "手写左勾拳锁点", "左勾拳锁点模块", "左拳出击后略作停顿，形成锁点。", frames((120, "guard"), (90, "punch_left_mid"), (140, "punch_left"), (100, "punch_left_mid"), (140, "guard"))),
    (372, "手写右勾拳锁点", "右勾拳锁点模块", "右拳出击后略作停顿，形成锁点。", frames((120, "guard"), (90, "punch_right_mid"), (140, "punch_right"), (100, "punch_right_mid"), (140, "guard"))),
    (373, "手写左右勾拳往返", "左右勾拳往返模块", "左右拳各打一拍，中间保留回拉过程。", frames((120, "guard"), (90, "punch_left_mid"), (120, "punch_left"), (90, "guard_left"), (90, "punch_right_mid"), (120, "punch_right"), (140, "guard"))),
    (374, "手写左拳回拉", "左拳回拉模块", "左拳打出后带一点身体回拉。", frames((120, "guard"), (90, "punch_left_mid"), (120, "punch_left"), (90, "punch_left_mid"), (90, "weight_left"), (140, "guard"))),
    (375, "手写右拳回拉", "右拳回拉模块", "右拳打出后带一点身体回拉。", frames((120, "guard"), (90, "punch_right_mid"), (120, "punch_right"), (90, "punch_right_mid"), (90, "weight_right"), (140, "guard"))),
    (376, "手写左踢预备", "左踢预备模块", "左腿抬起前先做预备压拍。", frames((140, "stand"), (100, "kick_left_mid"), (140, "kick_left"), (100, "kick_left_mid"), (140, "stand"))),
    (377, "手写右踢预备", "右踢预备模块", "右腿抬起前先做预备压拍。", frames((140, "stand"), (100, "kick_right_mid"), (140, "kick_right"), (100, "kick_right_mid"), (140, "stand"))),
    (378, "手写左踢停顿", "左踢停顿模块", "左踢后保留一拍停顿，强化造型。", frames((140, "stand"), (100, "kick_left_mid"), (180, "kick_left"), (120, "kick_left_mid"), (140, "stand"))),
    (379, "手写右踢停顿", "右踢停顿模块", "右踢后保留一拍停顿，强化造型。", frames((140, "stand"), (100, "kick_right_mid"), (180, "kick_right"), (120, "kick_right_mid"), (140, "stand"))),
    (380, "手写左右点踢", "左右点踢模块", "左右各点踢一次，适合轻快节奏。", frames((140, "stand"), (90, "kick_left_mid"), (110, "kick_left"), (90, "stand"), (90, "kick_right_mid"), (110, "kick_right"), (140, "stand"))),
    (381, "手写下蹲预备", "下蹲预备模块", "从站姿压低到下蹲位置，再回到站姿。", frames((160, "stand"), (120, "squat_mid"), (160, "squat"), (120, "squat_mid"), (180, "stand"))),
    (382, "手写下蹲回弹", "下蹲回弹模块", "下蹲后快速回弹一次。", frames((160, "stand"), (100, "squat_mid"), (140, "squat"), (100, "squat_mid"), (120, "squat"), (180, "stand"))),
    (383, "手写下蹲停拍", "下蹲停拍模块", "下蹲后稍作停顿，适合重拍。", frames((160, "stand"), (120, "squat_mid"), (220, "squat"), (120, "squat_mid"), (180, "stand"))),
    (384, "手写浅礼起身", "浅礼起身模块", "做一个浅鞠躬后立刻起身。", frames((160, "stand"), (120, "bow_mid"), (160, "bow_open"), (120, "bow_mid"), (180, "stand"))),
    (385, "手写深礼收束", "深礼收束模块", "从浅礼深入到深礼，再完整回到站姿。", frames((160, "stand"), (120, "bow_mid"), (140, "bow_open"), (140, "bow_deep_mid"), (180, "bow_deep"), (140, "bow_mid"), (180, "stand"))),
    (386, "手写礼后回正", "礼后回正模块", "从礼姿直接恢复到标准站姿。", frames((160, "bow_open"), (120, "bow_mid"), (200, "stand"))),
    (387, "手写左低位摇摆", "左低位摇摆模块", "在低位姿态下向左摇摆一次。", frames((140, "squat_mid"), (120, "squat_left"), (140, "squat"), (120, "squat_mid"), (180, "stand"))),
    (388, "手写右低位摇摆", "右低位摇摆模块", "在低位姿态下向右摇摆一次。", frames((140, "squat_mid"), (120, "squat_right"), (140, "squat"), (120, "squat_mid"), (180, "stand"))),
    (389, "手写低位提振", "低位提振模块", "从下蹲位做一次提振回弹。", frames((160, "stand"), (120, "squat_mid"), (140, "squat"), (120, "squat_mid"), (120, "weight_left"), (180, "stand"))),
    (390, "手写低位回正", "低位回正模块", "从低位姿态平滑回到站姿。", frames((160, "squat"), (140, "squat_mid"), (200, "stand"))),
    (391, "手写开场点头", "开场点头模块", "用两次轻点头式前倾作为开场提示。", frames((160, "stand"), (100, "bow_mid"), (120, "stand"), (100, "bow_mid"), (160, "stand"))),
    (392, "手写展肩亮相", "展肩亮相模块", "左右展肩后回到中心，适合亮相。", frames((140, "stand"), (100, "guard_left"), (120, "guard"), (100, "guard_right"), (160, "stand"))),
    (393, "手写左引导入拳", "左引导入拳模块", "先向左引导，再接一记左拳。", frames((140, "weight_left"), (100, "punch_left_mid"), (120, "punch_left"), (100, "guard"), (160, "stand"))),
    (394, "手写右引导入拳", "右引导入拳模块", "先向右引导，再接一记右拳。", frames((140, "weight_right"), (100, "punch_right_mid"), (120, "punch_right"), (100, "guard"), (160, "stand"))),
    (395, "手写左引导入踢", "左引导入踢模块", "先向左蓄力，再接左腿点踢。", frames((140, "weight_left"), (100, "kick_left_mid"), (120, "kick_left"), (100, "stand"), (160, "stand"))),
    (396, "手写右引导入踢", "右引导入踢模块", "先向右蓄力，再接右腿点踢。", frames((140, "weight_right"), (100, "kick_right_mid"), (120, "kick_right"), (100, "stand"), (160, "stand"))),
    (397, "手写科目三左引导", "科目三左引导模块", "带踏点和左扭腰的科目三式引导句。", frames((120, "stand"), (90, "step_mid"), (90, "weight_left"), (100, "twist_left_mid"), (120, "twist_left"), (140, "stand"))),
    (398, "手写科目三右引导", "科目三右引导模块", "带踏点和右扭腰的科目三式引导句。", frames((120, "stand"), (90, "step_mid"), (90, "weight_right"), (100, "twist_right_mid"), (120, "twist_right"), (140, "stand"))),
    (399, "手写科目三连摆", "科目三连摆模块", "左右各摆一次的科目三小副歌。", frames((120, "stand"), (90, "weight_left"), (100, "twist_left_mid"), (90, "stand"), (90, "weight_right"), (100, "twist_right_mid"), (140, "stand"))),
    (400, "手写科目三收束拍", "科目三收束拍模块", "左右引导后加一个轻礼收束。", frames((120, "stand"), (90, "weight_left"), (90, "stand"), (90, "weight_right"), (90, "stand"), (110, "bow_mid"), (160, "stand"))),
]


def build_spec(module_id, name, prompt, notes, frame_list):
    return {
        "name": "{}号{}".format(module_id, name),
        "prompt": prompt,
        "output": {
            "rob": "动作/{}号{}.rob".format(module_id, name),
        },
        "segments": [
            {
                "label": "manual-{}".format(module_id),
                "source_name": "manual:{}".format(module_id),
                "notes": notes,
                "frames": frame_list,
            }
        ],
    }


def main():
    MODULE_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for module_id, name, prompt, notes, frame_list in MODULES:
        spec = build_spec(module_id, name, prompt, notes, frame_list)
        path = MODULE_DIR / "{}号{}.json".format(module_id, name)
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)

    index_lines = ["# 手写预设模块索引", "", "当前自动展开了 351-400 共 50 个手写模块：", ""]
    for path in written:
        index_lines.append("- {}".format(path.stem))
    index_lines.append("")
    (MODULE_DIR / "手写预设模块索引.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    print("generated={}".format(len(written)))
    for path in written:
        print(path.name)


if __name__ == "__main__":
    main()