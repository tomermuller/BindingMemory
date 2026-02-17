import random
import psychopy
from psychopy import visual, core, event, parallel


def shuffle_trials(items, max_consecutive=2):
    """shuffle items while limiting consecutive identical items:
        input: items: list of items to shuffle
               max_consecutive: maximum allowed consecutive identical items (default 2)
        output: shuffled list with no more than max_consecutive identical items in a row
        1. create a copy of items and shuffle randomly
        2. shuffle the list in random order.
        3. check if there are more then max_consecutive identical items in the list, if true, try again, else return
        3. return the shuffled list"""
    for _ in range(10000):
        shuffled = items.copy()
        random.shuffle(shuffled)
        if not has_too_many_consecutive(shuffled, max_consecutive):
            return shuffled
    raise ValueError("Could not shuffle within constraints")

def has_too_many_consecutive(lst, max_consecutive):
    count = 1
    for i in range(1, len(lst)):
        count = count + 1 if lst[i] == lst[i - 1] else 1
        if count > max_consecutive:
            return True
    return False

def show_instruction(win: psychopy.visual.window.Window, instruction: str, time: float = None):
    """display instruction text on screen and wait for keypress or time:
        input: win: psychopy window to display on
               instruction: text string to display
               time: optional duration in seconds (if None, wait for keypress)
        1. create text stimulus with RTL support for Hebrew
        2. draw and flip to screen
        3. if time provided, wait for that duration; otherwise wait for any keypress"""
    text = visual.TextStim(win, text=instruction, font='Arial', pos=(0, 0), height=0.03, languageStyle='rtl', wrapWidth=0.8)
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