import random
import psychopy
from psychopy import visual, core, event, parallel

from src.binding_task.enums.Enums import StringEnums

def shuffle_trials(items, max_consecutive=2):
    """shuffle items while limiting consecutive identical items:
        input: items: list of items to shuffle
               max_consecutive: maximum allowed consecutive identical items (default 2)
        output: shuffled list with no more than max_consecutive identical items in a row
        uses weighted random selection at each step to guarantee a valid arrangement
        even for large lists with many repeats."""
    from collections import Counter
    counts = Counter(items)
    result = []

    for _ in range(len(items)):
        forbidden = None
        if len(result) >= max_consecutive and len(set(result[-max_consecutive:])) == 1:
            forbidden = result[-1]

        available = [item for item, cnt in counts.items() if cnt > 0 and item != forbidden]
        weights = [counts[item] for item in available]

        if not available:
            raise ValueError("Cannot arrange items within constraints")

        chosen = random.choices(available, weights=weights, k=1)[0]
        result.append(chosen)
        counts[chosen] -= 1

    return result

def show_instruction(win: psychopy.visual.window.Window, instruction: str, time: float = None):
    """display instruction text on screen and wait for keypress or time:
        input: win: psychopy window to display on
               instruction: text string to display
               time: optional duration in seconds (if None, wait for keypress)
        1. create text stimulus with RTL support for Hebrew
        2. draw and flip to screen
        3. if time provided, wait for that duration; otherwise wait for any keypress"""
    text = visual.TextStim(win, text=instruction, font=StringEnums.ARIAL_FONT, pos=(0, 0), height=0.03, languageStyle='rtl', wrapWidth=1.8)
    text.draw()
    win.flip()
    if time:
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