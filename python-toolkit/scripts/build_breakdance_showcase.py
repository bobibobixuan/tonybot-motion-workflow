import json
import pathlib

from dance_workflow import build_workflow
from rob_safety import audit_plain_file


WORKSPACE = pathlib.Path(__file__).resolve().parent
SPEC_OUT = WORKSPACE / "编舞" / "170号霹雳舞炫技版.json"
ROB_OUT = WORKSPACE / "动作" / "170号霹雳舞炫技版.rob"
ACTION_DIR = WORKSPACE / "动作"


def build_spec():
    spec = {
        "name": "170号霹雳舞炫技版",
        "prompt": "单机炫技展示版霹雳舞。目标是视觉冲击强，融合街舞、拳击、侧踢、下蹲拳、俯卧撑、仰卧起坐等高动态动作，做出接近翻腾和地板炫技的观感。注意：不凭空手写未验证翻跟头轨迹，只使用官方或已审计模块做安全近似。",
        "research": {
            "query": "Tonybot 霹雳舞 炫技 地板动作 单机视觉冲击",
            "summary": [
                "这版是单机炫技，不追求队列稳定，重点是视觉效果和动作强度。",
                "由于当前仓库没有已验证的真翻跟头动作，不能安全硬写空翻轨迹，因此用街舞、地板、下蹲拳、侧踢、俯卧撑、仰卧起坐等动作做高冲击近似。",
                "整体结构按街舞亮相 -> 拳腿爆发 -> 地板炫技 -> 强势起身 -> 结尾定格来设计。"
            ],
            "references": []
        },
        "visualization": {
            "title": "170号霹雳舞炫技版时间线",
            "theme": "sunset"
        },
        "output": {
            "rob": "动作/170号霹雳舞炫技版.rob",
            "report_json": "编舞/170号霹雳舞炫技版.report.json",
            "visualization_html": "编舞/170号霹雳舞炫技版.timeline.html"
        },
        "guards": {
            "pre_segments": [
                {
                    "label": "pre-quick-recenter",
                    "source": "302号快速回正.rob",
                    "notes": "开场前回正。"
                },
                {
                    "label": "pre-stand-settle",
                    "source": "0号立正.rob",
                    "notes": "从稳定站姿起舞。"
                }
            ],
            "post_segments": [
                {
                    "label": "post-quick-recenter",
                    "source": "302号快速回正.rob",
                    "notes": "收尾回正。"
                },
                {
                    "label": "post-stand-settle",
                    "source": "0号立正.rob",
                    "notes": "结束稳定站姿。"
                }
            ]
        },
        "segments": [
            {
                "label": "intro-show",
                "source": "333号街舞片段.rob",
                "frame_range": [0, 18],
                "notes": "先用街舞片段亮相，直接拉高街头感。"
            },
            {
                "label": "hook-burst",
                "source": "319号左右勾拳组合.rob",
                "repeat": 2,
                "notes": "双轮勾拳爆发，制造霹雳舞 battle 开场压迫感。"
            },
            {
                "label": "wing-chun-rush",
                "source": "324号咏春拳.rob",
                "notes": "连续快手近身输出，像切拍和卡点。"
            },
            {
                "label": "left-kick-hit",
                "source": "314号左侧踢.rob",
                "notes": "左侧踢拉出高位视觉冲击。"
            },
            {
                "label": "right-kick-hit",
                "source": "315号右侧踢.rob",
                "notes": "右侧踢补全对称冲击。"
            },
            {
                "label": "squat-punch-low",
                "source": "323号下蹲拳.rob",
                "notes": "快速下沉出拳，做低位炫技感。"
            },
            {
                "label": "push-up-floor",
                "source": "331号俯卧撑短句.rob",
                "notes": "地板俯卧撑片段，模拟 break floor move。"
            },
            {
                "label": "sit-up-floor",
                "source": "332号仰卧起坐短句.rob",
                "notes": "仰卧起坐作为地板翻身/起身观感的近似。"
            },
            {
                "label": "street-dance-reload",
                "source": "333号街舞片段.rob",
                "frame_range": [18, 36],
                "notes": "第二段街舞片段拉回站立高能状态。"
            },
            {
                "label": "alternating-punch",
                "source": "370号手写左右交替拳.rob",
                "repeat": 2,
                "notes": "交替拳做最后一轮密集卡点。"
            },
            {
                "label": "power-hit",
                "source": "325号捶胸强调.rob",
                "repeat": 2,
                "notes": "重击收束，像 battle 胜利定点。"
            },
            {
                "label": "final-freeze",
                "source": "305号展示姿态.rob",
                "notes": "用大开合定格作为终止 freeze。"
            },
            {
                "label": "ending-bow",
                "source": "303号礼貌鞠躬.rob",
                "notes": "炫技结束后致意。"
            },
            {
                "label": "ending-recover",
                "source": "386号手写礼后回正.rob",
                "notes": "礼后回正。"
            }
        ]
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
