"""
Tonybot 物理模拟器 — 基于 16 舵机的简化运动学模型
用于预测姿态重心、支撑多边形、平衡得分
"""
import math
import json
import pathlib
from collections import defaultdict

# ============================================================
# 机器人几何参数（估计值，基于 ≈30cm 双足机器人）
# ============================================================

# 舵机值 → 弧度：value/1000 * π（假设 0-1000 映射 0-180°）
def servo_to_rad(value):
    return (value / 1000.0) * math.pi

# 各体段长度 (cm) 和质量 (相对单位)
SEGMENTS = {
    # 下肢
    "upper_leg":  {"length": 6.0, "mass": 0.12},   # 大腿
    "lower_leg":  {"length": 5.5, "mass": 0.08},   # 小腿
    "foot":       {"length": 2.0, "mass": 0.03},   # 脚
    # 躯干
    "torso":      {"length": 8.0, "mass": 0.30},   # 躯干（含头）
    # 上肢
    "upper_arm":  {"length": 5.0, "mass": 0.06},   # 大臂
    "forearm":    {"length": 4.0, "mass": 0.04},   # 前臂
    "hand":       {"length": 1.5, "mass": 0.01},   # 手
}

# 关节轴方向：正角度对应的世界坐标方向
# +X = 前, +Y = 左, +Z = 上
# 对于 pitch 关节(前/后)：正角度 = 向前
# 对于 roll 关节(内/外)：正角度 = 向外

# 中立位（0 rad 偏置）时各关节的默认角度
# 这些是 servo=500 时对应的关节角度（radians from neutral）
JOINT_NEUTRAL = {
    # 右腿
    "r_hip_pitch":    0.0,    # ID4: 髋前后，正=前
    "r_knee":         0.0,    # ID3: 膝，正=后弯
    "r_ankle":        0.0,    # ID2: 踝俯仰，正=脚掌前后倾斜
    # 左腿
    "l_hip_pitch":    0.0,    # ID12: 髋前后，正=前 (注意 ID12 减小=前)
    "l_knee":         0.0,    # ID11: 膝，正=后弯 (注意 ID11 减小=弯)
    "l_ankle":        0.0,    # ID10: 踝俯仰，正=脚掌前后倾斜
    # 右臂
    "r_shoulder_pitch": 0.0,  # ID8: 肩前后，正=前 (ID8 减小=前)
    "r_shoulder_roll":  0.0,  # ID7: 肩内外，正=外展 (ID7 减小=外展)
    "r_elbow":          0.0,  # ID6: 肘，正=弯 (ID6 增大=弯)
    # 左臂
    "l_shoulder_pitch": 0.0,  # ID16: 肩前后，正=前 (ID16 增大=前)
    "l_shoulder_roll":  0.0,  # ID15: 肩内外，正=外展 (ID15 增大=外展)
    "l_elbow":          0.0,  # ID14: 肘，正=弯 (ID14 增大=弯)
}

# 关节中立对应的舵机值
SERVO_NEUTRAL = {
    "r_hip_pitch":    593,   # ID4
    "r_knee":         500,   # ID3
    "r_ankle":        387,   # ID2
    "l_hip_pitch":    406,   # ID12
    "l_knee":         500,   # ID11
    "l_ankle":        612,   # ID10
    "r_shoulder_pitch": 724, # ID8
    "r_shoulder_roll":  800, # ID7
    "r_elbow":          575, # ID6
    "l_shoulder_pitch": 275, # ID16
    "l_shoulder_roll":  200, # ID15
    "l_elbow":          425, # ID14
}

# 舵机方向系数：+1 = 增大舵机值 → 增大关节角，-1 = 反向
SERVO_DIRECTION = {
    "r_hip_pitch":    +1,   # ID4↑ = 腿前抬
    "r_knee":         -1,   # ID3↑ = 膝后弯
    "r_ankle":        -1,   # ID2 与右踝俯仰同向，脚尖上翘/下压细节按真机微调
    "l_hip_pitch":    -1,   # ID12↓ = 腿前抬  
    "l_knee":         +1,   # ID11↓ = 弯；此处方向系数按 pose_to_joint_angles 的正向定义保留
    "l_ankle":        +1,   # ID10 与左踝俯仰同向，脚尖上翘/下压细节按真机微调
    "r_shoulder_pitch": -1, # ID8↓ = 臂前抬
    "r_shoulder_roll":  -1, # ID7↓ = 臂外展
    "r_elbow":         +1,  # ID6↑ = 肘弯
    "l_shoulder_pitch": +1, # ID16↑ = 臂前抬
    "l_shoulder_roll":  +1, # ID15↑ = 臂外展
    "l_elbow":         +1,  # ID14↑ = 肘弯
}


