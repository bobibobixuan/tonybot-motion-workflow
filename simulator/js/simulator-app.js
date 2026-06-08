import {
  BACKWARD_TEST_FRAMES,
  CHANNEL_LABELS,
  DEFAULT_POSE,
  PRESETS,
  PRESET_I18N_KEYS,
  SLIDER_GROUPS,
  formatServoAngle,
} from "./config.js";

export class SimulatorApp {
  constructor({ scene, t, parseRobFile }) {
    this.scene = scene;
    this.t = t;
    this.parseRobFile = parseRobFile;

    this.currentPose = [...DEFAULT_POSE];
    this.sliderInputs = [];
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
    };
  }

  init() {
    this.buildSliderPanel();
    this.buildPresetButtons();
    this.bindEvents();
    this.initActionLibrary();
    this.scene.setPose(this.currentPose);
  }

  buildSliderPanel() {
    const container = this.elements.slidersScroll;
    container.innerHTML = "";
    this.sliderInputs = [];

    for (const group of SLIDER_GROUPS) {
      const groupElement = document.createElement("div");
      groupElement.className = "slider-group";

      const title = document.createElement("div");
      title.className = `slider-group-title ${group.cls}`;
      title.textContent = this.t(group.titleKey);
      groupElement.appendChild(title);

      for (const channel of group.channels) {
        const row = document.createElement("div");
        row.className = "slider-row";

        const label = document.createElement("label");
        label.textContent = this.t(`channel_labels.${channel}`) || CHANNEL_LABELS[channel];
        label.title = label.textContent;
        row.appendChild(label);

        const input = document.createElement("input");
        input.type = "range";
        input.min = 0;
        input.max = 1000;
        input.value = this.currentPose[channel];
        input.step = 1;
        row.appendChild(input);

        const valueSpan = document.createElement("span");
        valueSpan.className = "val";
        valueSpan.textContent = this.currentPose[channel];
        row.appendChild(valueSpan);

        const degreeSpan = document.createElement("span");
        degreeSpan.className = "deg";
        degreeSpan.textContent = formatServoAngle(channel, this.currentPose[channel]);
        row.appendChild(degreeSpan);

        input.addEventListener("input", () => {
          const value = parseInt(input.value, 10);
          this.currentPose[channel] = value;
          valueSpan.textContent = value;
          degreeSpan.textContent = formatServoAngle(channel, value);
          this.scene.setPose(this.currentPose);
        });

        this.sliderInputs.push({ channel, input, valueSpan, degreeSpan });
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

  setPose(pose) {
    this.currentPose = [...pose];
    for (const slider of this.sliderInputs) {
      slider.input.value = pose[slider.channel];
      slider.valueSpan.textContent = pose[slider.channel];
      slider.degreeSpan.textContent = formatServoAngle(slider.channel, pose[slider.channel]);
    }
    this.scene.setPose(this.currentPose);
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
    for (let i = 0; i < this.currentFrameIdx; i++) {
      elapsed += this.loadedFrames[i].duration;
    }
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
        this.showOverlay("重置为立正姿态");
        break;
      default:
        break;
    }
  }
}
