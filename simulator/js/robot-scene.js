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
} from "./config.js";

function pyOffsetToThree(offsetPy) {
  return new THREE.Vector3(-offsetPy[1], offsetPy[2], offsetPy[0]);
}

export class RobotScene {
  constructor(viewport) {
    this.viewport = viewport;
    this.showGrid = true;
    this.showServoLabels = true;

    this.robotParts = {};
    this.jointParts = {};
    this.servoParts = {};
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
      right: new THREE.MeshStandardMaterial({ color: 0xe06c75, roughness: 0.32, metalness: 0.34 }),
      left: new THREE.MeshStandardMaterial({ color: 0x58a6ff, roughness: 0.32, metalness: 0.34 }),
      rightDark: new THREE.MeshStandardMaterial({ color: 0x9f4b53, roughness: 0.45, metalness: 0.22 }),
      leftDark: new THREE.MeshStandardMaterial({ color: 0x3e7fb7, roughness: 0.45, metalness: 0.22 }),
      torso: new THREE.MeshStandardMaterial({ color: 0x4a5568, roughness: 0.42, metalness: 0.34 }),
      chest: new THREE.MeshStandardMaterial({ color: 0x66758a, roughness: 0.38, metalness: 0.35 }),
      pelvis: new THREE.MeshStandardMaterial({ color: 0x3d4758, roughness: 0.46, metalness: 0.28 }),
      head: new THREE.MeshStandardMaterial({ color: 0x9aa6b5, roughness: 0.3, metalness: 0.42 }),
      face: new THREE.MeshStandardMaterial({
        color: 0x111827,
        roughness: 0.55,
        metalness: 0.12,
        emissive: 0x0d1b2a,
        emissiveIntensity: 0.2,
      }),
      joint: new THREE.MeshStandardMaterial({ color: 0xb8c1ce, roughness: 0.22, metalness: 0.55 }),
      jointDark: new THREE.MeshStandardMaterial({ color: 0x6d7888, roughness: 0.35, metalness: 0.38 }),
      foot: new THREE.MeshStandardMaterial({ color: 0x4d5869, roughness: 0.52, metalness: 0.22 }),
      servoBody: new THREE.MeshStandardMaterial({ color: 0x20242b, roughness: 0.5, metalness: 0.25 }),
      servoFace: new THREE.MeshStandardMaterial({ color: 0xd8dde6, roughness: 0.28, metalness: 0.35 }),
      servoAxis: new THREE.MeshStandardMaterial({ color: 0xffb86c, roughness: 0.24, metalness: 0.45 }),
      screw: new THREE.MeshStandardMaterial({ color: 0x0f1116, roughness: 0.55, metalness: 0.25 }),
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

  registerServo(id, group, parent = this.robotGroup) {
    this.servoParts[id] = group;
    parent.add(group);
    return group;
  }

  registerPivot(name, parent, position = new THREE.Vector3()) {
    const pivot = new THREE.Group();
    pivot.position.copy(position);
    parent.add(pivot);
    this.robotRig.pivots[name] = pivot;
    return pivot;
  }

  registerMarker(name, parent, position = new THREE.Vector3()) {
    const marker = new THREE.Group();
    marker.position.copy(position);
    parent.add(marker);
    this.robotRig.markers[name] = marker;
    return marker;
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

  createServoModule(id, side = "r") {
    const group = new THREE.Group();
    group.userData.id = id;
    group.userData.side = side;

    const body = new THREE.Mesh(new THREE.BoxGeometry(1.02, 0.58, 0.34), this.materials.servoBody);
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);

    const face = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.42, 0.08), this.materials.servoFace);
    face.position.z = 0.20;
    face.castShadow = true;
    group.add(face);

