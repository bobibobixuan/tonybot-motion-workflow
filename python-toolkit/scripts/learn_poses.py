"""学习官方动作库 v2: 排除生成文件，提取可复用的安全姿态"""
from rob_reverse import parse_file, parse_plain_frame
from collections import defaultdict
import pathlib

actions_dir = pathlib.Path("动作")
rob_files = sorted(actions_dir.glob("*.rob"))

# 只分析官方动作（有编号的），排除 EYPT 和生成文件
plain_files = []
for f in rob_files:
    raw = f.read_bytes()
    if raw[8:12] == b'EYPT':
        continue
    name = f.stem
    # 排除生成/原创文件
    if '原创' in name or 'v2' in name:
        continue
    plain_files.append(f)

print(f"官方明文动作: {len(plain_files)} 个")

# 收集关节数据
all_poses = []
all_joint_values = defaultdict(list)
stable_poses = []  # 双腿着地 + 上半身有变化的帧

for f in plain_files:
    try:
        r = parse_file(str(f))
    except:
        continue
    for i, fb in enumerate(r['frames']):
        pf = parse_plain_frame(fb)
        pose = [c[0] for c in pf['channels'][:16]]
        dur = pf['duration']
        for ch, val in enumerate(pose):
            all_joint_values[ch].append(val)
        all_poses.append((f.stem, i, dur, pose))
        
        # 双腿稳定: 膝盖和髋接近立正，双脚不位移
        # ID3≈500, ID4≈593, ID11≈500, ID12≈406
        r_knee_d = abs(pose[2] - 500)
        r_hip_d = abs(pose[3] - 593)
        l_knee_d = abs(pose[10] - 500)
        l_hip_d = abs(pose[11] - 406)
        leg_stable = (r_knee_d < 100 and r_hip_d < 100 and l_knee_d < 100 and l_hip_d < 100)
        
        if leg_stable:
            # 计算上肢偏离度
            arm_dev = abs(pose[7]-724) + abs(pose[6]-800) + abs(pose[14]-200) + abs(pose[15]-275)
            stable_poses.append((f.stem, i, dur, pose, arm_dev))

print(f"双腿稳定帧: {len(stable_poses)} / {len(all_poses)}")

