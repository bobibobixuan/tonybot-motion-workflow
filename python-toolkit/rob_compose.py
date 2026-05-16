import argparse
import json
import pathlib

from rob_reverse import ACTIVE_CHANNELS, CHANNEL_COUNT, FILLER_TRIPLET, parse_file, parse_plain_frame
from rob_safety import audit_boundaries, audit_frame_sequence, learn_reference_envelope, pose_from_frame


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_OUTPUT_FILE = WORKSPACE_ROOT / "动作" / "159号自制舞蹈.rob"
DEFAULT_ACTIONS_DIR = DEFAULT_OUTPUT_FILE.parent


DEFAULT_RECIPE = [
    {
        "source": "0号立正.rob",
        "label": "intro-stand",
        "notes": "开场立正，降低后续拼接冲击。",
    },
    {
        "source": "9号挥手.rob",
        "label": "wave",
        "notes": "先做打招呼动作，建立展示感。",
    },
    {
        "source": "50号扭腰.rob",
        "label": "twist",
        "repeat": 2,
        "notes": "用重复段制造节奏感。",
    },
    {
        "source": "49号原地踏步.rob",
        "label": "march",
        "frame_range": (0, 12),
        "notes": "截取前 12 帧，避免过长。",
    },
    {
        "source": "48号介绍动作.rob",
        "label": "pose",
        "notes": "作为中段展示姿态。",
    },
    {
        "source": "10号鞠躬.rob",
        "label": "bow",
        "notes": "收尾致意。",
    },
    {
        "source": "0号立正.rob",
        "label": "outro-stand",
        "notes": "回到安全站姿。",
    },
]


def build_header(frame_count):
    header = bytearray(16)
    header[0:6] = b"ACT-40"
    header[6:8] = frame_count.to_bytes(2, "little")
    header[12:14] = (2).to_bytes(2, "little")
    return bytes(header)


def workspace_path(value):
    path = pathlib.Path(value)
    if path.is_absolute():
        return path
    return WORKSPACE_ROOT / path


def detect_actions_dir(preferred_dir=DEFAULT_ACTIONS_DIR):
    candidates = [
        pathlib.Path(preferred_dir),
        WORKSPACE_ROOT,
        WORKSPACE_ROOT / "动作",
    ]
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (candidate / "0号立正.rob").exists():
            return candidate
    raise FileNotFoundError(
        "unable to locate action library root; expected 0号立正.rob in one of: {}".format(
            ", ".join(str(path) for path in candidates)
        )
    )


def resolve_action_source(value, actions_dir):
    candidate = pathlib.Path(value)
    if candidate.is_absolute():
        return candidate
    direct = actions_dir / candidate
    if direct.exists():
        return direct
    workspace_candidate = workspace_path(value)
    if workspace_candidate.exists():
        return workspace_candidate
    return direct


def validate_u16(value, field_name):
    number = int(value)
    if number < 0 or number > 0xFFFF:
        raise ValueError("{} must be within u16 range: {}".format(field_name, value))
    return number


def normalize_triplet(triplet, label, frame_index, channel_index):
    if len(triplet) != 3:
        raise ValueError(
            "{} frame {} channel {} must contain exactly 3 values".format(
                label,
                frame_index,
                channel_index,
            )
        )
    return tuple(
        validate_u16(value, "{} frame {} channel {} field {}".format(label, frame_index, channel_index, field_index + 1))
        for field_index, value in enumerate(triplet)
    )


def normalize_custom_frame(frame, label, frame_index):
    normalized = dict(frame)
    normalized["duration"] = validate_u16(normalized["duration"], "{} frame {} duration".format(label, frame_index))
    if "pose" in normalized and "channels" in normalized:
        raise ValueError("{} frame {} cannot define both pose and channels".format(label, frame_index))
    if "channels" in normalized:
        channels = [
            normalize_triplet(triplet, label, frame_index, channel_index + 1)
            for channel_index, triplet in enumerate(normalized["channels"])
        ]
        if len(channels) not in (ACTIVE_CHANNELS, CHANNEL_COUNT):
            raise ValueError(
                "{} frame {} channels must contain {} or {} triplets".format(
                    label,
                    frame_index,
                    ACTIVE_CHANNELS,
                    CHANNEL_COUNT,
                )
            )
        if len(channels) == ACTIVE_CHANNELS:
            channels.extend([FILLER_TRIPLET] * (CHANNEL_COUNT - ACTIVE_CHANNELS))
    elif "pose" in normalized:
        pose = [
            validate_u16(value, "{} frame {} joint {}".format(label, frame_index, joint_index + 1))
            for joint_index, value in enumerate(normalized["pose"])
        ]
        if len(pose) != ACTIVE_CHANNELS:
            raise ValueError(
                "{} frame {} pose must contain {} joints".format(label, frame_index, ACTIVE_CHANNELS)
            )
        channels = [(value, 0, 0) for value in pose]
        channels.extend([FILLER_TRIPLET] * (CHANNEL_COUNT - ACTIVE_CHANNELS))
    else:
        raise ValueError("{} frame {} must define pose or channels".format(label, frame_index))
    normalized["channels"] = channels
    normalized["marker"] = validate_u16(normalized.get("marker", 0x5555), "{} frame {} marker".format(label, frame_index))
    normalized["reserved_a"] = validate_u16(normalized.get("reserved_a", 0), "{} frame {} reserved_a".format(label, frame_index))
    normalized["reserved_b"] = validate_u16(normalized.get("reserved_b", 0), "{} frame {} reserved_b".format(label, frame_index))
    return normalized


