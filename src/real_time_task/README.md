# Real-Time Task

An EEG experiment in which subjects learn verb-feature associations in real time and are later tested on their memory.

## Structure

The experiment runs in three stages:

### Stage 1 — Functional Localizer
Subjects view feature images (colors, animacy, etc.) and answer attention questions. Used to localize category-selective brain regions.

### Stage 2 — Couple Learning (5 blocks)
Each block:
1. **Fixation** — 0.5–1.5 s
2. **Verb** — a verb is shown for 1.5 s; subjects imagine performing it
3. **Feature image** — the associated feature image is shown for 2–10 s; subjects press ↑ when they have formed a vivid mental image

Each verb is permanently paired with the same specific image across all blocks. Images are distributed equally across verbs (e.g. 2 verbs per image for animacy, 4 for colors).

### Stage 3 — Retrieval (Couple Retrieval)
Subjects are cued with a verb and must:
1. Press ↑ if they recall the associated image (up to 7 s)
2. Select the correct feature from on-screen options using ↑ / ← / → arrows

## Running

```bash
cd src/real_time_task
python real_time_task.py
```

A dialog will prompt for the subject ID. Stages can be toggled on/off by commenting out calls in `main()`.

## Categories

Categories are passed as a list and can include any combination of:

| Category | Features | Images per feature |
|---|---|---|
| `colors` | red, green, yellow | 1 each |
| `animacy` | animate, inanimate | 3 each |

To change active categories, edit the `categories` list in `real_time_task.py`:
```python
categories = ["colors", "animacy"]
```

## File outputs

All data is saved under `src/real_time_task/subject_answer/`:
- `final_data/subject_<id>/` — JSON + CSV per stage
- `temp/subject_<id>/` — trial-by-trial crash-recovery backups

## Key files

| File | Purpose |
|---|---|
| `real_time_task.py` | Entry point, orchestrates all stages |
| `couple_learning.py` | Stage 2 — verb-feature learning |
| `retrival_couple.py` | Stage 3 — cued retrieval |

## EEG triggers

Trigger codes are defined in `src/enums/Enums.py` under `RealTimeTaskTriggers`. The parallel port address is `0x5EFC`.