def pose_to_joint_angles(pose):
    """将 16 个舵机值转换为关节弧度
    
    pose: [ID1..ID16] 共 16 个值
    返回: dict of joint_name -> radians
    """
    servo_map = {
        3: "r_knee",           # ID4=593 实际是 r_hip_pitch
        2: "r_ankle",
        10: "l_knee",
        11: "l_hip_pitch",
        9: "l_ankle",
        7: "r_shoulder_pitch",
        6: "r_shoulder_roll",
        5: "r_elbow",
        15: "l_shoulder_pitch",
        14: "l_shoulder_roll",
        13: "l_elbow",
    }
    # ID4→r_hip_pitch, ID3→r_knee, ID2→r_ankle
    # ID12→l_hip_pitch, ID11→l_knee, ID10→l_ankle
    # ID8→r_shoulder_pitch, ID7→r_shoulder_roll, ID6→r_elbow
    # ID16→l_shoulder_pitch, ID15→l_shoulder_roll, ID14→l_elbow
    
    # 重新映射 (0-based index → servo ID)
    mapping = {
        3: "r_hip_pitch",    # ID4
        2: "r_knee",         # ID3
        1: "r_ankle",        # ID2
        11: "l_hip_pitch",   # ID12
        10: "l_knee",        # ID11
        9: "l_ankle",        # ID10
        7: "r_shoulder_pitch", # ID8
        6: "r_shoulder_roll",  # ID7
        5: "r_elbow",          # ID6
        15: "l_shoulder_pitch",# ID16
        14: "l_shoulder_roll", # ID15
        13: "l_elbow",         # ID14
    }
    
    angles = {}
    for ch_idx, joint_name in mapping.items():
        neutral = SERVO_NEUTRAL[joint_name]
        direction = SERVO_DIRECTION[joint_name]
        delta = (pose[ch_idx] - neutral) * direction
        rad = delta / 1000.0 * math.pi
        angles[joint_name] = rad
    
    return angles


def vec3(x, y, z):
    return [x, y, z]


def rotate_y(v, angle):
    """绕 Y 轴（上下）旋转 — pitch"""
    c, s = math.cos(angle), math.sin(angle)
    return [c*v[0] + s*v[2], v[1], -s*v[0] + c*v[2]]


def rotate_x(v, angle):
    """绕 X 轴（前后）旋转 — roll"""
    c, s = math.cos(angle), math.sin(angle)
    return [v[0], c*v[1] - s*v[2], s*v[1] + c*v[2]]


def rotate_z(v, angle):
    """绕 Z 轴（左右）旋转 — yaw"""
    c, s = math.cos(angle), math.sin(angle)
    return [c*v[0] - s*v[1], s*v[0] + c*v[1], v[2]]


