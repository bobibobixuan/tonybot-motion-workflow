"""生成 正步高抬腿v2（大鹏展翅式平衡策略）"""
from rob_compose import (
    detect_actions_dir, normalize_segment, collect_frames, build_output_bytes
)
import pathlib

actions_dir = detect_actions_dir()

# 策略：先双腿微蹲降重心 → 右腿抬+左腿深蹲+双臂前压 → 定格 → 回落
frames_data = [
    # 帧1: 立正
    {"duration": 200, "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275]},

    # 帧2: 双腿微蹲降重心（学大鹏展翅）
    {"duration": 150, "pose": [500, 420, 550, 550, 500, 575, 800, 724, 500, 560, 580, 380, 500, 425, 200, 275]},

    # 帧3: 双臂前伸压重心 + 左腿深蹲 + 右腿开始抬
    {"duration": 150, "pose": [500, 370, 500, 680, 500, 575, 700, 450, 500, 500, 650, 350, 500, 425, 280, 550]},

    # 帧4: 右腿抬高定格 + 双臂最大前伸 + 左腿深蹲支撑
    {"duration": 300, "pose": [500, 340, 500, 720, 500, 575, 650, 380, 500, 480, 680, 340, 500, 425, 310, 600]},

    # 帧5: 开始回落
    {"duration": 150, "pose": [500, 370, 500, 680, 500, 575, 700, 450, 500, 500, 650, 350, 500, 425, 280, 550]},

    # 帧6: 双腿微蹲缓冲
    {"duration": 150, "pose": [500, 420, 550, 550, 500, 575, 800, 724, 500, 560, 580, 380, 500, 425, 200, 275]},

    # 帧7: 回立正
    {"duration": 200, "pose": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275]},
]

recipe = [
    normalize_segment({"label": "goose-step-v2", "frames": frames_data}, actions_dir),
]

frames, manifest = collect_frames(recipe)
output_bytes = build_output_bytes(frames)

out_path = pathlib.Path("动作/正步高抬腿v2_原创.rob")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_bytes(output_bytes)

total_ms = sum(f["duration"] for f in frames_data)
print(f"输出: {out_path}")
print(f"帧数: {len(frames)}")
print(f"总时长: {total_ms} ms")
print()
print("v2 相比 v1 的改进:")
print("  帧2 新增: 双腿弯膝降重心 (ID3→550, ID11→580)")
print("  帧3-4 新增: 双臂前伸压重心 (ID8 724→380, ID16 275→600)")
print("  帧3-4 新增: 左腿深蹲支撑 (ID11 500→680)")
print("  帧3-4 调整: 右腿抬得略低 (ID4→720 vs v1的730)")
