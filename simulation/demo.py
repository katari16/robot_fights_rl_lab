#!/usr/bin/env python3
"""Run, inspect or render the RSL two-G1 arena."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import webbrowser

from arena import Arena, DEFAULT_LOGO, HERE
from motion import FPS, fetch_clip, load_clip, make_replay, sample
import mujoco
import numpy as np

CAMERA = dict(lookat=[0, 0, 0.55], distance=5.6, azimuth=105, elevation=-31)


def check(arena, replay):
    model = arena.model
    assert (model.nq, model.nv, model.nu) == (72, 70, 58)
    collidable = (model.geom_contype != 0) | (model.geom_conaffinity != 0)
    assert not np.any(model.geom_type[collidable] == mujoco.mjtGeom.mjGEOM_MESH)
    minimum_gap = float("inf")
    penetration = 0.0
    for pose in replay:
        arena.set_pose(pose)
        minimum_gap = min(minimum_gap, np.linalg.norm(pose[:2] - pose[36:38]))
        for contact in arena.data.contact:
            if contact.dist < penetration:
                penetration = float(contact.dist)
            names = [model.geom(g).name for g in contact.geom]
            assert not (
                any(n.startswith("g1_0/") for n in names)
                and any(n.startswith("g1_1/") for n in names)
            ), "Air-punch preview contains robot-to-robot contact"
    assert penetration > -1e-4, "Reference has penetrating contacts"
    arena.reset()
    for _ in range(1000):
        arena.step(np.zeros((2, 29)))
        assert np.isfinite(arena.data.qpos).all()
    arena.reset()
    result = dict(
        robots=2,
        joints=58,
        collision_geoms=int(collidable.sum()),
        mesh_colliders=0,
        replay_frames=len(replay),
        duration_seconds=len(replay) / FPS,
        minimum_root_separation_m=round(minimum_gap, 4),
        deepest_reference_contact_m=round(penetration, 4),
        physics_smoke_steps=1000,
    )
    print(json.dumps(result, indent=2))
    return result


def render(
    arena, replay, path, fps, duration, width, height, speed, poster=None, gif=None
):
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw, ImageFont

    path.parent.mkdir(parents=True, exist_ok=True)
    camera = mujoco.MjvCamera()
    for key, value in CAMERA.items():
        if key == "lookat":
            camera.lookat[:] = value
        else:
            setattr(camera, key, value)
    option = mujoco.MjvOption()
    option.geomgroup[3] = 0
    duration = duration or len(replay) / FPS / speed
    preview = []
    font = ImageFont.load_default(size=max(14, width // 75))
    with (
        mujoco.Renderer(arena.model, height, width) as renderer,
        imageio.get_writer(
            str(path),
            fps=fps,
            codec="libx264",
            quality=8,
            macro_block_size=2,
            pixelformat="yuv420p",
            ffmpeg_params=["-movflags", "+faststart"],
        ) as writer,
    ):
        for frame in range(round(duration * fps)):
            t = frame / fps * speed
            arena.set_pose(sample(replay, t))
            renderer.update_scene(arena.data, camera, scene_option=option)
            img = Image.fromarray(renderer.render())
            draw = ImageDraw.Draw(img)
            draw.text(
                (width * 0.035, height * 0.045),
                "RSL  /  G1 arena",
                font=font,
                fill=(226, 235, 242),
            )
            draw.text(
                (width * 0.035, height * 0.92),
                "Kinematic reference replay  ·  Motion: Robo Jab",
                font=font,
                fill=(167, 185, 202),
            )
            writer.append_data(np.asarray(img))
            if poster and frame == min(
                round(4.8 / speed * fps), round(duration * fps) - 1
            ):
                poster.parent.mkdir(parents=True, exist_ok=True)
                img.save(poster)
            if gif and 2.8 <= t < 7.8 and frame % max(1, round(fps / 10)) == 0:
                preview.append(img.resize((640, 360)).quantize(colors=96))
            if frame % fps == 0:
                print(f"Rendered {frame / fps:.0f}/{duration:.1f} seconds", flush=True)
    if gif and preview:
        gif.parent.mkdir(parents=True, exist_ok=True)
        preview[0].save(
            gif,
            save_all=True,
            append_images=preview[1:],
            duration=100,
            loop=0,
            optimize=True,
        )
    print(f"Video: {path.resolve()}")


def build_web(
    arena,
    replay,
    output,
    logo,
    speed=1,
    mode="replay",
    fps=FPS,
    label="Reference motion",
    description="Jab recording",
):
    from mjswan.build.frontend import ClientBuilder, TEMPLATE_DIR, install_spa
    from mjswan.build.mjz import to_zip_deflated

    output.mkdir(parents=True, exist_ok=True)
    builder = ClientBuilder(TEMPLATE_DIR)
    builder.create_env()
    build_env = os.environ.copy()
    build_env["PATH"] = (
        str(builder.nodeenv_dir / "bin") + os.pathsep + build_env.get("PATH", "")
    )
    npm = str(builder.nodeenv_dir / "bin/npm")
    # A lockfile installation makes a fresh checkout use the same browser dependencies.
    if not (TEMPLATE_DIR / "node_modules/.package-lock.json").exists():
        subprocess.run([npm, "ci"], cwd=TEMPLATE_DIR, env=build_env, check=True)
    subprocess.run([npm, "run", "build"], cwd=TEMPLATE_DIR, env=build_env, check=True)
    install_spa(output / "engine")
    to_zip_deflated(arena.spec, str(output / "scene.mjz"))
    nominal = sample(replay, 0, fps).tolist()
    (output / "motion.json").write_text(
        json.dumps(
            dict(
                fps=fps,
                label=label,
                description=description,
                nominal=nominal,
                initial_speed=speed,
                initial_mode=mode,
                quaternion_starts=[3, 39],
                qpos=np.round(replay, 7).tolist(),
            ),
            separators=(",", ":"),
        )
    )
    for path in (HERE / "web").iterdir():
        shutil.copy2(path, output / path.name)
    shutil.copy2(logo, output / "logo.svg")
    print(f"Browser demo: {output.resolve()}")


def native(arena, replay, speed, mode):
    import mujoco.viewer

    with mujoco.viewer.launch_passive(arena.model, arena.data) as viewer:
        for key, value in CAMERA.items():
            if key == "lookat":
                viewer.cam.lookat[:] = value
            else:
                setattr(viewer.cam, key, value)
        viewer.opt.geomgroup[3] = 0
        start = time.monotonic()
        while viewer.is_running():
            arena.set_pose(
                sample(replay, (time.monotonic() - start) * speed)
                if mode == "replay"
                else replay[0]
            )
            viewer.sync()
            time.sleep(1 / 60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--viewer", choices=["mjswan", "native"], default="mjswan")
    parser.add_argument("--mode", choices=["replay", "nominal"], default="replay")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--render", type=Path, metavar="MP4")
    parser.add_argument("--poster", type=Path)
    parser.add_argument("--gif", type=Path)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--logo", type=Path, default=DEFAULT_LOGO)
    parser.add_argument("--output", type=Path, default=HERE / "output/web")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--serve-existing", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if (
        not 0 < args.speed <= 2
        or args.fps <= 0
        or args.width <= 0
        or args.height <= 0
        or (args.duration is not None and args.duration <= 0)
    ):
        parser.error(
            "Speed must be in (0, 2]; frame rate, size and duration must be positive"
        )
    if not args.serve_existing:
        arena = Arena(args.logo)
        replay = (
            make_replay(arena, load_clip(fetch_clip()))
            if args.mode == "replay"
            else np.tile(arena.reset(), (60, 1))
        )
        if args.check:
            check(arena, replay)
            return
        if args.render:
            render(
                arena,
                replay,
                args.render,
                args.fps,
                args.duration,
                args.width,
                args.height,
                args.speed,
                args.poster,
                args.gif,
            )
            return
        if args.viewer == "native":
            native(arena, replay, args.speed, args.mode)
            return
        build_web(arena, replay, args.output, args.logo, args.speed, args.mode)
    if args.build_only:
        return
    if not (args.output / "index.html").is_file():
        parser.error("No built demo found; omit --serve-existing for the first run")
    url = f"http://localhost:{args.port}"
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port),
        partial(SimpleHTTPRequestHandler, directory=str(args.output.resolve())),
    )
    print(f"Open {url} (Ctrl+C to stop)", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
