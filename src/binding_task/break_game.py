from psychopy import visual, core, event, parallel
import psychopy
import random
from src.binding_task.enums.Enums import BreakGameEnums, Instruction, StringEnums, ParallelPortEnums, \
    BindingAndTestEnums
from src.binding_task.utils import show_instruction, send_to_parallel_port


class BreakGame:
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort):
        """initialize the break game where subject counts how many times the rectangle gets brighter:
            1. save game parameters from BreakGameEnums (duration, interval, brightness, change amount)
            2. init brighter_count and compute num_changes (game_duration // change_interval)
            3. create the rectangle stimulus at base brightness"""
        self.game_duration = BreakGameEnums.GAME_DURATION  # seconds
        self.change_interval = BreakGameEnums.CHANGE_INTERVAL
        self.brightness = BreakGameEnums.BASE_BRIGHTNESS
        self.trial_change = BreakGameEnums.TRIAL_CHANGE

        self.parallel_port = parallel_port
        self.win = win
        self.brighter_count = 0
        self.subject_answer = None
        self.num_changes = self.game_duration // self.change_interval
        self.rect = visual.Rect(self.win, width=0.5, height=0.5, fillColor=[self.brightness] * 3)

    def run_example(self):
        """run a 10-second example of the break game:
            show one brighter change then one darker change (5 seconds each),
            then ask the subject how many times it was brighter"""
        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_EXAMPLE_INSTRUCTION)

        for brightness in [BreakGameEnums.BASE_BRIGHTNESS + BreakGameEnums.TRIAL_CHANGE,
                           BreakGameEnums.BASE_BRIGHTNESS - BreakGameEnums.TRIAL_CHANGE]:
            self.rect.fillColor = [brightness] * 3
            self.rect.draw()
            self.win.flip()
            core.wait(0.5)
            self.rect.fillColor = [BreakGameEnums.BASE_BRIGHTNESS] * 3
            self.rect.draw()
            self.win.flip()
            core.wait(4.5)

        self.subject_answer = 1
        self._get_subject_answer_in_break_game()
        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_FINISH)

    def run(self):
        """run the break game:
            1. send START_BREAK_GAME trigger
            2. show instructions
            3. for each change interval: show rectangle and set next brightness randomly
            4. ask subject how many times the rectangle was brighter
            5. show finish instruction
            output: (subject_answer, brighter_count)"""
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.START_BREAK_GAME)

        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_INSTRUCTION)
        for _ in range(self.num_changes):
            self._show_rectangle()
            self._random_next_trial_brightness()
        self._get_subject_answer_in_break_game()

        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_FINISH)
        return self.subject_answer, self.brighter_count

    def _show_rectangle(self):
        """show rectangle at current brightness for 0.5s, then reset to base brightness for the remaining
           (change_interval - 0.5) seconds before the next trial"""
        self.rect.fillColor = [self.brightness] * 3
        self.rect.draw()
        self.win.flip()
        core.wait(0.5)
        self.rect.fillColor = [BreakGameEnums.BASE_BRIGHTNESS] * 3
        self.rect.draw()
        self.win.flip()
        core.wait(self.change_interval-0.5)

    def _random_next_trial_brightness(self):
        """randomly set next brightness to brighter or darker than base"""
        if random.choice([True, False]):
            self.brightness = BreakGameEnums.BASE_BRIGHTNESS + self.trial_change
            self.brighter_count += 1
        else:
            self.brightness = BreakGameEnums.BASE_BRIGHTNESS - self.trial_change

    def _get_subject_answer_in_break_game(self):
        """ask subject how many times rectangle was brighter"""
        text = visual.TextStim(self.win, text=Instruction.BREAK_GAME_QUESTION, font=StringEnums.ARIAL_FONT, pos=(0, 0),
                               height=BindingAndTestEnums.TEXT_HEIGHT, languageStyle='rtl', wrapWidth=0.8)
        text.draw()
        self.win.flip()
        self.subject_answer = int(event.waitKeys(keyList=BreakGameEnums.ANSWER_KEY_LIST)[0])


