# Adaptation and training

[Main guide](README.md)

This guide follows the adaptation path: begin with a working SONIC controller, then change its behavior through a contact curriculum and measured fine tuning. For a controller whose weights are learned from scratch, see [scratch training and SuperMimic](from_scratch.md). The two paths should eventually meet at the same evaluation suite.

## What is available

| Component | Starting point | Work still required |
| --- | --- | --- |
| Nominal controller | [SONIC training and checkpoints](https://github.com/NVlabs/GR00T-WholeBodyControl) | Reproduce the selected G1 baseline |
| Transfer method | [TRACE paper](https://arxiv.org/abs/2610.17999) and [H2 deployment](https://github.com/QinnyuLan/SONIC_unitree_h2) | Adapt the method to G1 contact tasks |
| Decoder LoRA example | [SONIC X2 project](https://sonic-agibot-x2.github.io/sonic-transfer/) and [runtime](https://github.com/meetsitaram/sonic-x2) | Verify training artifacts separately from the quick play bundle |
| GPU environment | [mjlab v1.6.0](https://github.com/mujocolab/mjlab/tree/v1.6.0) | Integrate SONIC and the contact curriculum |
| Alternative learning method | [SuperMimic project](https://supermimic.github.io/) | Reproduce the learner and validate any contact extension; see [scratch training](from_scratch.md) |

The H2 repository is primarily a deployment release. TRACE describes kinematic and dynamic alignment, encoder distillation and decoder adaptation with PPO. It reports about eight hours on one RTX PRO 6000 for G1 to H2 adaptation. This excludes source pretraining and is not a budget estimate for fighting.

The X2 draft describes a joint codec with LoRA on the dynamics decoder while the core remains frozen. Its results concern embodiment transfer and tracking. Treat the release as a research example, with its stated evaluation limitations.

[![TRACE adaptation workflow](https://bfm-trace.github.io/assets/method-overview.webp)](https://bfm-trace.github.io/)

*TRACE method overview, Lan et al. Interface alignment precedes adaptation. [Project](https://bfm-trace.github.io/) and [paper](https://arxiv.org/abs/2610.17999).*

## Proposed G1 adaptation

For a linear layer, LoRA represents the adapted weights as `W = W_base + (alpha / rank) B A`. Start with zero effective update so the initial adapter reproduces the baseline. Freeze the intended base parameters, verify the trainable parameter list, and train the critic appropriate to the new environment.

Keep the command encoder fixed in the first experiment. Add decoder adapters and compare against both the untouched baseline and a full fine tuning control at a matched sample budget. LoRA does not remove forward inference through the base network or the cost of physics. Record GPU hours to reach a predefined validation target.

Use a staged curriculum:

1. Reproduce nominal motions with the configured robot, padding and actuator model.
2. Add bounded external disturbances, sensor noise, delay and parameter variation.
3. Execute one skill against a compliant target, varying its position and motion.
4. Include misses, blocked limbs and interruption into guard or stance.
5. Train recovery from representative fallen states with suitable episode duration.
6. Evaluate two interacting robots before considering self play.

Balance motion accuracy with stability, legal target contact, recovery and actuator constraints. Do not reward raw impact magnitude as a substitute for task success. Preserve nominal motions in the sampling mixture and reserve unseen motions, target configurations and disturbances for evaluation.

GigaBrain motivates interaction data and feasible command handling; it is not evidence that adding LoRA to SONIC reproduces its architecture or results. [Research reference](https://arxiv.org/abs/2608.18234)

## Follow one skill through an experiment

Use a jab as the first complete contact task. Its reference should include the weight shift, extension and return to guard. In the initial scene, place a stationary padded target at a reachable position and test whether the nominal controller can finish the sequence. Save this result before changing the policy.

Next, train the adapter with a mixture of nominal motions and target interactions. Define success over the full sequence: the intended surface makes allowed contact, the robot remains within the tested actuator envelope, and it reaches an acceptable exit state. A low hand-position error alone misses the reason we are adding contact training.

Widen one part of the scene at a time. Move the target slightly, change its compliance, then include motion and external disturbances. Maintain a separate evaluation set with target settings never used for updates. Include misses and blocked attempts even when they lower the average score; those cases determine whether the pilot can trust the skill during a match.

Compare the original checkpoint, adapter and full fine tuning control on the same trials. Record the number of attempts, completed skills, falls, successful recoveries and limit violations. Retest walking and turning after each change. Save the result with the robot model and adapter version so another developer can repeat the comparison.

This is our proposed league experiment. The linked transfer papers provide adaptation methods, while this contact curriculum still needs implementation and measurement on the chosen G1.

## Porting to mjlab

The official [SONIC training guide](https://nvlabs.github.io/GR00T-WholeBodyControl/user_guide/training.html) uses Isaac Lab and PPO with auxiliary losses. Keep this as the reproduction path until the mjlab port is verified.

The port needs matching joint order, coordinate frames, observation history, reference lookahead, action processing, motor model and control timing. Add SONIC's policy and adapter parameter groups to the learner explicitly; the standard mjlab MLP checkpoint is not interchangeable with SONIC.

Compare a saved batch through both input pipelines and exported policies, then compare short dynamic rollouts. Contact behavior requires separate calibration of collision shapes, friction, compliance, timestep and solver settings. See [mjlab's design](https://mujocolab.github.io/mjlab/v1.6.0/source/motivation.html) and [MuJoCo contact modeling](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters).

For an independent tracking exercise, mjlab supplies `Mjlab-Tracking-Flat-Unitree-G1`. Use **mjlab's own CSV to NPZ converter**: body ordering differs from Isaac Lab, so an apparently compatible NPZ can attach targets to the wrong body. The v1.6.0 workflow uses a W&B motion registry. [Motion imitation instructions](https://mujocolab.github.io/mjlab/v1.6.0/source/training/motion_imitation.html)

```bash
uv run train Mjlab-Tracking-Flat-Unitree-G1 \
  --registry-name YOUR_ENTITY/motions/YOUR_MOTION \
  --env.scene.num-envs 1024
```

This trains the stock tracking task. It does not fine tune SONIC or train a contact skill.

## AWS through SkyPilot

The supplied [Unitree AWS task](examples/sky_unitree_aws.yaml) adds SkyPilot support around `unitree_rl_mjlab`, using the setup/run pattern from [upstream mjlab](https://github.com/mujocolab/mjlab/tree/main/scripts/cloud). It fetches Unitree commit `1425b15f73bd4095f0df53709d7c389c3eb9e790`, matching our submodule, and installs its dependencies in a separate Python 3.11 environment. Unitree pins `mjlab==1.2.0` and `mujoco-warp==3.5.0`; installed dependency versions are saved with the outputs. Local submodule edits are not uploaded by this task.

The default is `Unitree-G1-Flat`, 512 environments and 100 iterations on one AWS L4. This is a small locomotion test with TensorBoard logging, requiring neither a motion dataset nor a W&B credential. It exercises Unitree's training workflow; the proposed contact curriculum and SONIC adaptation still need implementation. The template and command construction were checked locally; a GPU training run remains to be validated.

Install `uv`, SkyPilot and AWS CLI v2 locally. Configure your own AWS account and an enabled GPU region with sufficient quota and SkyPilot permissions. SSO users can use a named profile:

```bash
uv tool install "skypilot[aws]"
aws configure sso --profile robot-fights
export AWS_PROFILE=robot-fights
aws sso login --profile robot-fights
sky check aws
sky launch -c robot-fights-unitree docs/examples/sky_unitree_aws.yaml
sky logs robot-fights-unitree
```

Run the launch command from this repository's root. L4 is an initial resource request; choose a supported GPU and region after checking availability. Launching creates billable resources. [AWS setup](https://docs.skypilot.ai/en/latest/cloud-setup/cloud-permissions/aws.html)

After the small run succeeds, start a longer run on the same cluster:

```bash
sky exec robot-fights-unitree docs/examples/sky_unitree_aws.yaml \
  --env NUM_ENVS=4096 --env MAX_ITERATIONS=10001 --env SEED=42
```

For multiple GPUs, change `resources.accelerators` before launching a cluster. The trainer uses `--gpu-ids all`; adjust environment count to fit each GPU. These settings control experiment size and are not a guarantee of convergence.

For motion tracking, select the Unitree task and pass a compatible NPZ. This example uses the G1 reference already present in the pinned upstream repository:

```bash
sky exec robot-fights-unitree docs/examples/sky_unitree_aws.yaml \
  --env TASK=Unitree-G1-Tracking-No-State-Estimation \
  --env MOTION_FILE=deploy/robots/g1/config/policy/mimic/dance1_subject2/params/dance1_subject2.npz \
  --env NUM_ENVS=1024 --env MAX_ITERATIONS=1000
```

For your own motion, use Unitree's `scripts/csv_to_npz.py` and matching robot configuration, then upload the result to the existing cluster:

```bash
scp /path/to/motion.npz robot-fights-unitree:~/robot_fights_unitree_mjlab/motion.npz
```

Use `--env MOTION_FILE=motion.npz` in the tracking command. Paths are resolved on the remote machine, relative to its Unitree checkout. The launcher rejects tracking jobs with a missing motion file. See the pinned [Unitree motion workflow](https://github.com/unitreerobotics/unitree_rl_mjlab/blob/1425b15f73bd4095f0df53709d7c389c3eb9e790/README.md#2-motion-imitation-training).

The instance stays running so checkpoints can be inspected and retrieved. Copy outputs before terminating it:

```bash
mkdir -p runs
rsync -av robot-fights-unitree:~/robot_fights_unitree_mjlab/logs/ runs/unitree/
sky logs robot-fights-unitree --sync-down
sky down robot-fights-unitree
```

The SSH alias is created by SkyPilot. Training outputs are under `logs/rsl_rl/g1_velocity/` or `logs/rsl_rl/g1_tracking/`. `--sync-down` retrieves job logs, not arbitrary model files. Confirm the model files and resolved configs arrived before running `sky down`. [CLI reference](https://docs.skypilot.ai/en/latest/reference/cli.html)

For recurring training, write checkpoints to durable storage, test resume, then enable automatic teardown or managed jobs. Persist model, optimizer, normalizer, curriculum and random state where exact resume is required. Spot recovery depends on that application support. mjlab's [upstream cloud templates](https://mujocolab.github.io/mjlab/v1.6.0/source/training/cloud.html) are a useful next step.

The separate [stock mjlab AWS example](examples/sky_aws.yaml) remains available. It uses mjlab v1.6.0 at `0fb8a681136be94ffc636a3dd423cabb97d91f10` and the upstream G1 velocity task. Launch it as `robot-fights-dev`; its outputs are under `~/robot_fights_mjlab/logs/`. Keep its environment and checkpoints separate from the Unitree workflow.
