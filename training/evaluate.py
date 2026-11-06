"""Measure complete physics rollouts from nominal, including entry and recovery."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from train import HERE, configuration
import numpy as np
import torch
from mjlab.envs import ManagerBasedRlEnv
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
from mjlab.tasks.tracking.mdp.commands import MotionLoader
from src.tasks.tracking.config.g1.rl_cfg import unitree_g1_tracking_ppo_runner_cfg


def evaluate(checkpoint, output, num_envs=64, seed=314, perturb=False):
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    torch.set_num_threads(4)
    cfg = configuration(HERE / "data/left_punch.npz", num_envs, seed, play=True)
    cfg.commands["motion"].debug_vis = False
    agent = unitree_g1_tracking_ppo_runner_cfg()
    agent.logger, agent.upload_model = "tensorboard", False
    env = RslRlVecEnvWrapper(
        ManagerBasedRlEnv(cfg, device="cuda:0"), clip_actions=agent.clip_actions
    )
    runner = MjlabOnPolicyRunner(env, asdict(agent), None, device="cuda:0")
    runner.load(str(checkpoint))
    policy = runner.get_inference_policy(device="cuda:0")
    raw = env.unwrapped
    cmd = raw.command_manager.get_term("motion")
    robot = raw.scene["robot"]
    limits = torch.tensor(
        np.abs(raw.sim.mj_model.actuator_forcerange).max(axis=1), device="cuda:0"
    )
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "checkpoint": str(checkpoint.resolve()),
        "seed": seed,
        "num_envs": num_envs,
        "perturb": perturb,
        "condition": "Clean model; initial root velocity +/-0.15 m/s and +/-0.15 rad/s"
        if perturb
        else "Clean model; exact nominal start",
        "skills": {},
    }
    for skill in ("left_punch", "right_punch", "right_kick"):
        cmd.motion = MotionLoader(
            str(HERE / f"data/{skill}.npz"), cmd.body_indexes, "cuda:0"
        )
        obs, _ = env.reset()
        # Upstream reset writes reference state but does not refresh the relative
        # body targets used by termination checks until the first command update.
        # Refresh those targets without advancing the reference clock or physics.
        cmd.time_steps.sub_(1)
        cmd._update_command()
        obs = env.get_observations()
        if perturb:
            state = torch.cat(
                [robot.data.root_link_pose_w, robot.data.root_link_vel_w], dim=1
            ).clone()
            state[:, 7:13] += (
                torch.rand((num_envs, 6), device="cuda:0") * 2 - 1
            ) * 0.15
            robot.write_root_state_to_sim(state)
            raw.sim.forward()
            raw.sim.sense()
            obs = env.get_observations()
        alive = torch.ones(num_envs, dtype=torch.bool, device="cuda:0")
        tip_name = (
            "right_ankle_roll_link"
            if skill == "right_kick"
            else skill.split("_")[0] + "_wrist_yaw_link"
        )
        tip_index = robot.body_names.index(tip_name)
        torso_index = robot.body_names.index("torso_link")
        tip_forward = torch.full((num_envs,), -torch.inf, device="cuda:0")
        tip_height = torch.zeros(num_envs, device="cuda:0")
        failure_reasons = {name: 0 for name in raw.termination_manager.active_terms}
        first_failure = np.full(num_envs, -1, dtype=int)
        qpos, torque, joint_error, body_error, height, saturation = (
            [],
            [],
            [],
            [],
            [],
            [],
        )
        qpos.append(raw.sim.data.qpos[0].cpu().numpy().copy())
        with torch.no_grad():
            # Stop before the upstream command's end-of-clip state resampling.
            for frame in range(cmd.motion.time_step_total - 1):
                obs, _, done, _ = env.step(policy(obs))
                failed = alive & done.bool()
                for name in failure_reasons:
                    failure_reasons[name] += int(
                        (failed & raw.termination_manager.get_term(name)).sum()
                    )
                first_failure[failed.cpu().numpy()] = frame + 1
                alive &= ~done.bool()
                if first_failure[0] < 0:
                    qpos.append(raw.sim.data.qpos[0].cpu().numpy().copy())
                    torque.append(robot.data.actuator_force[0].cpu().numpy().copy())
                if alive.any():
                    positions = robot.data.body_link_pos_w
                    forward = positions[:, tip_index, 0] - positions[:, torso_index, 0]
                    tip_forward[alive] = torch.maximum(
                        tip_forward[alive], forward[alive]
                    )
                    tip_height[alive] = torch.maximum(
                        tip_height[alive], positions[alive, tip_index, 2]
                    )
                    joint_error.extend(
                        (robot.data.joint_pos[alive] - cmd.joint_pos[alive])
                        .square()
                        .mean(1)
                        .sqrt()
                        .cpu()
                        .tolist()
                    )
                    body_error.extend(
                        (cmd.robot_body_pos_w[alive] - cmd.body_pos_w[alive])
                        .norm(dim=-1)
                        .mean(1)
                        .cpu()
                        .tolist()
                    )
                    height.extend(robot.data.root_link_pos_w[alive, 2].cpu().tolist())
                    ratio = robot.data.actuator_force[alive].abs() / limits.clamp(
                        min=1e-6
                    )
                    saturation.extend((ratio >= 0.95).float().mean(1).cpu().tolist())
                if not alive.any():
                    break
        np.savez_compressed(
            output / f"{skill}.npz",
            qpos=qpos,
            actuator_force=torque,
            fps=[50],
            failed=first_failure[0] >= 0,
            failure_frame=first_failure[0],
        )
        result = {
            "completed": int(alive.sum()),
            "trials": num_envs,
            "first_failure_frames": first_failure.tolist(),
            "joint_rmse_rad": float(np.mean(joint_error)) if joint_error else None,
            "body_position_error_m": float(np.mean(body_error)) if body_error else None,
            "minimum_root_height_m": float(np.min(height)) if height else None,
            "motor_saturation_fraction": float(np.mean(saturation))
            if saturation
            else None,
            "recorded_frames": len(qpos),
            "failure_reasons": failure_reasons,
            "peak_tip_forward_m": tip_forward.cpu().tolist(),
            "peak_tip_height_m": tip_height.cpu().tolist(),
        }
        reference = np.load(HERE / f"data/{skill}.npz")
        result["reference_peak_tip_forward_m"] = float(
            np.max(
                reference["body_pos_w"][:, tip_index, 0]
                - reference["body_pos_w"][:, torso_index, 0]
            )
        )
        result["reference_peak_tip_height_m"] = float(
            np.max(reference["body_pos_w"][:, tip_index, 2])
        )
        report["skills"][skill] = result
        print(skill, json.dumps(result), flush=True)
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    env.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--num-envs", type=int, default=64)
    parser.add_argument("--seed", type=int, default=314)
    parser.add_argument("--perturb", action="store_true")
    args = parser.parse_args()
    evaluate(args.checkpoint, args.output, args.num_envs, args.seed, args.perturb)
