import random
from collections import Counter
import psychopy
from psychopy import visual, core, event, parallel

from src.binding_task.enums.Enums import StringEnums, BindingAndTestEnums

def shuffle_trials(items, max_consecutive=2):
    """Shuffle items ensuring no more than max_consecutive identical items in a row.

    Uses a greedy algorithm with a mandatory-placement safety check: before doing a
    random weighted pick, it detects whether any available item *must* be placed now
    (because skipping it would make its remaining count impossible to fit later).
    This prevents the greedy from painting itself into a corner and guarantees a valid
    arrangement is always found whenever one mathematically exists.

    The feasibility limit per step is: floor(remaining * k / (k+1))
    where k = max_consecutive. Any item whose count exceeds this limit must be placed
    immediately.

    input:  items          - list of items to shuffle (may contain duplicates)
            max_consecutive - max allowed identical items in a row (default 2)
    output: shuffled list satisfying the constraint
    raises: ValueError if no valid arrangement exists (e.g. one item dominates too much)
    """
    counts = Counter(items)
    n = len(items)
    result = []

    while len(result) < n:
        remaining = n - len(result)

        forbidden = None
        if len(result) >= max_consecutive and len(set(result[-max_consecutive:])) == 1:
            forbidden = result[-1]

        available = [(item, cnt) for item, cnt in counts.items()
                     if cnt > 0 and item != forbidden]

        if not available:
            raise ValueError("Cannot arrange items within the max_consecutive constraint — impossible input")

        # Safety check: if any item's count exceeds the maximum it could ever occupy
        # in the remaining slots, we MUST place it now or we'll never fit all of them.
        # Maximum slots one item can fill in `remaining-1` future positions = floor((remaining-1+1)*k/(k+1))
        # simplified to floor(remaining * k / (k+1)).
        limit = (remaining * max_consecutive) // (max_consecutive + 1)
        must_place = None
        for item, cnt in sorted(available, key=lambda x: -x[1]):
            if cnt > limit:
                must_place = item
                break  # only the single most-frequent item can exceed the limit

        if must_place is not None:
            chosen = must_place
        else:
            chosen = random.choices([i for i, _ in available],
                                    weights=[c for _, c in available])[0]

        result.append(chosen)
        counts[chosen] -= 1

    return result

def show_instruction(win: psychopy.visual.window.Window, instruction: str, time: float = None):
    """display instruction text on screen and wait for keypress or time:
        input: win: psychopy window to display on
               instruction: text string to display
               time: optional duration in seconds (if None, waits for keypress; 0 returns immediately)
        1. create text stimulus with RTL support for Hebrew
        2. draw and flip to screen
        3. if time provided, wait for that duration; otherwise wait for any keypress"""
    text = visual.TextStim(win, text=instruction, font=StringEnums.ARIAL_FONT, pos=(0, 0),
                           height=BindingAndTestEnums.TEXT_HEIGHT, languageStyle='rtl', wrapWidth=1.8)
    text.draw()
    win.flip()
    if time is not None:
        core.wait(time)
    else:
        event.waitKeys()

def show_fixation(win: psychopy.visual.window.Window, min_time: float, max_time: float):
    """display fixation cross (+) on screen for random duration:
        input: win: psychopy window to display on
               min_time: minimum duration in seconds
               max_time: maximum duration in seconds
        1. create white fixation cross text stimulus
        2. draw and flip to screen
        3. wait for random duration between min_time and max_time"""
    fixation = visual.TextStim(win, text='+', pos=(0, 0), height=0.1, color='white')
    fixation.draw()
    win.flip()
    core.wait(random.uniform(min_time, max_time))

def show_nothing(win: psychopy.visual.window.Window, min_time: float, max_time: float):
    """display blank screen for random duration:
        input: win: psychopy window to display on
               min_time: minimum duration in seconds
               max_time: maximum duration in seconds
        1. flip window to show blank screen
        2. wait for random duration between min_time and max_time"""
    win.flip()
    core.wait(random.uniform(min_time, max_time))

def send_to_parallel_port(parallel_port: parallel.ParallelPort, pulse_number):
    """send trigger pulse to parallel port for EEG/fMRI synchronization:
        input: parallel_port: psychopy ParallelPort object
               pulse_number: integer code to send (defined in ParallelPortEnums)
        1. set data on parallel port (currently commented for testing)
        2. wait 10ms for pulse duration
        3. reset parallel port to 0"""
    #parallel_port.setData(pulse_number)
    print(f"pulse_number: {pulse_number}")
    core.wait(0.01)
    #parallel_port.setData(0)