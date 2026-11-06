# Unitree G1 repositories

[Main guide](README.md)

This repository targets Unitree G1. League documentation, figures and examples live in `docs/`. All source projects under `external/` are ordinary tracked folders. Edit and commit them directly in `robot_fights_rl_lab`; there are no submodules or nested Git repositories.

## Included source

| Directory | Role | Upstream revision | Import tag |
| --- | --- | --- | --- |
| [GR00T-WholeBodyControl](../external/GR00T-WholeBodyControl) | NVIDIA SONIC whole body control baseline and deployment | [1e1ec4f](https://github.com/NVlabs/GR00T-WholeBodyControl/commit/1e1ec4f5f27e6c3e03048f693bd7c60cce04afda) | `upstream/GR00T-WholeBodyControl/1e1ec4f` |
| [supermimic_vibed](../external/supermimic_vibed) | Independent SuperMimic reproduction for training motion trackers | [0525a23](https://github.com/zita-ch/supermimic_vibed/commit/0525a23a2dcfa61f8543f98b84c075fe66d9d286) | `upstream/supermimic_vibed/0525a23` |
| [unitree_rl_mjlab](../external/unitree_rl_mjlab) | Unitree G1 locomotion, motion tracking and deployment with mjlab | [1425b15](https://github.com/unitreerobotics/unitree_rl_mjlab/commit/1425b15f73bd4095f0df53709d7c389c3eb9e790) | `upstream/unitree_rl_mjlab/1425b15` |
| [unitree_rl_lab](../external/unitree_rl_lab) | Unitree G1 training with Isaac Lab and controller deployment | [4960b84](https://github.com/unitreerobotics/unitree_rl_lab/commit/4960b84732b0c2ec593dccbfe963fda1bcd7b1e3) | `upstream/unitree_rl_lab/4960b84` |
| [unitree_sdk2](../external/unitree_sdk2) | C++ robot communication SDK used by deployment controllers | [8e1b927](https://github.com/unitreerobotics/unitree_sdk2/commit/8e1b927586712edd6a4c29d50dd52dff1e163439) | `upstream/unitree_sdk2/8e1b927` |
| [mjswan](../external/mjswan) | Interactive MuJoCo simulation and ONNX policy visualization in the browser | [ad5dd61](https://github.com/ttktjmt/mjswan/commit/ad5dd61a13459849ca78d5be4f8c6337b895bab5) | `upstream/mjswan/ad5dd61` |
| [UMR](../external/UMR) | Human to humanoid motion retargeting with learned point cloud correspondence | [d1cdaed](https://github.com/hanyang9/UMR/commit/d1cdaedaf67a827198da71c5fa831f48b2e51f91) | `upstream/UMR/d1cdaed` |
| [ProtoMotions](../external/ProtoMotions) | Motion imitation and generative humanoid policy training, including G1 workflows | [b43fc6f](https://github.com/NVlabs/ProtoMotions/commit/b43fc6fcfebb4996eb651dda8ea8ce981c5433a6) | `upstream/ProtoMotions/b43fc6f` |

Each annotated tag points to the import baseline in this repository. Its message records the original repository and full upstream commit ID. Source files, licenses and notices are preserved at that baseline. Later edits belong to this repository's normal history.

SONIC supplies the existing controller path. SuperMimic supplies an independent implementation to study and train a new tracker. The two Unitree training repositories provide alternative simulator workflows, while SDK2 connects deployment software to the robot. Keep their installation environments separate: Unitree mjlab pins mjlab 1.2.0, while mjswan's mjlab extra pins 1.6.0, and Isaac Lab has its own runtime. The shared Git repository does not make their checkpoints, dependencies or task commands interchangeable.

## Unitree training and deployment

`unitree_rl_mjlab` trains with mjlab and MuJoCo Warp. `unitree_rl_lab` trains with Isaac Lab on Isaac Sim; its pinned README targets Isaac Lab 2.3.0 and Isaac Sim 5.1.0. The latter also describes validation in MuJoCo before physical deployment, which is a separate stage from Isaac Lab training. Follow its [installation and robot asset instructions](https://github.com/unitreerobotics/unitree_rl_lab/blob/4960b84732b0c2ec593dccbfe963fda1bcd7b1e3/README.md#installation), then run in the Isaac Lab environment:

```bash
cd external/unitree_rl_lab
python scripts/rsl_rl/train.py --headless --task Unitree-G1-29dof-Velocity
```

`unitree_sdk2` provides the C++ communication library and robot examples. Unitree RL Lab's deployment controllers link against it. Follow the [SDK build instructions](https://github.com/unitreerobotics/unitree_sdk2/blob/8e1b927586712edd6a4c29d50dd52dff1e163439/README.md) and the selected controller's setup instructions; the policy runtime still defines observations, joint mapping and control timing.

## Browser visualization

[mjswan](../external/mjswan) combines MuJoCo WebAssembly, ONNX Runtime and Three.js to run interactive simulations in the browser. Scenes can be shared as static websites, including through GitHub Pages. Use it to inspect robot motion, apply disturbances interactively and share exported policy demonstrations. See the [upstream demo](https://ttktjmt.github.io/mjswan/) and [setup instructions](https://github.com/ttktjmt/mjswan/blob/ad5dd61a13459849ca78d5be4f8c6337b895bab5/README.md#quick-start).

For a G1 policy, bring the MuJoCo model, exported ONNX policy and matching observation and action logic into the viewer. The upstream [mjlab porting guide](https://mjswan.readthedocs.io/en/latest/skills/mjlab-to-mjswan/) is a starting point. The mjswan source is editable here; a league scene and policy integration still need to be built and checked against the original simulator.

## Retargeting and motion learning

[UMR](../external/UMR) maps human motion onto a humanoid using learned surface correspondence, then optimizes the robot motion with contact and kinematic constraints. Its examples include Unitree G1. Follow its [installation instructions](../external/UMR/README.md#installation), including the separately obtained SMPL-X body model, then run from its directory:

```bash
cd external/UMR
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/humanoid_retarget_unitree_g1_example.json
```

[ProtoMotions](../external/ProtoMotions) supplies motion imitation and generative policy learning, G1 workflows and multiple simulator backends. Start with its [installation guide](https://nvlabs.github.io/ProtoMotions/getting_started/installation.html) and [G1 deployment workflow](https://nvlabs.github.io/ProtoMotions/tutorials/workflows/g1_deployment.html). Keep its environment separate from the Unitree mjlab environment.

The intended pipeline is human motion, retargeting, validated robot references, tracking training, then contact training. Check joint and body ordering, coordinate conventions, sampling rate and velocities when moving UMR output into a trainer. The [motion preparation guide](motions.md#recover-motion-from-video) compares reconstruction options, including FlowHMR, GVHMR and OnlineHMR. These are linked for review and have not been imported.

## SuperMimic source

The complete tracked contents of upstream revision `0525a23a2dcfa61f8543f98b84c075fe66d9d286` were imported into `external/supermimic_vibed`, including its [original MIT license](../external/supermimic_vibed/LICENSE), scripts and demonstration assets. There is no nested Git repository. Changes to this code are committed directly in `robot_fights_rl_lab`.

## Get the sources

Install Git LFS, then clone normally. Git LFS retrieves SONIC and ProtoMotions model and asset files, roughly 5.8 GB of unique content at the imported revisions:

```bash
git lfs install
git clone https://github.com/katari16/robot_fights_rl_lab.git
cd robot_fights_rl_lab
git lfs pull
```

For an older checkout with initialized submodules, preserve local edits and run `git submodule deinit --all` **before pulling this migration**. Without `--force`, Git refuses to discard local changes. Then use the normal update commands:

```bash
git pull --ff-only
git fetch --tags
git lfs pull
```

Follow the upstream instructions for additional model weights, datasets and environment installation. Match the controller to the actual G1 actuator configuration before deployment.

## Edit the sources

Work in any `external/` folder and commit from the repository root. For example:

```bash
git diff upstream/unitree_rl_mjlab/1425b15 -- external/unitree_rl_mjlab
git add external/unitree_rl_mjlab
git commit -m "Update G1 training configuration"
```

Keep import tags unchanged. When incorporating a newer upstream version, review the diff against its previous baseline and add a new import tag recording the new upstream commit.

## Cloud training

This repository adds a [Unitree mjlab AWS task](examples/sky_unitree_aws.yaml), following the setup/run pattern in [upstream mjlab's cloud scripts](https://github.com/mujocolab/mjlab/tree/main/scripts/cloud). `unitree_rl_mjlab` does not bundle those templates at the pinned revision. This launcher uses the mjlab workflow; Isaac Lab training needs its own environment and launch configuration.

The task uploads your local `external/unitree_rl_mjlab` source, creates a separate Python 3.11 environment, installs its dependencies and runs `scripts/train.py`. Defaults are a small G1 locomotion run on one AWS L4 with TensorBoard logging. Task, environment count, iterations, seed and motion file are configurable.

After configuring SkyPilot and AWS, launch from the top-level repository directory:

```bash
sky launch -c robot-fights-unitree docs/examples/sky_unitree_aws.yaml
```

See [cloud training](training.md#aws-through-skypilot) for credentials, motion tracking, checkpoint retrieval and shutdown. `unitree_rl_mjlab` pins `mjlab==1.2.0`; the separate [stock mjlab example](examples/sky_aws.yaml) uses v1.6.0. SkyPilot synchronizes the Unitree source, including local edits, on launch and execution. Cloning this repository launches no cloud resources.
