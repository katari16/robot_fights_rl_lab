"""Pinned Robo Jab reference data and explicit G1 pose mapping."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from scipy.spatial.transform import Rotation

from arena import Arena, HERE, JOINTS, SPAWNS, foot_bottom

COMMIT = "bd8a0a65c60787296c7eb9a90be10b17fae3e12b"
SOURCE = f"https://raw.githubusercontent.com/abtonmoy/ai_hackathon_calhacks/{COMMIT}/data/IMG_3430.csv"
GIT_BLOB = "3775f20da7d7b5279f281702cb080006078eec5d"
FPS = 30


def fetch_clip(cache: Path = HERE / "data") -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / "IMG_3430.csv"
    payload = path.read_bytes() if path.exists() else urlopen(SOURCE, timeout=60).read()
    digest = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
    if digest != GIT_BLOB:
        raise ValueError(f"Robo Jab clip checksum mismatch: {path}")
    if not path.exists():
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)
    return path


def load_clip(path: Path) -> np.ndarray:
    clip = np.loadtxt(path, delimiter=",")
    if (
        clip.ndim != 2
        or clip.shape[1] != 36
        or len(clip) < 2
        or not np.isfinite(clip).all()
    ):
        raise ValueError("Motion CSV must contain finite 36-column G1 poses")
    if not np.allclose(np.linalg.norm(clip[:, 3:7], axis=1), 1, atol=0.01):
        raise ValueError("Root quaternions are not normalized")
    return clip


def interpolate(a: np.ndarray, b: np.ndarray, weight: float) -> np.ndarray:
    """Linear translation/joints, shortest-path spherical root rotation."""
    pose = a * (1 - weight) + b * weight
    for start in (0, 36):
        qa, qb = a[start + 3 : start + 7], b[start + 3 : start + 7]
        dot = float(np.dot(qa, qb))
        if dot < 0:
            qb, dot = -qb, -dot
        if dot > 0.9995:
            q = qa * (1 - weight) + qb * weight
        else:
            theta = np.arccos(np.clip(dot, -1, 1))
            q = (
                qa * np.sin((1 - weight) * theta) + qb * np.sin(weight * theta)
            ) / np.sin(theta)
        pose[start + 3 : start + 7] = q / np.linalg.norm(q)
    return pose


def make_replay(arena: Arena, clip: np.ndarray) -> np.ndarray:
    clip = clip[85:290].copy()
    nominal = arena.model.key_qpos[0].copy()
    poses = np.tile(nominal, (len(clip), 1))
    source_rot = Rotation.from_quat(clip[:, 3:7])  # CSV xyzw, MuJoCo wxyz.
    forward = source_rot.apply(np.tile([1, 0, 0], (len(clip), 1)))
    initial_yaw = float(np.median(np.unwrap(np.arctan2(forward[:, 1], forward[:, 0]))))
    for index, (x, y, yaw) in enumerate(SPAWNS):
        root = arena.model.joint(f"g1_{index}/floating_base_joint").qposadr[0]
        rotation = Rotation.from_euler("z", yaw - initial_yaw)
        local = clip[:, :3].copy()
        local[:, :2] -= local[0, :2]
        poses[:, root : root + 3] = rotation.apply(local) + [x, y, 0]
        quat = (rotation * source_rot).as_quat()
        poses[:, root + 3 : root + 7] = quat[:, [3, 0, 1, 2]]
        for col, name in enumerate(JOINTS):
            joint = arena.model.joint(f"g1_{index}/{name}")
            values = clip[:, 7 + col]
            if np.any(values < joint.range[0] - 0.01) or np.any(
                values > joint.range[1] + 0.01
            ):
                raise ValueError(f"Reference exceeds the model's joint limits: {name}")
            poses[:, joint.qposadr[0]] = values
    # Align each recorded frame with the mat. This is a kinematic visual correction,
    # not a dynamics correction or a claim of feasible torque/contact trajectories.
    for pose in poses:
        arena.set_pose(pose)
        for index in range(2):
            root = arena.model.joint(f"g1_{index}/floating_base_joint").qposadr[0]
            pose[root + 2] -= foot_bottom(arena.model, arena.data, index)
    arena.set_pose(nominal)
    for index in range(2):
        nominal[36 * index + 2] -= foot_bottom(arena.model, arena.data, index)
    # Both ends return to nominal so replay can loop without a discontinuous reset.
    blend = 30
    ramp = np.linspace(0, 1, blend)
    ramp = ramp * ramp * (3 - 2 * ramp)
    sequence = np.vstack(
        [
            np.tile(nominal, (30, 1)),
            [interpolate(nominal, poses[0], w) for w in ramp],
            poses,
            [interpolate(poses[-1], nominal, w) for w in ramp],
            np.tile(nominal, (30, 1)),
        ]
    )
    # Separate the punches in time while keeping the same genuine recorded reference.
    sequence[:, 36:] = np.roll(sequence[:, 36:], 21, axis=0)
    for pose in sequence:
        arena.set_pose(pose)
        for index in range(2):
            pose[index * 36 + 2] -= foot_bottom(arena.model, arena.data, index)
    arena.reset()
    return sequence


def sample(replay: np.ndarray, seconds: float) -> np.ndarray:
    frame = (seconds * FPS) % len(replay)
    i = int(frame)
    return interpolate(replay[i], replay[(i + 1) % len(replay)], frame - i)
