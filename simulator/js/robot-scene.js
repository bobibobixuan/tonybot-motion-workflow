import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import {
  poseToJointAngles,
  SERVO_LAYOUT,
} from "./config.js";

/*
 * Tonybot visual FK model v2
 *
 * Coordinate system:
 *   +X = robot left (viewer right in the default front view)
 *   +Y = up
 *   +Z = robot front
 *
 * The physical robot is compact and servo-dense. The previous model used
 * long thin rods and also mixed viewer-left with robot-left, which made the
 * shoulder roll signs appear impossible to fix. This model keeps every
 * output shaft at a real hierarchy pivot and mirrors the two sides by
 * position only (never by negative scale).
 */

const MODEL = Object.freeze({
  hipBaseY: 6.95,

  torso: {
    width: 5.25,
    height: 4.15,
    depth: 2.15,
    centerY: 2.72,
  },

  pelvis: {
    width: 3.05,
    height: 0.85,
    depth: 1.45,
    centerY: 0.45,
  },

  // 根部舵机输出轴位于胸腔内部，靠近胸口中线
  shoulderDriveX: 1.15,

  // 外侧肩关节实际位置
  shoulderOuterX: 3.05,

  shoulderY: 4.80,
  hipX: 1.08,

  head: {
    width: 2.15,
    height: 2.05,
    depth: 1.75,
    centerY: 7.00,
  },

  neckY: 5.78,

  upperArm: 2.75,
  forearm: 3.05,
  thigh: 3.15,
  shin: 3.00,

  foot: {
    width: 1.55,
    length: 2.75,
    thickness: 0.28,
    forward: 0.72,
  },
});

const AXIS_BY_JOINT = Object.freeze({
  r_hip_yaw: "y",
  r_ankle: "x",
  r_knee: "x",
  r_hip_pitch: "x",
  r_hip_roll: "z",

  // 机器人左臂：ID8 → ID7 → ID6
  l_shoulder_pitch: "x", // ID8，胸内根部旋转
  l_shoulder_roll: "y",  // ID7，肩关节
  l_elbow: "y",          // ID6，和 ID7 平行

  l_hip_yaw: "y",
  l_ankle: "x",
  l_knee: "x",
  l_hip_pitch: "x",
  l_hip_roll: "z",

  // 机器人右臂：ID16 → ID15 → ID14
  r_shoulder_pitch: "x", // ID16，胸内根部旋转
  r_shoulder_roll: "y",  // ID15，肩关节
  r_elbow: "y",          // ID14，和 ID15 平行
});

/*
 * poseToJointAngles already applies the raw direction from config.js.
 * These signs only convert semantic joint angle into this model's local
 * coordinate orientation.
 *
 * Important verified shoulder behaviour:
 *   ID7  (left shoulder roll): raw down from 800 => arm opens to robot left
 *   ID15 (right shoulder roll): raw up from 200 => arm opens to robot right
 */
const VISUAL_SIGN_BY_JOINT = Object.freeze({
  r_hip_yaw: 1,
  r_ankle: 1,
  r_knee: -1,
  r_hip_pitch: -1,
  r_hip_roll: -1,

  l_elbow: -1,
  l_shoulder_roll: 1,
  l_shoulder_pitch: -1,

  l_hip_yaw: 1,
  l_ankle: 1,
  l_knee: -1,
  l_hip_pitch: -1,
  l_hip_roll: -1,

  r_elbow: 1,
  r_shoulder_roll: -1,
  r_shoulder_pitch: -1,
});

const JOINT_TO_SERVO_ID = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [servo.joint, servo.id]),
);

const SERVO_META = Object.fromEntries(
  SERVO_LAYOUT.map((servo) => [
    servo.id,
    {
      joint: servo.joint,
      axis: AXIS_BY_JOINT[servo.joint],
      axisType: servo.axisType,
      visualSign: VISUAL_SIGN_BY_JOINT[servo.joint] ?? 1,
    },
  ]),
);

function v3(x = 0, y = 0, z = 0) {
  return new THREE.Vector3(x, y, z);
}

