# Binding Task

An EEG experiment in which subjects learn object-feature bindings and are later tested on their memory.

## Structure

The experiment runs in three stages:

### Stage 1 — Functional Localizer
Subjects view a series of color and scene images and answer attention questions (true/false word matching). Used to localize category-selective brain regions.

### Stage 2 — Binding Learning + Test (5 blocks)
Each block:
1. **Learning** — subjects view objects paired with a color and a scene image
2. **Break game** — short distractor task
3. **Test** — subjects are shown the object again and must recall its paired color and scene

### Stage 3 — Partial Retrieval Test
Subjects are shown a color or scene probe and must identify which object it was paired with and report whether they remember.

### End — Memory Strategy
Subjects rate the degree to which they used visualization, semantic, or association strategies (1–10 sliders).

## Running

```bash
cd src/binding_task
python main.py
```

A dialog will prompt for the subject ID.

## File outputs

All data is saved under `src/binding_task/subject_answer/`:
- `final_data/subject_<id>/` — full JSON + CSV per stage
- `temp/subject_<id>/` — trial-by-trial crash-recovery backups
- `final_data/subject_<id>/combined_data/` — merged binding + test CSV

## Key files

| File | Purpose |
|---|---|
| `main.py` | Entry point, orchestrates all stages |
| `binding_learning.py` | Stage 2 learning phase |
| `test_phase.py` | Stage 2 test phase |
| `partial_retrival_test.py` | Stage 3 |
| `second_day_task.py` | Day-2 follow-up retrieval |
| `record_baseline.py` | EEG resting-state baseline recording |

## EEG triggers

Trigger codes are defined in `src/enums/Enums.py` under `ParallelPortEnums`. The parallel port address is `0x5EFC`.

## Categories

Colors: red, green, yellow
Scenes: living room, bathroom, kitchen
