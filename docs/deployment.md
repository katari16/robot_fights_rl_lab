# Deployment and evaluation

[Main guide](README.md)

## Preserve the policy contract

Pin the checkpoint, adapter, robot model, observation specification and executable together. Use the same preprocessing in simulation and on hardware. SONIC publishes separate model variants with matching configuration files; mixing an encoder from one variant with another decoder is not a supported substitution. [Model card](https://huggingface.co/nvidia/GEAR-SONIC)

| Check | What to compare |
| --- | --- |
| Joint mapping | Names, order, signs, offsets and actuator limits |
| IMU and frames | Quaternion ordering, body frame, gravity and angular velocity |
| Timing | Sensor timestamps, history, policy frequency and motor frequency |
| Reference | Heading alignment, phase, lookahead and velocity conventions |
| Actions | Normalization, scale, clipping, gains and previous action feedback |
| Available state | Every actor input must be measured or estimated at deployment |

Do not silently replace unavailable base velocity or global position with simulation truth. Define the estimator and its latency, or train a policy that does not need those inputs. mjlab includes a [tracking configuration without selected state estimation inputs](https://github.com/mujocolab/mjlab/blob/0fb8a681136be94ffc636a3dd423cabb97d91f10/src/mjlab/tasks/tracking/config/g1/env_cfgs.py); it is a distinct observation contract.

## Measure each conversion

Compare the nominal policy, adapted policy, distilled student and exported runtime using the same motion and disturbance suite. Report completion, falls, recovery, contact success, actuator saturation and tracking error. Include failure counts and denominators; tracking error on survivors can hide deterioration.

If a teacher uses privileged state, train the student from sensor realistic history and test it in closed loop. Low imitation loss on teacher trajectories does not establish stability in states the student visits. If no smaller policy is required, avoid introducing distillation into the first baseline.

Replay recorded input tensors through PyTorch, ONNX and the deployment runtime. Then compare dynamic execution. Include the adapter in export, either merged into compatible weights or implemented explicitly, and verify numerical agreement after merging or precision changes.

## Separate speed from action scale

For a typical position policy, `q_target = q_default + scale * action`. The scale controls amplitude. Reducing it also changes corrective balance commands. mjlab applies scale and offset to action values; it does not advance the motion clock more slowly. [Action implementation](https://github.com/mujocolab/mjlab/blob/0fb8a681136be94ffc636a3dd423cabb97d91f10/src/mjlab/envs/mdp/actions/actions.py)

To retime a reference, use `phase_next = phase + speed * dt`, keeping policy and motor rates fixed. A speed of `0.3` takes approximately `1 / 0.3 = 3.33` times as long. Consistently recompute reference velocities and accelerations, including future reference windows.

Slower timing is not automatically feasible for a jump or a dynamically balanced kick. Test a validated timing range in simulation first. Keep action scale and gains at their qualified values unless explicitly testing a new controller configuration. Use separate bounded command range and actuator limits for commissioning.

## Bring up hardware progressively

Verify the robot model and actuator behavior with the actual battery, padding and payload. Measure friction, delay and tracking response before widening randomization ranges. Test supported startup, stand, locomotion and simple skills before contact trials.

Keep inference and the watchdog on the robot. Define a state dependent response to expired commands, lost sensor updates and network interruption. A stable stance, damping or controlled descent may be appropriate in different states; freezing the last attack command is not a recovery strategy.

Use an independent operator stop and a controlled test area. Reset motion phase and policy history according to the checkpoint contract after a fall or mode switch. Log the reason for every transition. Move to two robot hardware trials only after each robot and the shared stop procedure have passed independently.
