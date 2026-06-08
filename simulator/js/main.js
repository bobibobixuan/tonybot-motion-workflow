import { DEFAULT_POSE } from "./config.js";
import { initI18n, t } from "./i18n.js";
import { parseRobFile } from "./rob-parser.js";
import { RobotScene } from "./robot-scene.js";
import { SimulatorApp } from "./simulator-app.js";

await initI18n();

const scene = new RobotScene(document.getElementById("viewport"));
const app = new SimulatorApp({
  scene,
  t,
  parseRobFile,
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
