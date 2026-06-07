import json
import pathlib


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_DIR = WORKSPACE_ROOT / "动作模块"


def wrap(module_id, name, source, prompt, notes, frame_range=None, repeat=None):
    segment = {
        "label": source.replace(".rob", ""),
        "source": source,
        "notes": notes,
    }
    if frame_range is not None:
        segment["frame_range"] = list(frame_range)
    if repeat is not None:
        segment["repeat"] = repeat
    stem = "{}号{}".format(module_id, name)
    return {
        "name": stem,
        "prompt": prompt,
        "output": {
            "rob": "动作/{}.rob".format(stem),
        },
        "segments": [segment],
    }


PRESETS = [
    wrap(301, "站姿基座", "0号立正.rob", "标准站姿基座模块，用于所有编舞的安全起点或终点。", "标准站姿，用作安全基座。"),
    wrap(302, "快速回正", "19号快速立正.rob", "快速回正模块，用于高节奏段落后的迅速归位。", "快速回正，适合高节奏段落后归位。"),
    wrap(303, "礼貌鞠躬", "10号鞠躬.rob", "礼貌收尾模块，用于结束致意。", "礼貌收尾。"),
    wrap(304, "招手问候", "9号挥手.rob", "问候模块，用于开场建立互动感。", "开场问候。"),
    wrap(305, "展示姿态", "48号介绍动作.rob", "展示姿态模块，用于舞蹈中段停顿和亮相。", "展示姿态。"),
    wrap(306, "笑场互动", "15号开怀大笑.rob", "表情互动模块，用于轻松型表演。", "轻松互动。"),
    wrap(307, "短拍踏步", "49号原地踏步.rob", "短拍踏步模块，用于建立基础节拍。", "短拍踏步。", frame_range=(0, 8)),
    wrap(308, "标准踏步", "49号原地踏步.rob", "标准踏步模块，用于更完整的节拍表达。", "标准踏步。", frame_range=(0, 12)),
    wrap(309, "左侧滑短句", "11号左侧滑.rob", "左侧滑短句模块，用于横向律动。", "左侧滑短句。"),
    wrap(310, "右侧滑短句", "12号右侧滑.rob", "右侧滑短句模块，用于横向律动。", "右侧滑短句。"),
    wrap(311, "左右侧滑往返", "11号左侧滑.rob", "左右侧滑往返模块，用于一组对称横移。", "左滑起拍。", repeat=1),
    wrap(312, "扭腰单拍", "50号扭腰.rob", "扭腰单拍模块，用于制造核心律动。", "单次扭腰。"),
    wrap(313, "扭腰双拍", "50号扭腰.rob", "扭腰双拍模块，用于强化节奏循环。", "双次扭腰。", repeat=2),
    wrap(314, "左侧踢", "51号左侧踢.rob", "左侧踢模块，用于强调型节拍。", "左侧踢。"),
    wrap(315, "右侧踢", "52号右侧踢.rob", "右侧踢模块，用于强调型节拍。", "右侧踢。"),
    wrap(316, "左右侧踢组合", "51号左侧踢.rob", "左右侧踢组合的前半模块。", "左右侧踢组合前半。"),
    wrap(317, "左勾拳", "57号左勾拳2.rob", "左勾拳模块，用于拳击节奏。", "左勾拳。"),
    wrap(318, "右勾拳", "58号右勾拳2.rob", "右勾拳模块，用于拳击节奏。", "右勾拳。"),
    wrap(319, "左右勾拳组合", "57号左勾拳2.rob", "左右勾拳组合的起始模块。", "左右勾拳组合起始。", repeat=1),
    wrap(320, "左弯勾拳", "53号左弯勾拳2.rob", "左弯勾拳模块，用于强调型上肢动作。", "左弯勾拳。"),
    wrap(321, "右弯勾拳", "54号右弯勾拳2.rob", "右弯勾拳模块，用于强调型上肢动作。", "右弯勾拳。"),
    wrap(322, "前进拳击", "59号前进拳击.rob", "前进拳击模块，用于带位移的攻击节奏。", "前进拳击。"),
    wrap(323, "下蹲拳", "60号下蹲拳.rob", "下蹲拳模块，用于低位节奏表达。", "下蹲拳。"),
    wrap(324, "咏春拳", "61号咏春拳.rob", "咏春拳模块，用于连续上肢节拍。", "咏春拳。"),
    wrap(325, "捶胸强调", "62号捶胸.rob", "捶胸模块，用于强拍强调。", "捶胸强调。"),
    wrap(326, "大鹏展翅", "17号大鹏展翅.rob", "展开姿态模块，用于视觉打开。", "大鹏展翅。"),
    wrap(327, "抱娃娃", "26号抱娃娃.rob", "抱娃娃姿态模块，用于剧情化动作。", "抱娃娃。"),
    wrap(328, "伸右手", "27号伸右手.rob", "伸手展示模块，用于点位和邀请感。", "伸右手。"),
    wrap(329, "下蹲回正", "30号下蹲立正.rob", "下蹲回正模块，用于从低位回到站姿。", "下蹲回正。"),
    wrap(330, "下蹲前压", "31号下蹲前进.rob", "下蹲前压模块，用于低位推进。", "下蹲前压。"),
    wrap(331, "俯卧撑短句", "7号俯卧撑.rob", "俯卧撑模块，用于体能展示。", "俯卧撑短句。"),
    wrap(332, "仰卧起坐短句", "8号仰卧起坐.rob", "仰卧起坐模块，用于体能展示。", "仰卧起坐短句。"),
    wrap(333, "街舞片段", "150号街舞.rob", "街舞风格片段模块。", "街舞片段。"),
    wrap(334, "江南节奏", "151号江南STYLE舞蹈.rob", "江南节奏片段模块。", "江南节奏。"),
    wrap(335, "小苹果节奏", "152号小苹果舞蹈.rob", "小苹果节奏片段模块。", "小苹果节奏。"),
    wrap(336, "LaSong节奏", "153号La Song舞蹈.rob", "La Song 片段模块。", "La Song 片段。"),
    wrap(337, "倍儿爽节奏", "154号倍儿爽舞蹈.rob", "倍儿爽片段模块。", "倍儿爽片段。"),
    wrap(338, "Fantastic节奏", "155号fantastic baby舞蹈.rob", "Fantastic Baby 片段模块。", "Fantastic Baby 片段。"),
    wrap(339, "超级冠军节奏", "156号超级冠军舞蹈.rob", "超级冠军片段模块。", "超级冠军片段。"),
    wrap(340, "青春修炼手册节奏", "157号青春修炼手册舞蹈.rob", "青春修炼手册片段模块。", "青春修炼手册片段。"),
    wrap(341, "爱出发节奏", "158号爱出发舞蹈.rob", "爱出发片段模块。", "爱出发片段。"),
    wrap(342, "前行两步", "71号向前走俩步.rob", "前行两步模块，用于舞台推进。", "向前走两步。"),
    wrap(343, "后退两步", "72号后退俩步.rob", "后退两步模块，用于舞台回收。", "后退两步。"),
    wrap(344, "左转七步", "73号向左转7步.rob", "左转七步模块，用于大角度方向变化。", "左转七步。"),
    wrap(345, "右转七步", "74号右转7步.rob", "右转七步模块，用于大角度方向变化。", "右转七步。"),
    wrap(346, "左转九十", "75号原地左转90°.rob", "原地左转九十度模块。", "左转九十度。"),
    wrap(347, "右转九十", "76号原地右转.rob", "原地右转九十度模块。", "右转九十度。"),
    wrap(348, "头顶抓取", "78号抓取（头顶）.rob", "头顶抓取模块，用于夹取类流程。", "头顶抓取。"),
    wrap(349, "头顶放下", "79号放下（头顶）.rob", "头顶放下模块，用于放置类流程。", "头顶放下。"),
    wrap(350, "头顶携带前进一步", "80号抓着前进第一步（头顶）.rob", "头顶携带前进一步模块，用于夹持推进。", "头顶携带前进一步。"),
]


def write_spec(spec):
    path = MODULE_DIR / "{}.json".format(spec["name"])
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_index(paths):
    lines = ["# 预设模块索引", "", "当前自动生成了 50 个预设模块：", ""]
    for path in paths:
        lines.append("- {}".format(path.stem))
    lines.append("")
    lines.append("使用方式：")
    lines.append("")
    lines.append("- python rob_compose.py 动作模块/301号站姿基座.json")
    lines.append("- python rob_compose.py 动作模块/350号头顶携带前进一步.json")
    (MODULE_DIR / "预设模块索引.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    MODULE_DIR.mkdir(parents=True, exist_ok=True)
    written = [write_spec(spec) for spec in PRESETS]
    write_index(written)
    print("generated={}".format(len(written)))
    for path in written:
        print(path.name)


if __name__ == "__main__":
    main()