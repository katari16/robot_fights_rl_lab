# References

[Main guide](README.md)

The initial sources were checked on 21 October 2026; SuperMimic and additional demonstration sources were checked on 23 October 2026. Reported research results are attributed to their authors and were not reproduced for this guide. The league architecture and its acceptance milestones are proposals.

## Controllers and adaptation

| Material | Use | Release boundary |
| --- | --- | --- |
| [SONIC project and paper](https://nvlabs.github.io/GEAR-SONIC/) | Nominal motion tracking architecture | General whole body control, not a combat validation |
| [NVIDIA implementation](https://github.com/NVlabs/GR00T-WholeBodyControl) and [models](https://huggingface.co/nvidia/GEAR-SONIC) | Training, inference and G1 checkpoints | Published training uses Isaac Lab; match model variants and configs |
| [SuperMimic project](https://supermimic.github.io/), [paper](https://arxiv.org/abs/2610.28480) and [demo](https://supermimic.github.io/demo/) | Training a tracker with a learned dynamics model | Project page did not link an author-maintained trainer when checked; contact extension remains research |
| [Independent SuperMimic reproduction](https://github.com/zita-ch/supermimic_vibed) | Implementation reading for a small motion set | Unofficial, author-described as unreviewed, with documented deviations; not an mjlab release |
| [TRACE paper](https://arxiv.org/abs/2610.17999) and [project](https://bfm-trace.github.io/) | LoRA and interface alignment across embodiments | H2 transfer results, not G1 contact robustness |
| [SONIC Unitree H2](https://github.com/QinnyuLan/SONIC_unitree_h2) | TRACE deployment and interfaces | Do not assume the deployment repository contains the complete training release |
| [SONIC X2 transfer draft](https://sonic-agibot-x2.github.io/sonic-transfer/) and [runtime](https://github.com/meetsitaram/sonic-x2) | Frozen controller with codec and decoder adapters | Draft results; runtime bundle and training reproduction are different artifacts |
| [GigaBrain WBC 0.5](https://shepherd1226.github.io/gigabrain-wbc-0.5/) and [paper](https://arxiv.org/abs/2608.18234) | Interaction, feasible commands and recovery | Project page lists code as coming soon; method reference rather than immediate dependency |

## Data and simulation

| Material | Use |
| --- | --- |
| [GVHMR](https://github.com/zju3dv/GVHMR) | Recover human motion from monocular video |
| [GMR](https://github.com/YanjieZe/GMR) and [paper](https://arxiv.org/abs/2510.02252) | Retarget human motion to robot joints |
| [UMR](https://github.com/hanyang9/UMR) and [paper](https://arxiv.org/abs/2609.02134) | Retarget with learned surface correspondence |
| [BONES SEED](https://huggingface.co/datasets/bones-studio/seed) | Existing human and robot motion references |
| [Robo Jab](https://github.com/abtonmoy/ai_hackathon_calhacks) | Video-to-jab pipeline and animated simulation examples |
| [mjlab v1.6.0](https://github.com/mujocolab/mjlab/tree/v1.6.0) | GPU environments and baseline tasks |
| [MuJoCo contact modeling](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters) | Contact compliance and solver parameters |
| [mjlab cloud guide](https://mujocolab.github.io/mjlab/v1.6.0/source/training/cloud.html) | Upstream SkyPilot templates |
| [SkyPilot AWS setup](https://docs.skypilot.ai/en/latest/cloud-setup/cloud-permissions/aws.html) | Account access, permissions and profiles |

## REK and PufferLib

| Material | Interpretation |
| --- | --- |
| [REK collaborator account](https://reflexarc.co.uk/projects/rek-robots) | Firsthand description of piloting, control and simulator work |
| [REK simulator](https://store.steampowered.com/app/4582660/REK/) | Public product description, not a technical benchmark |
| [PufferAI upstream](https://github.com/PufferAI/PufferLib) | Learning infrastructure; distinct from the xinpw8 fork |
| [G1 policy interface](https://github.com/xinpw8/PufferLib/blob/05558657729a3776f693a795cbac0806efd12912/ocean/rek_g1/POLICY_ADAPTER_DESIGN.md) | Trains command selection over an existing tracker |
| [Physical training record](https://github.com/xinpw8/PufferLib/blob/05558657729a3776f693a795cbac0806efd12912/ocean/rek_g1/native5/mujoco_gpu/validation/training-20260914/result.json) | About 6,020 learner steps per second on GB10; not a tracker training benchmark |
| [Simplified training report](https://github.com/xinpw8/PufferLib/blob/05558657729a3776f693a795cbac0806efd12912/ocean/rek_g1/native5/FAST_TRAINING.md) | Much higher throughput with different dynamics; not equivalent physics |
| [T800 source release](https://github.com/xinpw8/PufferLib/blob/9139823a502846f2a616e1fafb6718cee43ce22b/README.md) | Partial source without trained policies or complete physical validation |

## Figures and reuse

The main guide combines research figures, an animated jab example and links to actual fighting footage. The [demonstration notes](demonstrations.md) distinguish physical events, simulated fights and motion tracking. The [media source register](assets/README.md) records attribution, embedding and the extraction of SuperMimic Figure 2.

External code, models, datasets and figures retain their respective terms. Code licensing does not automatically cover model weights, body models, source videos or game assets. External images can change or become unavailable; adjacent source links remain the reading path.