    const axis = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.10, 20), this.materials.servoAxis);
    axis.rotation.x = Math.PI / 2;
    axis.position.z = 0.29;
    axis.castShadow = true;
    group.add(axis);

    for (const sx of [-0.31, 0.31]) {
      for (const sy of [-0.15, 0.15]) {
        const screw = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.04, 10), this.materials.screw);
        screw.rotation.x = Math.PI / 2;
        screw.position.set(sx, sy, 0.255);
        group.add(screw);
      }
    }

    const label = this.createLabelSprite(`ID${id}`, side === "r" ? "#ff9aa2" : "#8fd0ff");
    label.position.set(0, 0.88, 0.05);
    group.add(label);
    group.userData.label = label;
    return group;
  }

  lookServoOutward(group, side = "r", yawExtra = 0) {
    const yaw = side === "r" ? Math.PI / 2 : -Math.PI / 2;
    group.rotation.set(0, yaw + yawExtra, 0);
  }

  attachServo(id, parent, side = "r", offsetPy = [0, 0, 0], scale = 1, yawExtra = 0) {
    const group = this.createServoModule(id, side);
    group.position.copy(pyOffsetToThree(offsetPy));
    group.scale.setScalar(scale);
    this.lookServoOutward(group, side, yawExtra);
    group.visible = this.showServoLabels;
    if (group.userData.label) group.userData.label.visible = this.showServoLabels;
    return this.registerServo(id, group, parent);
  }

  createBoneMesh(material, radialSegments = 20) {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, radialSegments), material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  createBoxMesh(material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  createSphereMesh(material, segments = 20) {
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(1, segments, Math.max(12, Math.floor(segments * 0.75))),
      material,
    );
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }

  createRingMesh(color) {
    const material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(1, 0.035, 8, 48), material);
    mesh.renderOrder = 2;
    return mesh;
  }

  createScaledBone(length, radius, material, radialSegments = 20) {
    const mesh = this.createBoneMesh(material, radialSegments);
    mesh.scale.set(radius, length, radius);
    mesh.position.y = -length * 0.5;
    return mesh;
  }

  createScaledBox(width, height, depth, material) {
    const mesh = this.createBoxMesh(material);
    mesh.scale.set(width, height, depth);
    return mesh;
  }

  createScaledSphere(radius, material, segments = 20) {
    const mesh = this.createSphereMesh(material, segments);
    mesh.scale.setScalar(radius);
    return mesh;
  }

  createFootMesh(side = "r") {
    const mesh = this.createScaledBox(
      FOOT_PLATE.halfWidth * 2.0,
      FOOT_PLATE.thickness,
      FOOT_PLATE.halfLength * 2.0,
      this.materials.foot,
    );
    mesh.position.set(side === "r" ? 0.05 : -0.05, -FOOT_PLATE.thickness * 0.5, FOOT_CENTER_FORWARD);
    return mesh;
  }

  createHandMesh(material) {
    const mesh = this.createScaledBox(0.52, 0.36, 0.44, material);
    mesh.position.y = -0.20;
    return mesh;
  }

  getMeshWorldMinY(mesh) {
    if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
    const box = mesh.geometry.boundingBox;
    const corners = [
      new THREE.Vector3(box.min.x, box.min.y, box.min.z),
      new THREE.Vector3(box.min.x, box.min.y, box.max.z),
      new THREE.Vector3(box.min.x, box.max.y, box.min.z),
      new THREE.Vector3(box.min.x, box.max.y, box.max.z),
      new THREE.Vector3(box.max.x, box.min.y, box.min.z),
      new THREE.Vector3(box.max.x, box.min.y, box.max.z),
      new THREE.Vector3(box.max.x, box.max.y, box.min.z),
      new THREE.Vector3(box.max.x, box.max.y, box.max.z),
    ];

    let minY = Infinity;
    for (const corner of corners) {
      corner.applyMatrix4(mesh.matrixWorld);
      minY = Math.min(minY, corner.y);
    }
    return minY;
  }

  clearRobotGroup() {
    while (this.robotGroup.children.length > 0) {
      this.robotGroup.remove(this.robotGroup.children[0]);
    }
    this.robotParts = {};
    this.jointParts = {};
    this.servoParts = {};
    this.robotRig = { pivots: {}, markers: {} };
  }

  buildRobotModel() {
    this.clearRobotGroup();
    const m = this.materials;

    const bodyRoot = this.registerPivot("bodyRoot", this.robotGroup, new THREE.Vector3(0, HIP_BASE_HEIGHT, 0));

    this.registerPart("spine", this.createScaledBone(SEGMENTS.torso.length, 0.32, m.torso, 24), bodyRoot).position.y = SEGMENTS.torso.length * 0.5;
    this.registerPart("pelvis", this.createScaledBox(HIP_HALF_WIDTH * 1.24, 0.95, 0.82, m.pelvis), bodyRoot).position.y = 0.62;
    this.registerPart("hipBar", this.createScaledBox(HIP_HALF_WIDTH * 2.0, 0.32, 0.36, m.pelvis), bodyRoot).position.y = 0.14;
    this.registerPart("chest", this.createScaledBox(SHOULDER_HALF_WIDTH * 1.16, 1.45, 1.00, m.chest), bodyRoot).position.y = SEGMENTS.torso.length * 0.58;
    this.registerPart("shoulderBar", this.createScaledBox(SHOULDER_HALF_WIDTH * 2.0, 0.34, 0.34, m.torso), bodyRoot).position.y = SEGMENTS.torso.length;
    this.registerPart("neck", this.createScaledBone(0.85, 0.24, m.jointDark, 16), bodyRoot).position.y = SEGMENTS.torso.length + 0.425;

    const head = this.registerPart("head", this.createScaledSphere(1.08, m.head, 28), bodyRoot);
    head.position.y = SEGMENTS.torso.length + 1.85;
    const face = this.registerPart("face", this.createScaledBox(0.78, 0.42, 0.06, m.face), head);
    face.position.set(0, 0.05, 0.86);

    const shoulderGuide = this.registerPart("shoulderGuide", this.createRingMesh(0x9aa6b5), bodyRoot);
    shoulderGuide.position.y = SEGMENTS.torso.length;
    shoulderGuide.scale.set(2.60, 2.60, 1);
    shoulderGuide.rotation.x = Math.PI / 2;

    const pelvisGuide = this.registerPart("pelvisGuide", this.createRingMesh(0x9aa6b5), bodyRoot);
    pelvisGuide.position.y = 0.14;
    pelvisGuide.scale.set(1.65, 1.65, 1);
    pelvisGuide.rotation.x = Math.PI / 2;

    this.buildLeg("right", bodyRoot, m.right, m.rightDark);
    this.buildLeg("left", bodyRoot, m.left, m.leftDark);
    this.buildArm("right", bodyRoot, m.right, m.rightDark);
    this.buildArm("left", bodyRoot, m.left, m.leftDark);
  }

  buildLeg(side, bodyRoot, upperMaterial, lowerMaterial) {
    const isRight = side === "right";
    const sign = isRight ? 1 : -1;
    const prefix = isRight ? "r" : "l";
    const anchor = this.registerPivot(`${side}HipAnchor`, bodyRoot, new THREE.Vector3(HIP_HALF_WIDTH * sign, 0, 0));

    this.registerJoint(`${prefix}Hip`, this.createScaledSphere(0.52, this.materials.joint, 20), anchor);
    const yaw = this.registerPivot(`${side}HipYawPivot`, anchor);
    const roll = this.registerPivot(`${side}HipRollPivot`, yaw);
    const pitch = this.registerPivot(`${side}HipPitchPivot`, roll);
    this.registerMarker(`${prefix}Hip`, pitch);
    this.registerPart(`${prefix}UpperLeg`, this.createScaledBone(SEGMENTS.upper_leg.length, 0.36, upperMaterial, 22), pitch);

    const knee = this.registerPivot(`${side}KneePivot`, pitch, new THREE.Vector3(0, -SEGMENTS.upper_leg.length, 0));
    this.registerJoint(`${prefix}Knee`, this.createScaledSphere(0.46, this.materials.joint, 20), knee);
    this.registerMarker(`${prefix}Knee`, knee);
    this.registerPart(`${prefix}LowerLeg`, this.createScaledBone(SEGMENTS.lower_leg.length, 0.30, lowerMaterial, 22), knee);

    const ankle = this.registerPivot(`${side}AnklePivot`, knee, new THREE.Vector3(0, -SEGMENTS.lower_leg.length, 0));
    this.registerJoint(`${prefix}Ankle`, this.createScaledSphere(0.38, this.materials.joint, 20), ankle);
    this.registerMarker(`${prefix}Ankle`, ankle);
    this.registerPart(`${prefix}FootBox`, this.createFootMesh(isRight ? "r" : "l"), ankle);
    this.registerMarker(`${prefix}Foot`, ankle, new THREE.Vector3(0, -FOOT_PLATE.thickness * 0.5, FOOT_CENTER_FORWARD));

    this.attachServo(isRight ? 1 : 9, yaw, isRight ? "r" : "l", [0.04, isRight ? -0.52 : 0.52, 0.42], 0.60, 0.00);
    this.attachServo(isRight ? 5 : 13, roll, isRight ? "r" : "l", [-0.16, isRight ? -0.48 : 0.48, 0.20], 0.64, 0.00);
    this.attachServo(isRight ? 4 : 12, pitch, isRight ? "r" : "l", [0.08, isRight ? -0.45 : 0.45, -0.70], 0.66, 0.00);
    this.attachServo(isRight ? 3 : 11, knee, isRight ? "r" : "l", [0.00, isRight ? -0.42 : 0.42, 0.00], 0.66, 0.00);
    this.attachServo(isRight ? 2 : 10, ankle, isRight ? "r" : "l", [0.00, isRight ? -0.38 : 0.38, 0.30], 0.60, 0.00);
  }

  buildArm(side, bodyRoot, upperMaterial, lowerMaterial) {
    const isRight = side === "right";
    const sign = isRight ? 1 : -1;
    const prefix = isRight ? "r" : "l";
    const anchor = this.registerPivot(`${side}ShoulderAnchor`, bodyRoot, new THREE.Vector3(SHOULDER_HALF_WIDTH * sign, SEGMENTS.torso.length, 0));

    this.registerJoint(`${prefix}Shoulder`, this.createScaledSphere(0.50, this.materials.joint, 20), anchor);
    const axis1 = this.registerPivot(`${side}ShoulderAxis1Pivot`, anchor);
    const axis2 = this.registerPivot(`${side}ShoulderAxis2Pivot`, axis1);
    this.registerMarker(`${prefix}Shoulder`, axis2);
    this.registerPart(`${prefix}UpperArm`, this.createScaledBone(SEGMENTS.upper_arm.length, 0.30, upperMaterial, 22), axis2);

    const elbow = this.registerPivot(`${side}ElbowPivot`, axis2, new THREE.Vector3(0, -SEGMENTS.upper_arm.length, 0));
    this.registerJoint(`${prefix}Elbow`, this.createScaledSphere(0.42, this.materials.joint, 20), elbow);
    this.registerMarker(`${prefix}Elbow`, elbow);
    this.registerPart(`${prefix}Forearm`, this.createScaledBone(SEGMENTS.forearm.length, 0.24, lowerMaterial, 22), elbow);

    const wrist = this.registerPivot(`${side}WristAnchor`, elbow, new THREE.Vector3(0, -SEGMENTS.forearm.length, 0));
    this.registerJoint(`${prefix}Wrist`, this.createScaledSphere(0.32, this.materials.joint, 18), wrist);
    this.registerMarker(`${prefix}Hand`, wrist);
    this.registerPart(`${prefix}Hand`, this.createHandMesh(lowerMaterial), wrist);

    this.attachServo(isRight ? 8 : 16, axis1, isRight ? "r" : "l", [0.10, isRight ? -0.52 : 0.52, 0.38], 0.68, 0.00);
    this.attachServo(isRight ? 7 : 15, axis2, isRight ? "r" : "l", [0.02, isRight ? -0.52 : 0.52, -0.38], 0.64, 0.00);
    this.attachServo(isRight ? 6 : 14, elbow, isRight ? "r" : "l", [0.00, isRight ? -0.42 : 0.42, 0.00], 0.60, 0.00);
  }

  setPose(pose) {
    const angles = poseToJointAngles(pose);
    const pivots = this.robotRig.pivots;

    pivots.rightHipYawPivot.rotation.set(0, angles.r_hip_yaw || 0, 0);
    pivots.rightHipRollPivot.rotation.set(0, 0, angles.r_hip_roll || 0);
    pivots.rightHipPitchPivot.rotation.set(angles.r_hip_pitch || 0, 0, 0);
    pivots.rightKneePivot.rotation.set(angles.r_knee || 0, 0, 0);
    // ID2 轴向仍需实测确认，目前只临时按单轴 hinge 渲染，避免恢复到万向近似。
    pivots.rightAnklePivot.rotation.set(angles.r_ankle_axis || 0, 0, 0);

    pivots.leftHipYawPivot.rotation.set(0, angles.l_hip_yaw || 0, 0);
    pivots.leftHipRollPivot.rotation.set(0, 0, -(angles.l_hip_roll || 0));
    pivots.leftHipPitchPivot.rotation.set(angles.l_hip_pitch || 0, 0, 0);
    pivots.leftKneePivot.rotation.set(angles.l_knee || 0, 0, 0);
    // ID10 轴向仍需实测确认，目前只临时按单轴 hinge 渲染，避免恢复到万向近似。
    pivots.leftAnklePivot.rotation.set(angles.l_ankle_axis || 0, 0, 0);

    pivots.rightShoulderAxis1Pivot.rotation.set(angles.r_shoulder_pitch || 0, 0, 0);
    // ID7 轴向仍需实测确认，目前只临时按单轴侧抬渲染，不宣称已确认是 yaw 或 roll。
    pivots.rightShoulderAxis2Pivot.rotation.set(0, 0, -(angles.r_shoulder_axis_2 || 0));
    pivots.rightElbowPivot.rotation.set(angles.r_elbow || 0, 0, 0);

    pivots.leftShoulderAxis1Pivot.rotation.set(angles.l_shoulder_pitch || 0, 0, 0);
    // ID15 轴向仍需实测确认，目前只临时按单轴侧抬渲染，不宣称已确认是 yaw 或 roll。
    pivots.leftShoulderAxis2Pivot.rotation.set(0, 0, angles.l_shoulder_axis_2 || 0);
    pivots.leftElbowPivot.rotation.set(angles.l_elbow || 0, 0, 0);

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
    Object.values(this.servoParts).forEach((group) => {
      group.visible = this.showServoLabels;
      if (group.userData.label) group.userData.label.visible = this.showServoLabels;
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
