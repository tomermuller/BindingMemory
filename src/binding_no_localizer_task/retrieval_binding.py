import json
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
from psychopy import event
from src.binding_task.partial_retrival_test import PartialRetrivalTest
from src.binding_task.test_phase import TestPhase
from src.binding_no_localizer_task.config import NoLocalizerConfig
from src.enums import Features, StringEnums, BindingAndTestEnums, ParallelPortEnums, TimeAttribute
from src.tools.utils import show_nothing, send_to_parallel_port


class NoLocalizerTestMixin:
    """mixin: feature questions with the no localizer features, and per-trial temp save into the no localizer temp folder"""

    def _show_question(self, category: str, trial_times: dict, is_example: bool = False):
        """show this task's features of the category in random order at arrow positions, return the chosen feature"""
        question_answers = list(NoLocalizerConfig.CATEGORY_TO_FEATURES[category].keys())
        random.shuffle(question_answers)
        self._show_words_arrow_locations(words=question_answers, trial_times=trial_times, category=category, is_example=is_example)
        answer = self._subject_choose(question_answers=question_answers, category=category, trial_times=trial_times, is_example=is_example)
        show_nothing(win=self.win, min_time=1.0, max_time=1.0)
        return answer

    def _subject_choose(self, question_answers: list, category: str, trial_times: dict, is_example: bool = False):
        """wait for an arrow key that has a feature shown at its position, return the corresponding feature"""
        valid_keys = [key for key, location in BindingAndTestEnums.ARROW_TO_LOCATION.items() if location < len(question_answers)]
        keyboard_answer = event.waitKeys(keyList=valid_keys)[0]
        if not is_example:
            trial_times[f'{category}_{TimeAttribute.ANSWER_TIME}'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,
                                  pulse_number=ParallelPortEnums.CATEGORY_QUESTION_ANSWER_TO_PULSE_CODE[category])
        return question_answers[BindingAndTestEnums.ARROW_TO_LOCATION[keyboard_answer]]

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        temp_save_path = f'{NoLocalizerConfig.SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_save_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        file_prefix = f'{temp_save_path}subject_{self.subject_id}_subject_answers_trial_{trial}_{curr_time}'
        with open(f'{file_prefix}.json', 'w') as f:
            json.dump(self.subject_answers, f)
        self.convert_answer_to_df().to_csv(f'{file_prefix}.csv')


class RetrievalBinding(NoLocalizerTestMixin, TestPhase):
    """test phase of the no localizer task: same trial flow as TestPhase, saving into the no localizer folders"""

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files"""
        subject_answer_folder = f"{NoLocalizerConfig.SAVE_DATA_FOLDER}subject_{self.subject_id}/{StringEnums.SUBJECT_ANSWER}/"
        Path(subject_answer_folder).mkdir(parents=True, exist_ok=True)
        file_prefix = f'{subject_answer_folder}subject_{self.subject_id}_{time}_{StringEnums.SUBJECT_ANSWER}'
        with open(f'{file_prefix}.json', 'w') as f:
            json.dump(self.subject_answers, f)
        self.convert_answer_to_df().to_csv(f'{file_prefix}.csv')


class PartialRetrievalBinding(NoLocalizerTestMixin, PartialRetrivalTest):
    """partial retrieval test of the no localizer task: loads correct objects from and saves into the no localizer folders"""

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files in <SAVE_DATA_FOLDER>/subject_<id>/partial_retrival/"""
        save_folder = f"{NoLocalizerConfig.SAVE_DATA_FOLDER}subject_{self.subject_id}/partial_retrival/"
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        file_prefix = f'{save_folder}subject_{self.subject_id}_{time}_partial_retrival'
        with open(f'{file_prefix}.json', 'w') as f:
            json.dump(self.subject_answers, f)
        self.convert_answer_to_df().to_csv(f'{file_prefix}.csv', index=False)

    @staticmethod
    def _load_correct_objects(subject_id: str) -> list:
        """load paths of objects correctly retrieved in both color and scene from the most recent combined_data CSV,
           a random sample of at most PARTIAL_RETRIEVAL_MAX_OBJECTS (all of them if there are fewer)"""
        combined_data_path = Path(NoLocalizerConfig.SAVE_DATA_FOLDER) / f"subject_{subject_id}" / "combined_data"
        csv_files = sorted(combined_data_path.glob("*.csv"), key=lambda f: f.stat().st_mtime)
        df = pd.read_csv(csv_files[-1])
        correct_objects = df[df[StringEnums.BOTH_CORRECT] == True][Features.OBJECT].tolist()
        chosen_objects = random.sample(correct_objects, min(len(correct_objects), NoLocalizerConfig.PARTIAL_RETRIEVAL_MAX_OBJECTS))
        return [NoLocalizerConfig.OBJECTS_PATH / f"{obj}{NoLocalizerConfig.OBJECTS_EXTENSION}" for obj in chosen_objects]
