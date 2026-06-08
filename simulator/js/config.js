export const SEGMENTS = {
  upper_leg: { length: 6.0, mass: 0.12 },
  lower_leg: { length: 5.5, mass: 0.08 },
  foot: { length: 2.0, mass: 0.03 },
  torso: { length: 8.0, mass: 0.30 },
  upper_arm: { length: 5.0, mass: 0.06 },
  forearm: { length: 4.0, mass: 0.04 },
  hand: { length: 1.5, mass: 0.01 },
};

export const SERVO_NEUTRAL = {
  r_hip_yaw: 500,
  r_ankle_axis: 387,
  r_knee: 500,
  r_hip_pitch: 593,
  r_hip_roll: 500,
  r_elbow: 575,
  r_shoulder_axis_2: 800,
  r_shoulder_pitch: 724,
  l_hip_yaw: 500,
  l_ankle_axis: 612,
  l_knee: 500,
  l_hip_pitch: 406,
  l_hip_roll: 500,
  l_elbow: 425,
  l_shoulder_axis_2: 200,
  l_shoulder_pitch: 275,
};

export const SERVO_DIRECTION = {
  r_hip_yaw: +1,
  r_ankle_axis: -1,
  r_knee: -1,
  r_hip_pitch: +1,
  r_hip_roll: +1,
  r_elbow: +1,
  r_shoulder_axis_2: -1,
  r_shoulder_pitch: -1,
  l_hip_yaw: +1,
  l_ankle_axis: +1,
  l_knee: +1,
  l_hip_pitch: -1,
  l_hip_roll: +1,
  l_elbow: +1,
  l_shoulder_axis_2: +1,
  l_shoulder_pitch: +1,
};

export const CHANNEL_TO_JOINT = {
  0: "r_hip_yaw",
  1: "r_ankle_axis",
  2: "r_knee",
  3: "r_hip_pitch",
  4: "r_hip_roll",
  5: "r_elbow",
  6: "r_shoulder_axis_2",
  7: "r_shoulder_pitch",
  8: "l_hip_yaw",
  9: "l_ankle_axis",
  10: "l_knee",
  11: "l_hip_pitch",
  12: "l_hip_roll",
  13: "l_elbow",
  14: "l_shoulder_axis_2",
  15: "l_shoulder_pitch",
};

export const CHANNEL_LABELS = {
  0: "ID1 r_hip_yaw",
  1: "ID2 r_ankle_axis",
  2: "ID3 r_knee",
  3: "ID4 r_hip_pitch",
  4: "ID5 r_hip_roll",
  5: "ID6 r_elbow",
  6: "ID7 r_shoulder_axis_2",
  7: "ID8 r_shoulder_pitch",
  8: "ID9 l_hip_yaw",
  9: "ID10 l_ankle_axis",
  10: "ID11 l_knee",
  11: "ID12 l_hip_pitch",
  12: "ID13 l_hip_roll",
  13: "ID14 l_elbow",
  14: "ID15 l_shoulder_axis_2",
  15: "ID16 l_shoulder_pitch",
};

export const SLIDER_GROUPS = [
  { titleKey: "group_r_arm", cls: "group-r", channels: [7, 6, 5] },
  { titleKey: "group_l_arm", cls: "group-l", channels: [15, 14, 13] },
  { titleKey: "group_r_leg", cls: "group-r", channels: [3, 2, 1] },
  { titleKey: "group_l_leg", cls: "group-l", channels: [11, 10, 9] },
  { titleKey: "group_unused", cls: "group-u", channels: [0, 4, 8, 12] },
];

export const PRESET_I18N_KEYS = {
  "立正": "preset_lizheng",
  "军礼": "preset_junli",
  "展臂": "preset_zhanbi",
  "捶胸": "preset_chuixiong",
  "正步": "preset_zhengbu",
  "伸手": "preset_shenshou",
  "大鹏展翅": "preset_dapeng",
};