def forward_kinematics(pose):
    """计算 16 个舵机值对应的各体段质心位置
    
    返回: {
        'com': [x, y, z],           # 总质心
        'support_left': [x, y],     # 左脚支撑点
        'support_right': [x, y],    # 右脚支撑点
        'segments': {name: [x,y,z]}, # 各段质心
        'balance': {...},           # 平衡指标
    }
    """
    angles = pose_to_joint_angles(pose)
    
    # 髋关节在世界坐标系的基准位置 (cm)
    hip_base = vec3(0, 0, 16.0)  # 髋在躯干底部
    
    # 脚间距
    foot_spacing = 3.0  # 双脚中心间距 cm
    
    # === 右腿 ===
    r_hip = vec3(0, -foot_spacing/2, hip_base[2])
    # 大腿: 从髋向下
    r_upper_leg_dir = vec3(0, 0, -1)  # 默认向下
    r_upper_leg_dir = rotate_y(r_upper_leg_dir, angles.get("r_hip_pitch", 0))
    r_knee = [r_hip[i] + r_upper_leg_dir[i] * SEGMENTS["upper_leg"]["length"] for i in range(3)]
    
    # 小腿: 从膝向下
    r_lower_leg_dir = vec3(0, 0, -1)
    r_lower_leg_dir = rotate_y(r_lower_leg_dir, angles.get("r_hip_pitch", 0) + angles.get("r_knee", 0))
    r_ankle = [r_knee[i] + r_lower_leg_dir[i] * SEGMENTS["lower_leg"]["length"] for i in range(3)]
    
    # 脚
    r_foot_dir = vec3(1, 0, 0)  # 默认向前
    r_foot_dir = rotate_y(r_foot_dir, angles.get("r_ankle", 0))
    r_foot = [r_ankle[i] + r_foot_dir[i] * SEGMENTS["foot"]["length"] * 0.5 for i in range(3)]
    
    # 质心
    r_upper_com = [(r_hip[i] + r_knee[i]) / 2 for i in range(3)]
    r_lower_com = [(r_knee[i] + r_ankle[i]) / 2 for i in range(3)]
    r_foot_com = r_foot
    
    # 右脚支撑点（踝关节投影到地面）
    r_support = [r_ankle[0], r_ankle[1]]
    
    # === 左腿 ===
    l_hip = vec3(0, foot_spacing/2, hip_base[2])
    l_upper_leg_dir = vec3(0, 0, -1)
    l_upper_leg_dir = rotate_y(l_upper_leg_dir, angles.get("l_hip_pitch", 0))
    l_knee = [l_hip[i] + l_upper_leg_dir[i] * SEGMENTS["upper_leg"]["length"] for i in range(3)]
    
    l_lower_leg_dir = vec3(0, 0, -1)
    l_lower_leg_dir = rotate_y(l_lower_leg_dir, angles.get("l_hip_pitch", 0) + angles.get("l_knee", 0))
    l_ankle = [l_knee[i] + l_lower_leg_dir[i] * SEGMENTS["lower_leg"]["length"] for i in range(3)]
    
    l_foot_dir = vec3(1, 0, 0)
    l_foot_dir = rotate_y(l_foot_dir, angles.get("l_ankle", 0))
    l_foot = [l_ankle[i] + l_foot_dir[i] * SEGMENTS["foot"]["length"] * 0.5 for i in range(3)]
    
    l_upper_com = [(l_hip[i] + l_knee[i]) / 2 for i in range(3)]
    l_lower_com = [(l_knee[i] + l_ankle[i]) / 2 for i in range(3)]
    l_foot_com = l_foot
    
    l_support = [l_ankle[0], l_ankle[1]]
    
    # === 躯干 ===
    torso_base = vec3(0, 0, hip_base[2])
    torso_top = vec3(0, 0, hip_base[2] + SEGMENTS["torso"]["length"])
    torso_com = [(torso_base[i] + torso_top[i]) / 2 for i in range(3)]
    
    # 肩基准位置
    shoulder_base = vec3(0, 0, torso_top[2])
    
    # === 右臂 ===
    r_shoulder_pos = vec3(0, -2.5, shoulder_base[2])
    r_upper_arm_dir = vec3(0, 0, -1)  # 默认向下
    r_upper_arm_dir = rotate_y(r_upper_arm_dir, angles.get("r_shoulder_pitch", 0))
    r_upper_arm_dir = rotate_x(r_upper_arm_dir, angles.get("r_shoulder_roll", 0))
    r_elbow_pos = [r_shoulder_pos[i] + r_upper_arm_dir[i] * SEGMENTS["upper_arm"]["length"] for i in range(3)]
    
    r_forearm_dir = vec3(0, 0, -1)
    r_forearm_dir = rotate_y(r_forearm_dir, angles.get("r_shoulder_pitch", 0) + angles.get("r_elbow", 0))
    r_forearm_dir = rotate_x(r_forearm_dir, angles.get("r_shoulder_roll", 0))
    r_hand_pos = [r_elbow_pos[i] + r_forearm_dir[i] * SEGMENTS["forearm"]["length"] for i in range(3)]
    
    r_upper_arm_com = [(r_shoulder_pos[i] + r_elbow_pos[i]) / 2 for i in range(3)]
    r_forearm_com = [(r_elbow_pos[i] + r_hand_pos[i]) / 2 for i in range(3)]
    r_hand_com = r_hand_pos
    
    # === 左臂 ===
    l_shoulder_pos = vec3(0, 2.5, shoulder_base[2])
    l_upper_arm_dir = vec3(0, 0, -1)
    l_upper_arm_dir = rotate_y(l_upper_arm_dir, angles.get("l_shoulder_pitch", 0))
    l_upper_arm_dir = rotate_x(l_upper_arm_dir, angles.get("l_shoulder_roll", 0))
    l_elbow_pos = [l_shoulder_pos[i] + l_upper_arm_dir[i] * SEGMENTS["upper_arm"]["length"] for i in range(3)]
    
    l_forearm_dir = vec3(0, 0, -1)
    l_forearm_dir = rotate_y(l_forearm_dir, angles.get("l_shoulder_pitch", 0) + angles.get("l_elbow", 0))
    l_forearm_dir = rotate_x(l_forearm_dir, angles.get("l_shoulder_roll", 0))
    l_hand_pos = [l_elbow_pos[i] + l_forearm_dir[i] * SEGMENTS["forearm"]["length"] for i in range(3)]
    
    l_upper_arm_com = [(l_shoulder_pos[i] + l_elbow_pos[i]) / 2 for i in range(3)]
    l_forearm_com = [(l_elbow_pos[i] + l_hand_pos[i]) / 2 for i in range(3)]
    l_hand_com = l_hand_pos
    
    # === 总质心 ===
    all_segments = [
        (torso_com,      SEGMENTS["torso"]["mass"]),
        (r_upper_com,    SEGMENTS["upper_leg"]["mass"]),
        (r_lower_com,    SEGMENTS["lower_leg"]["mass"]),
        (r_foot_com,     SEGMENTS["foot"]["mass"]),
        (l_upper_com,    SEGMENTS["upper_leg"]["mass"]),
        (l_lower_com,    SEGMENTS["lower_leg"]["mass"]),
        (l_foot_com,     SEGMENTS["foot"]["mass"]),
        (r_upper_arm_com, SEGMENTS["upper_arm"]["mass"]),
        (r_forearm_com,  SEGMENTS["forearm"]["mass"]),
        (r_hand_com,     SEGMENTS["hand"]["mass"]),
        (l_upper_arm_com, SEGMENTS["upper_arm"]["mass"]),
        (l_forearm_com,  SEGMENTS["forearm"]["mass"]),
        (l_hand_com,     SEGMENTS["hand"]["mass"]),
    ]
    
    total_mass = sum(m for _, m in all_segments)
    com = [0.0, 0.0, 0.0]
    for pos, mass in all_segments:
        for i in range(3):
            com[i] += pos[i] * mass
    com = [c / total_mass for c in com]
    
    # === 支撑多边形 ===
    # 每只脚简化为脚踝前后 ±2cm 的线
    support_polygon = [
        [r_support[0] - 1.5, r_support[1]],  # 右脚后
        [r_support[0] + 1.5, r_support[1]],  # 右脚前
        [l_support[0] + 1.5, l_support[1]],  # 左脚前
        [l_support[0] - 1.5, l_support[1]],  # 左脚后
    ]
    
    # === 平衡指标 ===
    # 质心投影到地面
    com_ground = [com[0], com[1]]
    
    # 支撑多边形中心
    poly_center = [
        sum(p[0] for p in support_polygon) / 4,
        sum(p[1] for p in support_polygon) / 4,
    ]
    
    # 质心偏离支撑中心的距离
    com_offset = math.sqrt(
        (com_ground[0] - poly_center[0])**2 + 
        (com_ground[1] - poly_center[1])**2
    )
    
    # 支撑多边形面积（简化：左右脚间距越大越稳定）
    support_width = abs(r_support[1] - l_support[1])
    support_length = 3.0  # 脚前后长度
    
    # 点到多边形最近边的距离（负值=在多边形内）
    min_dist = _point_to_polygon_dist(com_ground, support_polygon)
    
    # 平衡得分 0-100
    # 考虑: CoM高度、支撑面积、CoM偏离中心距离
    com_height = com[2]
    stability_margin = min_dist  # 稳定性裕度
    height_penalty = com_height / 16.0  # 越高越不稳
    
    # 综合得分 0-100
    # 基础分 100，各项扣分
    score = 100.0
    
    # 扣分1: 质心高度（越高越不稳，14cm 以下不扣）
    if com_height > 14:
        score -= (com_height - 14) * 8
    
    # 扣分2: 质心偏离支撑中心（偏移越大越不稳）
    score -= com_offset * 6
    
    # 扣分3: 质心接近支撑边界（stability_margin 负值=安全，正值=危险）
    if stability_margin > -1.0:  # 离边界不到 1cm
        score -= (stability_margin + 1.0) * 15
    if stability_margin > 0:  # 已经在边界外
        score -= 30
    
    # 奖励: 支撑宽度大（双脚分开更稳）
    if support_width > 4:
        score += min(10, (support_width - 4) * 3)
    
    balance_score = max(0, min(100, score))
    
    return {
        'com': com,
        'com_ground': com_ground,
        'com_height': com_height,
        'com_offset': com_offset,
        'support_polygon': support_polygon,
        'support_width': support_width,
        'stability_margin': stability_margin,
        'balance_score': round(balance_score, 1),
        'segments': {
            'r_hip': r_hip, 'r_knee': r_knee, 'r_ankle': r_ankle, 'r_foot': r_foot,
            'l_hip': l_hip, 'l_knee': l_knee, 'l_ankle': l_ankle, 'l_foot': l_foot,
            'torso_com': torso_com,
            'r_shoulder': r_shoulder_pos, 'r_elbow': r_elbow_pos, 'r_hand': r_hand_pos,
            'l_shoulder': l_shoulder_pos, 'l_elbow': l_elbow_pos, 'l_hand': l_hand_pos,
        }
    }


