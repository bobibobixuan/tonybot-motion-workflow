import argparse
import pathlib
from collections import Counter, defaultdict
from dataclasses import dataclass

from rob_reverse import parse_file, parse_plain_frame


ACTIVE_JOINTS = 16
SEMANTIC_CONFIDENCE_SLACK = 80
MIN_DYNAMIC_DURATION = 80
MAX_ACTION_FRAMES = 510


def mix(left, right, ratio):
    return [int(round(a + (b - a) * ratio)) for a, b in zip(left, right)]


SEMANTIC_ANCHORS = {
    "stand": [500, 387, 500, 593, 500, 575, 800, 724, 500, 612, 500, 406, 500, 425, 200, 275],
    "step": [540, 330, 568, 612, 505, 575, 800, 724, 530, 612, 500, 406, 500, 425, 200, 275],
    "slide_left": [500, 395, 489, 594, 500, 575, 800, 725, 519, 605, 511, 406, 444, 425, 200, 275],
    "slide_right": [481, 395, 489, 594, 556, 575, 800, 725, 500, 605, 511, 406, 500, 425, 200, 275],
    "twist_left": [560, 368, 528, 608, 612, 237, 537, 724, 526, 578, 584, 455, 575, 762, 462, 275],
    "twist_right": [473, 421, 415, 545, 425, 237, 537, 724, 440, 631, 471, 391, 387, 762, 462, 275],
    "guard": [500, 395, 500, 593, 500, 575, 800, 724, 500, 605, 500, 406, 500, 425, 200, 275],
    "punch_left": [600, 395, 500, 593, 544, 681, 826, 288, 447, 713, 372, 406, 431, 425, 310, 275],
    "punch_right": [576, 395, 500, 593, 528, 575, 544, 724, 479, 705, 336, 359, 447, 423, 125, 711],
    "kick_left": [593, 387, 500, 593, 575, 500, 800, 724, 556, 612, 500, 406, 500, 500, 200, 275],
    "kick_right": [443, 387, 500, 593, 500, 500, 800, 724, 406, 612, 500, 406, 425, 500, 200, 275],
    "squat": [500, 200, 838, 744, 500, 575, 800, 725, 500, 800, 162, 256, 500, 425, 200, 275],
    "bow_open": [500, 500, 303, 500, 500, 500, 800, 724, 500, 500, 696, 500, 500, 500, 200, 275],
    "bow_deep": [500, 500, 433, 758, 500, 800, 790, 325, 500, 500, 566, 241, 500, 200, 210, 674],
}
SEMANTIC_ANCHORS["weight_left"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["slide_left"], 0.5)
SEMANTIC_ANCHORS["weight_right"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["slide_right"], 0.5)
SEMANTIC_ANCHORS["step_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["step"], 0.5)
SEMANTIC_ANCHORS["twist_left_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["twist_left"], 0.5)
SEMANTIC_ANCHORS["twist_right_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["twist_right"], 0.5)
SEMANTIC_ANCHORS["punch_left_mid"] = mix(SEMANTIC_ANCHORS["guard"], SEMANTIC_ANCHORS["punch_left"], 0.5)
SEMANTIC_ANCHORS["punch_right_mid"] = mix(SEMANTIC_ANCHORS["guard"], SEMANTIC_ANCHORS["punch_right"], 0.5)
SEMANTIC_ANCHORS["kick_left_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["kick_left"], 0.5)
SEMANTIC_ANCHORS["kick_right_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["kick_right"], 0.5)
SEMANTIC_ANCHORS["squat_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["squat"], 0.5)
SEMANTIC_ANCHORS["squat_left"] = mix(SEMANTIC_ANCHORS["squat"], SEMANTIC_ANCHORS["slide_left"], 0.5)
SEMANTIC_ANCHORS["squat_right"] = mix(SEMANTIC_ANCHORS["squat"], SEMANTIC_ANCHORS["slide_right"], 0.5)
SEMANTIC_ANCHORS["bow_mid"] = mix(SEMANTIC_ANCHORS["stand"], SEMANTIC_ANCHORS["bow_open"], 0.5)
SEMANTIC_ANCHORS["bow_deep_mid"] = mix(SEMANTIC_ANCHORS["bow_open"], SEMANTIC_ANCHORS["bow_deep"], 0.5)
SEMANTIC_ANCHORS["guard_left"] = mix(SEMANTIC_ANCHORS["guard"], SEMANTIC_ANCHORS["weight_left"], 0.5)
SEMANTIC_ANCHORS["guard_right"] = mix(SEMANTIC_ANCHORS["guard"], SEMANTIC_ANCHORS["weight_right"], 0.5)


HIGH_LOAD_STATES = {
    "punch_left",
    "punch_right",
    "kick_left",
    "kick_right",
    "squat",
    "bow_deep",
}

PREPARATION_STATES = {
    "punch_left": {"guard", "guard_left", "punch_left_mid", "weight_left"},
    "punch_right": {"guard", "guard_right", "punch_right_mid", "weight_right"},
    "kick_left": {"stand", "kick_left_mid", "weight_left", "step_mid"},
    "kick_right": {"stand", "kick_right_mid", "weight_right", "step_mid"},
    "squat": {"stand", "squat_mid", "squat_left", "squat_right"},
    "bow_deep": {"bow_mid", "bow_open", "bow_deep_mid", "stand"},
}

FORBIDDEN_OPPOSITE_TRANSITIONS = {
    ("kick_left", "kick_right"),
    ("kick_right", "kick_left"),
    ("punch_left", "punch_right"),
    ("punch_right", "punch_left"),
}


@dataclass
class SafetyEnvelope:
    reference_files: int
    reference_frames: int
    duration_min: int
    duration_max: int
    duration_p95: int
    triplet_min: list[list[int]]
    triplet_max: list[list[int]]
    joint_min: list[int]
    joint_max: list[int]
    joint_delta_max: list[int]
    transition_l1_p95: int
    transition_l1_max: int
    stand_pose: list[int]
    semantic_radius_max: dict[str, int]
    semantic_radius_p95: dict[str, int]
    semantic_transition_counts: dict[str, int]
    semantic_state_counts: dict[str, int]


def percentile(values, ratio):
    ordered = sorted(values)
    if not ordered:
        return 0
    index = min(len(ordered) - 1, int(len(ordered) * ratio))
    return ordered[index]


def pose_from_frame(frame):
    info = parse_plain_frame(frame)
    return [triple[0] for triple in info["channels"][:ACTIVE_JOINTS]]


def l1_distance(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


def pair_key(left, right):
    return "{}->{}".format(left, right)


def classify_pose(pose):
    best_label = None
    best_distance = None
    for label, anchor in SEMANTIC_ANCHORS.items():
        distance = l1_distance(pose, anchor)
        if best_distance is None or distance < best_distance:
            best_label = label
            best_distance = distance
    return best_label, best_distance


def is_plain_reference_action(path, ignore_paths):
    resolved = path.resolve()
    if resolved in ignore_paths:
        return False
    if "自制" in path.name:
        return False
    workspace_root = path.parent.parent
    if (workspace_root / "动作模块" / "{}.json".format(path.stem)).exists():
        return False
    if (workspace_root / "编舞" / "{}.json".format(path.stem)).exists():
        return False
    parsed = parse_file(path)
    return parsed["tag"] == ""


def iter_reference_actions(actions_dir, ignore_paths=None):
    ignored = {pathlib.Path(item).resolve() for item in (ignore_paths or [])}
    for path in sorted(pathlib.Path(actions_dir).glob("*.rob")):
        if is_plain_reference_action(path, ignored):
            yield path, parse_file(path)


def semantic_confidence_limit(envelope, label):
    return envelope.semantic_radius_max.get(label, 0) + SEMANTIC_CONFIDENCE_SLACK


def is_confident_semantic(envelope, label, distance):
    return distance <= semantic_confidence_limit(envelope, label)


def classify_frames(frames):
    classified = []
    for frame in frames:
        info = parse_plain_frame(frame)
        pose = [triple[0] for triple in info["channels"][:ACTIVE_JOINTS]]
        label, distance = classify_pose(pose)
        classified.append(
            {
                "pose": pose,
                "duration": info["duration"],
                "label": label,
                "distance": distance,
            }
        )
    return classified


def learn_reference_envelope(actions_dir, ignore_paths=None):
    actions_dir = pathlib.Path(actions_dir)
    stand_file = actions_dir / "0号立正.rob"
    stand_parsed = parse_file(stand_file)
    stand_pose = pose_from_frame(stand_parsed["frames"][0])

    joint_min = [10**9] * ACTIVE_JOINTS
    joint_max = [-1] * ACTIVE_JOINTS
    triplet_min = [[10**9] * 3 for _ in range(ACTIVE_JOINTS)]
    triplet_max = [[-1] * 3 for _ in range(ACTIVE_JOINTS)]
    joint_delta_max = [0] * ACTIVE_JOINTS
    durations = []
    transition_l1 = []
    semantic_distances = defaultdict(list)
    semantic_transition_counts = Counter()
    semantic_state_counts = Counter()
    reference_files = 0
    reference_frames = 0

    for _, parsed in iter_reference_actions(actions_dir, ignore_paths):
        reference_files += 1
        previous_pose = None
        previous_label = None
        for frame in parsed["frames"]:
            info = parse_plain_frame(frame)
            durations.append(info["duration"])
            current_triples = info["channels"][:ACTIVE_JOINTS]
            current_pose = [triple[0] for triple in current_triples]
            current_label, current_distance = classify_pose(current_pose)
            semantic_state_counts[current_label] += 1
            semantic_distances[current_label].append(current_distance)
            for joint_index, triple in enumerate(current_triples):
                joint_min[joint_index] = min(joint_min[joint_index], triple[0])
                joint_max[joint_index] = max(joint_max[joint_index], triple[0])
                for field_index, value in enumerate(triple):
                    triplet_min[joint_index][field_index] = min(triplet_min[joint_index][field_index], value)
                    triplet_max[joint_index][field_index] = max(triplet_max[joint_index][field_index], value)
            if previous_pose is not None:
                deltas = [abs(current - previous) for current, previous in zip(current_pose, previous_pose)]
                for index, value in enumerate(deltas):
                    joint_delta_max[index] = max(joint_delta_max[index], value)
                transition_l1.append(sum(deltas))
                semantic_transition_counts[pair_key(previous_label, current_label)] += 1
            previous_pose = current_pose
            previous_label = current_label
            reference_frames += 1

    return SafetyEnvelope(
        reference_files=reference_files,
        reference_frames=reference_frames,
        duration_min=min(durations),
        duration_max=max(durations),
        duration_p95=percentile(durations, 0.95),
        triplet_min=triplet_min,
        triplet_max=triplet_max,
        joint_min=joint_min,
        joint_max=joint_max,
        joint_delta_max=joint_delta_max,
        transition_l1_p95=percentile(transition_l1, 0.95),
        transition_l1_max=max(transition_l1),
        stand_pose=stand_pose,
        semantic_radius_max={label: max(values) for label, values in semantic_distances.items()},
        semantic_radius_p95={label: percentile(values, 0.95) for label, values in semantic_distances.items()},
        semantic_transition_counts=dict(semantic_transition_counts),
        semantic_state_counts=dict(semantic_state_counts),
    )


def audit_semantic_sequence(classified, envelope, label):
    violations = []
    for index, item in enumerate(classified):
        current_label = item["label"]
        current_distance = item["distance"]
        if not is_confident_semantic(envelope, current_label, current_distance):
            continue
        if current_label in HIGH_LOAD_STATES and item["duration"] < MIN_DYNAMIC_DURATION:
            violations.append(
                "{} frame {} semantic {} duration {} below {}".format(
                    label,
                    index,
                    current_label,
                    item["duration"],
                    MIN_DYNAMIC_DURATION,
                )
            )
        if current_label in PREPARATION_STATES:
            allowed = PREPARATION_STATES[current_label]
            allowed_with_hold = set(allowed)
            allowed_with_hold.add(current_label)
            previous_ok = False
            next_ok = False
            for offset in (1, 2):
                previous_item = classified[index - offset] if index - offset >= 0 else None
                next_item = classified[index + offset] if index + offset < len(classified) else None
                if (
                    previous_item
                    and is_confident_semantic(envelope, previous_item["label"], previous_item["distance"])
                    and previous_item["label"] in allowed_with_hold
                ):
                    previous_ok = True
                if (
                    next_item
                    and is_confident_semantic(envelope, next_item["label"], next_item["distance"])
                    and next_item["label"] in allowed_with_hold
                ):
                    next_ok = True
            if not previous_ok and not next_ok:
                violations.append(
                    "{} frame {} semantic {} missing mid-state preparation/recovery".format(
                        label,
                        index,
                        current_label,
                    )
                )
        if index == 0:
            continue
        previous_item = classified[index - 1]
        previous_label = previous_item["label"]
        if not is_confident_semantic(envelope, previous_label, previous_item["distance"]):
            continue
        if (previous_label, current_label) in FORBIDDEN_OPPOSITE_TRANSITIONS:
            violations.append(
                "{} frame {} semantic transition {} -> {} skips center recovery".format(
                    label,
                    index,
                    previous_label,
                    current_label,
                )
            )
            continue
        transition_name = pair_key(previous_label, current_label)
        if transition_name not in envelope.semantic_transition_counts:
            delta = l1_distance(previous_item["pose"], item["pose"])
            if delta > envelope.transition_l1_p95:
                violations.append(
                    "{} frame {} semantic transition {} unseen in reference library with l1 {}".format(
                        label,
                        index,
                        transition_name,
                        delta,
                    )
                )
    return violations


def audit_frame_sequence(frames, envelope, label):
    violations = []
    previous_pose = None
    max_l1 = 0
    classified = classify_frames(frames)
    for frame_index, frame in enumerate(frames):
        info = parse_plain_frame(frame)
        if info["duration"] < envelope.duration_min or info["duration"] > envelope.duration_max:
            violations.append(
                "{} frame {} duration {} outside [{}..{}]".format(
                    label,
                    frame_index,
                    info["duration"],
                    envelope.duration_min,
                    envelope.duration_max,
                )
            )
        current_triples = info["channels"][:ACTIVE_JOINTS]
        current_pose = [triple[0] for triple in current_triples]
        for joint_index, triple in enumerate(current_triples):
            for field_index, value in enumerate(triple):
                lower = envelope.triplet_min[joint_index][field_index]
                upper = envelope.triplet_max[joint_index][field_index]
                if value < lower or value > upper:
                    violations.append(
                        "{} frame {} joint {} field {} value {} outside [{}..{}]".format(
                            label,
                            frame_index,
                            joint_index + 1,
                            field_index + 1,
                            value,
                            lower,
                            upper,
                        )
                    )
        if previous_pose is not None:
            deltas = [abs(current - previous) for current, previous in zip(current_pose, previous_pose)]
            max_l1 = max(max_l1, sum(deltas))
            for joint_index, value in enumerate(deltas):
                limit = envelope.joint_delta_max[joint_index]
                if value > limit:
                    violations.append(
                        "{} frame {} joint {} delta {} exceeds {}".format(
                            label,
                            frame_index,
                            joint_index + 1,
                            value,
                            limit,
                        )
                    )
            if sum(deltas) > envelope.transition_l1_max:
                violations.append(
                    "{} frame {} total delta {} exceeds {}".format(
                        label,
                        frame_index,
                        sum(deltas),
                        envelope.transition_l1_max,
                    )
                )
        previous_pose = current_pose
    violations.extend(audit_semantic_sequence(classified, envelope, label))
    return {
        "violations": violations,
        "max_l1": max_l1,
        "semantic_frames": classified,
    }


def audit_boundaries(segments, envelope):
    reports = []
    for left, right in zip(segments, segments[1:]):
        deltas = [abs(current - previous) for current, previous in zip(left["end_pose"], right["start_pose"])]
        max_delta = max(deltas)
        total_delta = sum(deltas)
        level = "ok"
        left_label, left_distance = classify_pose(left["end_pose"])
        right_label, right_distance = classify_pose(right["start_pose"])
        confident_left = is_confident_semantic(envelope, left_label, left_distance)
        confident_right = is_confident_semantic(envelope, right_label, right_distance)
        if (
            any(delta > limit for delta, limit in zip(deltas, envelope.joint_delta_max))
            or total_delta > envelope.transition_l1_max
        ):
            level = "error"
        elif confident_left and confident_right and (left_label, right_label) in FORBIDDEN_OPPOSITE_TRANSITIONS:
            level = "error"
        elif total_delta > envelope.transition_l1_p95:
            level = "warn"
        reports.append(
            {
                "left": left["label"],
                "right": right["label"],
                "source_left": left["source"],
                "source_right": right["source"],
                "max_delta": max_delta,
                "l1": total_delta,
                "level": level,
                "semantic_left": left_label,
                "semantic_right": right_label,
            }
        )
    return reports


def audit_plain_file(file_path, actions_dir=None, ignore_paths=None):
    file_path = pathlib.Path(file_path)
    envelope = learn_reference_envelope(actions_dir or file_path.parent, ignore_paths=ignore_paths)
    parsed = parse_file(file_path)
    if parsed["tag"]:
        raise ValueError("target file must be plain ACT-40: {}".format(file_path))
    if parsed["frame_count"] > MAX_ACTION_FRAMES:
        raise ValueError(
            "frame count {} exceeds device load limit of {}".format(parsed["frame_count"], MAX_ACTION_FRAMES)
        )
    result = audit_frame_sequence(parsed["frames"], envelope, file_path.name)
    return envelope, result


def print_envelope(envelope):
    print("reference_files={}".format(envelope.reference_files))
    print("reference_frames={}".format(envelope.reference_frames))
    print("duration_range={}..{}".format(envelope.duration_min, envelope.duration_max))
    print("duration_p95={}".format(envelope.duration_p95))
    print("transition_l1_p95={}".format(envelope.transition_l1_p95))
    print("transition_l1_max={}".format(envelope.transition_l1_max))
    print("semantic_states={}".format(len(envelope.semantic_state_counts)))
    print("semantic_transitions={}".format(len(envelope.semantic_transition_counts)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="plain ACT-40 file to audit")
    parser.add_argument("--actions-dir", default=r"c:\mycode\bot\动作")
    args = parser.parse_args()

    envelope, result = audit_plain_file(args.target, actions_dir=args.actions_dir, ignore_paths=[args.target])
    print_envelope(envelope)
    print("target_max_l1={}".format(result["max_l1"]))
    if result["violations"]:
        print("violations={}".format(len(result["violations"])))
        for item in result["violations"]:
            print(item)
        raise SystemExit(1)
    print("violations=0")


if __name__ == "__main__":
    main()