export const PRESETS = {
  "立正": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
  "军礼": [500, 387, 500, 593, 500, 1000, 640, 0, 500, 612, 500, 406, 500, 425, 200, 275],
  "展臂": [500, 395, 500, 593, 500, 500, 500, 0, 500, 605, 500, 406, 500, 500, 500, 1000],
  "捶胸": [537, 500, 303, 500, 537, 875, 741, 218, 462, 500, 696, 500, 462, 125, 258, 781],
  "正步": [500, 340, 500, 720, 500, 575, 650, 380, 500, 480, 680, 340, 500, 425, 310, 600],
  "伸手": [500, 388, 500, 594, 500, 575, 800, 725, 500, 612, 500, 406, 500, 500, 125, 669],
  "大鹏展翅": [500, 596, 539, 421, 522, 404, 395, 612, 556, 500, 696, 395, 500, 587, 622, 387],
};

export const BACKWARD_TEST_FRAMES = [
  [524, 411, 569, 683, 524, 537, 837, 837, 524, 683, 430, 411, 524, 462, 162, 387],
  [527, 362, 689, 730, 527, 537, 837, 837, 524, 683, 430, 440, 524, 462, 162, 387],
  [527, 296, 703, 680, 527, 537, 837, 725, 524, 642, 416, 370, 524, 462, 162, 274],
  [527, 244, 689, 636, 527, 537, 837, 612, 524, 588, 430, 316, 524, 462, 162, 162],
  [500, 312, 576, 591, 500, 537, 837, 612, 500, 591, 422, 312, 500, 462, 162, 162],
  [474, 316, 569, 588, 474, 537, 837, 612, 474, 588, 430, 316, 474, 462, 162, 162],
  [474, 316, 569, 580, 474, 537, 837, 612, 471, 636, 309, 260, 471, 462, 162, 162],
  [474, 356, 583, 642, 474, 537, 837, 725, 471, 702, 296, 296, 471, 462, 162, 274],
  [474, 411, 569, 683, 474, 537, 837, 837, 471, 755, 309, 362, 471, 462, 162, 387],
  [500, 408, 576, 687, 500, 537, 837, 837, 500, 687, 422, 408, 500, 462, 162, 387],
];

export const DEFAULT_POSE = PRESETS["立正"];
export const FOOT_PLATE = { halfLength: 1.75, halfWidth: 0.78, thickness: 0.32 };
export const FOOT_CENTER_FORWARD = SEGMENTS.foot.length * 0.5;
export const HIP_HALF_WIDTH = 1.5;
export const SHOULDER_HALF_WIDTH = 2.5;
export const HIP_BASE_HEIGHT = SEGMENTS.upper_leg.length + SEGMENTS.lower_leg.length + FOOT_PLATE.thickness;

export function getChannelGroup(ch) {
  if (ch >= 5 && ch <= 7) return "r";
  if (ch >= 13 && ch <= 15) return "l";
  if (ch >= 0 && ch <= 4) return "r";
  if (ch >= 8 && ch <= 12) return "l";
  return "u";
}

export function formatServoAngle(ch, value) {
  const jointName = CHANNEL_TO_JOINT[ch];
  if (!jointName) return "";
  const neutral = SERVO_NEUTRAL[jointName] ?? 500;
  const direction = SERVO_DIRECTION[jointName] ?? 1;
  const deg = (value - neutral) * direction / 1000 * 180;
  const sign = deg > 0 ? "+" : "";
  return `${sign}${deg.toFixed(0)}°`;
}

export function poseToJointAngles(pose) {
  const angles = {};
  for (const [channelIndex, jointName] of Object.entries(CHANNEL_TO_JOINT)) {
    const neutral = SERVO_NEUTRAL[jointName];
    const direction = SERVO_DIRECTION[jointName];
    const delta = (pose[parseInt(channelIndex, 10)] - neutral) * direction;
    angles[jointName] = delta / 1000.0 * Math.PI;
  }
  return angles;
}
