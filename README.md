# Binding Memory Retrieval (BMR)

A PsychoPy-based neuroscience experiment for studying how subjects encode and retrieve bindings between objects and contextual features (color and scene). Designed for EEG/fMRI recording, with parallel port triggers for neural synchronization.

The experiment is in Hebrew (RTL).

---

## Experiment Overview

The experiment consists of 3 stages:

### Stage 1 — Functional Localizer
- Subjects view repeating images of colors and scenes
- After each image, a Hebrew word appears
- Subject presses an arrow key to judge whether the word matches the image
- 70 trials per feature × 5 features = 350 trials total
- Break every 50 trials

### Stage 2 — Binding Learning & Test (5 blocks)
Each block has two phases:

**Learning phase:**
- Subject sees an object colored and placed on a scene background for 3 seconds
- Rates difficulty of remembering (1 = easy, 5 = hard)

**Break game** (between learning and test):
- Subject counts how many times a rectangle becomes brighter (~100 seconds)

**Test phase:**
- Subject sees the plain object for 2 seconds
- Has 3 seconds to press a key if they remember the binding
- If no press → automatically moves to the next trial
- If pressed → asked what they remember: color / scene / both
- Then asked to select the specific feature for each reported category

After all 5 blocks, a unified CSV is generated combining learning and test data.

### Stage 3 — Partial Retrieval Test
- Only objects correctly retrieved (both color and scene) in Stage 2 are used
- Each trial shows a probe image (color or scene cue) followed by the object
- Subject has 3 seconds to press if they remember
- If pressed → asked to choose the specific feature for the probed category

---

## Project Structure

```
src/binding_task/
├── main.py                     # Entry point and BindingTask orchestrator
├── functional_localizer.py     # Stage 1
├── binding_learning.py         # Stage 2 — learning phase
├── test_phase.py               # Stage 2 — test phase (base class)
├── partial_retrival_test.py    # Stage 3 (inherits TestPhase)
├── break_game.py               # Break activity between blocks
├── second_day_task.py          # Optional second-day re-test
├── utils.py                    # Shared helpers (fixation, shuffle, triggers, etc.)
├── enums/
│   └── Enums.py                # All experiment parameters and constants
└── features/
    ├── objects/                 # Object PNG images
    ├── colors/                  # Color feature images
    ├── scenes/                  # Scene background images
    ├── probes/                  # Probe cue images
    ├── binding_photos/          # Generated stimuli (object on scene)
    └── object example/          # Example images (fork, robot)
```

---

## Output Data

All data is saved under `subject_answer/`:

```
subject_answer/
├── final_data/subject_<id>/
│   ├── functional_localizer/       # Stage 1 results
│   ├── true_answers/               # Correct binding answers + difficulty ratings
│   ├── subject_answer/             # Subject test responses
│   ├── combined_data/              # Merged binding + test CSV (main output)
│   └── partial_retrival/           # Stage 3 results
└── temp/subject_<id>/              # Trial-by-trial crash recovery backups
```

**Key columns in `combined_data`:**
- `object`, `colors`, `scenes`, `difficulty`
- `subject_color`, `subject_scene` (answers given)
- `color_correct`, `scene_correct`, `both_correct`
- `color_rt_ms`, `scene_rt_ms`
- Timestamps for all events

---

## Key Parameters (`enums/Enums.py`)

| Parameter | Value |
|---|---|
| Number of blocks | 5 |
| Binding trials total | 45 (9 per block) |
| Functional localizer trials per feature | 70 |
| Colors used | Red, Green, Yellow |
| Scenes used | Living Room, Bathroom, Kitchen |
| Difficulty scale | 1 (easy) – 5 (hard) |
| Object size on scene | 40% of scene dimensions |
| Retrieval window | 3 seconds |

---

## Dependencies

- [PsychoPy](https://www.psychopy.org/) — stimulus presentation and input
- [Pillow (PIL)](https://pillow.readthedocs.io/) — image generation (coloring objects, compositing)
- [pandas](https://pandas.pydata.org/) — data saving and CSV generation
- [numpy](https://numpy.org/)

---

## Running the Experiment

```bash
python -m src.binding_task.main
```

A GUI dialog will appear asking for the subject ID. The experiment then runs automatically.

---

## EEG/fMRI Integration

Parallel port triggers are sent at all key events (stimulus onset/offset, question appearance, subject response). Trigger codes are defined in `ParallelPortEnums` in `Enums.py`. The parallel port address is `0x5EFC`.
