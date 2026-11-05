# League systems

[Main guide](README.md)

## Pilot interface

REK collaborator Reflex Arc describes human pilots choosing actions while learned control maintains robot balance. The team also describes shared pilot controls across physical events and a multiplayer simulator. This is a useful precedent for pilot training and consistent interfaces. It is not a public specification of REK's controller training or proof of simulator equivalence. [Engineering account](https://reflexarc.co.uk/projects/rek-robots)

Our proposed first format is human piloted, robot against robot, with a fixed approved skill set. Teleoperation supports development and demonstrations; a gamepad becomes the competition interface after skills and transitions are reliable.

## Shared infrastructure

| System | Minimum responsibility |
| --- | --- |
| Robot specification | Model, mass changes, padding, permitted hardware and actuator envelope |
| Skill protocol | Skill identifier, parameters, sequence number, timestamp, expiry and cancellation |
| Local controller | Balance, valid transitions, rejection reasons, recovery and watchdog |
| Referee | Authoritative round state, legal contact rules, stops and final results |
| Replay | Synchronized commands, robot state, contact evidence and video |
| Event operations | Containment, independent stops, inspection, battery and thermal checks |

A command acknowledgement should distinguish receipt, acceptance, start and completion. Accepting a punch request is not evidence of contact or a scored hit. Define scoring separately from shaping rewards, and reconcile every score event with its source. Use external observation or instrumented targets where robot sensing is insufficient.

The local motor loop must not wait on the match server. On a network failure the robot applies its qualified fallback while the referee stops or invalidates the round under published rules. Log incomplete rounds as incomplete.

## Simulation and evaluation

Put both articulated robots in one physical world so they share contacts. Test timing, opposing directions, mutual contact, wall interaction, falls and resets. A simulator for pilot practice should use the same command meanings and skill availability as hardware, with its known differences documented.

Keep development opponents separate from validation opponents. Evaluate frozen checkpoints from varied initial states on both sides, preserve all attempts, and publish completion rate alongside win rate. A policy that exploits one scripted opponent is not an adequate league baseline.

The [PufferLib REK fork](https://github.com/xinpw8/PufferLib/tree/rek-native-play/ocean/rek_g1) is useful reading for these distinctions. It includes training of high level action selection over an existing SONIC controller, a physical backend and simplified alternatives. It does not establish a publicly reproducible low level fighting controller deployed at REK events. PufferLib can be considered for later tactical learning after the motion layer works; the first version uses mjlab's existing learner path to reduce integration work.

Venue requirements, containment design and human access procedures need qualified review before an event. This guide specifies the developer architecture, not a completed event safety case or competition rulebook.
