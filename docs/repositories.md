# Unitree G1 repositories

[Main guide](README.md)

This repository targets Unitree G1. League documentation, figures and examples live in `docs/`. Under `external/`, SuperMimic is included as ordinary tracked source files. SONIC, both Unitree training repositories, Unitree SDK2 and mjswan are pinned Git submodules.

## Included source

| Directory | Role | Storage | Upstream revision |
| --- | --- | --- | --- |
| [GR00T-WholeBodyControl](../external/GR00T-WholeBodyControl) | NVIDIA SONIC whole body control baseline and deployment | Submodule | [1e1ec4f](https://github.com/NVlabs/GR00T-WholeBodyControl/commit/1e1ec4f5f27e6c3e03048f693bd7c60cce04afda) |
| [supermimic_vibed](../external/supermimic_vibed) | Independent SuperMimic reproduction for training motion trackers | Tracked source | [0525a23](https://github.com/zita-ch/supermimic_vibed/commit/0525a23a2dcfa61f8543f98b84c075fe66d9d286) |
| [unitree_rl_mjlab](../external/unitree_rl_mjlab) | Unitree G1 locomotion, motion tracking and deployment with mjlab | Submodule | [1425b15](https://github.com/unitreerobotics/unitree_rl_mjlab/commit/1425b15f73bd4095f0df53709d7c389c3eb9e790) |
| [unitree_rl_lab](../external/unitree_rl_lab) | Unitree G1 training with Isaac Lab and controller deployment | Submodule | [4960b84](https://github.com/unitreerobotics/unitree_rl_lab/commit/4960b84732b0c2ec593dccbfe963fda1bcd7b1e3) |
| [unitree_sdk2](../external/unitree_sdk2) | C++ robot communication SDK used by deployment controllers | Submodule | [8e1b927](https://github.com/unitreerobotics/unitree_sdk2/commit/8e1b927586712edd6a4c29d50dd52dff1e163439) |
| [mjswan](../external/mjswan) | Interactive MuJoCo simulation and ONNX policy visualization in the browser | Submodule | [ad5dd61](https://github.com/ttktjmt/mjswan/commit/ad5dd61a13459849ca78d5be4f8c6337b895bab5) |

SONIC supplies the existing controller path. SuperMimic supplies an independent implementation to study and train a new tracker. The two Unitree training repositories provide alternative simulator workflows, while SDK2 connects deployment software to the robot. Use each training repository's installation instructions in a separate environment; their checkpoints and task commands are not interchangeable.

## Unitree training and deployment

`unitree_rl_mjlab` trains with mjlab and MuJoCo Warp. `unitree_rl_lab` trains with Isaac Lab on Isaac Sim; its pinned README targets Isaac Lab 2.3.0 and Isaac Sim 5.1.0. The latter also describes validation in MuJoCo before physical deployment, which is a separate stage from Isaac Lab training. Follow its [installation and robot asset instructions](https://github.com/unitreerobotics/unitree_rl_lab/blob/4960b84732b0c2ec593dccbfe963fda1bcd7b1e3/README.md#installation), then run in the Isaac Lab environment:

```bash
cd external/unitree_rl_lab
python scripts/rsl_rl/train.py --headless --task Unitree-G1-29dof-Velocity
```

`unitree_sdk2` provides the C++ communication library and robot examples. Unitree RL Lab's deployment controllers link against it. Follow the [SDK build instructions](https://github.com/unitreerobotics/unitree_sdk2/blob/8e1b927586712edd6a4c29d50dd52dff1e163439/README.md) and the selected controller's setup instructions; the policy runtime still defines observations, joint mapping and control timing.

## Browser visualization

[mjswan](../external/mjswan) combines MuJoCo WebAssembly, ONNX Runtime and Three.js to run interactive simulations in the browser. Scenes can be shared as static websites, including through GitHub Pages. Use it to inspect robot motion, apply disturbances interactively and share exported policy demonstrations. See the [upstream demo](https://ttktjmt.github.io/mjswan/) and [setup instructions](https://github.com/ttktjmt/mjswan/blob/ad5dd61a13459849ca78d5be4f8c6337b895bab5/README.md#quick-start).

For a G1 policy, bring the MuJoCo model, exported ONNX policy and matching observation and action logic into the viewer. The upstream [mjlab porting guide](https://mjswan.readthedocs.io/en/latest/skills/mjlab-to-mjswan/) is a starting point. This repository includes mjswan's source reference; a league scene and policy integration still need to be built and checked against the original simulator.

## SuperMimic source

The complete tracked contents of upstream revision `0525a23a2dcfa61f8543f98b84c075fe66d9d286` were imported into `external/supermimic_vibed`, including its [original MIT license](../external/supermimic_vibed/LICENSE), scripts and demonstration assets. There is no nested Git repository. Changes to this code are committed directly in `robot_fights_rl_lab`.

## Get the sources

SuperMimic is included in an ordinary clone. Recursive submodule initialization fetches SONIC, both Unitree training repositories, SDK2 and mjswan:

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

This repository adds a [Unitree mjlab AWS task](examples/sky_unitree_aws.yaml), following the setup/run pattern in [upstream mjlab's cloud scripts](https://github.com/mujocolab/mjlab/tree/main/scripts/cloud). `unitree_rl_mjlab` does not bundle those templates at the pinned revision. This launcher uses the mjlab workflow; Isaac Lab training needs its own environment and launch configuration.

The task fetches the same `unitree_rl_mjlab` revision as our submodule, creates a separate Python 3.11 environment, installs its dependencies and runs `scripts/train.py`. Defaults are a small G1 locomotion run on one AWS L4 with TensorBoard logging. Task, environment count, iterations, seed and motion file are configurable.

After configuring SkyPilot and AWS, launch from the top-level repository directory:

```bash
sky launch -c robot-fights-unitree docs/examples/sky_unitree_aws.yaml
```

See [cloud training](training.md#aws-through-skypilot) for credentials, motion tracking, checkpoint retrieval and shutdown. `unitree_rl_mjlab` pins `mjlab==1.2.0`; the separate [stock mjlab example](examples/sky_aws.yaml) uses v1.6.0. The Unitree task fetches upstream source on the remote machine; local submodule edits are not uploaded. Cloning this repository launches no cloud resources.