def _point_to_polygon_dist(point, polygon):
    """点到凸多边形边界的距离（内部为负值）"""
    min_dist = float('inf')
    n = len(polygon)
    for i in range(n):
        a = polygon[i]
        b = polygon[(i + 1) % n]
        # 边向量
        edge = [b[0] - a[0], b[1] - a[1]]
        edge_len = math.sqrt(edge[0]**2 + edge[1]**2)
        if edge_len < 0.001:
            continue
        edge_unit = [edge[0]/edge_len, edge[1]/edge_len]
        # 法向量（指向外侧）
        normal = [edge_unit[1], -edge_unit[0]]
        # 点到边的有向距离
        vec_to_point = [point[0] - a[0], point[1] - a[1]]
        dist = vec_to_point[0] * normal[0] + vec_to_point[1] * normal[1]
        min_dist = min(min_dist, dist)
    return min_dist


# ============================================================
# 批量分析
# ============================================================

def analyze_pose(pose, label=""):
    """分析单个姿态"""
    r = forward_kinematics(pose)
    print(f"\n{'='*50}")
    print(f"姿态: {label}")
    print(f"  质心: X={r['com'][0]:.1f} Y={r['com'][1]:.1f} Z={r['com'][2]:.1f} cm")
    print(f"  质心地面投影: ({r['com_ground'][0]:.1f}, {r['com_ground'][1]:.1f})")
    print(f"  支撑宽度: {r['support_width']:.1f} cm")
    print(f"  平衡得分: {r['balance_score']:.1f}/100")
    margin = r['stability_margin']
    if margin < -1.0:
        status_text = '✅深安全区'
    elif margin < 0:
        status_text = '🟡接近边界'
    elif margin < 1.0:
        status_text = '🟠危险'
    else:
        status_text = '❌超出支撑面'
    print(f"  稳定性裕度: {margin:.2f} cm ({status_text})")
    
    # 诊断
    issues = []
    if r['balance_score'] < 50:
        issues.append("🔴 严重失衡")
    elif r['balance_score'] < 75:
        issues.append("🟡 轻度不稳")
    else:
        issues.append("🟢 稳定")
    
    if r['com_offset'] > 3.0:
        issues.append(f"质心偏离中心 {r['com_offset']:.1f}cm")
    if r['com_height'] > 18:
        issues.append(f"重心偏高 {r['com_height']:.1f}cm")
    
    if len(issues) > 1:
        print(f"  诊断: {' | '.join(issues)}")
    
    return r


