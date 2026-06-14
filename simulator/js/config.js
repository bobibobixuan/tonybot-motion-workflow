export const SEGMENTS = {
  upper_leg: { length: 6.0, mass: 0.12 },
  lower_leg: { length: 5.5, mass: 0.08 },
  foot: { length: 2.0, mass: 0.03 },
  torso: { length: 8.0, mass: 0.30 },
  upper_arm: { length: 5.0, mass: 0.06 },
  forearm: { length: 4.0, mass: 0.04 },
  hand: { length: 1.5, mass: 0.01 },
};

export const SERVO_LAYOUT = [
  {
    id: 1,
    channel: 0,
    joint: "r_hip_yaw",
    labelZh: "右髋旋转轴",
    labelEn: "right hip yaw",
    axisType: "yaw_vertical",
    neutral: 500,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "右腿及右脚尖发生旋转",
    motionZh: "控制右腿及右脚尖内旋、外旋",
    group: "r_leg",
    mirrorId: 9,
  },
  {
    id: 2,
    channel: 1,
    joint: "r_ankle",
    labelZh: "右踝俯仰轴",
    labelEn: "right ankle pitch",
    axisType: "pitch_lateral",
    neutral: 387,
    direction: -1,
    testedChange: "increase",
    testedMotionZh: "右踝前后角度改变",
    motionZh: "控制右脚掌前后倾斜，补偿身体前后重心",
    group: "r_leg",
    mirrorId: 10,
  },
  {
    id: 3,
    channel: 2,
    joint: "r_knee",
    labelZh: "右膝轴",
    labelEn: "right knee",
    axisType: "pitch_lateral",
    neutral: 500,
    direction: -1,
    testedChange: "increase",
    testedMotionZh: "右膝弯曲",
    motionZh: "控制右膝弯曲和伸直",
    group: "r_leg",
    mirrorId: 11,
  },
  {
    id: 4,
    channel: 3,
    joint: "r_hip_pitch",
    labelZh: "右髋前后轴",
    labelEn: "right hip pitch",
    axisType: "pitch_lateral",
    neutral: 593,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "右大腿向前抬",
    motionZh: "控制右大腿向前抬或向后摆",
    group: "r_leg",
    mirrorId: 12,
  },
  {
    id: 5,
    channel: 4,
    joint: "r_hip_roll",
    labelZh: "右髋侧摆轴",
    labelEn: "right hip roll",
    axisType: "roll_longitudinal",
    neutral: 500,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "右腿侧向展开、身体侧倾",
    motionZh: "控制右腿向外展开、向内收回，以及身体侧倾",
    group: "r_leg",
    mirrorId: 13,
  },
  {
    id: 6,
    channel: 5,
    joint: "l_elbow",
    labelZh: "左肘轴",
    labelEn: "left elbow",
    axisType: "pitch_lateral",
    neutral: 575,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "左肘弯曲",
    motionZh: "控制左小臂弯曲和伸直",
    group: "l_arm",
    mirrorId: 14,
  },
  {
    id: 7,
    channel: 6,
    joint: "l_shoulder_roll",
    labelZh: "左肩侧向轴",
    labelEn: "left shoulder roll",
    axisType: "roll_longitudinal",
    neutral: 800,
    direction: -1,
    testedChange: "decrease",
    testedMotionZh: "左臂侧向展开",
    motionZh: "控制左臂侧向展开、向身体收回",
    group: "l_arm",
    mirrorId: 15,
  },
  {
    id: 8,
    channel: 7,
    joint: "l_shoulder_pitch",
    labelZh: "左肩根部旋转轴",
    labelEn: "left shoulder root pitch",
    axisType: "pitch_lateral",
    neutral: 724,
    direction: -1,
    testedChange: "decrease",
    testedMotionZh: "左臂向前、向上旋转",
    motionZh: "控制整条左臂前后转动、上举和下放",
    group: "l_arm",
    mirrorId: 16,
  },
  {
    id: 9,
    channel: 8,
    joint: "l_hip_yaw",
    labelZh: "左髋旋转轴",
    labelEn: "left hip yaw",
    axisType: "yaw_vertical",
    neutral: 500,
    direction: +1,
    testedChange: "decrease",
    testedMotionZh: "左腿及左脚尖发生镜像旋转",
    motionZh: "控制左腿及左脚尖内旋、外旋",
    group: "l_leg",
    mirrorId: 1,
  },
  {
    id: 10,
    channel: 9,
    joint: "l_ankle",
    labelZh: "左踝俯仰轴",
    labelEn: "left ankle pitch",
    axisType: "pitch_lateral",
    neutral: 612,
    direction: +1,
    testedChange: "decrease",
    testedMotionZh: "左踝前后角度改变",
    motionZh: "控制左脚掌前后倾斜，补偿身体前后重心",
    group: "l_leg",
    mirrorId: 2,
  },
  {
    id: 11,
    channel: 10,
    joint: "l_knee",
    labelZh: "左膝轴",
    labelEn: "left knee",
    axisType: "pitch_lateral",
    neutral: 500,
    direction: +1,
    testedChange: "decrease",
    testedMotionZh: "左膝弯曲",
    motionZh: "控制左膝弯曲和伸直",
    group: "l_leg",
    mirrorId: 3,
  },
  {
    id: 12,
    channel: 11,
    joint: "l_hip_pitch",
    labelZh: "左髋前后轴",
    labelEn: "left hip pitch",
    axisType: "pitch_lateral",
    neutral: 406,
    direction: -1,
    testedChange: "decrease",
    testedMotionZh: "左大腿向前抬",
    motionZh: "控制左大腿向前抬或向后摆",
    group: "l_leg",
    mirrorId: 4,
  },
  {
    id: 13,
    channel: 12,
    joint: "l_hip_roll",
    labelZh: "左髋侧摆轴",
    labelEn: "left hip roll",
    axisType: "roll_longitudinal",
    neutral: 500,
    direction: +1,
    testedChange: "decrease",
    testedMotionZh: "左腿侧向展开、身体侧倾",
    motionZh: "控制左腿向外展开、向内收回，以及身体侧倾",
    group: "l_leg",
    mirrorId: 5,
  },
  {
    id: 14,
    channel: 13,
    joint: "r_elbow",
    labelZh: "右肘轴",
    labelEn: "right elbow",
    axisType: "pitch_lateral",
    neutral: 425,
    direction: +1,
    testedChange: "decrease",
    testedMotionZh: "右肘弯曲",
    motionZh: "控制右小臂弯曲和伸直",
    group: "r_arm",
    mirrorId: 6,
  },
  {
    id: 15,
    channel: 14,
    joint: "r_shoulder_roll",
    labelZh: "右肩侧向轴",
    labelEn: "right shoulder roll",
    axisType: "roll_longitudinal",
    neutral: 200,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "右臂侧向展开",
    motionZh: "控制右臂侧向展开、向身体收回",
    group: "r_arm",
    mirrorId: 7,
  },
  {
    id: 16,
    channel: 15,
    joint: "r_shoulder_pitch",
    labelZh: "右肩根部旋转轴",
    labelEn: "right shoulder root pitch",
    axisType: "pitch_lateral",
    neutral: 275,
    direction: +1,
    testedChange: "increase",
    testedMotionZh: "右臂向前、向上旋转",
    motionZh: "控制整条右臂前后转动、上举和下放",
    group: "r_arm",
    mirrorId: 8,
  },
];

