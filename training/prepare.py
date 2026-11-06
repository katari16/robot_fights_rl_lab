"""Prepare auditable 50 Hz G1 references using the exact mjlab training model."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen

os.environ.setdefault("MPLCONFIGDIR", "/tmp/robot-fights-mpl")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "training/data"
FPS = 50
ISAAC_TO_MJ = [
    0,
    3,
    6,
    9,
    13,
    17,
    1,
    4,
    7,
    10,
    14,
    18,
    2,
    5,
    8,
    11,
    15,
    19,
    21,
    23,
    25,
    27,
    12,
    16,
    20,
    22,
    24,
    26,
    28,
]
JAB_COMMIT = "bd8a0a65c60787296c7eb9a90be10b17fae3e12b"
JAB_URL = f"https://raw.githubusercontent.com/abtonmoy/ai_hackathon_calhacks/{JAB_COMMIT}/data/IMG_3430.csv"
JAB_BLOB = "3775f20da7d7b5279f281702cb080006078eec5d"


def training_scene():
    from mjlab.scene import Scene
    from src.tasks.tracking.config.g1.env_cfgs import unitree_g1_flat_tracking_env_cfg

    scene = Scene(unitree_g1_flat_tracking_env_cfg().scene, device="cpu")
    return scene, scene.compile()


def resample(qpos, input_fps):
    old = np.arange(len(qpos)) / input_fps
    new = np.arange(round(old[-1] * FPS) + 1) / FPS
    new = np.minimum(new, old[-1])
    result = np.stack([np.interp(new, old, x) for x in qpos.T], axis=1)
    result[:, 3:7] = Slerp(old, Rotation.from_quat(qpos[:, [4, 5, 6, 3]]))(
        new
    ).as_quat()[:, [3, 0, 1, 2]]
    return result


def face_forward(qpos):
    result = qpos.copy()
    rot = Rotation.from_quat(result[:, [4, 5, 6, 3]])
    forward = rot.apply(np.tile([1, 0, 0], (len(rot), 1)))
    yaw = np.median(np.unwrap(np.arctan2(forward[:, 1], forward[:, 0])))
    turn = Rotation.from_euler("z", -yaw)
    result[:, :2] -= result[0, :2]
    result[:, :3] = turn.apply(result[:, :3])
    result[:, 3:7] = (turn * rot).as_quat()[:, [3, 0, 1, 2]]
    return result


def mirror(qpos, names):
    result = qpos.copy()
    result[:, 1] *= -1
    # Reflection across the sagittal plane: R' = S R S.
    reflect = np.diag([1, -1, 1])
    rot = Rotation.from_quat(qpos[:, [4, 5, 6, 3]]).as_matrix()
    result[:, 3:7] = Rotation.from_matrix(reflect @ rot @ reflect).as_quat()[
        :, [3, 0, 1, 2]
    ]
    for i, name in enumerate(names):
        other = (
            name.replace("left_", "TEMP_")
            .replace("right_", "left_")
            .replace("TEMP_", "right_")
        )
        sign = -1 if "roll" in name or "yaw" in name else 1
        result[:, 7 + i] = sign * qpos[:, 7 + names.index(other)]
    return result


def ground(model, qpos):
    data = mujoco.MjData(model)
    ids = [
        model.geom(f"robot/{s}_foot{n}_collision").id
        for s in ("left", "right")
        for n in range(1, 8)
    ]
    for pose in qpos:
        data.qpos[:] = pose
        mujoco.mj_forward(model, data)
        # Feet use capsules: radius plus projected half cylinder length.
        bottom = (
            data.geom_xpos[ids, 2]
            - model.geom_size[ids, 0]
            - model.geom_size[ids, 1] * np.abs(data.geom_xmat[ids, 8])
        )
        pose[2] -= bottom.min()
    return qpos


def blend(a, b, frames=40):
    t = np.linspace(0, 1, frames)
    t = t**3 * (10 - 15 * t + 6 * t**2)
    q = a[None] * (1 - t[:, None]) + b[None] * t[:, None]
    q[:, 3:7] = Slerp([0, 1], Rotation.from_quat(np.array([a, b])[:, [4, 5, 6, 3]]))(
        t
    ).as_quat()[:, [3, 0, 1, 2]]
    return q


def wrap(model, raw):
    nominal = ground(model, model.key_qpos[:1].copy())[0]
    return ground(
        model,
        np.vstack(
            [
                np.tile(nominal, (35, 1)),
                blend(nominal, raw[0]),
                raw,
                blend(raw[-1], nominal),
                np.tile(nominal, (75, 1)),
            ]
        ),
    )


def save_motion(scene, model, name, qpos):
    data = mujoco.MjData(model)
    names = scene["robot"].body_names
    ids = [model.body("robot/" + n).id for n in names]
    joints = scene["robot"].joint_names
    limits = np.array([model.joint("robot/" + n).range for n in joints])
    violation = np.maximum(limits[:, 0] - qpos[:, 7:], qpos[:, 7:] - limits[:, 1]).max()
    if violation > 0.01:
        raise ValueError(f"{name} exceeds joint limits by {violation:.4f} rad")
    qvel = np.empty((len(qpos), model.nv))
    pos, quat, lin, ang = [], [], [], []
    jp, jr = np.zeros((3, model.nv)), np.zeros((3, model.nv))
    for i, pose in enumerate(qpos):
        lo, hi = max(0, i - 1), min(len(qpos) - 1, i + 1)
        mujoco.mj_differentiatePos(model, qvel[i], (hi - lo) / FPS, qpos[lo], qpos[hi])
        data.qpos[:], data.qvel[:] = pose, qvel[i]
        mujoco.mj_forward(model, data)
        pos.append(data.xpos[ids].copy())
        quat.append(data.xquat[ids].copy())
        lv, av = [], []
        for body in ids:
            mujoco.mj_jacBody(model, data, jp, jr, body)
            lv.append(jp @ qvel[i])
            av.append(jr @ qvel[i])
        lin.append(lv)
        ang.append(av)
    arrays = dict(
        fps=np.array([FPS]),
        joint_pos=qpos[:, 7:],
        joint_vel=qvel[:, 6:],
        body_pos_w=pos,
        body_quat_w=quat,
        body_lin_vel_w=lin,
        body_ang_vel_w=ang,
        qpos=qpos,
        qvel=qvel,
        joint_names=np.array(joints),
        body_names=np.array(names),
    )
    arrays = {k: np.asarray(v) for k, v in arrays.items()}
    np.savez_compressed(DATA / f"{name}.npz", **arrays)
    return {
        "frames": len(qpos),
        "seconds": len(qpos) / FPS,
        "joint_speed_max_rad_s": float(np.abs(qvel[:, 6:]).max()),
        "sha256": hashlib.sha256((DATA / f"{name}.npz").read_bytes()).hexdigest(),
    }


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    scene, model = training_scene()
    cache = ROOT / "simulation/data/IMG_3430.csv"
    payload = (
        cache.read_bytes() if cache.exists() else urlopen(JAB_URL, timeout=60).read()
    )
    if (
        hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
        != JAB_BLOB
    ):
        raise ValueError("Robo Jab checksum mismatch")
    from io import BytesIO

    raw = np.loadtxt(BytesIO(payload), delimiter=",")[125:220]
    raw[:, 3:7] = raw[:, [6, 3, 4, 5]]  # CSV xyzw -> MuJoCo wxyz.
    right = wrap(model, resample(face_forward(raw), 30))
    left = mirror(right, scene["robot"].joint_names)

    folder = (
        ROOT
        / "external/GR00T-WholeBodyControl/gear_sonic_deploy/reference/example/neutral_kick_R_001__A543"
    )
    joint = np.loadtxt(folder / "joint_pos.csv", delimiter=",", skiprows=1)[
        :, ISAAC_TO_MJ
    ]
    root_pos = np.loadtxt(folder / "body_pos.csv", delimiter=",", skiprows=1)[:, :3]
    root_quat = np.loadtxt(folder / "body_quat.csv", delimiter=",", skiprows=1)[:, :4]
    kick = wrap(model, face_forward(np.column_stack([root_pos, root_quat, joint])))
    motions = {"left_punch": left, "right_punch": right, "right_kick": kick}
    motions["skills"] = np.vstack(list(motions.values()))
    report = {name: save_motion(scene, model, name, q) for name, q in motions.items()}
    report["sources"] = {
        "punch": JAB_URL,
        "punch_git_blob": JAB_BLOB,
        "kick": str(folder.relative_to(ROOT)),
        "kick_fps": 50,
        "punch_frames": [125, 220],
        "left_punch": "Sagittal reflection of right punch",
        "processing": "50 Hz, constant heading alignment, foot grounding, nominal entry and recovery",
        "limits": "Kinematic joint bounds only; dynamic feasibility must be measured during rollouts.",
    }
    (DATA / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