def compare_poses(poses_dict):
    """比较多组姿态"""
    print(f"\n{'='*60}")
    print(f"{'姿态':<20} {'平衡分':>6} {'CoM高':>6} {'偏移':>6} {'裕度':>6} {'判定'}")
    print(f"{'-'*20} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*10}")
    
    results = {}
    for label, pose in poses_dict.items():
        r = forward_kinematics(pose)
        results[label] = r
        status = '✅' if r['stability_margin'] < -1.0 else '🟡' if r['stability_margin'] < 0 else '🔴'
        print(f"{label:<20} {r['balance_score']:>6.1f} {r['com_height']:>6.1f} {r['com_offset']:>6.1f} {r['stability_margin']:>6.2f} {status:>10}")
    
    return results


# ============================================================
# 命令行接口
# ============================================================

def search_balance_improvement(base_pose, label, vary_specs):
    """搜索改进平衡的最佳关节值
    
    vary_specs: [(joint_idx, lo, hi, step), ...]
    """
    print(f"\n{'='*60}")
    print(f"搜索优化: {label}")
    print(f"{'='*60}")
    
    best_score = -1
    best_pose = None
    base_r = forward_kinematics(base_pose)
    
    # 网格搜索
    def search_recursive(current_pose, spec_idx):
        nonlocal best_score, best_pose
        if spec_idx >= len(vary_specs):
            r = forward_kinematics(current_pose)
            if r['balance_score'] > best_score:
                best_score = r['balance_score']
                best_pose = (list(current_pose), r)
            return
        
        joint_idx, lo, hi, step = vary_specs[spec_idx]
        for val in range(lo, hi + 1, step):
            current_pose[joint_idx] = val
            search_recursive(current_pose, spec_idx + 1)
            current_pose[joint_idx] = base_pose[joint_idx]  # restore
    
    search_recursive(list(base_pose), 0)
    
    if best_pose:
        pose, r = best_pose
        print(f"  最佳得分: {r['balance_score']:.1f} (原始: {base_r['balance_score']:.1f})")
        print(f"  提升: +{r['balance_score'] - base_r['balance_score']:.1f}")
        print(f"  CoM偏移: {r['com_offset']:.1f}cm | 裕度: {r['stability_margin']:.2f}cm")
        for joint_idx, lo, hi, step in vary_specs:
            print(f"  ID{joint_idx+1}: {base_pose[joint_idx]} → {pose[joint_idx]} (搜索范围 {lo}-{hi})")
    
    return best_pose