export const SERVO_NEUTRAL = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [servo.joint, servo.neutral]),
);

export const SERVO_DIRECTION = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [servo.joint, servo.direction]),
);

export const CHANNEL_TO_JOINT = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [servo.channel, servo.joint]),
);

export const CHANNEL_LABELS = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [servo.channel, `ID${servo.id} ${servo.joint}`]),
);

export const SLIDER_GROUPS = [
  { key: "r_arm", titleKey: "group_r_arm", cls: "group-r", channels: [15, 14, 13] },
  { key: "l_arm", titleKey: "group_l_arm", cls: "group-l", channels: [7, 6, 5] },
  { key: "r_leg", titleKey: "group_r_leg", cls: "group-r", channels: [0, 4, 3, 2, 1] },
  { key: "l_leg", titleKey: "group_l_leg", cls: "group-l", channels: [8, 12, 11, 10, 9] },
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

export function getChannelGroup(channel) {
  if (channel >= 13 && channel <= 15) return "r";
  if (channel >= 5 && channel <= 7) return "l";
  if (channel >= 0 && channel <= 4) return "r";
  if (channel >= 8 && channel <= 12) return "l";
  return "u";
}

export function getServoByChannel(channel) {
  return SERVO_LAYOUT.find((servo) => servo.channel === channel) ?? null;
}

export function getServoById(id) {
  return SERVO_LAYOUT.find((servo) => servo.id === id) ?? null;
}

export function getServoByJoint(joint) {
  return SERVO_LAYOUT.find((servo) => servo.joint === joint) ?? null;
}

export function formatServoAngle(channel, value) {
  const servo = getServoByChannel(channel);
  if (!servo) return "";
  const deg = ((value - servo.neutral) * servo.direction / 1000) * 180;
  const sign = deg > 0 ? "+" : "";
  return `${sign}${deg.toFixed(0)}°`;
}

export function formatServoOffset(channel, value) {
  const servo = getServoByChannel(channel);
  if (!servo) return "";
  const delta = value - servo.neutral;
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta}`;
}

export function poseToJointAngles(pose) {
  const angles = {};
  for (const servo of SERVO_LAYOUT) {
    const delta = (pose[servo.channel] - servo.neutral) * servo.direction;
    angles[servo.joint] = delta / 1000.0 * Math.PI;
  }
  return angles;
}