def build_custom_frame(frame):
    output = bytearray()
    output.extend(int(frame["duration"]).to_bytes(2, "little"))
    output.extend(int(frame["marker"]).to_bytes(2, "little"))
    output.extend(int(frame["reserved_a"]).to_bytes(2, "little"))
    output.extend(int(frame["reserved_b"]).to_bytes(2, "little"))
    for triplet in frame["channels"]:
        for value in triplet:
            output.extend(int(value).to_bytes(2, "little"))
    return bytes(output)


def normalize_segment(segment, actions_dir):
    normalized = dict(segment)
    if "frames" in normalized:
        normalized["type"] = "custom"
        normalized["label"] = normalized.get("label", "custom-segment")
        normalized["source_name"] = normalized.get("source_name", "<custom>")
        normalized["frames"] = [
            normalize_custom_frame(frame, normalized["label"], frame_index + 1)
            for frame_index, frame in enumerate(normalized["frames"])
        ]
    else:
        source = resolve_action_source(normalized["source"], actions_dir)
        normalized["type"] = "source"
        normalized["source"] = source
        normalized["label"] = normalized.get("label", source.stem)
    normalized["repeat"] = int(normalized.get("repeat", 1))
    if normalized["repeat"] < 1:
        raise ValueError("repeat must be >= 1: {}".format(normalized["label"]))
    if normalized["type"] == "source" and "frame_range" in normalized:
        start, end = normalized["frame_range"]
        normalized["frame_range"] = (int(start), int(end))
    return normalized


def normalize_guard_segments(spec, actions_dir):
    guard_config = spec.get("guards") or {}
    pre_segments = guard_config.get("pre_segments") or []
    post_segments = guard_config.get("post_segments") or []
    return {
        "pre": [normalize_segment(segment, pathlib.Path(actions_dir)) for segment in pre_segments],
        "post": [normalize_segment(segment, pathlib.Path(actions_dir)) for segment in post_segments],
    }


def load_recipe_spec(spec_path):
    spec_path = workspace_path(spec_path)
    return json.loads(spec_path.read_text(encoding="utf-8"))


def load_recipe_from_spec(spec, actions_dir=DEFAULT_ACTIONS_DIR):
    actions_dir = detect_actions_dir(actions_dir)
    segments = spec.get("segments") or []
    if not segments:
        raise ValueError("spec must contain at least one segment")
    guards = normalize_guard_segments(spec, actions_dir)
    recipe = [normalize_segment(segment, pathlib.Path(actions_dir)) for segment in segments]
    return guards["pre"] + recipe + guards["post"]


def collect_frames(recipe):
    frames = []
    manifest = []
    for segment in recipe:
        if segment["type"] == "custom":
            selected = [build_custom_frame(frame) for frame in segment["frames"]]
            start, end = (0, len(selected))
            source_name = segment["source_name"]
            source_path = "<inline>"
        else:
            if not pathlib.Path(segment["source"]).exists():
                raise FileNotFoundError("action source not found: {}".format(segment["source"]))
            parsed = parse_file(segment["source"])
            if parsed["tag"]:
                raise ValueError("source file must be plain ACT-40: {}".format(segment["source"]))
            start, end = segment.get("frame_range", (0, parsed["frame_count"]))
            selected = parsed["frames"][start:end]
            if not selected:
                raise ValueError("no frames selected from {}".format(segment["source"]))
            source_name = segment["source"].name
            source_path = str(segment["source"])
        repeat = segment.get("repeat", 1)
        duration_ms = sum(parse_plain_frame(frame)["duration"] for frame in selected)
        for repeat_index in range(repeat):
            frame_start = len(frames)
            frames.extend(selected)
            frame_end = len(frames) - 1
            label = segment["label"]
            if repeat > 1:
                label = "{}-{}".format(segment["label"], repeat_index + 1)
            manifest.append(
                {
                    "label": label,
                    "source": source_name,
                    "source_path": source_path,
                    "frame_count": len(selected),
                    "frame_range": [start, end],
                    "repeat_index": repeat_index + 1,
                    "repeat_total": repeat,
                    "duration_ms": duration_ms,
                    "frame_start": frame_start,
                    "frame_end": frame_end,
                    "start_pose": pose_from_frame(selected[0]),
                    "end_pose": pose_from_frame(selected[-1]),
                    "notes": segment.get("notes", ""),
                }
            )
    return frames, manifest


