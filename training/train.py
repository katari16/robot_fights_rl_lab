"""Local PPO training for reference-conditioned, proprioceptive G1 skills."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/robot-fights-mpl")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import torch
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
from mjlab.utils.torch import configure_torch_backends
from mjlab.utils.os import dump_yaml
from src.tasks.tracking.config.g1.env_cfgs import unitree_g1_flat_tracking_env_cfg
from src.tasks.tracking.config.g1.rl_cfg import unitree_g1_tracking_ppo_runner_cfg

HERE = Path(__file__).resolve().parent


def configuration(motion, num_envs, seed, stage="foundation", play=False):
    cfg = unitree_g1_flat_tracking_env_cfg(has_state_estimation=False, play=play)
    cfg.seed = seed
    cfg.scene.num_envs = num_envs
    cfg.commands["motion"].motion_file = str(Path(motion).resolve())
    if stage == "foundation":
        # Learn clean execution before introducing the full upstream disturbances.
        cfg.events.clear()
        cfg.commands["motion"].pose_range = {}
        cfg.commands["motion"].velocity_range = {}
        cfg.commands["motion"].joint_position_range = (-0.02, 0.02)
    if play:
        cfg.commands["motion"].joint_position_range = (0.0, 0.0)
    return cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--motion", type=Path, default=HERE / "data/skills.npz")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--num-envs", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--stage", choices=["foundation", "robust"], default="foundation"
    )
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    if args.iterations < 1 or args.num_envs < 1:
        parser.error("Iterations and environment count must be positive")
    if not args.motion.is_file():
        parser.error("Motion file is missing; run training/prepare.py first")
    if (args.output / "run.json").exists():
        parser.error("Choose a new output directory for each run, including resumes")
    torch.set_num_threads(4)
    configure_torch_backends()
    cfg = configuration(args.motion, args.num_envs, args.seed, args.stage)
    agent = unitree_g1_tracking_ppo_runner_cfg()
    agent.logger = "tensorboard"
    agent.upload_model = False
    agent.seed = args.seed
    agent.save_interval = 100
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    manifest["motion_sha256"] = hashlib.sha256(args.motion.read_bytes()).hexdigest()
    manifest["packages"] = {
        name: importlib.metadata.version(name)
        for name in (
            "torch",
            "mujoco",
            "mujoco-warp",
            "warp-lang",
            "mjlab",
            "rsl-rl-lib",
        )
    }
    manifest["gpu"] = torch.cuda.get_device_name(0)
    (args.output / "run.json").write_text(json.dumps(manifest, indent=2) + "\n")
    dump_yaml(args.output / "env.yaml", asdict(cfg))
    dump_yaml(args.output / "agent.yaml", asdict(agent))
    env = RslRlVecEnvWrapper(
        ManagerBasedRlEnv(cfg, device="cuda:0"), clip_actions=agent.clip_actions
    )
    runner = MjlabOnPolicyRunner(env, asdict(agent), str(args.output), device="cuda:0")
    if args.resume:
        runner.load(str(args.resume))
    runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=True)
    runner.export_policy_to_onnx(str(args.output))
    env.close()


if __name__ == "__main__":
    main()
