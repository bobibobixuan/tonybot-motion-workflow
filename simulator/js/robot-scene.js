import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import {
  SEGMENTS,
  FOOT_PLATE,
  FOOT_CENTER_FORWARD,
  HIP_HALF_WIDTH,
  SHOULDER_HALF_WIDTH,
  HIP_BASE_HEIGHT,
  poseToJointAngles,
  SERVO_LAYOUT,
} from "./config.js";

const AXIS_BY_JOINT = {
  r_hip_yaw: "y",
  r_ankle: "x",
  r_knee: "x",
  r_hip_pitch: "x",
  r_hip_roll: "z",
  l_elbow: "x",
  l_shoulder_roll: "z",
  l_shoulder_pitch: "x",
  l_hip_yaw: "y",
  l_ankle: "x",
  l_knee: "x",
  l_hip_pitch: "x",
  l_hip_roll: "z",
  r_elbow: "x",
  r_shoulder_roll: "z",
  r_shoulder_pitch: "x",
};

const VISUAL_SIGN_BY_JOINT = {
  r_hip_yaw: 1,
  r_ankle: 1,
  r_knee: 1,
  r_hip_pitch: 1,
  r_hip_roll: 1,
  l_elbow: 1,
  l_shoulder_roll: -1,
  l_shoulder_pitch: 1,
  l_hip_yaw: 1,
  l_ankle: 1,
  l_knee: 1,
  l_hip_pitch: 1,
  l_hip_roll: -1,
  r_elbow: 1,
  r_shoulder_roll: 1,
  r_shoulder_pitch: 1,
};

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
    this.robotRig = { pivots: {}, markers: {} };

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    viewport.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x13151a);
    this.scene.fog = new THREE.Fog(0x13151a, 40, 80);

    this.camera = new THREE.PerspectiveCamera(48, 2, 0.5, 120);
    this.camera.position.set(8, 18, 28);
    this.camera.lookAt(0, 12, 0);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 12, 0);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 5;
    this.controls.maxDistance = 60;
    this.controls.maxPolarAngle = Math.PI * 0.8;
    this.controls.update();

    this.setupLights();
    this.setupGround();
    this.createMaterials();

    this.robotGroup = new THREE.Group();
    this.scene.add(this.robotGroup);
    this.buildRobotModel();
  }

  setupLights() {
    this.scene.add(new THREE.AmbientLight(0x8899bb, 1.8));

    const keyLight = new THREE.DirectionalLight(0xffeedd, 4.5);
    keyLight.position.set(12, 22, 15);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0002;
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xaaccff, 1.8);
    fillLight.position.set(-5, 8, -3);
    this.scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xffffff, 1.2);
    rimLight.position.set(0, 6, -8);
    this.scene.add(rimLight);
  }

  setupGround() {
    const groundGeo = new THREE.PlaneGeometry(60, 60);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x1f2229,
      roughness: 0.85,
      metalness: 0.05,
    });

    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    ground.receiveShadow = true;
    this.scene.add(ground);

    this.gridHelper = new THREE.PolarGridHelper(28, 48, 24, 256, 0x2a2d35, 0x1c1f26);
    this.gridHelper.position.y = 0.01;
    this.scene.add(this.gridHelper);
  }

  createMaterials() {
    this.materials = {
      shellWhite: new THREE.MeshStandardMaterial({ color: 0xf2f5f7, roughness: 0.42, metalness: 0.16 }),
      shellWarm: new THREE.MeshStandardMaterial({ color: 0xe3e8ef, roughness: 0.48, metalness: 0.12 }),
      bracket: new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.36, metalness: 0.22 }),
      bracketDark: new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.48, metalness: 0.18 }),

      servoBody: new THREE.MeshStandardMaterial({ color: 0x111318, roughness: 0.55, metalness: 0.28 }),
      servoLabel: new THREE.MeshStandardMaterial({ color: 0x2d333d, roughness: 0.58, metalness: 0.2 }),
      horn: new THREE.MeshStandardMaterial({ color: 0xdbe3ed, roughness: 0.28, metalness: 0.42 }),
      hornCenter: new THREE.MeshStandardMaterial({ color: 0xffb86c, roughness: 0.24, metalness: 0.46 }),
      screw: new THREE.MeshStandardMaterial({ color: 0x0b0d11, roughness: 0.6, metalness: 0.3 }),

      torsoPanel: new THREE.MeshStandardMaterial({ color: 0xf3f6fa, roughness: 0.42, metalness: 0.16 }),
      darkPanel: new THREE.MeshStandardMaterial({ color: 0x161b22, roughness: 0.58, metalness: 0.22 }),
      face: new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.5,
        metalness: 0.15,
        emissive: 0x0d1b2a,
        emissiveIntensity: 0.25,
      }),

      rightAccent: new THREE.MeshStandardMaterial({ color: 0xe06c75, roughness: 0.38, metalness: 0.18 }),
      leftAccent: new THREE.MeshStandardMaterial({ color: 0x58a6ff, roughness: 0.38, metalness: 0.18 }),
      guide: new THREE.MeshBasicMaterial({
        color: 0x9aa6b5,
        transparent: true,
        opacity: 0.35,
        depthWrite: false,
      }),
    };
  }

  registerPart(name, mesh, parent = this.robotGroup) {
    this.robotParts[name] = mesh;
    parent.add(mesh);
    return mesh;
  }

  registerJoint(name, mesh, parent = this.robotGroup) {
    this.jointParts[name] = mesh;
    parent.add(mesh);
    return mesh;
  }

  registerMarker(name, parent, position = new THREE.Vector3()) {
    const marker = new THREE.Group();
    marker.position.copy(position);
    parent.add(marker);
    this.robotRig.markers[name] = marker;
    return marker;
  }

  createGroup(name, parent, position = new THREE.Vector3()) {
    const group = new THREE.Group();
    group.name = name;
    group.position.copy(position);
    parent.add(group);
    return group;
  }

  createLabelSprite(text, color = "#ffbd75") {
    const canvas = document.createElement("canvas");
    canvas.width = 192;
    canvas.height = 80;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '700 34px "Segoe UI", Arial, sans-serif';
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 8;
    ctx.strokeStyle = "rgba(0,0,0,0.65)";
    ctx.strokeText(text, 96, 40);
    ctx.fillStyle = color;
    ctx.fillText(text, 96, 40);

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;

    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
      depthWrite: false,
    });

    const sprite = new THREE.Sprite(material);
    sprite.scale.set(2.35, 0.98, 1);
    sprite.renderOrder = 9;
    return sprite;
  }

  createBox(width, height, depth, material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  createCylinder(radiusTop, radiusBottom, height, radialSegments, material) {
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments),
      material,
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  createSphere(radius, material, segments = 24) {
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(radius, segments, Math.max(12, Math.floor(segments * 0.75))),
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

  createRingMesh() {
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(1, 0.035, 8, 48), this.materials.guide);
    mesh.renderOrder = 2;
    return mesh;
  }

  createServoCase(id, side = "r", scale = 1) {
    const group = new THREE.Group();

    const body = this.createBox(1.04 * scale, 0.62 * scale, 0.46 * scale, this.materials.servoBody);
    group.add(body);

    const sticker = this.createBox(0.72 * scale, 0.36 * scale, 0.035 * scale, this.materials.servoLabel);
    sticker.position.z = 0.248 * scale;
    group.add(sticker);

    const earTop = this.createBox(1.24 * scale, 0.12 * scale, 0.52 * scale, this.materials.bracket);
    earTop.position.y = 0.39 * scale;
    group.add(earTop);

    const earBottom = this.createBox(1.24 * scale, 0.12 * scale, 0.52 * scale, this.materials.bracket);
    earBottom.position.y = -0.39 * scale;
    group.add(earBottom);

    const clampA = this.createBox(0.12 * scale, 0.92 * scale, 0.56 * scale, this.materials.bracketDark);
    clampA.position.x = -0.62 * scale;
    group.add(clampA);

    const clampB = this.createBox(0.12 * scale, 0.92 * scale, 0.56 * scale, this.materials.bracketDark);
    clampB.position.x = 0.62 * scale;
    group.add(clampB);

    const label = this.createLabelSprite(`ID${id}`, side === "r" ? "#ff9aa2" : "#8fd0ff");
    label.position.set(0, 0.93 * scale, 0.08 * scale);
    label.visible = this.showServoLabels;
    group.add(label);
    group.userData.label = label;

    return group;
  }

  createServoHorn(axis = "x", scale = 1) {
    const group = new THREE.Group();

    const disk = this.createCylinder(0.30 * scale, 0.30 * scale, 0.12 * scale, 32, this.materials.horn);
    this.orientCylinderToAxis(disk, axis);
    group.add(disk);

    const center = this.createCylinder(0.11 * scale, 0.11 * scale, 0.145 * scale, 20, this.materials.hornCenter);
    this.orientCylinderToAxis(center, axis);
    group.add(center);

    const screwRadius = 0.20 * scale;
    for (let i = 0; i < 4; i += 1) {
      const a = (Math.PI / 2) * i;
      const screw = this.createCylinder(0.035 * scale, 0.035 * scale, 0.155 * scale, 10, this.materials.screw);
      this.orientCylinderToAxis(screw, axis);

      if (axis === "x") {
        screw.position.set(0, Math.cos(a) * screwRadius, Math.sin(a) * screwRadius);
      } else if (axis === "y") {
        screw.position.set(Math.cos(a) * screwRadius, 0, Math.sin(a) * screwRadius);
      } else {
        screw.position.set(Math.cos(a) * screwRadius, Math.sin(a) * screwRadius, 0);
      }

      group.add(screw);
    }

    return group;
  }

  createServoActuator(id, parent, options = {}) {
    const meta = SERVO_META[id] ?? {};
    const side = options.side ?? (id <= 8 ? "r" : "l");
    const sideSign = side === "r" ? 1 : -1;
    const axis = options.axis ?? meta.axis ?? "x";
    const scale = options.scale ?? 1;
    const rootPosition = options.position ?? new THREE.Vector3();
    const caseOffset = options.caseOffset ?? new THREE.Vector3(sideSign * 0.52, 0, 0);
    const caseRotation = options.caseRotation ?? new THREE.Euler(0, 0, 0);

    const root = new THREE.Group();
    root.name = `servo_ID${id}_${meta.joint ?? "unknown"}`;
    root.position.copy(rootPosition);
    root.userData.id = id;
    root.userData.joint = meta.joint;
    root.userData.axis = axis;
    root.userData.axisType = options.axisType ?? meta.axisType ?? "unknown";
    parent.add(root);

    const caseGroup = this.createServoCase(id, side, scale);
    caseGroup.name = `servo_ID${id}_case_fixed`;
    caseGroup.position.copy(caseOffset);
    caseGroup.rotation.copy(caseRotation);
    root.add(caseGroup);

    const hornGroup = new THREE.Group();
    hornGroup.name = `servo_ID${id}_horn_rotates`;
    root.add(hornGroup);

    const hornVisual = this.createServoHorn(axis, scale);
    hornGroup.add(hornVisual);

    const shaft = this.createCylinder(0.07 * scale, 0.07 * scale, Math.abs(caseOffset.x) + 0.06, 16, this.materials.hornCenter);
    shaft.rotation.z = Math.PI / 2;
    shaft.position.x = caseOffset.x * 0.5;
    root.add(shaft);

    const childRoot = new THREE.Group();
    childRoot.name = `servo_ID${id}_childRoot`;
    hornGroup.add(childRoot);

    const actuator = {
      id,
      root,
      caseGroup,
      hornGroup,
      childRoot,
      axis,
      axisType: options.axisType ?? meta.axisType ?? "unknown",
      label: caseGroup.userData.label,
      visualSign: options.visualSign ?? meta.visualSign ?? 1,
    };

    this.servoActuators[id] = actuator;
    this.servoParts[id] = root;

    return actuator;
  }

  applyServoAngle(id, angle) {
    const actuator = this.servoActuators[id];
    if (!actuator) return;

    const finalAngle = angle * actuator.visualSign;
    actuator.hornGroup.rotation.set(0, 0, 0);

    if (actuator.axis === "x") actuator.hornGroup.rotation.x = finalAngle;
    if (actuator.axis === "y") actuator.hornGroup.rotation.y = finalAngle;
    if (actuator.axis === "z") actuator.hornGroup.rotation.z = finalAngle;
  }

  createLimbPlate(name, parent, length, width, depth, material, options = {}) {
    const group = new THREE.Group();
    group.name = name;
    parent.add(group);

    const zSpread = options.zSpread ?? depth * 0.7;
    const railWidth = options.railWidth ?? width * 0.42;

    const railA = this.createBox(railWidth, length, depth, material);
    railA.position.set(0, -length * 0.5, -zSpread * 0.5);
    group.add(railA);

    const railB = this.createBox(railWidth, length, depth, material);
    railB.position.set(0, -length * 0.5, zSpread * 0.5);
    group.add(railB);

    const capTop = this.createBox(width, 0.18, depth * 1.5, this.materials.bracketDark);
    capTop.position.y = -0.12;
    group.add(capTop);

    const capBottom = this.createBox(width, 0.18, depth * 1.5, this.materials.bracketDark);
    capBottom.position.y = -length + 0.12;
    group.add(capBottom);

    const holeCount = Math.max(2, Math.floor(length / 1.6));
    for (let i = 0; i < holeCount; i += 1) {
      const t = (i + 1) / (holeCount + 1);
      const y = -length * t;

      for (const z of [-zSpread * 0.5, zSpread * 0.5]) {
        const hole = this.createCylinder(0.075, 0.075, 0.018, 16, this.materials.screw);
        hole.rotation.x = Math.PI / 2;
        hole.position.set(0, y, z + Math.sign(z) * (depth * 0.52));
        group.add(hole);
      }
    }

    return group;
  }

  createFootMesh(side = "r") {
    const group = new THREE.Group();
    const sign = side === "r" ? 1 : -1;

    const plate = this.createBox(
      FOOT_PLATE.halfWidth * 2.15,
      FOOT_PLATE.thickness,
      FOOT_PLATE.halfLength * 2.2,
      this.materials.shellWhite,
    );
    plate.position.set(sign * 0.05, -FOOT_PLATE.thickness * 0.5, FOOT_CENTER_FORWARD);
    group.add(plate);

    const toe = this.createBox(
      FOOT_PLATE.halfWidth * 1.8,
      FOOT_PLATE.thickness * 0.62,
      0.46,
      this.materials.bracketDark,
    );
    toe.position.set(sign * 0.05, -FOOT_PLATE.thickness * 0.18, FOOT_CENTER_FORWARD + FOOT_PLATE.halfLength * 0.92);
    group.add(toe);

    const heel = this.createBox(
      FOOT_PLATE.halfWidth * 1.65,
      FOOT_PLATE.thickness * 0.55,
      0.36,
      this.materials.bracketDark,
    );
    heel.position.set(sign * 0.05, -FOOT_PLATE.thickness * 0.14, FOOT_CENTER_FORWARD - FOOT_PLATE.halfLength * 0.92);
    group.add(heel);

    return group;
  }

  createHandMesh(side = "r") {
    const group = new THREE.Group();
    const sign = side === "r" ? 1 : -1;

    const palm = this.createBox(0.52, 0.36, 0.44, this.materials.shellWhite);
    palm.position.y = -0.18;
    group.add(palm);

    const fingerA = this.createBox(0.14, 0.52, 0.12, this.materials.bracketDark);
    fingerA.position.set(sign * 0.16, -0.56, 0.12);
    group.add(fingerA);

    const fingerB = this.createBox(0.14, 0.52, 0.12, this.materials.bracketDark);
    fingerB.position.set(-sign * 0.16, -0.56, 0.12);
    group.add(fingerB);

    return group;
  }

  getMeshWorldMinY(object3d) {
    if (!object3d) return 0;

    object3d.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(object3d);
    return box.min.y;
  }

  clearRobotGroup() {
    while (this.robotGroup.children.length > 0) {
      this.robotGroup.remove(this.robotGroup.children[0]);
    }

    this.robotParts = {};
    this.jointParts = {};
    this.servoParts = {};
    this.servoActuators = {};
    this.robotRig = { pivots: {}, markers: {} };
  }

  buildRobotModel() {
    this.clearRobotGroup();
    const m = this.materials;

    const bodyRoot = this.createGroup("bodyRoot", this.robotGroup, new THREE.Vector3(0, HIP_BASE_HEIGHT, 0));
    this.robotRig.pivots.bodyRoot = bodyRoot;

    const pelvis = this.registerPart("pelvis", this.createBox(HIP_HALF_WIDTH * 1.55, 0.78, 0.86, m.shellWhite), bodyRoot);
    pelvis.position.y = 0.35;

    const pelvisCore = this.registerPart("pelvisCore", this.createBox(HIP_HALF_WIDTH * 1.1, 0.48, 0.58, m.darkPanel), bodyRoot);
    pelvisCore.position.y = 0.38;
    pelvisCore.position.z = 0.06;

    const spinePanel = this.registerPart("spinePanel", this.createBox(1.22, SEGMENTS.torso.length * 0.76, 0.58, m.darkPanel), bodyRoot);
    spinePanel.position.y = SEGMENTS.torso.length * 0.47;
    spinePanel.position.z = -0.08;

    const chest = this.registerPart("chest", this.createBox(SHOULDER_HALF_WIDTH * 1.16, 1.65, 1.02, m.torsoPanel), bodyRoot);
    chest.position.y = SEGMENTS.torso.length * 0.67;

    const chestCore = this.registerPart("chestCore", this.createBox(1.48, 1.2, 0.18, m.darkPanel), bodyRoot);
    chestCore.position.y = SEGMENTS.torso.length * 0.67;
    chestCore.position.z = 0.56;

    const shoulderBar = this.registerPart("shoulderBar", this.createBox(SHOULDER_HALF_WIDTH * 2.1, 0.38, 0.42, m.shellWhite), bodyRoot);
    shoulderBar.position.y = SEGMENTS.torso.length;

    const neck = this.registerPart("neck", this.createCylinder(0.22, 0.22, 0.72, 20, m.bracketDark), bodyRoot);
    neck.position.y = SEGMENTS.torso.length + 0.44;

    const head = this.registerPart("head", this.createBox(1.55, 1.28, 1.18, m.shellWhite), bodyRoot);
    head.position.y = SEGMENTS.torso.length + 1.45;

    const face = this.registerPart("face", this.createBox(0.86, 0.34, 0.075, m.face), head);
    face.position.set(0, 0.05, 0.61);

    const eyeL = this.registerPart("leftEyeGlow", this.createBox(0.16, 0.08, 0.03, m.leftAccent), face);
    eyeL.position.set(-0.22, 0.02, 0.045);

    const eyeR = this.registerPart("rightEyeGlow", this.createBox(0.16, 0.08, 0.03, m.rightAccent), face);
    eyeR.position.set(0.22, 0.02, 0.045);

    const shoulderGuide = this.registerPart("shoulderGuide", this.createRingMesh(), bodyRoot);
    shoulderGuide.position.y = SEGMENTS.torso.length;
    shoulderGuide.scale.set(2.6, 2.6, 1);
    shoulderGuide.rotation.x = Math.PI / 2;

    const pelvisGuide = this.registerPart("pelvisGuide", this.createRingMesh(), bodyRoot);
    pelvisGuide.position.y = 0.15;
    pelvisGuide.scale.set(1.65, 1.65, 1);
    pelvisGuide.rotation.x = Math.PI / 2;

    this.buildLeg("right", bodyRoot);
    this.buildLeg("left", bodyRoot);
    this.buildArm("right", bodyRoot);
    this.buildArm("left", bodyRoot);
  }

  buildLeg(side, bodyRoot) {
    const isRight = side === "right";
    const sign = isRight ? 1 : -1;
    const prefix = isRight ? "r" : "l";
    const sideKey = isRight ? "r" : "l";

    const ids = isRight
      ? { hipYaw: 1, ankle: 2, knee: 3, hipPitch: 4, hipRoll: 5 }
      : { hipYaw: 9, ankle: 10, knee: 11, hipPitch: 12, hipRoll: 13 };

    const hipAnchor = this.createGroup(
      `${side}HipAnchor`,
      bodyRoot,
      new THREE.Vector3(HIP_HALF_WIDTH * sign, 0.15, 0),
    );

    this.registerMarker(`${prefix}Hip`, hipAnchor);

    const hipYaw = this.createServoActuator(ids.hipYaw, hipAnchor, {
      side: sideKey,
      axis: "y",
      scale: 0.76,
      caseOffset: v3(sign * 0.62, 0.02, 0.08),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const hipYawBracket = this.createBox(0.42, 0.34, 0.88, this.materials.bracket);
    hipYawBracket.position.set(0, -0.14, 0);
    hipYaw.childRoot.add(hipYawBracket);

    const hipRoll = this.createServoActuator(ids.hipRoll, hipYaw.childRoot, {
      side: sideKey,
      axis: "z",
      scale: 0.74,
      position: v3(0, -0.42, 0),
      caseOffset: v3(sign * 0.55, 0, -0.02),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const hipRollBracket = this.createBox(0.54, 0.42, 0.92, this.materials.bracket);
    hipRollBracket.position.set(0, -0.08, 0);
    hipRoll.childRoot.add(hipRollBracket);

    const hipPitch = this.createServoActuator(ids.hipPitch, hipRoll.childRoot, {
      side: sideKey,
      axis: "x",
      scale: 0.76,
      position: v3(0, -0.48, 0),
      caseOffset: v3(sign * 0.58, 0.02, 0.02),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    this.createLimbPlate(
      `${prefix}UpperLegPlate`,
      hipPitch.childRoot,
      SEGMENTS.upper_leg.length,
      0.68,
      0.22,
      this.materials.shellWhite,
      { zSpread: 0.62 },
    );

    const kneeAnchor = this.createGroup(
      `${side}KneeServoMount`,
      hipPitch.childRoot,
      new THREE.Vector3(0, -SEGMENTS.upper_leg.length, 0),
    );
    this.registerMarker(`${prefix}Knee`, kneeAnchor);

    const knee = this.createServoActuator(ids.knee, kneeAnchor, {
      side: sideKey,
      axis: "x",
      scale: 0.76,
      caseOffset: v3(sign * 0.56, 0, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const kneeBracket = this.createBox(0.58, 0.54, 0.96, this.materials.bracket);
    kneeBracket.position.set(0, -0.08, 0);
    knee.childRoot.add(kneeBracket);

    this.createLimbPlate(
      `${prefix}LowerLegPlate`,
      knee.childRoot,
      SEGMENTS.lower_leg.length,
      0.58,
      0.20,
      this.materials.shellWarm,
      { zSpread: 0.58 },
    );

    const ankleAnchor = this.createGroup(
      `${side}AnkleServoMount`,
      knee.childRoot,
      new THREE.Vector3(0, -SEGMENTS.lower_leg.length, 0),
    );
    this.registerMarker(`${prefix}Ankle`, ankleAnchor);

    const ankle = this.createServoActuator(ids.ankle, ankleAnchor, {
      side: sideKey,
      axis: "x",
      scale: 0.70,
      caseOffset: v3(sign * 0.52, 0.02, 0.08),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const footMount = this.createBox(0.82, 0.30, 0.88, this.materials.bracket);
    footMount.position.set(0, -0.18, 0.14);
    ankle.childRoot.add(footMount);

    const foot = this.createFootMesh(sideKey);
    ankle.childRoot.add(foot);
    this.robotParts[`${prefix}FootBox`] = foot;
    this.registerMarker(`${prefix}Foot`, ankle.childRoot, new THREE.Vector3(0, -FOOT_PLATE.thickness * 0.5, FOOT_CENTER_FORWARD));
  }

  buildArm(side, bodyRoot) {
    const isRight = side === "right";
    const sign = isRight ? 1 : -1;
    const prefix = isRight ? "r" : "l";
    const sideKey = isRight ? "r" : "l";

    const ids = isRight
      ? { shoulderPitch: 8, shoulderAxis2: 7, elbow: 6 }
      : { shoulderPitch: 16, shoulderAxis2: 15, elbow: 14 };

    const shoulderAnchor = this.createGroup(
      `${side}ShoulderAnchor`,
      bodyRoot,
      new THREE.Vector3(SHOULDER_HALF_WIDTH * sign, SEGMENTS.torso.length, 0),
    );

    this.registerMarker(`${prefix}Shoulder`, shoulderAnchor);

    const shoulderPitch = this.createServoActuator(ids.shoulderPitch, shoulderAnchor, {
      side: sideKey,
      axis: "x",
      scale: 0.72,
      caseOffset: v3(sign * 0.56, 0, 0.05),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const shoulderYoke = this.createBox(0.54, 0.42, 0.92, this.materials.bracket);
    shoulderYoke.position.set(0, -0.12, 0);
    shoulderPitch.childRoot.add(shoulderYoke);

    const shoulderAxis2 = this.createServoActuator(ids.shoulderAxis2, shoulderPitch.childRoot, {
      side: sideKey,
      axis: "z",
      scale: 0.70,
      position: v3(0, -0.56, 0),
      caseOffset: v3(sign * 0.54, 0, -0.06),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    this.createLimbPlate(
      `${prefix}UpperArmPlate`,
      shoulderAxis2.childRoot,
      SEGMENTS.upper_arm.length,
      0.54,
      0.18,
      this.materials.shellWhite,
      { zSpread: 0.50 },
    );

    const elbowAnchor = this.createGroup(
      `${side}ElbowServoMount`,
      shoulderAxis2.childRoot,
      new THREE.Vector3(0, -SEGMENTS.upper_arm.length, 0),
    );
    this.registerMarker(`${prefix}Elbow`, elbowAnchor);

    const elbow = this.createServoActuator(ids.elbow, elbowAnchor, {
      side: sideKey,
      axis: "x",
      scale: 0.68,
      caseOffset: v3(sign * 0.50, 0, 0),
      caseRotation: new THREE.Euler(0, 0, Math.PI / 2),
    });

    const elbowBracket = this.createBox(0.50, 0.42, 0.78, this.materials.bracket);
    elbowBracket.position.set(0, -0.10, 0);
    elbow.childRoot.add(elbowBracket);

    this.createLimbPlate(
      `${prefix}ForearmPlate`,
      elbow.childRoot,
      SEGMENTS.forearm.length,
      0.44,
      0.16,
      this.materials.shellWarm,
      { zSpread: 0.42 },
    );

    const handAnchor = this.createGroup(
      `${side}HandMount`,
      elbow.childRoot,
      new THREE.Vector3(0, -SEGMENTS.forearm.length, 0),
    );
    this.registerMarker(`${prefix}Hand`, handAnchor);

    const hand = this.createHandMesh(sideKey);
    handAnchor.add(hand);
    this.robotParts[`${prefix}Hand`] = hand;
  }

  setPose(pose) {
    const angles = poseToJointAngles(pose);

    for (const [jointName, servoId] of Object.entries(JOINT_TO_SERVO_ID)) {
      this.applyServoAngle(servoId, angles[jointName] || 0);
    }

    this.robotGroup.position.set(0, 0, 0);
    this.robotGroup.updateMatrixWorld(true);

    const minFootY = Math.min(
      this.getMeshWorldMinY(this.robotParts.rFootBox),
      this.getMeshWorldMinY(this.robotParts.lFootBox),
    );

    this.robotGroup.position.y = -minFootY + 0.02;
    this.robotGroup.updateMatrixWorld(true);
  }

  toggleGrid() {
    this.showGrid = !this.showGrid;
    this.gridHelper.visible = this.showGrid;
    return this.showGrid;
  }

  toggleServoLabels() {
    this.showServoLabels = !this.showServoLabels;

    Object.values(this.servoActuators).forEach((actuator) => {
      if (actuator.label) {
        actuator.label.visible = this.showServoLabels;
      }
    });

    return this.showServoLabels;
  }

  resetView() {
    this.camera.position.set(8, 18, 28);
    this.controls.target.set(0, 12, 0);
    this.controls.update();
  }

  resize() {
    const rect = this.viewport.getBoundingClientRect();
    this.renderer.setSize(rect.width, rect.height);
    this.camera.aspect = rect.width / Math.max(rect.height, 1);
    this.camera.updateProjectionMatrix();
  }

  start() {
    const renderLoop = () => {
      this.animationFrame = requestAnimationFrame(renderLoop);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };

    renderLoop();
  }
}
