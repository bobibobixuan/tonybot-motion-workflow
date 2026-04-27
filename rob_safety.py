import argparse
import pathlib
from dataclasses import dataclass

from rob_reverse import parse_file, parse_plain_frame


ACTIVE_JOINTS = 16


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


def is_plain_reference_action(path, ignore_paths):
    resolved = path.resolve()
    if resolved in ignore_paths:
        return False
    if "自制" in path.name:
        return False
    parsed = parse_file(path)
    return parsed["tag"] == ""


def iter_reference_actions(actions_dir, ignore_paths=None):
    ignored = {pathlib.Path(item).resolve() for item in (ignore_paths or [])}
    for path in sorted(pathlib.Path(actions_dir).glob("*.rob")):
        if is_plain_reference_action(path, ignored):
            yield path, parse_file(path)


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
    reference_files = 0
    reference_frames = 0

    for _, parsed in iter_reference_actions(actions_dir, ignore_paths):
        reference_files += 1
        previous_pose = None
        for frame in parsed["frames"]:
            info = parse_plain_frame(frame)
            durations.append(info["duration"])
            current_triples = info["channels"][:ACTIVE_JOINTS]
            current_pose = [triple[0] for triple in current_triples]
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
            previous_pose = current_pose
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
    )


def audit_frame_sequence(frames, envelope, label):
    violations = []
    previous_pose = None
    max_l1 = 0
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
    return {
        "violations": violations,
        "max_l1": max_l1,
    }


def audit_boundaries(segments, envelope):
    reports = []
    for left, right in zip(segments, segments[1:]):
        deltas = [abs(current - previous) for current, previous in zip(left["end_pose"], right["start_pose"])]
        max_delta = max(deltas)
        total_delta = sum(deltas)
        level = "ok"
        if any(delta > limit for delta, limit in zip(deltas, envelope.joint_delta_max)) or total_delta > envelope.transition_l1_max:
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
            }
        )
    return reports


def audit_plain_file(file_path, actions_dir=None, ignore_paths=None):
    file_path = pathlib.Path(file_path)
    envelope = learn_reference_envelope(actions_dir or file_path.parent, ignore_paths=ignore_paths)
    parsed = parse_file(file_path)
    if parsed["tag"]:
        raise ValueError("target file must be plain ACT-40: {}".format(file_path))
    result = audit_frame_sequence(parsed["frames"], envelope, file_path.name)
    return envelope, result


def print_envelope(envelope):
    print("reference_files={}".format(envelope.reference_files))
    print("reference_frames={}".format(envelope.reference_frames))
    print("duration_range={}..{}".format(envelope.duration_min, envelope.duration_max))
    print("duration_p95={}".format(envelope.duration_p95))
    print("transition_l1_p95={}".format(envelope.transition_l1_p95))
    print("transition_l1_max={}".format(envelope.transition_l1_max))


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