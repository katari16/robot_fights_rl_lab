# Media sources

[Main guide](../README.md) · [Demonstrations](../demonstrations.md)

Figures and demonstrations are attributed to their original creators. Their inclusion illustrates the technical discussion and does not imply affiliation or that the league has reproduced the results.

## Learned G1 skills

`g1-skills.mp4`, `g1-skills.gif` and `g1-skills.jpg` are locally rendered recordings of our first mjlab tracking experiment. They show physics rollouts from checkpoint 1200 of `training/output/foundation-v1`, with two copies of each single-robot evaluation placed in the RSL arena. They are not footage of a two-robot interaction or physical hardware.

The learned references originate from the pinned Robo Jab jab recording and the SONIC example kick. The video-to-retargeting stage was not rerun here. Source revisions, preparation, training settings and evaluation limitations are recorded in [G1 motion skills](../g1_skills.md), with [machine-readable results and hashes](../results/g1-skills.json). Generated rollout arrays are included under `simulation/assets/skill_rollouts` so the browser preview runs without training.

The arena uses the supplied RSL mark reconstruction and Unitree G1 visual assets described below. Rendering uses `simulation/skills.py`; browser visualization uses the included mjswan engine. No broader license to the source motions or upstream robot assets is granted by these recordings.

## SuperMimic figure

`supermimic-training-loop.png` is the diagram from Figure 2, page 4 of **SuperMimic: Scaling Humanoid Whole-Body Control with One Differentiable World Model**, by Qiayuan Liao, Yiyang Shao, Junfeng Long, Kevin Zakka, Roberto Horowitz, Pieter Abbeel and Koushil Sreenath, CoRL 2026.

Source: [arXiv version 1 PDF](https://arxiv.org/pdf/2610.28480v1#page=4), submitted 20 October 2026. [Project](https://supermimic.github.io/).

The diagram was cropped from the PDF at page coordinates `(106, 74, 506, 202)` points and rendered at three pixels per point. Surrounding prose and the original caption were excluded; the diagram's content was not changed. The main guide supplies its own explanatory caption and source link.

Copyright remains with the original rights holders. The [arXiv distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/) is not a general reuse license for this repository. This figure is a limited excerpt for technical commentary; no broader license to the figure is granted here.

## Embedded media

| Media | Creator and source | Presentation |
| --- | --- | --- |
| SONIC overview | NVIDIA and SONIC authors, [project](https://nvlabs.github.io/GEAR-SONIC/) | Author-hosted figure in the main guide |
| GigaBrain overview | Cheng et al., [project](https://shepherd1226.github.io/gigabrain-wbc-0.5/) | Author-hosted figure in the main guide |
| TRACE overview | Lan et al., [project](https://bfm-trace.github.io/) | Author-hosted figure in the training guide |
| Jab execution and pipeline GIFs | Robo Jab team, [repository at the referenced commit](https://github.com/abtonmoy/ai_hackathon_calhacks/tree/bd8a0a65c60787296c7eb9a90be10b17fae3e12b) | Remote GIFs; simulation and reference stages labeled |
| Mortal Kombat gameplay GIF | Game by NetherRealm Studios / Warner Bros. Games; [GIFDB upload by Wild Master](https://gifdb.com/gif/mortal-kombat-game-gameplay-ti3iu6f8addxfssi.html), with Gamelution watermark visible in the footage | Remote GIF illustrating candidate skill ideas; physical feasibility must be assessed for G1 |
| REK0 thumbnail and recording | REK, [event video](https://www.youtube.com/watch?v=PR7yNhfHAKg) | Remote thumbnail linking to the recording |
| REK simulator image and gameplay | REK / Reflex Arc, [engineering account](https://reflexarc.co.uk/projects/rek-robots) | Remote still linking to the published video |

The SuperMimic diagram and the locally generated G1 arena preview are stored in this repository. The other media remain hosted by their publishers, and adjacent source links provide a fallback if an embed becomes unavailable. External media retain their original terms; no ownership or blanket permission to redistribute them is claimed.


## G1 arena preview

`g1-arena.mp4`, `g1-arena.gif` and `g1-arena.jpg` are rendered locally with MuJoCo from [`simulation/demo.py`](../../simulation/demo.py). The MP4 is the full 10.83-second loop; the GIF is a five-second excerpt. They show reference pose playback, not a policy evaluation.

The robot model is from the included [Unitree G1 source](../../external/unitree_rl_mjlab/src/assets/robots/unitree_g1/xmls/g1.xml), imported from Unitree at commit `1425b15f73bd4095f0df53709d7c389c3eb9e790`. Its source license is retained in [`external/unitree_rl_mjlab/LICENCE`](../../external/unitree_rl_mjlab/LICENCE).

Motion: Robo Jab team, [ai_hackathon_calhacks](https://github.com/abtonmoy/ai_hackathon_calhacks/tree/bd8a0a65c60787296c7eb9a90be10b17fae3e12b), commit `bd8a0a65c60787296c7eb9a90be10b17fae3e12b`, [data/IMG_3430.csv](https://github.com/abtonmoy/ai_hackathon_calhacks/blob/bd8a0a65c60787296c7eb9a90be10b17fae3e12b/data/IMG_3430.csv). Git blob hash: `3775f20da7d7b5279f281702cb080006078eec5d`. The loader fetches the original CSV on demand instead of vendoring it. The source repository has no top-level license at this revision; this repository does not assign a new license to the recording. The authors describe its capture pipeline as phone video, GVHMR and GMR retargeting to G1. [Format documentation](https://github.com/abtonmoy/ai_hackathon_calhacks/blob/bd8a0a65c60787296c7eb9a90be10b17fae3e12b/data/README.md).

The preview uses original frames `[85:290]`, rotates and translates the root trajectories into the ring, aligns feet to the mat, adds smooth transitions to nominal and delays the second G1 by 21 frames. Joint angles in the recorded segment are preserved. These presentation changes do not establish dynamic feasibility.

The RSL logo was supplied by the repository owner as an SVG data URI. That URI was truncated in its final center path. [`simulation/assets/rsl-mark.svg`](../../simulation/assets/rsl-mark.svg) preserves the three complete interlocking ring paths, their gradients and the complete center hexagon outline. The incomplete center detail is omitted. The file documents this recovery; the demo accepts `--logo` to use a complete replacement.

The arena geometry and materials are authored in this repository. No outside ring textures, logos or robot costumes are included. The browser renderer is [mjswan](../../external/mjswan), with its Apache 2.0 license and notice retained in the source and built viewer.

`g1-arena-viewer.png` is a screenshot of the running local mjswan viewer, captured by the browser acceptance script.
