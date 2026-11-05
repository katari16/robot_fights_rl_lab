# Training a motion tracker from scratch

[Main guide](README.md) · [LoRA and cloud setup](training.md)

Training from scratch means learning the controller's weights for our chosen robot and tasks. We still use a robot model, reference motions and a training environment. The advantage is control over what the policy observes and what it learns to do. The cost is having to establish the entire baseline ourselves.

For this league, we would begin with a small collection of useful movements and a clear evaluation procedure. A successful first run should explain why the robot can execute those motions, what causes failure and how much compute was required. Scaling the library comes after that result is reproducible.

## Where SuperMimic fits

[SuperMimic](https://supermimic.github.io/) alternates simulator data collection, fitting a differentiable dynamics model, and policy improvement through predicted trajectories. A critic estimates the return beyond those short trajectories. The world model stays fixed during an individual policy update, but continues learning across iterations. The [Figure 2 diagram in the main guide](README.md#choose-between-adapting-and-training-from-scratch) illustrates the loop. [Paper, Sections 3.1 to 3.3](https://arxiv.org/pdf/2610.28480v1#page=4)

This is an alternative learning method to investigate alongside ordinary simulator-based PPO. It does not require starting from SONIC weights. It also does not turn a motion dataset into examples of physical interaction by itself: the paper filters out motions requiring unavailable objects or terrain. Adding opponents would be a new experiment. [Paper, Appendix E](https://arxiv.org/pdf/2610.28480v1#page=15)

As checked on 23 October 2026, the project page links a paper and a browser demo but no author-maintained training repository. The method is therefore a research direction to reproduce, not an installed training command in this repository.

An [independent implementation by Chong Zhang](https://github.com/zita-ch/supermimic_vibed) provides code for a small LAFAN1 experiment using Isaac Lab and MuJoCo Warp. Its author explicitly describes it as a fast, unreviewed reproduction, and lists deviations including disabled self collisions. It can help a developer inspect the implementation work, but it needs review before use as a contact-training baseline. It is not an official SuperMimic release or an mjlab integration.

## Read the compute result in context

| Author-reported result | Conditions to retain when citing it |
| --- | --- |
| One H100, three hours | Exceeds the released SONIC checkpoint's normalized return in the reported benchmark |
| Two H100s, 9.8 hours | Zero failures across 129,514 evaluated training motions; approximately 19.6 GPU hours |
| Timing scope | Includes simulation collection, model fitting and policy updates; excludes checkpoint evaluation |

The benchmark evaluates motion coverage under deterministic simulation conditions. SONIC and SuperMimic used different GPUs and training datasets. These numbers motivate experiments; they are not measured costs for our robot configuration, contact curriculum or AWS worker. [Project results and accounting](https://supermimic.github.io/#compute)

## Establish a small simulator baseline

Our proposed first experiment would use a few independently inspectable clips: stance, a step, a turn and a simple arm movement. Prepare them with the correct joint order, coordinate conventions and timing. Render the reference without a learned controller first. If its feet penetrate the floor or its joints are reversed, training will obscure the problem rather than resolve it.

Then train a stock tracker in mjlab using the [existing motion-imitation workflow](https://mujocolab.github.io/mjlab/v1.6.0/source/training/motion_imitation.html). The command and data preparation notes are in [the training guide](training.md#porting-to-mjlab). This first PPO experiment checks the robot model, observations, reward and export path without also introducing a new learner.

Choose completion conditions before launching a long run. A clip should execute from its intended entry state, stay inside the tested actuator envelope and end in an acceptable pose. Evaluate starts at the beginning of the clip as well as any randomized training resets. Otherwise a policy may look successful because it can finish short fragments while failing the complete skill.

Keep complete recording sessions together when splitting data. Reserve unseen clips for motion generalization and unseen initial conditions for robustness. Report those results separately from coverage of the training library.

## Add a learned dynamics model as a separate experiment

The following is a proposed integration plan, not released SuperMimic code. Keep the same robot task and evaluation suite when changing the learner so that differences can be attributed to the training method.

| Component to implement | Evidence to collect |
| --- | --- |
| Simulator transition logging | Actions and next states use the same timing and normalization as the controller |
| Replay and sequence sampling | Samples never silently cross resets, clip boundaries or incompatible model versions |
| Dynamics prediction | Errors stay bounded over the policy's intended prediction horizon |
| Policy optimization | Better predicted behavior also improves execution in the physics simulator |
| Checkpoint and resume | The learner, replay handling and random state follow a documented restart policy |

Distinguish the reference library from transition data. A reference specifies desired motion. A transition records what happened after an action. Save enough information to reproduce the latter, including relevant randomized environment parameters. Keep training-only state out of the deployed actor's observation contract.

Do not judge the new learner only by its predicted reward. Periodically run the policy in the physical simulator and compare complete skill outcomes. If predicted performance improves while simulator performance deteriorates, investigate model error and the states the policy visits before scaling the experiment.

At this stage, we want a convincing comparison on a small task. Log time spent collecting data, fitting the model, updating the policy and evaluating checkpoints. Repeat with multiple seeds before deciding whether the more complex learner is useful for this project.

## Extend the experiment to contact

Introduce one compliant target after free-space execution works. Define its state, collision geometry and permitted contact surfaces explicitly. A learned model intended to predict the interaction will need an appropriate representation of the target and new transition data covering it. Robot-only training data cannot establish accuracy for an unseen collision partner.

Begin with reproducible target placement, then vary position, motion and compliance. Include the cases that change a skill's outcome: a miss, an unexpectedly early hit, an arm that cannot finish its path, and a push during recovery. Inspect prediction errors around those events separately from the easier portions of the trajectory.

Use the same contact suite for the scratch-trained policy and the adapted SONIC baseline. Compare completion, falls, return to guard and actuator-limit violations. Test the original stance and locomotion suite after each adaptation so improvements do not hide lost basic capabilities.

Only then introduce a second articulated robot. This changes both the contact geometry and the behavior of the other body, so keep the initial opponent simple and frozen. More diverse opponents and tactical learning become useful once the low level controller passes repeatable interaction tests.

## Package the result for another developer

A useful release contains the trained policy, exact robot model, observation and action specifications, motion sources, resolved training configuration and evaluation cases. Include a checkpoint that can resume training and an exported policy that passes the [deployment checks](deployment.md).

The current [SkyPilot example](examples/sky_aws.yaml) remains an infrastructure smoke test for stock mjlab. It does not run this proposed learner. A SuperMimic experiment needs its own pinned implementation and dependencies before being placed on an AWS worker. The deliverable for this document is the development path; the controller and its measured training budget remain work to do.
