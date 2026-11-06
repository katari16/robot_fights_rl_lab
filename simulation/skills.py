#!/usr/bin/env python3
"""Render prepared skills or measured policy rollouts in the two-G1 arena."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

from arena import Arena, DEFAULT_LOGO, HERE, SPAWNS
from demo import CAMERA, build_web
from motion import sample

SKILLS = ("left_punch", "right_punch", "right_kick")


def load_sequences(source: Path, kind: str):
    sequences = []
    for skill in SKILLS:
        with np.load(source / f"{skill}.npz") as data:
            poses = data["qpos"].copy()
            if kind == "policy" and ("failed" not in data or bool(data["failed"])):
                raise ValueError(
                    f"{skill}: a complete successful evaluation rollout is required"
                )
            if poses.ndim != 2 or poses.shape[1] != 36 or not np.isfinite(poses).all():
                raise ValueError(f"{skill}: expected finite single-G1 qpos")
            if int(data["fps"][0]) != 50:
                raise ValueError("Skills must be sampled at 50 Hz")
        both = np.tile(poses, (1, 2))
        for robot, (x, y, yaw) in enumerate(SPAWNS):
            offset = robot * 36
            rot = Rotation.from_euler("z", yaw)
            both[:, offset : offset + 3] = rot.apply(poses[:, :3]) + [x, y, 0]
            both[:, offset + 3 : offset + 7] = (
                rot * Rotation.from_quat(poses[:, [4, 5, 6, 3]])
            ).as_quat()[:, [3, 0, 1, 2]]
        sequences.append(both)
    return sequences


def render(arena, sequences, output, kind, width=1280, height=720):
    output.parent.mkdir(parents=True, exist_ok=True)
    camera = mujoco.MjvCamera()
    for key, value in CAMERA.items():
        if key == "lookat":
            camera.lookat[:] = value
        else:
            setattr(camera, key, value)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    font = ImageFont.load_default(size=20)
    label = "Kinematic references" if kind == "reference" else "Physics policy rollouts"
    detail = (
        "Robo Jab punches / SONIC kick"
        if kind == "reference"
        else "Single-robot evaluations shown together / no opponent interaction"
    )
    sheets, preview = [], []
    with (
        mujoco.Renderer(arena.model, height, width) as renderer,
        imageio.get_writer(
            str(output),
            fps=30,
            codec="libx264",
            quality=8,
            macro_block_size=2,
            ffmpeg_params=["-movflags", "+faststart"],
        ) as writer,
    ):
        for name, sequence in zip(SKILLS, sequences, strict=True):
            for frame in range(round(len(sequence) / 50 * 30)):
                t = frame / 30
                arena.set_pose(sample(sequence, t, 50))
                renderer.update_scene(arena.data, camera, scene_option=option)
                image = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(image)
                draw.text(
                    (36, 26),
                    f"G1 skills  /  {name.replace('_', ' ')}",
                    font=font,
                    fill="#e4edf2",
                )
                draw.text((36, height - 64), label, font=font, fill="#c8d7e4")
                draw.text((36, height - 36), detail, font=font, fill="#a5b7c9")
                writer.append_data(np.asarray(image))
                if frame in (45, 80, 110):
                    sheets.append(image.resize((640, 360)))
                if 1.5 <= t < 3.5 and frame % 3 == 0:
                    preview.append(image.resize((640, 360)).quantize(colors=96))
            print(f"Rendered {name}", flush=True)
    sheet = Image.new("RGB", (1920, 1080))
    for i, image in enumerate(sheets):
        sheet.paste(image, ((i % 3) * 640, (i // 3) * 360))
    sheet.save(output.with_suffix(".jpg"))
    preview[0].save(
        output.with_suffix(".gif"),
        save_all=True,
        append_images=preview[1:],
        duration=100,
        loop=0,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "assets/skill_rollouts")
    parser.add_argument("--kind", choices=("reference", "policy"), default="policy")
    parser.add_argument("--render", type=Path)
    parser.add_argument("--web", type=Path)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--port", type=int, default=18766)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not (args.render or args.web):
        args.web = HERE / "output/skills-web"
    sequences = load_sequences(args.source, args.kind)
    arena = Arena()
    if args.render:
        render(arena, sequences, args.render, args.kind)
    if args.web:
        label = (
            "Kinematic references"
            if args.kind == "reference"
            else "Recorded policy rollouts"
        )
        build_web(
            arena,
            np.vstack(sequences),
            args.web,
            DEFAULT_LOGO,
            fps=50,
            label=label,
            description="Left punch, right punch, right kick",
        )
        # The browser plays recorded states. It does not perform policy inference.
        import json

        path = args.web / "motion.json"
        data = json.loads(path.read_text())
        data["segments"] = [
            {
                "name": name.replace("_", " "),
                "start": sum(len(q) for q in sequences[:i]) / 50,
            }
            for i, name in enumerate(SKILLS)
        ]
        data["detail"] = (
            "Reference playback"
            if args.kind == "reference"
            else "Recorded single-robot physics evaluations; no opponent interaction"
        )
        path.write_text(json.dumps(data, separators=(",", ":")))
        if not args.render and not args.build_only:
            command = [
                sys.executable,
                str(HERE / "demo.py"),
                "--serve-existing",
                "--output",
                str(args.web),
                "--port",
                str(args.port),
            ]
            if args.no_browser:
                command.append("--no-browser")
            subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
