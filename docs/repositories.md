# Unitree G1 repositories

[Main guide](README.md)

This repository targets Unitree G1. League documentation, figures and examples live in `docs/`. Under `external/`, SuperMimic is included as ordinary tracked source files. SONIC and Unitree mjlab remain pinned Git submodules.

## Included source

| Directory | Role | Storage | Upstream revision |
| --- | --- | --- | --- |
| [GR00T-WholeBodyControl](../external/GR00T-WholeBodyControl) | NVIDIA SONIC whole body control baseline and deployment | Submodule | [1e1ec4f](https://github.com/NVlabs/GR00T-WholeBodyControl/commit/1e1ec4f5f27e6c3e03048f693bd7c60cce04afda) |
| [supermimic_vibed](../external/supermimic_vibed) | Independent SuperMimic reproduction for training motion trackers | Tracked source | [0525a23](https://github.com/zita-ch/supermimic_vibed/commit/0525a23a2dcfa61f8543f98b84c075fe66d9d286) |
| [unitree_rl_mjlab](../external/unitree_rl_mjlab) | Unitree G1 locomotion, motion tracking and deployment with mjlab | Submodule | [1425b15](https://github.com/unitreerobotics/unitree_rl_mjlab/commit/1425b15f73bd4095f0df53709d7c389c3eb9e790) |

SONIC supplies the existing controller path. SuperMimic supplies an independent implementation to study and train a new tracker. Unitree mjlab supplies the robot-specific training and deployment workflow. Use each repository's installation instructions in a separate environment; their checkpoints and task commands are not interchangeable.

## SuperMimic source

The complete tracked contents of upstream revision `0525a23a2dcfa61f8543f98b84c075fe66d9d286` were imported into `external/supermimic_vibed`, including its [original MIT license](../external/supermimic_vibed/LICENSE), scripts and demonstration assets. There is no nested Git repository. Changes to this code are committed directly in `robot_fights_rl_lab`.

## Get the sources

SuperMimic is included in an ordinary clone. Recursive submodule initialization fetches SONIC and Unitree mjlab:

```bash
git clone --recurse-submodules https://github.com/katari16/robot_fights_rl_lab.git
cd robot_fights_rl_lab
```

If an older checkout initialized SuperMimic as a submodule, preserve any local edits and run `git submodule deinit external/supermimic_vibed` before pulling this migration. Without `--force`, Git refuses to discard local changes.

For an existing checkout, run from the repository root:

```bash
git pull --ff-only
git submodule sync --recursive
git submodule update --init --recursive
git submodule status
```

Follow the upstream instructions for model weights, datasets and environment installation. Match the controller to the actual G1 actuator configuration before deployment.

## Cloud training

This repository adds a [Unitree AWS task](examples/sky_unitree_aws.yaml), following the setup/run pattern in [upstream mjlab's cloud scripts](https://github.com/mujocolab/mjlab/tree/main/scripts/cloud). Unitree's repository does not bundle those templates at the pinned revision.

The task fetches the same Unitree revision as our submodule, creates a separate Python 3.11 environment, installs Unitree's dependencies and runs `scripts/train.py`. Defaults are a small G1 locomotion run on one AWS L4 with TensorBoard logging. Task, environment count, iterations, seed and motion file are configurable.

After configuring SkyPilot and AWS, launch from the top-level repository directory:

```bash
sky launch -c robot-fights-unitree docs/examples/sky_unitree_aws.yaml
```

See [cloud training](training.md#aws-through-skypilot) for credentials, motion tracking, checkpoint retrieval and shutdown. Unitree pins `mjlab==1.2.0`; the separate [stock mjlab example](examples/sky_aws.yaml) uses v1.6.0. The Unitree task fetches upstream source on the remote machine; local submodule edits are not uploaded. Cloning this repository launches no cloud resources.
