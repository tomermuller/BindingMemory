from datetime import datetime
import pandas as pd
import psychopy
from src.enums import (Paths, StringEnums, TimeAttribute, RealTimeTaskTriggers, HebrewEnums,
                       Features, BindingAndTestEnums, RealTimeTaskEnums, RealTimeInstruction, Instruction)
import random
from pathlib import Path
from psychopy import visual, core, parallel, event
import json
from src.tools.utils import send_to_parallel_port, show_fixation, show_instruction


class RetrivalCouple:

    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort,
                 subject_id: str, verb_list: list, categories: list):
        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.verb_list = verb_list
        self.categories = categories
        self.answers = {}

    def run_block(self):
        shuffled_verbs = self.verb_list.copy()
        random.shuffle(shuffled_verbs)
        for trial_index, verb in enumerate(shuffled_verbs):
            self._run_trial(verb=verb, trial_index=trial_index)

    def run_examples(self) -> None:
        show_instruction(win=self.win, instruction=RealTimeInstruction.RETRIVAL_COUPLE_INSTRUCTION)
        for verb in RealTimeTaskEnums.EXAMPLE_VERB_LIST:
            show_fixation(win=self.win, min_time=0.5, max_time=1.5)
            self._show_cue_verb(verb=verb, trial_times={}, is_example=True)
            for category in self.categories:
                self._ask_feature_question(category=category, trial_times={}, is_example=True)

    def _run_trial(self, verb: str, trial_index: int):
        trial_times = {'trial_index': trial_index}
        trial_num = trial_index + 1
        show_fixation(win=self.win, min_time=0.5, max_time=1.5)
        self._show_cue_verb(verb=verb, trial_times=trial_times)
        for category in self.categories:
            self._ask_feature_question(category=category, trial_times=trial_times)
        self._write_answers(verb=verb, trial_num=trial_num, trial_times=trial_times)
        self._temp_save(trial_num=trial_num)

    def _show_cue_verb(self, verb: str, trial_times: dict, is_example: bool = False):
        verb_stim = visual.TextStim(self.win, text=verb, pos=(0, 0), height=0.1, color='white',
                                    font=StringEnums.ARIAL_FONT, languageStyle='rtl')
        verb_stim.draw()
        self.win.flip()
        if not is_example:
            trial_times[TimeAttribute.CUE_VERB_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.SHOW_CUE_VERB)

        event.clearEvents()
        keys = event.waitKeys(maxWait=7.0, keyList=['up'])
        if not is_example:
            trial_times[StringEnums.RECALLED] = keys is not None
            trial_times[TimeAttribute.RECALL_KEY_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.ANSWER_CUE_VERB)

        if keys is not None:
            core.wait(2.0)
        if not is_example:
            trial_times[TimeAttribute.CUE_VERB_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]

    def _ask_feature_question(self, category: str, trial_times: dict, is_example: bool = False):
        features = list(Features.CATEGORY_TO_FEATURES[category].keys())
        random.shuffle(features)
        all_keys = [StringEnums.LEFT, StringEnums.RIGHT, StringEnums.UP]
        valid_keys = all_keys[:len(features)]
        positions = BindingAndTestEnums.FEATURE_QUESTION_POSITIONS[:len(features)]
        stims = [visual.TextStim(self.win, text=HebrewEnums.TRANSLATE[f], pos=pos,
                                 font=StringEnums.ARIAL_FONT, languageStyle='rtl')
                 for f, pos in zip(features, positions)]
        for stim in stims:
            stim.draw()
        self.win.flip()
        if not is_example:
            trial_times[f'{category}_question_appear'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.SHOW_FEATURE_QUESTION)

        event.clearEvents()
        key = event.waitKeys(keyList=valid_keys)[0]
        if not is_example:
            answer = features[BindingAndTestEnums.ARROW_TO_LOCATION[key]]
            trial_times[f'{category}_answer'] = answer
            trial_times[f'{category}_answer_time'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.ANSWER_FEATURE_QUESTION)

    def _write_answers(self, verb: str, trial_num: int, trial_times: dict):
        self.answers[trial_num] = {
            verb: {category: trial_times.get(f'{category}_answer') for category in self.categories},
            StringEnums.TRAIL_TIMES: trial_times
        }

    def save_subject(self, time: str):
        save_folder = f"{Paths.RT_SAVE_DATA_FOLDER}subject_{self.subject_id}/"
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        with open(f'{save_folder}subject_{self.subject_id}_{time}_retrival_couple.json', 'w') as f:
            json.dump(self.answers, f)
        self.convert_answer_to_df().to_csv(
            f'{save_folder}subject_{self.subject_id}_{time}_retrival_couple.csv')

    def _temp_save(self, trial_num: int):
        temp_path = f'{Paths.RT_SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'{temp_path}retrival_couple_trial_{trial_num}_{curr_time}.json', 'w') as f:
            json.dump(self.answers, f)
        self.convert_answer_to_df().to_csv(f'{temp_path}retrival_couple_trial_{trial_num}_{curr_time}.csv')

    def convert_answer_to_df(self):
        rows = []
        for trial_num, trial_data in self.answers.items():
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            for verb, _ in trial_data.items():
                if verb != StringEnums.TRAIL_TIMES:
                    row = {StringEnums.SUBJECT: self.subject_id, StringEnums.TRIAL: trial_num, 'verb': verb}
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)