MAX_ACTION_FRAMES = 510

def run_safety_checks(frames, manifest, actions_dir, output_file):
    violations = []
    if len(frames) > MAX_ACTION_FRAMES:
        violations.append(
            "frame count {} exceeds device load limit of {}".format(len(frames), MAX_ACTION_FRAMES)
        )
    envelope = learn_reference_envelope(actions_dir, ignore_paths=[output_file])
    frame_audit = audit_frame_sequence(frames, envelope, "composed-dance")
    boundary_reports = audit_boundaries(manifest, envelope)
    violations = list(frame_audit["violations"])
    violations.extend(
        "boundary {} -> {} exceeds learned safety envelope (max={}, l1={})".format(
            item["left"],
            item["right"],
            item["max_delta"],
            item["l1"],
        )
        for item in boundary_reports
        if item["level"] == "error"
    )
    return envelope, frame_audit, boundary_reports, violations


def build_output_bytes(frames):
    output = bytearray()
    output.extend(build_header(len(frames)))
    for frame in frames:
        output.extend(frame)
    return bytes(output)


def compile_recipe(recipe, output_file, actions_dir=DEFAULT_ACTIONS_DIR, write_output=True):
    output_file = pathlib.Path(output_file)
    actions_dir = detect_actions_dir(actions_dir)
    frames, manifest = collect_frames(recipe)
    envelope, frame_audit, boundary_reports, violations = run_safety_checks(frames, manifest, actions_dir, output_file)
    if violations:
        raise ValueError("\n".join(violations))

    output_bytes = build_output_bytes(frames)
    if write_output:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(output_bytes)

    return {
        "output": str(output_file),
        "frame_count": len(frames),
        "reference_files": envelope.reference_files,
        "reference_frames": envelope.reference_frames,
        "duration_range": [envelope.duration_min, envelope.duration_max],
        "duration_p95": envelope.duration_p95,
        "transition_l1_p95": envelope.transition_l1_p95,
        "transition_l1_max": envelope.transition_l1_max,
        "composed_max_l1": frame_audit["max_l1"],
        "segments": manifest,
        "boundaries": boundary_reports,
        "violations": violations,
    }


def print_report(report):
    print("output={}".format(report["output"]))
    print("frames={}".format(report["frame_count"]))
    print("reference_files={}".format(report["reference_files"]))
    print("reference_frames={}".format(report["reference_frames"]))
    print("duration_range={}..{}".format(*report["duration_range"]))
    print("duration_p95={}".format(report["duration_p95"]))
    print("transition_l1_p95={}".format(report["transition_l1_p95"]))
    print("transition_l1_max={}".format(report["transition_l1_max"]))
    print("composed_max_l1={}".format(report["composed_max_l1"]))
    for item in report["segments"]:
        print(
            "segment={label} source={source} frames={frame_count} duration_ms={duration_ms}".format(
                **item
            )
        )
    for item in report["boundaries"]:
        print(
            "boundary={left}->{right} level={level} max={max_delta} l1={l1}".format(
                **item
            )
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", nargs="?", help="optional JSON spec path")
    parser.add_argument("--output", help="override output .rob path")
    parser.add_argument("--actions-dir", default=str(DEFAULT_ACTIONS_DIR))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.spec:
        spec = load_recipe_spec(args.spec)
        recipe = load_recipe_from_spec(spec, actions_dir=args.actions_dir)
        output_file = args.output or spec.get("output", {}).get("rob") or str(DEFAULT_OUTPUT_FILE)
    else:
        detected_actions_dir = detect_actions_dir(args.actions_dir)
        recipe = [normalize_segment(segment, detected_actions_dir) for segment in DEFAULT_RECIPE]
        output_file = args.output or str(DEFAULT_OUTPUT_FILE)

    report = compile_recipe(
        recipe,
        workspace_path(output_file),
        actions_dir=detect_actions_dir(args.actions_dir),
        write_output=not args.dry_run,
    )
    print_report(report)


if __name__ == "__main__":
    main()
