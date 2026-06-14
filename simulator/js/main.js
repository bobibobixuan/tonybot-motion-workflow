import { DEFAULT_POSE, SERVO_LAYOUT } from "./config.js";
import { initI18n, t } from "./i18n.js";
import { parseRobFile } from "./rob-parser.js";
import { RobotScene } from "./robot-scene.js";
import { SimulatorApp } from "./simulator-app.js";

await initI18n();

async function loadServoMap() {
  try {
    const response = await fetch("../data/servo-map.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!Array.isArray(data.servos) || data.servos.length !== 16) {
      throw new Error("servo-map.json 缺少完整 servos 数组");
    }
    return data.servos
      .slice()
      .sort((left, right) => left.channel - right.channel)
      .map((servo) => ({
        id: servo.id,
        channel: servo.channel,
        joint: servo.joint,
        labelZh: servo.label_zh,
        labelEn: servo.label_en,
        axisType: servo.axis_type,
        neutral: servo.neutral,
        direction: servo.direction_sign,
        testedChange: servo.tested_change,
        testedMotionZh: servo.tested_motion_zh,
        motionZh: servo.motion_zh,
        group: servo.group,
        mirrorId: servo.mirror_id,
      }));
  } catch (error) {
    console.warn("servo map fallback to built-in layout:", error);
    return SERVO_LAYOUT;
  }
}

const scene = new RobotScene(document.getElementById("viewport"));
const app = new SimulatorApp({
  scene,
  t,
  parseRobFile,
  servoMap: await loadServoMap(),
});

scene.resize();
app.init();
app.setPose(DEFAULT_POSE);
scene.start();

console.log(t("console_ready"));
console.log(`  ${t("console_drop_hint")}`);
console.log(`  ${t("console_keyboard")}`);
console.log(`  ${t("console_copy_hint")}`);
console.log(`  ${t("console_mouse")}`);
