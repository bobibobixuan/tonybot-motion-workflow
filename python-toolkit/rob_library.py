import argparse
import hashlib
import json
import pathlib
from collections import Counter, defaultdict

from rob_crypto import decrypt_action_bytes
from rob_reverse import (
    ACTIVE_CHANNELS,
    CHANNEL_COUNT,
    FILLER_TRIPLET,
    parse_file,
    parse_plain_frame,
)


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_ACTIONS_DIR = WORKSPACE_ROOT / "动作"
DEFAULT_REPORT_PATH = WORKSPACE_ROOT / "动作库解析报告.json"
DEFAULT_EXPORT_DIR = WORKSPACE_ROOT / "动作库解析"
DEFAULT_DECRYPT_DIR = WORKSPACE_ROOT / "动作库解密"


def relative_path(path):
    path = pathlib.Path(path)
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


def workspace_path(value):
    path = pathlib.Path(value)
    if path.is_absolute():
        return path
    return WORKSPACE_ROOT / path


def plain_bytes_for_action(path):
    data = pathlib.Path(path).read_bytes()
    parsed = parse_file(path)
    if parsed["tag"] == "EYPT":
        data = decrypt_action_bytes(data)
    return data


def parse_action(path):
    path = pathlib.Path(path)
    data = plain_bytes_for_action(path)
    parsed = parse_file_from_bytes(path, data)
    original = parse_file(path)
    parsed["source_tag"] = original["tag"] or "plain"
    parsed["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    parsed["plain_sha256"] = hashlib.sha256(data).hexdigest()
    return parsed


def parse_file_from_bytes(path, data):
    virtual_path = pathlib.Path(path)
    if len(data) < 16:
        raise ValueError("file too small: {}".format(path))
    magic = data[:6].decode("ascii", errors="replace")
    frame_count = data[6] | (data[7] << 8)
    tag = data[8:12].decode("ascii", errors="replace").rstrip("\x00")
    version = data[12] | (data[13] << 8)
    reserved = data[14] | (data[15] << 8)
    expected_length = 16 + frame_count * 248
    frames = []
    for frame_index in range(frame_count):
        start = 16 + frame_index * 248
        end = start + 248
        frame = data[start:end]
        if len(frame) != 248:
            raise ValueError("truncated frame {}: {}".format(frame_index, path))
        frames.append(frame)
    return {
        "path": str(virtual_path),
        "magic": magic,
        "frame_count": frame_count,
        "tag": tag,
        "version": version,
        "reserved": reserved,
        "length": len(data),
        "expected_length": expected_length,
        "frames": frames,
    }


def channel_payload(info):
    return [list(triple) for triple in info["channels"][:ACTIVE_CHANNELS]]


def frame_to_json(frame, frame_index):
    info = parse_plain_frame(frame)
    active = channel_payload(info)
    filler = info["channels"][ACTIVE_CHANNELS:]
    return {
        "index": frame_index,
        "duration": info["duration"],
        "marker": info["marker"],
        "reserved_a": info["reserved_a"],
        "reserved_b": info["reserved_b"],
        "active_channels": active,
        "filler_ok": all(triple == FILLER_TRIPLET for triple in filler),
    }


def action_to_json(parsed):
    frames = [frame_to_json(frame, index) for index, frame in enumerate(parsed["frames"])]
    total_duration = sum(frame["duration"] for frame in frames)
    return {
        "path": relative_path(parsed["path"]),
        "source_tag": parsed["source_tag"],
        "magic": parsed["magic"],
        "frame_count": parsed["frame_count"],
        "length": parsed["length"],
        "expected_length": parsed["expected_length"],
        "version": parsed["version"],
        "reserved": parsed["reserved"],
        "source_sha256": parsed["source_sha256"],
        "plain_sha256": parsed["plain_sha256"],
        "total_duration": total_duration,
        "frames": frames,
    }


def pose_from_info(info):
    return [triple[0] for triple in info["channels"][:ACTIVE_CHANNELS]]


def action_summary(parsed):
    markers = Counter()
    frame_reserved = Counter()
    durations = []
    filler_errors = 0
    non_zero_fields = [[0, 0, 0] for _ in range(ACTIVE_CHANNELS)]
    field_min = [[None, None, None] for _ in range(ACTIVE_CHANNELS)]
    field_max = [[None, None, None] for _ in range(ACTIVE_CHANNELS)]
    max_joint_delta = 0
    max_l1_delta = 0
    previous_pose = None

    for frame in parsed["frames"]:
        info = parse_plain_frame(frame)
        markers[info["marker"]] += 1
        frame_reserved[(info["reserved_a"], info["reserved_b"])] += 1
        durations.append(info["duration"])
        if any(triple != FILLER_TRIPLET for triple in info["channels"][ACTIVE_CHANNELS:]):
            filler_errors += 1
        for channel_index, triple in enumerate(info["channels"][:ACTIVE_CHANNELS]):
            for field_index, value in enumerate(triple):
                if value:
                    non_zero_fields[channel_index][field_index] += 1
                current_min = field_min[channel_index][field_index]
                current_max = field_max[channel_index][field_index]
                field_min[channel_index][field_index] = value if current_min is None else min(current_min, value)
                field_max[channel_index][field_index] = value if current_max is None else max(current_max, value)
        pose = pose_from_info(info)
        if previous_pose is not None:
            deltas = [abs(left - right) for left, right in zip(pose, previous_pose)]
            max_joint_delta = max(max_joint_delta, max(deltas))
            max_l1_delta = max(max_l1_delta, sum(deltas))
        previous_pose = pose

    return {
        "path": relative_path(parsed["path"]),
        "source_tag": parsed["source_tag"],
        "frame_count": parsed["frame_count"],
        "total_duration": sum(durations),
        "duration_min": min(durations) if durations else 0,
        "duration_max": max(durations) if durations else 0,
        "markers": {"0x{:04X}".format(key): value for key, value in sorted(markers.items())},
        "frame_reserved": {
            "0x{:04X},0x{:04X}".format(key[0], key[1]): value
            for key, value in sorted(frame_reserved.items())
        },
        "filler_error_frames": filler_errors,
        "non_zero_fields": non_zero_fields,
        "field_min": field_min,
        "field_max": field_max,
        "max_joint_delta": max_joint_delta,
        "max_l1_delta": max_l1_delta,
    }


def iter_action_files(actions_dir):
    yield from sorted(pathlib.Path(actions_dir).glob("*.rob"))


def analyze_library(actions_dir):
    actions = []
    failures = []
    source_hashes = defaultdict(list)
    plain_hashes = defaultdict(list)
    global_markers = Counter()
    global_frame_reserved = Counter()
    global_file_tags = Counter()
    channel_field_nonzero = [[0, 0, 0] for _ in range(ACTIVE_CHANNELS)]
    channel_field_min = [[None, None, None] for _ in range(ACTIVE_CHANNELS)]
    channel_field_max = [[None, None, None] for _ in range(ACTIVE_CHANNELS)]
    total_frames = 0
    total_duration = 0
    filler_error_files = []
    second_third_files = []

    for path in iter_action_files(actions_dir):
        try:
            parsed = parse_action(path)
            summary = action_summary(parsed)
        except Exception as exc:
            failures.append({"path": relative_path(path), "error": str(exc)})
            continue
        actions.append(summary)
        source_hashes[parsed["source_sha256"]].append(relative_path(path))
        plain_hashes[parsed["plain_sha256"]].append(relative_path(path))
        global_file_tags[parsed["source_tag"]] += 1
        total_frames += summary["frame_count"]
        total_duration += summary["total_duration"]
        if summary["filler_error_frames"]:
            filler_error_files.append(summary["path"])
        has_extra_fields = False
        for marker, count in summary["markers"].items():
            global_markers[marker] += count
        for reserved, count in summary["frame_reserved"].items():
            global_frame_reserved[reserved] += count
        for channel_index in range(ACTIVE_CHANNELS):
            for field_index in range(3):
                value = summary["non_zero_fields"][channel_index][field_index]
                channel_field_nonzero[channel_index][field_index] += value
                current_min = channel_field_min[channel_index][field_index]
                current_max = channel_field_max[channel_index][field_index]
                local_min = summary["field_min"][channel_index][field_index]
                local_max = summary["field_max"][channel_index][field_index]
                channel_field_min[channel_index][field_index] = (
                    local_min if current_min is None else min(current_min, local_min)
                )
                channel_field_max[channel_index][field_index] = (
                    local_max if current_max is None else max(current_max, local_max)
                )
                if field_index in (1, 2) and value:
                    has_extra_fields = True
        if has_extra_fields:
            second_third_files.append(summary["path"])

    duplicate_source_files = [paths for paths in source_hashes.values() if len(paths) > 1]
    duplicate_plain_files = [paths for paths in plain_hashes.values() if len(paths) > 1]
    return {
        "actions_dir": relative_path(actions_dir),
        "file_count": len(actions),
        "failed_count": len(failures),
        "source_tags": dict(sorted(global_file_tags.items())),
        "total_frames": total_frames,
        "total_duration": total_duration,
        "markers": dict(sorted(global_markers.items())),
        "frame_reserved": dict(sorted(global_frame_reserved.items())),
        "filler_error_files": filler_error_files,
        "files_with_nonzero_field2_or_field3": second_third_files,
        "channel_field_nonzero": channel_field_nonzero,
        "channel_field_min": channel_field_min,
        "channel_field_max": channel_field_max,
        "duplicate_source_files": duplicate_source_files,
        "duplicate_plain_files": duplicate_plain_files,
        "actions": actions,
        "failures": failures,
    }


def print_analysis(report):
    print("actions_dir={}".format(report["actions_dir"]))
    print("file_count={}".format(report["file_count"]))
    print("failed_count={}".format(report["failed_count"]))
    print("source_tags={}".format(report["source_tags"]))
    print("total_frames={}".format(report["total_frames"]))
    print("total_duration={}".format(report["total_duration"]))
    print("markers={}".format(report["markers"]))
    print("frame_reserved={}".format(report["frame_reserved"]))
    print("filler_error_files={}".format(len(report["filler_error_files"])))
    print("files_with_nonzero_field2_or_field3={}".format(len(report["files_with_nonzero_field2_or_field3"])))
    print("duplicate_source_groups={}".format(len(report["duplicate_source_files"])))
    print("duplicate_plain_groups={}".format(len(report["duplicate_plain_files"])))


def write_json(path, payload):
    path = workspace_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("output={}".format(relative_path(path)))


def export_json(actions_dir, output_dir):
    output_dir = workspace_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in iter_action_files(actions_dir):
        parsed = parse_action(path)
        payload = action_to_json(parsed)
        output_path = output_dir / "{}.json".format(path.stem)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        count += 1
    print("export_dir={}".format(relative_path(output_dir)))
    print("exported={}".format(count))


def decrypt_library(actions_dir, output_dir, force):
    output_dir = workspace_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    skipped = 0
    for path in iter_action_files(actions_dir):
        parsed = parse_file(path)
        if parsed["tag"] != "EYPT":
            continue
        output_path = output_dir / "{}.plain.rob".format(path.stem)
        if output_path.exists() and not force:
            skipped += 1
            continue
        output_path.write_bytes(decrypt_action_bytes(path.read_bytes()))
        count += 1
    print("decrypt_dir={}".format(relative_path(output_dir)))
    print("decrypted={}".format(count))
    print("skipped={}".format(skipped))


def main():
    parser = argparse.ArgumentParser(description="Analyze, decrypt, and export Tonybot ACT-40 action libraries.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--actions-dir", default=str(DEFAULT_ACTIONS_DIR))
    analyze_parser.add_argument("--json", default=str(DEFAULT_REPORT_PATH))
    analyze_parser.add_argument("--no-json", action="store_true")

    export_parser = subparsers.add_parser("export-json")
    export_parser.add_argument("--actions-dir", default=str(DEFAULT_ACTIONS_DIR))
    export_parser.add_argument("--output-dir", default=str(DEFAULT_EXPORT_DIR))

    decrypt_parser = subparsers.add_parser("decrypt-eypt")
    decrypt_parser.add_argument("--actions-dir", default=str(DEFAULT_ACTIONS_DIR))
    decrypt_parser.add_argument("--output-dir", default=str(DEFAULT_DECRYPT_DIR))
    decrypt_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()
    actions_dir = workspace_path(args.actions_dir)

    if args.command == "analyze":
        report = analyze_library(actions_dir)
        print_analysis(report)
        if not args.no_json:
            write_json(args.json, report)
    elif args.command == "export-json":
        export_json(actions_dir, args.output_dir)
    elif args.command == "decrypt-eypt":
        decrypt_library(actions_dir, args.output_dir, args.force)


if __name__ == "__main__":
    main()
