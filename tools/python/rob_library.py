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


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_ACTIONS_DIR = WORKSPACE_ROOT / "data" / "raw-actions"
DEFAULT_REPORT_PATH = WORKSPACE_ROOT / "data" / "official-actions" / "index.json"
DEFAULT_EXPORT_DIR = WORKSPACE_ROOT / "data" / "official-actions" / "actions"
DEFAULT_DECRYPT_DIR = WORKSPACE_ROOT / "data" / "raw-actions"
DEFAULT_LEGACY_ACTIONS = WORKSPACE_ROOT / "python-toolkit" / "动作"


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


def make_slug(action_id, stem):
    import re
    # ASCII-only slug from action ID, safe for filesystems and URLs
    safe = re.sub(r'[^a-zA-Z0-9]+', '-', stem)
    safe = safe.strip('-').lower()
    if safe:
        return "action-{}-{}".format(action_id, safe[:40])
    return "action-{}".format(action_id)


def guess_category(name):
    name_lower = name.lower()
    if any(kw in name_lower for kw in ['前进', '后退', '左转', '右转', '循迹', '循环', 'forward', 'back', 'turn', 'track']):
        return 'locomotion'
    if any(kw in name_lower for kw in ['拳', '勾', '咏春', 'punch', 'box']):
        return 'punch'
    if any(kw in name_lower for kw in ['踢', '射门', 'kick', 'shoot']):
        return 'kick'
    if any(kw in name_lower for kw in ['下蹲', '蹲', 'squat']):
        return 'squat'
    if any(kw in name_lower for kw in ['鞠躬', '立正', '回正', '站姿', 'bow', 'stand', 'neutral']):
        return 'posture'
    if any(kw in name_lower for kw in ['俯卧撑', '仰卧起坐', 'pushup', 'situp']):
        return 'floor'
    if any(kw in name_lower for kw in ['扭', 'twist']):
        return 'twist'
    if any(kw in name_lower for kw in ['侧滑', 'slide']):
        return 'slide'
    if any(kw in name_lower for kw in ['挥手', '招手', 'wave', 'greet']):
        return 'greeting'
    if any(kw in name_lower for kw in ['舞蹈', '科目三', '街舞', '霹雳', '江南', '小苹果', '倍儿爽', 'fantastic', '超级冠军', '青春修炼', '爱出发', 'dance', 'street', 'break']):
        return 'dance'
    if any(kw in name_lower for kw in ['工业校歌', '队列', '广播操', '体操']):
        return 'choreography'
    if any(kw in name_lower for kw in ['抓', '取', '放', '头顶', '方块', 'grab', 'carry', 'drop']):
        return 'manipulation'
    return 'other'


# English labels for common Chinese action names
_ZH_TO_EN_LABEL = {
    '立正': 'Stand at Attention',
    '前进': 'Forward',
    '后退': 'Backward',
    '单脚左转': 'Single-Foot Left Turn',
    '单脚右转': 'Single-Foot Right Turn',
    '俯卧撑': 'Push-up',
    '仰卧起坐': 'Sit-up',
    '挥手': 'Wave',
    '鞠躬': 'Bow',
    '左侧滑': 'Left Slide',
    '右侧滑': 'Right Slide',
    '开怀大笑': 'Big Laugh',
    '下蹲': 'Squat',
    '大鹏展翅': 'Spread Wings',
    '循环前进第一步': 'Loop Forward Step 1',
    '快速立正': 'Quick Stand',
    '循环前进': 'Loop Forward',
    '循环后退': 'Loop Backward',
    '左转(原地)': 'Left Turn (In Place)',
    '右转(原地)': 'Right Turn (In Place)',
    '抱娃娃': 'Hold Baby',
    '伸右手': 'Reach Right Hand',
    '双手向前支撑': 'Two-Hand Forward Support',
    '双手向后支撑': 'Two-Hand Backward Support',
    '下蹲立正': 'Squat to Stand',
    '下蹲前进': 'Squat Forward',
    '循迹前进第一步': 'Track Forward Step 1',
    '循迹前进第二步': 'Track Forward Step 2',
    '左转(前进)': 'Left Turn (Forward)',
    '右转(前进)': 'Right Turn (Forward)',
    '左转过渡': 'Left Turn Transition',
    '右转过渡': 'Right Turn Transition',
    '循迹左转过渡': 'Track Left Turn Transition',
    '循迹右转过渡': 'Track Right Turn Transition',
    '介绍动作': 'Intro Action',
    '原地踏步': 'March in Place',
    '扭腰': 'Waist Twist',
    '左侧踢': 'Left Kick',
    '右侧踢': 'Right Kick',
    '左弯勾拳2': 'Left Hook 2',
    '右弯勾拳2': 'Right Hook 2',
    '左脚射门': 'Left Foot Shoot',
    '右脚射门': 'Right Foot Shoot',
    '左勾拳2': 'Left Hook 2',
    '右勾拳2': 'Right Hook 2',
    '前进拳击': 'Forward Punch',
    '下蹲拳': 'Squat Punch',
    '咏春拳': 'Wing Chun',
    '捶胸': 'Chest Pound',
    '后倒站立': 'Back Fall Stand',
    '前倒站立2': 'Forward Fall Stand 2',
    '体操': 'Gymnastics',
    '街舞': 'Street Dance',
    '科目三': 'Subject Three Dance',
    '电摇': 'Electric Shake',
    '霹雳舞': 'Breakdance',
    '工业校歌': 'Industrial School Song',
    '队列广播体操': 'Queue Calisthenics',
    '站姿基座': 'Stance Base',
    '快速回正': 'Quick Reset',
    '礼貌鞠躬': 'Polite Bow',
    '招手问候': 'Wave Greeting',
    '展示姿态': 'Display Pose',
    '笑场互动': 'Laugh Interaction',
    '短拍踏步': 'Short Step March',
    '标准踏步': 'Standard March',
    '左侧滑短句': 'Left Slide Phrase',
    '右侧滑短句': 'Right Slide Phrase',
    '左右侧滑往返': 'Left-Right Slide Round',
    '扭腰单拍': 'Waist Twist Single',
    '扭腰双拍': 'Waist Twist Double',
    '左右侧踢组合': 'Left-Right Kick Combo',
    '左勾拳': 'Left Hook',
    '右勾拳': 'Right Hook',
    '左右勾拳组合': 'Left-Right Hook Combo',
    '左弯勾拳': 'Left Curved Hook',
    '右弯勾拳': 'Right Curved Hook',
    '捶胸强调': 'Chest Pound Emphasis',
    '下蹲回正': 'Squat Reset',
    '下蹲前压': 'Squat Forward Press',
    '俯卧撑短句': 'Push-up Phrase',
    '仰卧起坐短句': 'Sit-up Phrase',
    '街舞片段': 'Street Dance Clip',
    '前行两步': 'Forward Two Steps',
    '后退两步': 'Backward Two Steps',
    '左转七步': 'Left Turn Seven Steps',
    '右转七步': 'Right Turn Seven Steps',
    '左转九十': 'Left Turn Ninety',
    '右转九十': 'Right Turn Ninety',
    '头顶抓取': 'Overhead Grab',
    '头顶放下': 'Overhead Drop',
    '头顶携带前进一步': 'Overhead Carry Forward Step',
    '手写': 'Custom',
}