if __name__ == "__main__":
    # 立正
    stand = [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275]
    
    # 军礼
    salute = [500, 387, 500, 593, 500, 1000, 640, 0, 500, 612, 500, 406, 500, 425, 200, 275]
    
    # 正步高抬腿 v1
    goosestep_v1 = [500, 310, 500, 730, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275]
    
    # 正步高抬腿 v2
    goosestep_v2 = [500, 340, 500, 720, 500, 575, 650, 380, 500, 480, 680, 340, 500, 425, 310, 600]
    
    # 捶胸
    punch_chest = [537, 500, 303, 500, 537, 875, 741, 218, 462, 500, 696, 500, 462, 125, 258, 781]
    
    # 展臂
    wide_arms = [500, 395, 500, 593, 500, 500, 500, 0, 500, 605, 500, 406, 500, 500, 500, 1000]
    
    # 左拳
    left_punch = [600, 395, 500, 593, 544, 681, 826, 288, 447, 713, 372, 406, 431, 425, 310, 275]
    
    # 伸手
    point_hand = [500, 388, 500, 594, 500, 575, 800, 725, 500, 612, 500, 406, 500, 500, 125, 669]
    
    # 大鹏展翅
    eagle = [500, 596, 539, 421, 522, 404, 395, 612, 556, 500, 696, 395, 500, 587, 622, 387]
    
    print("Tonybot 物理模拟器 v1.0")
    print("="*60)
    print("注意：几何参数为估计值，用于相对比较而非绝对精度")
    
    compare_poses({
        "立正(stand)": stand,
        "军礼(salute)": salute,
        "正步v1(旧)": goosestep_v1,
        "正步v2(新)": goosestep_v2,
        "捶胸(62号)": punch_chest,
        "展臂(151号)": wide_arms,
        "左拳(57号)": left_punch,
        "伸手(27号)": point_hand,
        "大鹏展翅(17号)": eagle,
    })
    
    # === 搜索：展臂时微调膝盖降重心 ===
    print("\n\n🔍 展臂姿态优化：微调膝盖降重心")
    for knee_val in [450, 475, 500, 525, 550]:
        test = list(wide_arms)
        test[2] = knee_val   # ID3 右膝
        test[10] = knee_val  # ID11 左膝
        r = forward_kinematics(test)
        print(f"  双膝={knee_val}: 得分={r['balance_score']:.1f} CoM高={r['com_height']:.1f}cm")
