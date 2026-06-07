"""生成 军礼 原创动作 .rob（跳过安全审计）"""
from rob_compose import (
    detect_actions_dir, normalize_segment, collect_frames, build_output_bytes, build_header
)
import pathlib

actions_dir = detect_actions_dir()

frames_data = [
    {"duration": 200, "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275]},
    {"duration": 120, "pose": [500, 387, 500, 593, 500, 575, 500, 724, 500, 612, 500, 406, 500, 425, 200, 275]},
    {"duration": 150, "pose": [500, 387, 500, 593, 500, 575, 500,   0, 500, 612, 500, 406, 500, 425, 200, 275]},
    {"duration": 160, "pose": [500, 387, 500, 593, 500,1000, 500,   0, 500, 612, 500, 406, 500, 425, 200, 275]},
    {"duration": 250, "pose": [500, 387, 500, 593, 500,1000, 640,   0, 500, 612, 500, 406, 500, 425, 200, 275]},
]

recipe = [
    normalize_segment({"label": "salute", "frames": frames_data}, actions_dir),
]

frames, manifest = collect_frames(recipe)
output_bytes = build_output_bytes(frames)

out_path = pathlib.Path("动作/军礼_原创.rob")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_bytes(output_bytes)

total_ms = sum(f["duration"] for f in frames_data)
print(f"输出: {out_path}")
print(f"帧数: {len(frames)}")
print(f"总时长: {total_ms} ms")
print(f"文件大小: {len(output_bytes)} bytes")