def en_label_for(name):
    if name in _ZH_TO_EN_LABEL:
        return _ZH_TO_EN_LABEL[name]
    # Try partial matches
    for zh, en in _ZH_TO_EN_LABEL.items():
        if zh in name:
            return en
    return name


def export_official_actions(actions_dir, output_dir, index_path):
    import re
    actions_dir = workspace_path(actions_dir)
    output_dir = workspace_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = workspace_path(index_path)

    if not actions_dir.exists():
        print("actions_dir not found: {}".format(actions_dir))
        return

    seen_ids = {}
    actions = []
    categories_set = set()
    count = 0
    for path in sorted(iter_action_files(actions_dir)):
        try:
            # Skip plaintext duplicates — they have the same frames as the EYPT original
            if path.stem.endswith('.plain'):
                continue

            parsed = parse_action(path)
            stem = path.stem
            match = re.match(r'^(\d+)', stem)
            base_id = int(match.group(1)) if match else count

            # Deduplicate: if same numeric ID already seen, append a suffix
            if base_id in seen_ids:
                action_id = base_id * 1000 + seen_ids[base_id]
                seen_ids[base_id] += 1
            else:
                action_id = base_id
                seen_ids[base_id] = 1

            slug = make_slug(base_id, stem)
            category = guess_category(stem)
            tags = [category]
            zh_label = stem
            en_label = en_label_for(stem)

            frames_json = []
            for idx, raw_frame in enumerate(parsed["frames"]):
                info = parse_plain_frame(raw_frame)
                frames_json.append({
                    "index": idx,
                    "duration": info["duration"],
                    "pose": pose_from_info(info),
                })

            total_duration = sum(f["duration"] for f in frames_json)

            entry = {
                "id": action_id,
                "name": stem,
                "slug": slug,
                "labels": {
                    "zh-CN": zh_label,
                    "en-US": en_label,
                },
                "source_file": str(path.name),
                "category": category,
                "tags": tags,
                "frame_count": parsed["frame_count"],
                "total_duration": total_duration,
                "source_tag": parsed["source_tag"],
                "source_sha256": parsed["source_sha256"],
                "frames": frames_json,
            }

            out_path = output_dir / "{}.json".format(slug)
            out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
            actions.append({
                "id": action_id,
                "name": stem,
                "slug": slug,
                "labels": {"zh-CN": zh_label, "en-US": en_label},
                "category": category,
                "frame_count": parsed["frame_count"],
                "total_duration": total_duration,
            })
            categories_set.add(category)
            count += 1
        except Exception as e:
            print("skip {}: {}".format(path.name, e))

    # Write index.json
    category_list = [{"key": c, "name": c.replace('-', ' ').title()} for c in sorted(categories_set)]
    index_data = {
        "total": count,
        "categories": category_list,
        "actions": sorted(actions, key=lambda a: a["id"]),
    }
    index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write categories.json
    cats_path = index_path.parent / "categories.json"
    cats_data = {
        "categories": category_list,
        "counts": {c["key"]: sum(1 for a in actions if a["category"] == c["key"]) for c in category_list},
    }
    cats_path.write_text(json.dumps(cats_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("export_dir={}".format(relative_path(output_dir)))
    print("exported={}".format(count))
    print("index={}".format(relative_path(index_path)))


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

    official_parser = subparsers.add_parser("export-official-actions")
    official_parser.add_argument("--actions-dir", default=str(DEFAULT_LEGACY_ACTIONS))
    official_parser.add_argument("--output-dir", default=str(DEFAULT_EXPORT_DIR))
    official_parser.add_argument("--index", default=str(DEFAULT_REPORT_PATH))

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
    elif args.command == "export-official-actions":
        export_official_actions(actions_dir, args.output_dir, args.index)


if __name__ == "__main__":
    main()
