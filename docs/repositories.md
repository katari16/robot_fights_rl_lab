# Unitree G1 repositories

[Main guide](README.md)

This repository targets Unitree G1. Documentation, figures and examples live in `docs/`. The three upstream source repositories are included as Git submodules in `external/`, pinned to specific commits rather than copied into this repository.

## Included source

| Directory | Role | Pinned revision |
| --- | --- | --- |
| [GR00T-WholeBodyControl](../external/GR00T-WholeBodyControl) | NVIDIA SONIC whole body control baseline and deployment | [1e1ec4f](https://github.com/NVlabs/GR00T-WholeBodyControl/commit/1e1ec4f5f27e6c3e03048f693bd7c60cce04afda) |
| [supermimic_vibed](../external/supermimic_vibed) | Independent SuperMimic reproduction for training motion trackers | [0525a23](https://github.com/zita-ch/supermimic_vibed/commit/0525a23a2dcfa61f8543f98b84c075fe66d9d286) |
| [unitree_rl_mjlab](../external/unitree_rl_mjlab) | Unitree G1 locomotion, motion tracking and deployment with mjlab | [1425b15](https://github.com/unitreerobotics/unitree_rl_mjlab/commit/1425b15f73bd4095f0df53709d7c389c3eb9e790) |

SONIC supplies the existing controller path. SuperMimic supplies an independent implementation to study and train a new tracker. Unitree mjlab supplies the robot-specific training and deployment workflow. Use each repository's installation instructions in a separate environment; their checkpoints and task commands are not interchangeable.

## Get the sources

```bash
git clone --recurse-submodules https://github.com/katari16/robot_fights_rl_lab.git
cd robot_fights_rl_lab
```

For an existing checkout, run from the repository root:

```bash
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
git submodule status
```

Submodules contain source code. Follow the upstream instructions for model weights, datasets and environment installation. Match the controller to the actual G1 actuator configuration before deployment.

## Cloud training

**Unitree's repository does not bundle SkyPilot task templates at the pinned revision.** They are in [upstream mjlab's cloud scripts](https://github.com/mujocolab/mjlab/tree/main/scripts/cloud), with a [cloud setup guide](https://mjlab.readthedocs.io/en/latest/source/training/cloud.html).

The upstream `train.yaml` currently targets Lambda Cloud. To run Unitree training on AWS, adapt the GPU/cloud resources, install Unitree's dependencies, and use its entry point, for example `python scripts/train.py Unitree-G1-Flat` from the Unitree repository directory.

Unitree's [setup.py](https://github.com/unitreerobotics/unitree_rl_mjlab/blob/1425b15f73bd4095f0df53709d7c389c3eb9e790/setup.py) pins `mjlab==1.2.0`. Our [AWS example](examples/sky_aws.yaml) uses upstream mjlab v1.6.0 and its stock G1 task; it is not a Unitree training launcher. Launch that example from the top-level repository directory with:

```bash
sky launch -c robot-fights-dev docs/examples/sky_aws.yaml
```

No training or cloud resources are launched by cloning this repository.
