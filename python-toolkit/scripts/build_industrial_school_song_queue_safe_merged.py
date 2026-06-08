import json
import pathlib

from dance_workflow import build_workflow
from rob_safety import audit_plain_file


WORKSPACE = pathlib.Path(__file__).resolve().parent
SPEC_OUT = WORKSPACE / "编舞" / "169号工业校歌队列广播体操合并版.json"
ROB_OUT = WORKSPACE / "动作" / "169号工业校歌队列广播体操合并版.rob"
ACTION_DIR = WORKSPACE / "动作"


def segment(label, source, notes, repeat=1, frame_range=None):
    item = {
        "label": label,
        "source": source,
        "repeat": repeat,
        "notes": notes,
    }
    if frame_range is not None:
        item["frame_range"] = list(frame_range)
    return item


def build_spec():
    spec = {
        "name": "169号工业校歌官方上半身队列版",
        "prompt": (
            "工业校歌 169 号官方上半身队列版 1分16秒精简版。整舞只允许拼接官方 0-104 号动作库，"
            "禁用手写模块、预设模块和一切下半身主导动作，整体保持多人并排同跳时的庄重、整齐和口号感。"
        ),
        "research": {
            "query": "工业校歌 官方动作库 上半身 队列表演 多机同步",
            "summary": [
                "本版对 169 号进行完全重编，所有片段都直接引用官方 0-104 号动作，不再混入任何手写或预设模块。",
                "选段只保留挥手、伸手、介绍、抱娃娃、捶胸和拳法等上肢主导动作，整体排除前进、侧滑、转向、下蹲、踢腿和鞠躬等下半身动作。",
                "本次按你的要求把总时长压到 1分16秒，保留前半段主歌到第一轮收束，删除后半段重复展开，并改成短收势后快速回正。"
            ],
            "references": []
        },
        "visualization": {
            "title": "169号工业校歌官方上半身队列版时间线",
            "theme": "sunrise"
        },
        "output": {
            "rob": "动作/169号工业校歌队列广播体操合并版.rob",
            "report_json": "编舞/169号工业校歌队列广播体操合并版.report.json",
            "visualization_html": "编舞/169号工业校歌队列广播体操合并版.timeline.html"
        },
        "guards": {
            "pre_segments": [
                {
                    "label": "pre-quick-recenter",
                    "source": "19号快速立正.rob",
                    "notes": "开场前统一快速回正。"
                },
                {
                    "label": "pre-stand-settle",
                    "source": "0号立正.rob",
                    "notes": "统一回到稳定立正。"
                }
            ],
            "post_segments": [
                {
                    "label": "post-quick-recenter",
                    "source": "19号快速立正.rob",
                    "notes": "收尾再次统一回正。"
                }
            ]
        },
        "segments": [
            segment("beat-01-boot-awake", "27号伸右手.rob", "用短促伸手替代点头起势，开场给出统一入拍提示。", frame_range=(0, 1)),
            segment("beat-02-river-ripple", "9号挥手.rob", "用完整挥手展开前奏，画面更像多人广播操的开场招呼。"),
            segment("beat-03-sail-ready", "27号伸右手.rob", "双次伸手保持上肢方向感，强调启航和指向。", repeat=2),
            segment("beat-04-mech-formation", "57号左勾拳2.rob", "截取左勾拳前四帧，做更克制的机械口号动作。", frame_range=(0, 4)),
            segment("beat-05-first-pose", "48号介绍动作.rob", "用介绍动作前三帧做第一轮整齐亮相。", frame_range=(0, 3)),
            segment("beat-06-riverside-story", "9号挥手.rob", "重复挥手母题，保持多人同跳时的上肢流动感。"),
            segment("beat-07-reform-spring", "26号抱娃娃.rob", "取抱娃娃首帧做短暂停顿，作为主歌切入前的收束。", frame_range=(0, 1)),
            segment("beat-08-new-voyage", "27号伸右手.rob", "保持双次伸手，继续传达启新航的方向感。", repeat=2),
            segment("beat-09-firm-steps", "48号介绍动作.rob", "用介绍动作前三帧替代踏步，视觉上更整齐稳重。", frame_range=(0, 3)),
            segment("beat-10-military-mech-arm", "58号右勾拳2.rob", "以右勾拳前四帧重复两次，形成整齐的机械臂节奏。", repeat=2, frame_range=(0, 4)),
            segment("beat-11-grand-chapter", "48号介绍动作.rob", "继续用介绍动作托举感替代大开大合的危险段。", frame_range=(0, 3)),
            segment("beat-12-spring-breeze", "53号左弯勾拳2.rob", "取左弯勾拳前两帧做轻量过渡，避免扭腰类下半身参与。", frame_range=(0, 2)),
            segment("beat-13-teach-skill", "27号伸右手.rob", "双次伸手作为授艺和指向动作，适合队列统一完成。", repeat=2),
            segment("beat-14-raise-talent", "48号介绍动作.rob", "以托举式开合表现育人主题，继续维持庄重气质。", frame_range=(0, 3)),
            segment("beat-15-high-spirit", "62号捶胸.rob", "捶胸前十四帧构成主歌第一个强拍口号段。", frame_range=(0, 14)),
            segment("beat-16-chase-wind", "27号伸右手.rob", "用单拍伸手做追风意象，避免原地扭腰。", frame_range=(0, 1)),
            segment("beat-17-break-wave", "48号介绍动作.rob", "短托举作为进入副歌前的大定格。", frame_range=(0, 3)),
            segment("beat-18-fujian-gongxiao-a", "62号捶胸.rob", "保留校名核心捶胸段，增强多人齐喊口号的同步感。", frame_range=(0, 14)),
            segment("beat-19-elite-hall-a", "48号介绍动作.rob", "托举姿态承接精英殿堂意象。", frame_range=(0, 3)),
            segment("beat-20-fujian-gongxiao-b", "62号捶胸.rob", "截取后半段捶胸变体，做副歌第二轮口号。", frame_range=(10, 20)),
            segment("beat-21-peach-fragrance-a", "26号抱娃娃.rob", "用胸前收放表现桃李芬芳，保留圆润的群舞气质。"),
            segment("beat-22-school-name-core", "62号捶胸.rob", "再次回到校名核心强拍，继续用近身动作保证稳定。", frame_range=(0, 14)),
            segment("beat-23-elite-hall-repeat", "48号介绍动作.rob", "重复托举段，强化副歌的整齐定格。", frame_range=(0, 3)),
            segment("beat-24-unity-diligence", "58号右勾拳2.rob", "短拳法节拍替代脚步节奏，保持团结勤奋的力度。", frame_range=(0, 4)),
            segment("beat-25-self-strength", "62号捶胸.rob", "自强不息仍用捶胸口号段承载。", frame_range=(0, 14)),
            segment("beat-26-truth-innovation", "27号伸右手.rob", "双次伸手保持上肢指向感，表达求实创新。", repeat=2),
            segment("beat-27-sing-aloud", "9号挥手.rob", "用挥手的大弧线做歌唱式打开。"),
            segment("beat-28-school-name-big", "62号捶胸.rob", "更完整的捶胸段做大一轮口号高潮。", frame_range=(0, 14)),
            segment("beat-29-peach-repeat", "26号抱娃娃.rob", "桃李芬芳母题回归，给副歌一段柔化收束。"),
            segment("beat-30-torch-passing", "9号挥手.rob", "挥手延续薪火相传的递送感。"),
            segment("ending-close-settle", "9号挥手.rob", "取挥手前两帧做最终缓收，然后交给保护段回正。", frame_range=(0, 2)),
        ],
    }
    SPEC_OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_output(path):
    envelope, result = audit_plain_file(path, actions_dir=ACTION_DIR, ignore_paths=[path])
    print("audit_target={}".format(path.name))
    print("reference_files={}".format(envelope.reference_files))
    print("reference_frames={}".format(envelope.reference_frames))
    print("target_max_l1={}".format(result["max_l1"]))
    print("violations={}".format(len(result["violations"])))
    if result["violations"]:
        for item in result["violations"]:
            print(item)
        raise SystemExit(1)


def main():
    build_spec()
    print("build_spec={}".format(SPEC_OUT.name))
    build_workflow(SPEC_OUT, actions_dir=ACTION_DIR)
    audit_output(ROB_OUT)


if __name__ == "__main__":
    main()
