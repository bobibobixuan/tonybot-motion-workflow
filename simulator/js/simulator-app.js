import {
  BACKWARD_TEST_FRAMES,
  DEFAULT_POSE,
  PRESETS,
  PRESET_I18N_KEYS,
  SERVO_LAYOUT,
  SLIDER_GROUPS,
  formatServoAngle,
  formatServoOffset,
  getServoById,
} from "./config.js";

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export class SimulatorApp {
  constructor({ scene, t, parseRobFile, servoMap }) {
    this.scene = scene;
    this.t = t;
    this.parseRobFile = parseRobFile;
    this.servoMap = this.normalizeServoMap(servoMap);

    this.currentPose = [...DEFAULT_POSE];
    this.selectedChannel = 7;
    this.sliderInputs = [];
    this.sliderRows = new Map();
    this.mappingCards = new Map();
    this.loadedFrames = null;
    this.currentFrameIdx = 0;
    this.playbackTimer = null;
    this.playbackSpeed = 1;

    this.elements = {
      viewport: document.getElementById("viewport"),
      topbarTitle: document.querySelector("#topbar h1"),
      frameSummary: document.getElementById("frame-summary"),
      actionSelect: document.getElementById("action-select"),
      panelPresets: document.getElementById("panel-presets"),
      slidersScroll: document.getElementById("sliders-scroll"),
      timeline: document.getElementById("timeline"),
      frameInfo: document.getElementById("frame-info"),
      frameSlider: document.getElementById("frame-slider"),
      speedSelect: document.getElementById("speed-select"),
      jumpWarning: document.getElementById("jump-warning"),
      overlay: document.getElementById("overlay-msg"),
      fileInput: document.getElementById("file-input"),
      btnCopyPose: document.getElementById("btn-copy-pose"),
      btnLoadRob: document.getElementById("btn-load-rob"),
      btnResetView: document.getElementById("btn-reset-view"),
      btnToggleGrid: document.getElementById("btn-toggle-grid"),
      btnToggleServoLabels: document.getElementById("btn-toggle-servo-labels"),
      btnPrev: document.getElementById("btn-prev"),
      btnPlay: document.getElementById("btn-play"),
      btnNext: document.getElementById("btn-next"),
      poseArray: document.getElementById("pose-array"),
      poseStats: document.getElementById("pose-stats"),
      focusId: document.getElementById("focus-id"),
      focusName: document.getElementById("focus-name"),
      focusJoint: document.getElementById("focus-joint"),
      focusAxis: document.getElementById("focus-axis"),
      focusNeutral: document.getElementById("focus-neutral"),
      focusCurrent: document.getElementById("focus-current"),
      focusOffset: document.getElementById("focus-offset"),
      focusMirror: document.getElementById("focus-mirror"),
      focusTested: document.getElementById("focus-tested"),
      focusMotion: document.getElementById("focus-motion"),
      mappingGrid: document.getElementById("mapping-grid"),
      mirrorList: document.getElementById("mirror-list"),
    };
  }

  normalizeServoMap(servoMap) {
    const source = Array.isArray(servoMap) && servoMap.length === 16 ? servoMap : SERVO_LAYOUT;
    return source
      .map((servo) => ({
        id: servo.id,
        channel: servo.channel,
        joint: servo.joint,
        labelZh: servo.labelZh ?? servo.label_zh,
        labelEn: servo.labelEn ?? servo.label_en,
        axisType: servo.axisType ?? servo.axis_type,
        neutral: servo.neutral,
        direction: servo.direction ?? servo.direction_sign,
        testedChange: servo.testedChange ?? servo.tested_change,
        testedMotionZh: servo.testedMotionZh ?? servo.tested_motion_zh,
        motionZh: servo.motionZh ?? servo.motion_zh,
        group: servo.group,
        mirrorId: servo.mirrorId ?? servo.mirror_id,
      }))
      .sort((left, right) => left.channel - right.channel);
  }

  init() {
    this.renderMappingGrid();
    this.renderMirrorPairs();
    this.buildSliderPanel();
    this.buildPresetButtons();
    this.bindEvents();
    this.initActionLibrary();
    this.scene.setPose(this.currentPose);
    this.setSelectedChannel(this.selectedChannel);
    this.updatePoseInspector();
  }

  isZh() {
    return (window._i18nLang || "zh-CN").startsWith("zh");
  }

  servoLabel(servo) {
    return this.isZh() ? servo.labelZh : servo.labelEn;
  }

  axisLabel(axisType) {
    const labels = {
      yaw_vertical: this.isZh() ? "垂直旋转轴" : "vertical yaw",
      pitch_lateral: this.isZh() ? "前后俯仰轴" : "lateral pitch",
      roll_longitudinal: this.isZh() ? "侧向翻转轴" : "longitudinal roll",
    };
    return labels[axisType] || axisType;
  }

  testedChangeLabel(change) {
    if (this.isZh()) return change === "increase" ? "增大" : "减小";
    return change === "increase" ? "increase" : "decrease";
  }

  buildSliderPanel() {
    const container = this.elements.slidersScroll;
    container.innerHTML = "";
    this.sliderInputs = [];
    this.sliderRows.clear();

    for (const group of SLIDER_GROUPS) {
      const groupElement = document.createElement("section");
      groupElement.className = "slider-group";

      const title = document.createElement("div");
      title.className = `slider-group-title ${group.cls}`;
      title.textContent = this.t(group.titleKey);
      groupElement.appendChild(title);

      for (const channel of group.channels) {
        const servo = this.servoMap[channel];
        const row = document.createElement("div");
        row.className = "slider-row";
        row.dataset.channel = String(channel);

        const idTag = document.createElement("span");
        idTag.className = "slider-id";
        idTag.textContent = `ID${servo.id}`;
        row.appendChild(idTag);

        const labelWrap = document.createElement("div");
        labelWrap.className = "slider-label-wrap";
        labelWrap.innerHTML = `
          <label>${escapeHtml(this.servoLabel(servo))}</label>
          <div class="slider-joint">${escapeHtml(servo.joint)}</div>
        `;
        row.appendChild(labelWrap);

        const input = document.createElement("input");
        input.type = "range";
        input.min = 0;
        input.max = 1000;
        input.value = this.currentPose[channel];
        input.step = 1;
        row.appendChild(input);

        const meta = document.createElement("div");
        meta.className = "slider-meta";

        const valueSpan = document.createElement("span");
        valueSpan.className = "val";
        valueSpan.textContent = this.currentPose[channel];
        meta.appendChild(valueSpan);

        const degreeSpan = document.createElement("span");
        degreeSpan.className = "deg";
        degreeSpan.textContent = formatServoAngle(channel, this.currentPose[channel]);
        meta.appendChild(degreeSpan);

        row.appendChild(meta);

        const handleInput = () => {
          const value = parseInt(input.value, 10);
          this.currentPose[channel] = value;
          valueSpan.textContent = value;
          degreeSpan.textContent = formatServoAngle(channel, value);
          this.scene.setPose(this.currentPose);
          this.setSelectedChannel(channel);
          this.updatePoseInspector();
        };

        input.addEventListener("input", handleInput);
        input.addEventListener("focus", () => this.setSelectedChannel(channel));
        row.addEventListener("click", () => this.setSelectedChannel(channel));

        this.sliderInputs.push({ channel, input, valueSpan, degreeSpan });
        this.sliderRows.set(channel, row);
        groupElement.appendChild(row);
      }

      container.appendChild(groupElement);
    }
  }

  buildPresetButtons() {
    const container = this.elements.panelPresets;
    container.innerHTML = "";

    for (const [name, pose] of Object.entries(PRESETS)) {
      const button = document.createElement("button");
      button.textContent = this.t(PRESET_I18N_KEYS[name]) || name;
      button.addEventListener("click", () => this.setPose(pose));
      container.appendChild(button);
    }

    const backwardButton = document.createElement("button");
    backwardButton.textContent = this.t("preset_back10");
    backwardButton.title = this.t("preset_back10");
    backwardButton.addEventListener("click", () => {
      const frames = BACKWARD_TEST_FRAMES.map((pose, index) => ({
        duration: 180,
        pose: [...pose],
        raw: null,
        label: `backward-${index}`,
      }));
      this.stopPlayback();
      this.loadFrames(frames);
      this.showOverlay(`${this.t("overlay_loaded")} ${this.t("preset_back10")}`);
    });
    container.appendChild(backwardButton);
  }

  renderMappingGrid() {
    const container = this.elements.mappingGrid;
    container.innerHTML = "";
    this.mappingCards.clear();

    for (const servo of this.servoMap) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = `map-card ${servo.group || ""}`;
      card.dataset.channel = String(servo.channel);
      card.innerHTML = `
        <div class="map-card-top">
          <span class="map-id">ID${servo.id}</span>
          <span class="map-neutral">${servo.neutral}</span>
        </div>
        <div class="map-name">${escapeHtml(this.servoLabel(servo))}</div>
        <div class="map-joint">${escapeHtml(servo.joint)}</div>
        <div class="map-axis">${escapeHtml(this.axisLabel(servo.axisType))}</div>
      `;
      card.addEventListener("click", () => this.focusChannel(servo.channel));
      container.appendChild(card);
      this.mappingCards.set(servo.channel, card);
    }
  }

  renderMirrorPairs() {
    const pairs = [
      [8, 16],
      [7, 15],
      [6, 14],
      [4, 12],
      [3, 11],
      [5, 13],
      [1, 9],
      [2, 10],
    ];

    this.elements.mirrorList.innerHTML = pairs
      .map(([leftId, rightId]) => {
        const left = getServoById(leftId);
        const right = getServoById(rightId);
        const leftName = this.isZh() ? left.labelZh : left.labelEn;
        const rightName = this.isZh() ? right.labelZh : right.labelEn;
        return `<li>ID${left.id} ${escapeHtml(leftName)} ↔ ID${right.id} ${escapeHtml(rightName)}</li>`;
      })
      .join("");
  }

  bindEvents() {
    this.elements.btnCopyPose.addEventListener("click", () => this.copyPoseToClipboard());
    this.elements.btnLoadRob.addEventListener("click", () => this.elements.fileInput.click());
    this.elements.fileInput.addEventListener("change", (event) => this.handleFileInput(event));

    this.elements.btnPrev.addEventListener("click", () => {
      if (!this.loadedFrames) return;
      this.stopPlayback();
      this.currentFrameIdx = Math.max(0, this.currentFrameIdx - 1);
      this.updateFrameDisplay();
    });

    this.elements.btnNext.addEventListener("click", () => {
      if (!this.loadedFrames) return;
      this.stopPlayback();
      this.currentFrameIdx = Math.min(this.loadedFrames.length - 1, this.currentFrameIdx + 1);
      this.updateFrameDisplay();
    });

    this.elements.btnPlay.addEventListener("click", () => this.togglePlayback());
    this.elements.frameSlider.addEventListener("input", (event) => {
      if (!this.loadedFrames) return;
      this.stopPlayback();
      this.currentFrameIdx = parseInt(event.target.value, 10);
      this.updateFrameDisplay();
    });

    this.elements.speedSelect.addEventListener("change", (event) => {
      this.playbackSpeed = parseFloat(event.target.value);
    });

    this.elements.btnResetView.addEventListener("click", () => this.scene.resetView());
    this.elements.btnToggleGrid.addEventListener("click", () => {
      this.elements.btnToggleGrid.classList.toggle("active", this.scene.toggleGrid());
    });
    this.elements.btnToggleServoLabels.addEventListener("click", () => {
      this.elements.btnToggleServoLabels.classList.toggle("active", this.scene.toggleServoLabels());
    });

    window.addEventListener("keydown", (event) => this.handleKeydown(event));
    this.elements.viewport.addEventListener("dragover", (event) => event.preventDefault());
    this.elements.viewport.addEventListener("drop", (event) => this.handleFileDrop(event));
  }

  async initActionLibrary() {
    try {
      const response = await fetch("../data/official-actions/index.json");
      if (!response.ok) return;

      const actionIndex = await response.json();
      const select = this.elements.actionSelect;
      select.style.display = "flex";
      select.innerHTML = `<option value="">${this.t("action_library")}</option>`;

      const actionsByCategory = {};
      for (const action of actionIndex.actions) {
        const category = action.category || "other";
        if (!actionsByCategory[category]) actionsByCategory[category] = [];
        actionsByCategory[category].push(action);
      }

      for (const [category, actions] of Object.entries(actionsByCategory)) {
        const optgroup = document.createElement("optgroup");
        optgroup.label = category;
        for (const action of actions) {
          const option = document.createElement("option");
          option.value = action.slug;
          option.textContent = (action.labels && action.labels["zh-CN"]) || action.name;
          optgroup.appendChild(option);
        }
        select.appendChild(optgroup);
      }

      select.addEventListener("change", async () => {
        const slug = select.value;
        if (!slug) return;
        try {
          const response = await fetch(`../data/official-actions/actions/${slug}.json`);
          if (!response.ok) {
            this.showOverlay("❌ 加载失败", 3000);
            return;
          }
          const action = await response.json();
          if (!action.frames || action.frames.length === 0) {
            this.showOverlay("⚠ 无帧数据", 3000);
            return;
          }
          this.stopPlayback();
          const frames = action.frames.map((frame) => ({
            duration: frame.duration,
            pose: frame.pose ? [...frame.pose] : [],
            raw: null,
          }));
          this.loadFrames(frames);
          this.setTitleSuffix(`${(action.labels && action.labels["zh-CN"]) || action.name} (${frames.length}${this.t("overlay_frames")})`);
        } catch (error) {
          this.showOverlay(`❌ 加载失败: ${error.message}`, 3000);
        }
      });
    } catch (_error) {
    }
  }

  focusChannel(channel) {
    this.setSelectedChannel(channel);
    const slider = this.sliderInputs.find((item) => item.channel === channel);
    if (slider) slider.input.focus();
  }

  setSelectedChannel(channel) {
    this.selectedChannel = channel;

    for (const [rowChannel, row] of this.sliderRows.entries()) {
      row.classList.toggle("active", rowChannel === channel);
    }

    for (const [cardChannel, card] of this.mappingCards.entries()) {
      card.classList.toggle("active", cardChannel === channel);
    }

    this.updateFocusCard();
  }

  updateFocusCard() {
    const servo = this.servoMap[this.selectedChannel];
    if (!servo) return;

    const current = this.currentPose[this.selectedChannel];
    const mirror = getServoById(servo.mirrorId);
    const tested = `${this.testedChangeLabel(servo.testedChange)} -> ${servo.testedMotionZh}`;

    this.elements.focusId.textContent = `ID${servo.id}`;
    this.elements.focusName.textContent = this.servoLabel(servo);
    this.elements.focusJoint.textContent = servo.joint;
    this.elements.focusAxis.textContent = this.axisLabel(servo.axisType);
    this.elements.focusNeutral.textContent = String(servo.neutral);
    this.elements.focusCurrent.textContent = `${current} / ${formatServoAngle(this.selectedChannel, current)}`;
    this.elements.focusOffset.textContent = formatServoOffset(this.selectedChannel, current);
    this.elements.focusMirror.textContent = mirror
      ? `ID${mirror.id} ${this.isZh() ? mirror.labelZh : mirror.labelEn}`
      : "-";
    this.elements.focusTested.textContent = tested;
    this.elements.focusMotion.textContent = servo.motionZh;
  }

  updatePoseInspector() {
    this.elements.poseArray.textContent = JSON.stringify(this.currentPose);
    const changed = this.currentPose.filter((value, index) => value !== DEFAULT_POSE[index]).length;
    this.elements.poseStats.textContent = this.isZh()
      ? `当前偏离立正的舵机数: ${changed} / 16`
      : `Channels offset from stand: ${changed} / 16`;
    this.updateFocusCard();
  }

  setPose(pose) {
    this.currentPose = [...pose];
    for (const slider of this.sliderInputs) {
      slider.input.value = pose[slider.channel];
      slider.valueSpan.textContent = pose[slider.channel];
      slider.degreeSpan.textContent = formatServoAngle(slider.channel, pose[slider.channel]);
    }
    this.scene.setPose(this.currentPose);
    this.updatePoseInspector();
  }

  loadFrames(frames) {
    this.loadedFrames = frames;
    this.currentFrameIdx = 0;
    this.elements.timeline.classList.add("visible");
    this.elements.frameSlider.max = Math.max(0, frames.length - 1);
    this.elements.frameSlider.value = 0;
    this.updateFrameDisplay();
    this.updateFrameSummary();
    this.updateJumpWarning(this.analyzeFrameJumps(frames));
    this.showOverlay(`${this.t("overlay_loaded")} ${frames.length} ${this.t("overlay_frames")}`, 2500);
  }

  updateFrameDisplay() {
    if (!this.loadedFrames) return;
    const frame = this.loadedFrames[this.currentFrameIdx];
    this.setPose(frame.pose);
    this.elements.frameInfo.textContent = this.t("frame_info", {
      current: this.currentFrameIdx + 1,
      total: this.loadedFrames.length,
      duration: frame.duration,
    });
    this.elements.frameSlider.value = this.currentFrameIdx;
    this.updateFrameSummary();
  }

  updateFrameSummary() {
    const element = this.elements.frameSummary;
    if (!this.loadedFrames || this.loadedFrames.length === 0) {
      element.style.display = "none";
      return;
    }
    const totalDuration = this.loadedFrames.reduce((sum, frame) => sum + frame.duration, 0);
    let elapsed = 0;
    for (let i = 0; i < this.currentFrameIdx; i++) elapsed += this.loadedFrames[i].duration;
    element.textContent = this.t("frame_summary", {
      total: this.loadedFrames.length,
      elapsed: this.formatTime(elapsed),
      totalTime: this.formatTime(totalDuration),
    });
    element.style.display = "inline";
  }

  stopPlayback() {
    if (this.playbackTimer) {
      clearTimeout(this.playbackTimer);
      this.playbackTimer = null;
    }
    this.elements.btnPlay.textContent = "▶";
  }

  togglePlayback() {
    if (!this.loadedFrames) return;
    if (this.playbackTimer) {
      this.stopPlayback();
      return;
    }

    this.elements.btnPlay.textContent = "⏸";
    const step = () => {
      if (!this.playbackTimer) return;
      const frame = this.loadedFrames[this.currentFrameIdx];
      const delay = Math.max(16, frame.duration / this.playbackSpeed);
      this.currentFrameIdx = (this.currentFrameIdx + 1) % this.loadedFrames.length;
      this.updateFrameDisplay();
      this.playbackTimer = setTimeout(step, delay);
    };
    this.playbackTimer = setTimeout(step, 16);
  }

  copyPoseToClipboard() {
    const text = JSON.stringify(this.currentPose);
    navigator.clipboard
      .writeText(text)
      .then(() => this.showOverlay(`${this.t("overlay_pose_copied")}: ${text}`, 2000))
      .catch(() => {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        this.showOverlay(`${this.t("overlay_pose_copied")}: ${text}`, 2000);
      });
  }

  showOverlay(message, duration = 2000) {
    const element = this.elements.overlay;
    element.textContent = message;
    element.classList.add("show");
    clearTimeout(element._timeout);
    element._timeout = setTimeout(() => element.classList.remove("show"), duration);
  }

  analyzeFrameJumps(frames) {
    const warnings = [];
    const threshold = 200;
    for (let i = 0; i < frames.length - 1; i++) {
      const current = frames[i].pose;
      const next = frames[i + 1].pose;
      const jumps = [];
      for (let channel = 0; channel < 16; channel++) {
        const delta = Math.abs(next[channel] - current[channel]);
        if (delta > threshold) jumps.push({ channel, delta });
      }
      if (jumps.length > 0) warnings.push({ fromIdx: i, toIdx: i + 1, jumps });
    }
    return warnings;
  }

  updateJumpWarning(warnings) {
    const element = this.elements.jumpWarning;
    if (!warnings || warnings.length === 0) {
      element.style.display = "none";
      return;
    }

    const lines = [];
    for (const warning of warnings.slice(0, 6)) {
      const ids = warning.jumps.map((jump) => `ID${jump.channel + 1}(Δ${jump.delta})`).join(", ");
      lines.push(this.t("jump_entry", {
        from: warning.fromIdx + 1,
        to: warning.toIdx + 1,
        ids,
      }));
    }
    if (warnings.length > 6) {
      lines.push(this.t("jump_warning_more", { count: warnings.length }));
    }

    element.textContent = `${this.t("jump_warning_prefix")} ${lines.join("; ")}`;
    element.style.display = "block";
  }

  formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
  }

  setTitleSuffix(suffix = "") {
    const base = `🤖 ${this.t("title")}`;
    this.elements.topbarTitle.textContent = suffix ? `${base} · ${suffix}` : base;
  }

  async loadFile(file) {
    this.stopPlayback();
    const buffer = await file.arrayBuffer();
    const parsed = this.parseRobFile(buffer);
    this.loadFrames(parsed.frames);
    this.setTitleSuffix(`${file.name} (${parsed.frames.length}${this.t("overlay_frames")}${parsed.tag === "EYPT" ? " EYPT" : ""})`);
  }

  async handleFileInput(event) {
    const file = event.target.files[0];
    if (!file) return;
    try {
      await this.loadFile(file);
    } catch (error) {
      this.showOverlay(`❌ ${this.t("overlay_load_fail")}: ${error.message}`, 4000);
      console.error(error);
    }
    event.target.value = "";
  }

  async handleFileDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (!file || !file.name.endsWith(".rob")) return;
    try {
      await this.loadFile(file);
    } catch (error) {
      this.showOverlay(`❌ ${this.t("overlay_load_fail")}: ${error.message}`, 4000);
    }
  }

  handleKeydown(event) {
    if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;

    switch (event.key.toLowerCase()) {
      case "arrowleft":
        if (this.loadedFrames) {
          this.stopPlayback();
          this.currentFrameIdx = Math.max(0, this.currentFrameIdx - 1);
          this.updateFrameDisplay();
        }
        break;
      case "arrowright":
        if (this.loadedFrames) {
          this.stopPlayback();
          this.currentFrameIdx = Math.min(this.loadedFrames.length - 1, this.currentFrameIdx + 1);
          this.updateFrameDisplay();
        }
        break;
      case " ":
        event.preventDefault();
        this.togglePlayback();
        break;
      case "r":
        this.setPose(DEFAULT_POSE);
        this.showOverlay(this.isZh() ? "重置为标准站立帧" : "Reset to stand pose");
        break;
      default:
        break;
    }
  }
}