# === 关节安全范围 ===
print("\n=== 16关节 P5-P95 安全区间 ===")
print(f"{'舵机':>5} {'P5':>5} {'P50':>6} {'P95':>5} | 立正")
for ch in range(16):
    vals = sorted(all_joint_values[ch])
    p5 = vals[len(vals)//20]
    p50 = vals[len(vals)//2]
    p95 = vals[len(vals)*19//20]
    stand_vals = [500,387,500,593,500,575,800,724,500,612,500,406,500,425,200,275]
    print(f"ID{ch+1:>2}: {p5:>5} {p50:>6} {p95:>5} | {stand_vals[ch]:>4}")

# === 上肢聚类：找代表性的双臂姿态 ===
# 按 ID8(右肩上) + ID16(左肩上) 二维聚类
print("\n=== 双腿稳定时的典型上肢姿态（按肩关节展开度分组）===")

stable_poses.sort(key=lambda x: x[4])  # 按 arm_dev 排序

# 近身组: arm_dev < 200
close_arms = [p for p in stable_poses if p[4] < 200]
if close_arms:
    # 找不同来源的
    seen = set()
    print("\n【近身姿态】双臂贴近身体:")
    for name, idx, dur, pose, dev in close_arms:
        if name not in seen and len(seen) < 6:
            seen.add(name)
            print(f"  {name} f{idx}: ID7={pose[6]:>4} ID8={pose[7]:>4} ID15={pose[14]:>4} ID16={pose[15]:>4} dur={dur}ms")

# 展开组: arm_dev > 500
wide_arms = [p for p in stable_poses if p[4] > 500]
if wide_arms:
    seen = set()
    print("\n【大开姿态】双臂远离身体:")
    for name, idx, dur, pose, dev in wide_arms:
        if name not in seen and len(seen) < 6:
            seen.add(name)
            print(f"  {name} f{idx}: ID7={pose[6]:>4} ID8={pose[7]:>4} ID15={pose[14]:>4} ID16={pose[15]:>4} dur={dur}ms")

# 中等组
mid_poses = [p for p in stable_poses if 200 <= p[4] <= 500]
if mid_poses:
    seen = set()
    print("\n【中等姿态】:")
    for name, idx, dur, pose, dev in mid_poses:
        if name not in seen and len(seen) < 6:
            seen.add(name)
            print(f"  {name} f{idx}: ID7={pose[6]:>4} ID8={pose[7]:>4} ID15={pose[14]:>4} ID16={pose[15]:>4} dur={dur}ms")

# === 关键军事姿态的官方参考 ===
print("\n=== 军事相关姿态的官方参考值 ===")

# 找捶胸、拳击、展臂的关键帧
military_actions = {
    '捶胸_收拳': None,
    '捶胸_展开': None,
    '左拳_冲出': None,
    '右拳_冲出': None,
    '展臂_大开': None,
    '伸手_前指': None,
    '抱物_合胸': None,
}

for name, idx, dur, pose in all_poses:
    # 62号捶胸
    if name == '62号捶胸':
        if abs(pose[7] - 232) < 50:  # 双臂收胸
            military_actions['捶胸_收拳'] = (name, idx, dur, pose)
        if abs(pose[7] - 299) < 50 and abs(pose[15] - 700) < 50:
            military_actions['捶胸_展开'] = (name, idx, dur, pose)
    # 57号左勾拳
    if name == '57号左勾拳2' and idx == 2:
        military_actions['左拳_冲出'] = (name, idx, dur, pose)
    # 58号右勾拳
    if name == '58号右勾拳2' and idx == 2:
        military_actions['右拳_冲出'] = (name, idx, dur, pose)
    # 27号伸右手
    if name == '27号伸右手' and idx == 1:
        military_actions['伸手_前指'] = (name, idx, dur, pose)
    # 26号抱娃娃
    if name == '26号抱娃娃' and idx == 1:
        military_actions['抱物_合胸'] = (name, idx, dur, pose)

# 找最展开的双臂姿态
max_spread = 0
for name, idx, dur, pose in all_poses:
    r_knee_d = abs(pose[2] - 500)
    r_hip_d = abs(pose[3] - 593)
    l_knee_d = abs(pose[10] - 500)
    l_hip_d = abs(pose[11] - 406)
    if r_knee_d < 150 and r_hip_d < 150 and l_knee_d < 150 and l_hip_d < 150:
        spread = abs(pose[7] - 724) + abs(pose[15] - 275)
        if spread > max_spread:
            max_spread = spread
            military_actions['展臂_大开'] = (name, idx, dur, pose)

for label, data in military_actions.items():
    if data:
        name, idx, dur, pose = data
        print(f"\n{label}: {name} f{idx} dur={dur}ms")
        print(f"  全身: {pose}")
        # 标注变化关节
        stand = [500,387,500,593,500,575,800,724,500,612,500,406,500,425,200,275]
        changes = []
        for ch in range(16):
            if abs(pose[ch] - stand[ch]) > 30:
                direction = '↑' if pose[ch] > stand[ch] else '↓'
                changes.append(f"ID{ch+1}:{stand[ch]}→{pose[ch]}{direction}")
        print(f"  变化: {', '.join(changes)}")

# === 安全间距建议 ===
print("\n" + "="*60)
print("多机队列安全间距模拟（肩宽+手臂不碰）")
print("="*60)
# 计算握手/展臂动作的最大横向展开
max_arm_width = 0
for name, idx, dur, pose in all_poses:
    # 用 ID7 + ID15 估计横向宽度
    width = abs(pose[6] - pose[14])  # 右肩下 vs 左肩下
    if width > max_arm_width:
        max_arm_width = width
        max_arm_pose = (name, idx, pose)
print(f"最大横向展开: {max_arm_width} ({max_arm_pose[0]} f{max_arm_pose[1]})")
