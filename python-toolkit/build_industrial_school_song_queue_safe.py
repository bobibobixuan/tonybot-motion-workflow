import pathlib

from dance_workflow import build_workflow
from rob_safety import audit_plain_file


WORKSPACE = pathlib.Path(__file__).resolve().parent
SPEC_A = WORKSPACE / "编舞" / "167号工业校歌队列广播体操版A.json"
SPEC_B = WORKSPACE / "编舞" / "168号工业校歌队列广播体操版B.json"
ROB_A = WORKSPACE / "动作" / "167号工业校歌队列广播体操版A.rob"
ROB_B = WORKSPACE / "动作" / "168号工业校歌队列广播体操版B.rob"
ACTION_DIR = WORKSPACE / "动作"


def audit_output(path):
    envelope, result = audit_plain_file(path, actions_dir=ACTION_DIR, ignore_paths=[path])
    print("audit_target={}".format(path.name))
    print("reference_files={}".format(envelope.reference_files))
    print("reference_frames={}".format(envelope.reference_frames))
    print("target_max_l1={}".format(result["max_l1"]))
    print("violations={}".format(len(result["violations"])))
    if result["violations"]:
        for item in result["violations"]:
            print(item)
        raise SystemExit(1)


def main():
    print("build_spec={}".format(SPEC_A.name))
    build_workflow(SPEC_A, actions_dir=ACTION_DIR)
    audit_output(ROB_A)
    print()
    print("build_spec={}".format(SPEC_B.name))
    build_workflow(SPEC_B, actions_dir=ACTION_DIR)
    audit_output(ROB_B)


if __name__ == "__main__":
    main()
