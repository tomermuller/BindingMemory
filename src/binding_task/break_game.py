from psychopy import visual, core, event
import psychopy
import random
from src.binding_task.enums.Enums import BreakGameEnums, Instruction
from src.binding_task.utils import show_instruction


class BreakGame:
    def __init__(self, win: psychopy.visual.window.Window):
        """init break game where subject counts brightness changes"""
        self.game_duration = BreakGameEnums.GAME_DURATION  # seconds
        self.change_interval = BreakGameEnums.CHANGE_INTERVAL
        self.brightness = BreakGameEnums.BASE_BRIGHTNESS
        self.trial_change = BreakGameEnums.TRIAL_CHANGE

        self.win = win
        self.brighter_count = 0
        self.num_changes = self.game_duration // self.change_interval
        self.rect = visual.Rect(self.win, width=0.5, height=0.5, fillColor=[self.brightness] * 3)

    def run(self):
        """run the break game and return subject answer and actual brighter count"""
        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_INSTRUCTION)
        for i in range(self.num_changes):
            self._show_rectangle()
            self._random_next_trial_brightness()
        self._get_subject_answer_in_break_game()

        show_instruction(win=self.win, instruction=Instruction.BREAK_GAME_FINISH)
        return self.subject_answer, self.brighter_count

    def _show_rectangle(self):
        """show rectangle with current brightness for 0.5s then return to base"""
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
        text = visual.TextStim(self.win, text=Instruction.BREAK_GAME_QUESTION, font='Arial', pos=(0, 0), height=0.03,
                               languageStyle='rtl', wrapWidth=0.8)
        text.draw()
        self.win.flip()
        self.subject_answer = int(event.waitKeys(keyList=['1', '2', '3', '4', '5', '6', '7', '8', '9'])[0])


