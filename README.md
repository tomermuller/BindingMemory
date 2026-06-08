# BMR — Binding Memory Retrieval

A PsychoPy-based EEG experiment suite for studying how subjects encode and retrieve memory bindings between verbs/objects and visual features (color, scene, animacy). All instructions are in Hebrew (RTL).

---

## Repository structure

```
src/
├── enums/                  # Shared constants, enums, and image paths (used by all tasks)
├── binding_task/           # Binding learning + test paradigm (main EEG experiment)
├── real_time_task/         # Real-time verb–feature association experiment
├── tools/                  # Shared utilities: functional localizer, break game, display helpers
└── analysis/               # EEG preprocessing pipeline (MNE-based)

src/binding_task/features/  # All stimulus images (colors, scenes, animacy, objects, probes)
requirements.txt
```

---

## Tasks

### Binding Task
Subjects learn object–color–scene bindings and are tested on their memory across 5 blocks.
See [`src/binding_task/README.md`](src/binding_task/README.md) for full details.

**Stages:**
1. Functional localizer (color + scene images with attention questions)
2. Binding learning + test (5 blocks, break game between phases)
3. Partial retrieval test (probe-cued recall)

**Entry point:** `src/binding_task/main.py`

---

### Real-Time Task
Subjects learn verb–feature associations in real time and are later tested on recall.
See [`src/real_time_task/README.md`](src/real_time_task/README.md) for full details.

**Stages:**
1. Functional localizer
2. Couple learning — verb shown → subject imagines action → feature image shown (5 blocks)
3. Retrieval — verb cue → subject recalls and selects correct feature

**Entry point:** `src/real_time_task/real_time_task.py`

---

## Setup

```bash
pip install -r requirements.txt
```

Run from the **project root**:

```bash
python src/binding_task/main.py
python src/real_time_task/real_time_task.py
```

A GUI dialog will prompt for the subject ID.

---

## EEG integration

Triggers are sent via parallel port at address `0x5EFC` at all key events (stimulus onset, response, etc.). All trigger codes are defined in `src/enums/Enums.py`:
- Binding task: `ParallelPortEnums`
- Real-time task: `RealTimeTaskTriggers`

---

## Data output

| Task | Output folder |
|---|---|
| Binding | `src/binding_task/subject_answer/` |
| Real-Time | `src/real_time_task/subject_answer/` |

Each folder contains:
- `final_data/subject_<id>/` — full JSON + CSV results per stage
- `temp/subject_<id>/` — per-trial crash-recovery backups

---

## Key parameters

| Parameter | Binding Task | Real-Time Task |
|---|---|---|
| Blocks | 5 | 5 |
| Trials per block | 9 | 12 verbs |
| Functional localizer trials/feature | 70 | 50 |
| Categories | colors, scenes | colors, animacy (configurable) |
| Language | Hebrew (RTL) | Hebrew (RTL) |

---

## Dependencies

- [PsychoPy](https://www.psychopy.org/) — stimulus presentation and keyboard input
- [Pillow](https://pillow.readthedocs.io/) — image processing
- [pandas](https://pandas.pydata.org/) — data saving and CSV generation
- [numpy](https://numpy.org/) — numerical operations
- [MNE](https://mne.tools/) — EEG preprocessing and analysis
- [autoreject](https://autoreject.github.io/) — automated artifact rejection
- [mne-icalabel](https://mne.tools/mne-icalabel/) — ICA component classification