export class RobotScene {
  constructor(viewport) {
    this.viewport = viewport;
    this.showGrid = true;
    this.showServoLabels = true;

    this.robotParts = {};
    this.jointParts = {};
    this.servoParts = {};
    this.servoActuators = {};
    this.robotRig = {
      pivots: {},
      markers: {},
    };

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
    });

    this.renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, 2),
    );

    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;

    viewport.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x13151a);
    this.scene.fog = new THREE.Fog(0x13151a, 36, 72);

    this.camera = new THREE.PerspectiveCamera(
      46,
      2,
      0.35,
      100,
    );

    this.camera.position.set(8.6, 12.8, 23.5);
    this.camera.lookAt(0, 7.1, 0);

    this.controls = new OrbitControls(
      this.camera,
      this.renderer.domElement,
    );

    this.controls.target.set(0, 7.1, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 5;
    this.controls.maxDistance = 52;
    this.controls.maxPolarAngle = Math.PI * 0.82;
    this.controls.update();

    this.setupLights();
    this.setupGround();
    this.createMaterials();

    this.robotGroup = new THREE.Group();
    this.robotGroup.name = "tonybot";

    this.scene.add(this.robotGroup);
    this.buildRobotModel();
  }

  setupLights() {
    this.scene.add(
      new THREE.HemisphereLight(
        0xbfd7ff,
        0x20242c,
        2.2,
      ),
    );

    const keyLight = new THREE.DirectionalLight(
      0xfff0dd,
      4.4,
    );

    keyLight.position.set(10, 20, 14);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0002;

    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(
      0x91bdff,
      1.7,
    );

    fillLight.position.set(-9, 10, 6);
    this.scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(
      0xffffff,
      1.4,
    );

    rimLight.position.set(2, 11, -12);
    this.scene.add(rimLight);
  }

  setupGround() {
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(52, 52),
      new THREE.MeshStandardMaterial({
        color: 0x20242c,
        roughness: 0.88,
        metalness: 0.04,
      }),
    );

    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    ground.receiveShadow = true;

    this.scene.add(ground);

    this.gridHelper = new THREE.PolarGridHelper(
      24,
      48,
      20,
      192,
      0x353a45,
      0x252932,
    );

    this.gridHelper.position.y = 0.01;
    this.scene.add(this.gridHelper);
  }

  createMaterials() {
    this.materials = {
      shellWhite: new THREE.MeshStandardMaterial({
        color: 0xf2f4f6,
        roughness: 0.38,
        metalness: 0.24,
      }),

      shellWarm: new THREE.MeshStandardMaterial({
        color: 0xdfe4ea,
        roughness: 0.46,
        metalness: 0.18,
      }),

      bracket: new THREE.MeshStandardMaterial({
        color: 0xf7f8fa,
        roughness: 0.34,
        metalness: 0.30,
      }),

      bracketDark: new THREE.MeshStandardMaterial({
        color: 0xbfc7d1,
        roughness: 0.44,
        metalness: 0.28,
      }),

      servoBody: new THREE.MeshStandardMaterial({
        color: 0x111318,
        roughness: 0.50,
        metalness: 0.30,
      }),

      servoLabel: new THREE.MeshStandardMaterial({
        color: 0x2b3038,
        roughness: 0.58,
        metalness: 0.16,
      }),

      horn: new THREE.MeshStandardMaterial({
        color: 0xd9e0e8,
        roughness: 0.26,
        metalness: 0.50,
      }),

      hornCenter: new THREE.MeshStandardMaterial({
        color: 0x9fa9b5,
        roughness: 0.28,
        metalness: 0.58,
      }),

      screw: new THREE.MeshStandardMaterial({
        color: 0x17191d,
        roughness: 0.52,
        metalness: 0.45,
      }),

      darkPanel: new THREE.MeshStandardMaterial({
        color: 0x15191f,
        roughness: 0.56,
        metalness: 0.20,
      }),

      face: new THREE.MeshStandardMaterial({
        color: 0x171b22,
        roughness: 0.36,
        metalness: 0.28,
      }),

      eyeBlue: new THREE.MeshStandardMaterial({
        color: 0x27a8ff,
        emissive: 0x008cff,
        emissiveIntensity: 4.0,
        roughness: 0.22,
        metalness: 0.12,
      }),

      eyeCore: new THREE.MeshStandardMaterial({
        color: 0xbcecff,
        emissive: 0x2fc4ff,
        emissiveIntensity: 5.0,
        roughness: 0.18,
      }),

      rightAccent: new THREE.MeshStandardMaterial({
        color: 0xe46c75,
        roughness: 0.38,
        metalness: 0.18,
      }),

      leftAccent: new THREE.MeshStandardMaterial({
        color: 0x58a6ff,
        roughness: 0.38,
        metalness: 0.18,
      }),
    };
  }

  createBox(width, height, depth, material) {
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(
        width,
        height,
        depth,
      ),
      material,
    );

    mesh.castShadow = true;
    mesh.receiveShadow = true;

    return mesh;
  }

  createCylinder(
    radiusTop,
    radiusBottom,
    height,
    radialSegments,
    material,
  ) {
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(
        radiusTop,
        radiusBottom,
        height,
        radialSegments,
      ),
      material,
    );

    mesh.castShadow = true;
    mesh.receiveShadow = true;

    return mesh;
  }

  orientCylinderToAxis(mesh, axis) {
    mesh.rotation.set(0, 0, 0);

    if (axis === "x") {
      mesh.rotation.z = Math.PI / 2;
    }

    if (axis === "z") {
      mesh.rotation.x = Math.PI / 2;
    }
  }

  createExtrudedPanel(
    points,
    depth,
    material,
    bevel = 0.06,
  ) {
    const shape = new THREE.Shape();

    shape.moveTo(
      points[0][0],
      points[0][1],
    );

    for (let i = 1; i < points.length; i += 1) {
      shape.lineTo(
        points[i][0],
        points[i][1],
      );
    }

    shape.closePath();

    const geometry = new THREE.ExtrudeGeometry(
      shape,
      {
        depth,
        bevelEnabled: true,
        bevelSegments: 2,
        bevelSize: bevel,
        bevelThickness: bevel,
        curveSegments: 1,
      },
    );

    geometry.translate(
      0,
      0,
      -depth * 0.5,
    );

    const mesh = new THREE.Mesh(
      geometry,
      material,
    );

    mesh.castShadow = true;
    mesh.receiveShadow = true;

    return mesh;
  }

  createGroup(
    name,
    parent,
    position = new THREE.Vector3(),
  ) {
    const group = new THREE.Group();

    group.name = name;
    group.position.copy(position);

    parent.add(group);

    return group;
  }

  registerPart(
    name,
    object,
    parent = this.robotGroup,
  ) {
    this.robotParts[name] = object;
    parent.add(object);

    return object;
  }

  registerMarker(
    name,
    parent,
    position = new THREE.Vector3(),
  ) {
    const marker = new THREE.Group();

    marker.name = `${name}Marker`;
    marker.position.copy(position);

    parent.add(marker);

    this.robotRig.markers[name] = marker;

    return marker;
  }

  createLabelSprite(
    text,
    color = "#ffbd75",
  ) {
    const canvas = document.createElement("canvas");

    canvas.width = 192;
    canvas.height = 80;

    const ctx = canvas.getContext("2d");

    ctx.clearRect(
      0,
      0,
      canvas.width,
      canvas.height,
    );

    ctx.font = '700 34px "Segoe UI", Arial, sans-serif';
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 8;
    ctx.strokeStyle = "rgba(0,0,0,0.72)";

    ctx.strokeText(
      text,
      96,
      40,
    );

    ctx.fillStyle = color;

    ctx.fillText(
      text,
      96,
      40,
    );

    const texture = new THREE.CanvasTexture(canvas);

    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;

    const sprite = new THREE.Sprite(
      new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthTest: false,
        depthWrite: false,
      }),
    );

    sprite.scale.set(
      1.82,
      0.76,
      1,
    );

    sprite.renderOrder = 9;

    return sprite;
  }

  createServoCase(
    id,
    side,
    scale = 1,
  ) {
    const group = new THREE.Group();

    const bodyWidth = 1.12 * scale;
    const bodyHeight = 0.78 * scale;
    const bodyDepth = 0.62 * scale;

    const body = this.createBox(
      bodyWidth,
      bodyHeight,
      bodyDepth,
      this.materials.servoBody,
    );

    group.add(body);

    const sticker = this.createBox(
      0.72 * scale,
      0.39 * scale,
      0.026 * scale,
      this.materials.servoLabel,
    );

    sticker.position.z = bodyDepth * 0.51;
    group.add(sticker);

    const topEar = this.createBox(
      bodyWidth + 0.28 * scale,
      0.13 * scale,
      bodyDepth + 0.05 * scale,
      this.materials.bracket,
    );

    topEar.position.y = bodyHeight * 0.60;
    group.add(topEar);

    const bottomEar = topEar.clone();

    bottomEar.position.y = -bodyHeight * 0.60;
    group.add(bottomEar);

    const label = this.createLabelSprite(
      `ID${id}`,
      side === "r"
        ? "#ff9aa2"
        : "#8fd0ff",
    );

    label.position.set(
      0,
      bodyHeight * 1.15,
      0.04,
    );

    label.visible = this.showServoLabels;

    group.add(label);

    group.userData.label = label;

    return group;
  }

  createServoHorn(
    axis,
    scale = 1,
  ) {
    const group = new THREE.Group();

    const disk = this.createCylinder(
      0.31 * scale,
      0.31 * scale,
      0.12 * scale,
      32,
      this.materials.horn,
    );

    this.orientCylinderToAxis(
      disk,
      axis,
    );

    group.add(disk);

    const center = this.createCylinder(
      0.105 * scale,
      0.105 * scale,
      0.145 * scale,
      20,
      this.materials.screw,
    );

    this.orientCylinderToAxis(
      center,
      axis,
    );

    group.add(center);

    const screwRadius = 0.205 * scale;

    for (let i = 0; i < 4; i += 1) {
      const angle = i * Math.PI * 0.5;

      const screw = this.createCylinder(
        0.035 * scale,
        0.035 * scale,
        0.15 * scale,
        10,
        this.materials.screw,
      );

      this.orientCylinderToAxis(
        screw,
        axis,
      );

      if (axis === "x") {
        screw.position.set(
          0,
          Math.cos(angle) * screwRadius,
          Math.sin(angle) * screwRadius,
        );
      } else if (axis === "y") {
        screw.position.set(
          Math.cos(angle) * screwRadius,
          0,
          Math.sin(angle) * screwRadius,
        );
      } else {
        screw.position.set(
          Math.cos(angle) * screwRadius,
          Math.sin(angle) * screwRadius,
          0,
        );
      }

      group.add(screw);
    }

    return group;
  }

  createServoActuator(id, parent, options = {}) {
    const meta = SERVO_META[id] ?? {};
    const side = options.side ?? "l";
    const axis = options.axis ?? meta.axis ?? "x";
    const scale = options.scale ?? 1;

    /*
     * root 位于真实输出轴中心。
     */
    const root = new THREE.Group();

    root.name =
      `servo_ID${id}_${meta.joint ?? "unknown"}_pivot`;

    root.position.copy(
      options.position ?? v3(),
    );

    root.userData.id = id;
    root.userData.joint = meta.joint;
    root.userData.axis = axis;

    parent.add(root);

    /*
     * 舵机外壳固定在父级结构上。
     */
    const caseGroup = this.createServoCase(
      id,
      side,
      scale,
    );

    caseGroup.name =
      `servo_ID${id}_physical_case`;

    caseGroup.position.copy(
      options.caseOffset ?? v3(),
    );

    caseGroup.rotation.copy(
      options.caseRotation ??
        new THREE.Euler(),
    );

    root.add(caseGroup);

    /*
     * 输出盘旋转，带动子区块。
     */
    const hornGroup = new THREE.Group();

    hornGroup.name =
      `servo_ID${id}_horn_rotates`;

    root.add(hornGroup);

    hornGroup.add(
      this.createServoHorn(axis, scale),
    );

    const childRoot = new THREE.Group();

    childRoot.name =
      `servo_ID${id}_childRoot`;

    hornGroup.add(childRoot);

    const actuator = {
      id,
      root,
      caseGroup,
      hornGroup,
      motionGroup: hornGroup,
      childRoot,
      axis,
      label: caseGroup.userData.label,
      visualSign:
        options.visualSign ??
        meta.visualSign ??
        1,
    };

    this.servoActuators[id] = actuator;
    this.servoParts[id] = root;
    this.jointParts[meta.joint] = root;

    return actuator;
  }

  createAxleX(parent, length, direction = 1, radius = 0.11) {
    const actualLength = Math.abs(length);

    const axle = this.createCylinder(
      radius,
      radius,
      actualLength,
      24,
      this.materials.hornCenter,
    );

    // Cylinder 默认沿 Y，转成沿 X
    this.orientCylinderToAxis(axle, "x");

    axle.position.x =
      direction * actualLength * 0.5;

    parent.add(axle);

    return axle;
  }

  createBearingX(parent, x = 0, scale = 1) {
    const bearing = this.createCylinder(
      0.34 * scale,
      0.34 * scale,
      0.18 * scale,
      28,
      this.materials.horn,
    );

    this.orientCylinderToAxis(
      bearing,
      "x",
    );

    bearing.position.x = x;
    parent.add(bearing);

    const center = this.createCylinder(
      0.13 * scale,
      0.13 * scale,
      0.21 * scale,
      20,
      this.materials.screw,
    );

    this.orientCylinderToAxis(
      center,
      "x",
    );

    center.position.x = x;
    parent.add(center);

    return bearing;
  }

  applyServoAngle(id, angle) {
    const actuator =
      this.servoActuators[id];

    if (!actuator) {
      return;
    }

    const finalAngle =
      angle * actuator.visualSign;

    actuator.hornGroup.rotation.set(
      0,
      0,
      0,
    );

    if (actuator.axis === "x") {
      actuator.hornGroup.rotation.x =
        finalAngle;
    }

    if (actuator.axis === "y") {
      actuator.hornGroup.rotation.y =
        finalAngle;
    }

    if (actuator.axis === "z") {
      actuator.hornGroup.rotation.z =
        finalAngle;
    }
  }

  createUBracket(
    parent,
    options = {},
  ) {
    const width = options.width ?? 1.20;
    const height = options.height ?? 0.86;
    const depth = options.depth ?? 0.74;
    const thickness = options.thickness ?? 0.12;

    const material =
      options.material ??
      this.materials.bracket;

    const group = new THREE.Group();

    parent.add(group);

    const cross = this.createBox(
      width,
      thickness,
      depth,
      material,
    );

    cross.position.y =
      -height + thickness * 0.5;

    group.add(cross);

    const sideA = this.createBox(
      thickness,
      height,
      depth,
      material,
    );

    sideA.position.set(
      -width * 0.5 + thickness * 0.5,
      -height * 0.5,
      0,
    );

    group.add(sideA);

    const sideB = this.createBox(
      thickness,
      height,
      depth,
      material,
    );

    sideB.position.set(
      width * 0.5 - thickness * 0.5,
      -height * 0.5,
      0,
    );

    group.add(sideB);

    return group;
  }

  createMechanicalLink(
    parent,
    options = {},
  ) {
    const length = options.length ?? 2.5;
    const width = options.width ?? 0.88;
    const depth = options.depth ?? 0.70;
    const rail = options.rail ?? 0.12;

    const group = new THREE.Group();

    parent.add(group);

    const leftRail = this.createBox(
      rail,
      length,
      depth,
      this.materials.bracket,
    );

    leftRail.position.set(
      -width * 0.5 + rail * 0.5,
      -length * 0.5,
      0,
    );

    group.add(leftRail);

    const rightRail = this.createBox(
      rail,
      length,
      depth,
      this.materials.bracket,
    );

    rightRail.position.set(
      width * 0.5 - rail * 0.5,
      -length * 0.5,
      0,
    );

    group.add(rightRail);

    const frontCover = this.createBox(
      width - rail * 1.25,
      length * 0.44,
      0.09,
      options.coverMaterial ??
        this.materials.shellWarm,
    );

    frontCover.position.set(
      0,
      -length * 0.48,
      depth * 0.52,
    );

    group.add(frontCover);

    const rearBrace = this.createBox(
      width,
      0.13,
      depth,
      this.materials.bracketDark,
    );

    rearBrace.position.y =
      -length + 0.08;

    group.add(rearBrace);

    const topBrace = rearBrace.clone();

    topBrace.position.y = -0.08;
    group.add(topBrace);

    return group;
  }

  createFootMesh(side) {
    const group = new THREE.Group();
    const sign = side === "l" ? 1 : -1;

    const sole = this.createBox(
      MODEL.foot.width,
      MODEL.foot.thickness,
      MODEL.foot.length,
      this.materials.shellWhite,
    );

    sole.position.set(
      sign * 0.05,
      -MODEL.foot.thickness * 0.5,
      MODEL.foot.forward,
    );

    group.add(sole);

    const ankleCup = this.createUBracket(
      group,
      {
        width: 1.06,
        height: 0.72,
        depth: 0.84,
        thickness: 0.13,
      },
    );

    ankleCup.position.set(
      0,
      0.06,
      -0.10,
    );

    const toe = this.createBox(
      MODEL.foot.width * 0.88,
      0.10,
      0.32,
      this.materials.bracketDark,
    );

    toe.position.set(
      0,
      -0.07,
      MODEL.foot.forward +
        MODEL.foot.length * 0.48,
    );

    group.add(toe);

    const heel = this.createBox(
      MODEL.foot.width * 0.80,
      0.10,
      0.30,
      this.materials.bracketDark,
    );

    heel.position.set(
      0,
      -0.07,
      MODEL.foot.forward -
        MODEL.foot.length * 0.48,
    );

    group.add(heel);

    return group;
  }

  createHandMesh(side) {
    const group = new THREE.Group();
    const sign = side === "l" ? 1 : -1;

    const wrist = this.createBox(
      0.72,
      0.28,
      0.62,
      this.materials.bracket,
    );

    wrist.position.y = -0.14;
    group.add(wrist);

    const palmTop = this.createBox(
      0.92,
      0.13,
      0.50,
      this.materials.bracket,
    );

    palmTop.position.y = -0.48;
    group.add(palmTop);

    const palmSideA = this.createBox(
      0.13,
      0.88,
      0.50,
      this.materials.bracket,
    );

    palmSideA.position.set(
      -0.395,
      -0.84,
      0,
    );

    group.add(palmSideA);

    const palmSideB = this.createBox(
      0.13,
      0.88,
      0.50,
      this.materials.bracket,
    );

    palmSideB.position.set(
      0.395,
      -0.84,
      0,
    );

    group.add(palmSideB);

    const fingerA = this.createBox(
      0.12,
      0.58,
      0.16,
      this.materials.bracketDark,
    );

    fingerA.position.set(
      sign * 0.24,
      -1.43,
      0.12,
    );

    fingerA.rotation.z =
      sign * 0.10;

    group.add(fingerA);

    const fingerB = this.createBox(
      0.12,
      0.58,
      0.16,
      this.materials.bracketDark,
    );

    fingerB.position.set(
      -sign * 0.24,
      -1.43,
      0.12,
    );

    fingerB.rotation.z =
      -sign * 0.10;

    group.add(fingerB);

    return group;
  }

  addHeartbeat(
    parent,
    y,
    z,
  ) {
    const points = [
      [-1.55, 0.00],
      [-0.54, 0.00],
      [-0.32, 0.32],
      [-0.05, -0.58],
      [0.24, 0.55],
      [0.43, 0.00],
      [1.56, 0.00],
    ].map(
      ([x, py]) =>
        new THREE.Vector3(
          x,
          y + py,
          z,
        ),
    );

    const geometry =
      new THREE.BufferGeometry()
        .setFromPoints(points);

    const line = new THREE.Line(
      geometry,
      new THREE.LineBasicMaterial({
        color: 0x111318,
      }),
    );

    line.renderOrder = 3;
    parent.add(line);
  }

  buildBody(bodyRoot) {
    const m = this.materials;

    const pelvis = this.registerPart(
      "pelvis",
      this.createBox(
        MODEL.pelvis.width,
        MODEL.pelvis.height,
        MODEL.pelvis.depth,
        m.shellWhite,
      ),
      bodyRoot,
    );

    pelvis.position.y =
      MODEL.pelvis.centerY;

    const pelvisCore = this.registerPart(
      "pelvisCore",
      this.createBox(
        2.15,
        0.56,
        0.92,
        m.darkPanel,
      ),
      bodyRoot,
    );

    pelvisCore.position.set(
      0,
      MODEL.pelvis.centerY + 0.04,
      -0.02,
    );

    /*
     * 空心胸腔：
     * 内部用于放置 ID8、ID16 和横向旋转轴。
     */

    // 胸腔后板
    const chestBack = this.registerPart(
      "chestBack",
      this.createBox(
        MODEL.torso.width - 0.30,
        MODEL.torso.height - 0.22,
        0.18,
        m.shellWarm,
      ),
      bodyRoot,
    );

    chestBack.position.set(
      0,
      MODEL.torso.centerY,
      -MODEL.torso.depth * 0.5 + 0.09,
    );

    // 胸腔顶部
    const chestTop = this.registerPart(
      "chestTop",
      this.createBox(
        MODEL.torso.width - 0.26,
        0.18,
        MODEL.torso.depth,
        m.shellWarm,
      ),
      bodyRoot,
    );

    chestTop.position.set(
      0,
      MODEL.torso.centerY +
        MODEL.torso.height * 0.5 -
        0.09,
      0,
    );

    // 胸腔底板
    const chestBottom = this.registerPart(
      "chestBottom",
      this.createBox(
        MODEL.torso.width - 0.55,
        0.18,
        MODEL.torso.depth - 0.18,
        m.shellWarm,
      ),
      bodyRoot,
    );

    chestBottom.position.set(
      0,
      MODEL.torso.centerY -
        MODEL.torso.height * 0.5 +
        0.22,
      0,
    );

    // 左侧胸腔加强筋
    const leftChestRib = this.registerPart(
      "leftChestRib",
      this.createBox(
        0.18,
        MODEL.torso.height * 0.58,
        MODEL.torso.depth - 0.15,
        m.bracketDark,
      ),
      bodyRoot,
    );

    leftChestRib.position.set(
      MODEL.torso.width * 0.5 - 0.15,
      MODEL.torso.centerY - 0.58,
      0,
    );

    // 右侧胸腔加强筋
    const rightChestRib =
      leftChestRib.clone();

    rightChestRib.position.x *= -1;

    bodyRoot.add(rightChestRib);

    this.robotParts.rightChestRib =
      rightChestRib;

    const chestShape = [
      [
        -MODEL.torso.width * 0.50,
        MODEL.torso.height * 0.49,
      ],
      [
        MODEL.torso.width * 0.50,
        MODEL.torso.height * 0.49,
      ],
      [
        MODEL.torso.width * 0.50,
        -MODEL.torso.height * 0.22,
      ],
      [
        MODEL.torso.width * 0.32,
        -MODEL.torso.height * 0.46,
      ],
      [
        0,
        -MODEL.torso.height * 0.54,
      ],
      [
        -MODEL.torso.width * 0.32,
        -MODEL.torso.height * 0.46,
      ],
      [
        -MODEL.torso.width * 0.50,
        -MODEL.torso.height * 0.22,
      ],
    ];

    const chestFront = this.registerPart(
      "chestFront",
      this.createExtrudedPanel(
        chestShape,
        0.16,
        m.shellWhite,
        0.07,
      ),
      bodyRoot,
    );

    chestFront.position.set(
      0,
      MODEL.torso.centerY,
      MODEL.torso.depth * 0.52 + 0.07,
    );

    const sidePanelLeft = this.createBox(
      0.20,
      3.18,
      1.78,
      m.bracketDark,
    );

    sidePanelLeft.position.set(
      MODEL.torso.width * 0.49,
      MODEL.torso.centerY + 0.12,
      0,
    );

    bodyRoot.add(sidePanelLeft);

    const sidePanelRight =
      sidePanelLeft.clone();

    sidePanelRight.position.x *= -1;

    bodyRoot.add(sidePanelRight);

    this.addHeartbeat(
      bodyRoot,
      MODEL.torso.centerY + 0.10,
      MODEL.torso.depth * 0.52 + 0.17,
    );

    const neckBase = this.createCylinder(
      0.34,
      0.34,
      0.60,
      24,
      m.darkPanel,
    );

    neckBase.position.y =
      MODEL.neckY;

    bodyRoot.add(neckBase);

    const neckRing = this.createCylinder(
      0.46,
      0.46,
      0.18,
      24,
      m.bracketDark,
    );

    neckRing.position.y =
      MODEL.neckY - 0.25;

    bodyRoot.add(neckRing);

    const headRoot = this.createGroup(
      "headRoot",
      bodyRoot,
      v3(
        0,
        MODEL.head.centerY,
        0,
      ),
    );

    const headCore = this.registerPart(
      "headCore",
      this.createBox(
        MODEL.head.width * 0.88,
        MODEL.head.height * 0.82,
        MODEL.head.depth,
        m.shellWarm,
      ),
      headRoot,
    );

    const headShape = [
      [
        -MODEL.head.width * 0.36,
        MODEL.head.height * 0.50,
      ],
      [
        MODEL.head.width * 0.36,
        MODEL.head.height * 0.50,
      ],
      [
        MODEL.head.width * 0.50,
        MODEL.head.height * 0.30,
      ],
      [
        MODEL.head.width * 0.50,
        -MODEL.head.height * 0.23,
      ],
      [
        MODEL.head.width * 0.33,
        -MODEL.head.height * 0.50,
      ],
      [
        -MODEL.head.width * 0.33,
        -MODEL.head.height * 0.50,
      ],
      [
        -MODEL.head.width * 0.50,
        -MODEL.head.height * 0.23,
      ],
      [
        -MODEL.head.width * 0.50,
        MODEL.head.height * 0.30,
      ],
    ];

    const facePlate = this.registerPart(
      "facePlate",
      this.createExtrudedPanel(
        headShape,
        0.15,
        m.shellWhite,
        0.06,
      ),
      headRoot,
    );

    facePlate.position.z =
      MODEL.head.depth * 0.51 + 0.07;

    const faceInset = this.createBox(
      1.45,
      0.82,
      0.08,
      m.face,
    );

    faceInset.position.set(
      0,
      0.08,
      MODEL.head.depth * 0.57 + 0.12,
    );

    headRoot.add(faceInset);

    for (const x of [-0.42, 0.42]) {
      const eyeRing = this.createCylinder(
        0.33,
        0.33,
        0.12,
        32,
        m.eyeBlue,
      );

      eyeRing.rotation.x =
        Math.PI / 2;

      eyeRing.position.set(
        x,
        0.08,
        MODEL.head.depth * 0.61 + 0.16,
      );

      headRoot.add(eyeRing);

      const eyeCore = this.createCylinder(
        0.16,
        0.16,
        0.14,
        24,
        m.eyeCore,
      );

      eyeCore.rotation.x =
        Math.PI / 2;

      eyeCore.position.set(
        x,
        0.08,
        MODEL.head.depth * 0.61 + 0.23,
      );

      headRoot.add(eyeCore);
    }

    const headSideLeft = this.createBox(
      0.18,
      1.48,
      1.40,
      m.bracket,
    );

    headSideLeft.position.set(
      MODEL.head.width * 0.50,
      0,
      -0.03,
    );

    headRoot.add(headSideLeft);

    const headSideRight =
      headSideLeft.clone();

    headSideRight.position.x *= -1;

    headRoot.add(headSideRight);

    const topCap = this.createBox(
      1.34,
      0.18,
      1.42,
      m.bracket,
    );

    topCap.position.set(
      0,
      MODEL.head.height * 0.48,
      -0.02,
    );

    headRoot.add(topCap);
  }

  buildArm(side, bodyRoot) {
    const isLeft = side === "left";
    const sign = isLeft ? 1 : -1;
    const sideKey = isLeft ? "l" : "r";

    const ids = isLeft
      ? {
          root: 8,
          shoulder: 7,
          elbow: 6,
        }
      : {
          root: 16,
          shoulder: 15,
          elbow: 14,
        };

    /*
     * ID8 / ID16：
     * 外壳固定在胸腔里，输出轴带动整条手臂。
     */
    const rootServo = this.createServoActuator(
      ids.root,
      bodyRoot,
      {
        side: sideKey,
        axis: "x",
        mountMode: "case-fixed",

        position: v3(
          sign * MODEL.shoulderDriveX,
          MODEL.shoulderY,
          0,
        ),

        // 黑色外壳隐藏在胸内
        caseOffset: v3(
          -sign * 0.50,
          0,
          0,
        ),
      },
    );

    /*
     * ID8 输出端到 ID7 安装位置。
     * 这里只是很短的肩部安装架，不是长上臂。
     */
    const shoulderMountLength = 0.72;

    const shoulderMount = this.createBox(
      shoulderMountLength,
      0.24,
      0.82,
      this.materials.bracket,
    );

    shoulderMount.position.set(
      sign * shoulderMountLength * 0.5,
      0,
      0,
    );

    rootServo.childRoot.add(shoulderMount);

    /*
     * ID7 / ID15：
     * 外壳固定在 ID8 控制的肩部框架上。
     * 必须紧挨胸口。
     */
    const shoulderServo = this.createServoActuator(
      ids.shoulder,
      rootServo.childRoot,
      {
        side: sideKey,
        axis: "y",
        mountMode: "case-fixed",

        position: v3(
          sign * shoulderMountLength,
          0,
          0,
        ),

        /*
         * 舵机外壳放在肩轴附近，
         * 不能再沿上臂偏移一大段。
         */
        caseOffset: v3(
          sign * 0.10,
          -0.52,
          0,
        ),

        caseRotation: new THREE.Euler(
          0,
          0,
          0,
        ),
      },
    );

    /*
     * ID7 输出盘带动的上臂。
     * 这一段包含白色连接板和 ID6 外壳。
     */
    const upperArmLength = 2.05;

    const upperArmTop = this.createBox(
      upperArmLength,
      0.14,
      0.72,
      this.materials.bracket,
    );

    upperArmTop.position.set(
      sign * upperArmLength * 0.5,
      0.22,
      0,
    );

    shoulderServo.childRoot.add(upperArmTop);

    const upperArmBottom = this.createBox(
      upperArmLength,
      0.14,
      0.72,
      this.materials.bracket,
    );

    upperArmBottom.position.set(
      sign * upperArmLength * 0.5,
      -0.54,
      0,
    );

    shoulderServo.childRoot.add(upperArmBottom);

    /*
     * ID6 / ID14：
     * 外壳固定在 ID7 带动的上臂末端。
     */
    const elbowServo = this.createServoActuator(
      ids.elbow,
      shoulderServo.childRoot,
      {
        side: sideKey,
        axis: "y",
        mountMode: "case-fixed",

        position: v3(
          sign * upperArmLength,
          0,
          0,
        ),

        caseOffset: v3(
          sign * 0.10,
          -0.52,
          0,
        ),

        caseRotation: new THREE.Euler(
          0,
          0,
          0,
        ),
      },
    );

    /*
     * ID6 输出盘带动的前臂和手掌。
     */
    const forearmLength = 2.10;

    const forearmTop = this.createBox(
      forearmLength,
      0.14,
      0.68,
      this.materials.bracket,
    );

    forearmTop.position.set(
      sign * forearmLength * 0.5,
      0.22,
      0,
    );

    elbowServo.childRoot.add(forearmTop);

    const forearmBottom = this.createBox(
      forearmLength,
      0.14,
      0.68,
      this.materials.bracket,
    );

    forearmBottom.position.set(
      sign * forearmLength * 0.5,
      -0.54,
      0,
    );

    elbowServo.childRoot.add(forearmBottom);

    const handRoot = this.createGroup(
      `${side}HandRoot`,
      elbowServo.childRoot,
      v3(
        sign * forearmLength,
        0,
        0,
      ),
    );

    const hand = this.createHandMesh(sideKey);
    hand.rotation.z =
      sign > 0 ? Math.PI / 2 : -Math.PI / 2;

    handRoot.add(hand);

    this.robotParts[`${sideKey}Hand`] = hand;
  }

  buildLeg(side, bodyRoot) {
    const isLeft = side === "left";
    const sign = isLeft ? 1 : -1;
    const sideKey = isLeft ? "l" : "r";

    const ids = isLeft
      ? { hipYaw: 9, hipRoll: 13, hipPitch: 12, knee: 11, ankle: 10 }
      : { hipYaw: 1, hipRoll: 5, hipPitch: 4, knee: 3, ankle: 2 };

    const hipAnchor = this.createGroup(
      `${side}HipAnchor`, bodyRoot,
      v3(sign * MODEL.hipX, 0.18, 0),
    );

    this.registerMarker(`${sideKey}Hip`, hipAnchor);

    const hipYaw = this.createServoActuator(ids.hipYaw, hipAnchor, {
      side: sideKey, axis: "y", scale: 0.82,
      caseOffset: v3(sign * 0.62, 0.04, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const hipYawCage = this.createUBracket(hipYaw.childRoot, {
      width: 1.18, height: 0.62, depth: 0.94, thickness: 0.13,
    });
    hipYawCage.position.y = 0.02;

    const hipRoll = this.createServoActuator(ids.hipRoll, hipYaw.childRoot, {
      side: sideKey, axis: "z", scale: 0.84,
      position: v3(0, -0.64, 0),
      caseOffset: v3(sign * 0.62, 0, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const hipRollCage = this.createUBracket(hipRoll.childRoot, {
      width: 1.24, height: 0.66, depth: 0.94, thickness: 0.13,
    });
    hipRollCage.position.y = 0.03;

    const hipPitch = this.createServoActuator(ids.hipPitch, hipRoll.childRoot, {
      side: sideKey, axis: "x", scale: 0.88,
      position: v3(0, -0.68, 0),
      caseOffset: v3(sign * 0.64, 0, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    this.createMechanicalLink(hipPitch.childRoot, {
      length: MODEL.thigh, width: 1.18, depth: 0.88,
      coverMaterial: this.materials.shellWhite,
    });

    const kneeAnchor = this.createGroup(
      `${side}KneeAnchor`, hipPitch.childRoot,
      v3(0, -MODEL.thigh, 0),
    );
    this.registerMarker(`${sideKey}Knee`, kneeAnchor);

    const knee = this.createServoActuator(ids.knee, kneeAnchor, {
      side: sideKey, axis: "x", scale: 0.88,
      caseOffset: v3(sign * 0.64, 0, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const kneeCage = this.createUBracket(knee.childRoot, {
      width: 1.25, height: 0.72, depth: 0.94, thickness: 0.13,
    });
    kneeCage.position.y = 0.03;

    this.createMechanicalLink(knee.childRoot, {
      length: MODEL.shin, width: 1.10, depth: 0.84,
      coverMaterial: this.materials.shellWarm,
    });

    const ankleAnchor = this.createGroup(
      `${side}AnkleAnchor`, knee.childRoot,
      v3(0, -MODEL.shin, 0),
    );
    this.registerMarker(`${sideKey}Ankle`, ankleAnchor);

    const ankle = this.createServoActuator(ids.ankle, ankleAnchor, {
      side: sideKey, axis: "x", scale: 0.80,
      caseOffset: v3(sign * 0.58, 0.02, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const foot = this.createFootMesh(sideKey);
    foot.position.y = -0.28;
    ankle.childRoot.add(foot);

    this.robotParts[`${sideKey}FootBox`] = foot;
    this.registerMarker(`${sideKey}Foot`, ankle.childRoot,
      v3(0, -MODEL.foot.thickness * 0.5, MODEL.foot.forward));
  }

  clearRobotGroup() {
    while (
      this.robotGroup.children.length > 0
    ) {
      this.robotGroup.remove(
        this.robotGroup.children[0],
      );
    }

    this.robotParts = {};
    this.jointParts = {};
    this.servoParts = {};
    this.servoActuators = {};

    this.robotRig = {
      pivots: {},
      markers: {},
    };
  }

  buildRobotModel() {
    this.clearRobotGroup();

    const bodyRoot = this.createGroup(
      "bodyRoot",
      this.robotGroup,
      v3(
        0,
        MODEL.hipBaseY,
        0,
      ),
    );

    this.robotRig.pivots.bodyRoot =
      bodyRoot;

    this.buildBody(bodyRoot);

    // Logical robot sides, not viewer sides.
    // Robot left appears on the viewer's right.
    this.buildArm(
      "left",
      bodyRoot,
    );

    // IDs 16, 15, 14 — viewer left.
    this.buildArm(
      "right",
      bodyRoot,
    );

    // IDs 1..5 — robot right, viewer left.
    this.buildLeg(
      "right",
      bodyRoot,
    );

    // IDs 9..13 — robot left, viewer right.
    this.buildLeg(
      "left",
      bodyRoot,
    );
  }

  getMeshWorldMinY(object3d) {
    if (!object3d) {
      return 0;
    }

    object3d.updateMatrixWorld(true);

    return new THREE.Box3()
      .setFromObject(object3d)
      .min
      .y;
  }

  setPose(pose) {
    const angles =
      poseToJointAngles(pose);

    // ID8 / ID16 are continuous-rotation servos: map 0–1000 → 360° centered at neutral
    angles.l_shoulder_pitch = ((pose[7] - 724) / 500) * Math.PI;
    angles.r_shoulder_pitch = ((pose[15] - 275) / 500) * Math.PI;

    for (
      const [jointName, servoId]
      of Object.entries(
        JOINT_TO_SERVO_ID,
      )
    ) {
      this.applyServoAngle(
        servoId,
        angles[jointName] ?? 0,
      );
    }

    this.robotGroup.position.set(
      0,
      0,
      0,
    );

    this.robotGroup.updateMatrixWorld(
      true,
    );

    const minFootY = Math.min(
      this.getMeshWorldMinY(
        this.robotParts.rFootBox,
      ),
      this.getMeshWorldMinY(
        this.robotParts.lFootBox,
      ),
    );

    this.robotGroup.position.y =
      -minFootY + 0.02;

    this.robotGroup.updateMatrixWorld(
      true,
    );
  }

  toggleGrid() {
    this.showGrid =
      !this.showGrid;

    this.gridHelper.visible =
      this.showGrid;

    return this.showGrid;
  }

  toggleServoLabels() {
    this.showServoLabels =
      !this.showServoLabels;

    Object.values(
      this.servoActuators,
    ).forEach((actuator) => {
      if (actuator.label) {
        actuator.label.visible =
          this.showServoLabels;
      }
    });

    return this.showServoLabels;
  }

  resetView() {
    this.camera.position.set(
      8.6,
      12.8,
      23.5,
    );

    this.controls.target.set(
      0,
      7.1,
      0,
    );

    this.controls.update();
  }

  resize() {
    const rect =
      this.viewport.getBoundingClientRect();

    this.renderer.setSize(
      rect.width,
      rect.height,
    );

    this.camera.aspect =
      rect.width /
      Math.max(rect.height, 1);

    this.camera.updateProjectionMatrix();
  }

  start() {
    const renderLoop = () => {
      this.animationFrame =
        requestAnimationFrame(
          renderLoop,
        );

      this.controls.update();

      this.renderer.render(
        this.scene,
        this.camera,
      );
    };

    renderLoop();
  }
}
