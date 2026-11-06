# Robot fights RL lab

[![Two Unitree G1s rehearsing punches in the RSL arena](docs/assets/g1-arena.gif)](docs/assets/g1-arena.mp4)

[Watch the arena video](docs/assets/g1-arena.mp4) · [Run the demo](docs/simulation.md) · [Technical guide](docs/README.md)

A development workspace for a humanoid fighting league using Unitree G1. The preview shows kinematic playback of retargeted Robo Jab motion in a rectangular RSL arena. A learned controller and contact training are the next stages.

```bash
uv sync --project simulation --locked
uv run --project simulation python simulation/demo.py
```

The Python script opens an interactive mjswan viewer with playback, nominal pose and camera controls. [Setup, rendering and validation](docs/simulation.md).

League documentation is in [`docs/`](docs/README.md). Editable source projects are in [`external/`](docs/repositories.md). [Media sources](docs/assets/README.md).
