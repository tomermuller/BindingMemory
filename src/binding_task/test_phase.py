import json
import pandas as pd
import psychopy
from psychopy import visual, event, parallel, core
import random
from pathlib import Path
from datetime import datetime
from src.binding_task.enums.Enums import Features, BindingAndTestEnums, ParallelPortEnums, Paths, StringEnums, \
    HebrewEnums, TimeAttribute, Instruction, TaskManage
from src.binding_task.utils import show_nothing, send_to_parallel_port, shuffle_trials

class TestPhase:
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list,
                 objects: list, subject_id: str) -> None:
        """input: win: psychopy window to display stimuli
                  parallel_port: parallel port for sending EEG/fMRI triggers
                  categories: list of feature categories to test (e.g., Colors, Scenes)
                  objects: list of object paths from BindingLearning (divided by blocks)
                  subject_id: subject identifier
            1. save all inputs as class attributes
            2. shuffle objects within each block (max 1 consecutive same object)
            3. init empty dict for subject_answers"""
        self.win = win
        self.parallel_port = parallel_port
        self.categories = categories
        self.subject_id = subject_id
        self.blocks = {}
        for block_index, block_objects in enumerate(objects):
            self.blocks[block_index] = shuffle_trials(items=block_objects, max_consecutive=1)
        self.subject_answers = {}

    def run_example(self):
        """run examples for test phase"""
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_FORK), trial_times={}, is_example=True)
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_ROBOT), trial_times={}, is_example=True)

    def run_block(self, block_index: int):
        """run all test trials in a single block:
            input: block_index: index of the current block
            1. send START_TESH_PHASE_BLOCK trigger
            2. for each trial in the block:
                a. run the test (show object, ask questions)
                b. write subject answers to self.subject_answers
                c. save temporary backup"""
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.START_TESH_PHASE_BLOCK)

        for trial_index in range(len(self.blocks[block_index])):
            trial_times = {}
            subject_answer = self.run_test(image_path=self.blocks[block_index][trial_index], trial_times=trial_times)
            self._write_subject_answers(object_path=self.blocks[block_index][trial_index], subject_answer=subject_answer, trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def run_test(self, image_path: Path, trial_times: dict, is_example: bool = False):
        """run a single test trial:
            input: image_path: path to the object image
                   trial_times: dict to store timing data
                   is_example: if True, skip EEG triggers
            output: dict of subject answers {category: answer}
            1. show object image for 2 seconds
            2. show retrieval prompt (subject presses key when they remember, or times out after 3s)
            3. blank screen for 0.5 seconds
            4. if no click: automatically move to next trial
            5. ask subject to report what they remember (color / scene / both)
            6. blank screen for 0.5 seconds
            7. for each reported category (randomized order), ask subject to choose the feature"""
        trial_answers = {}

        self._show_object(image_path=image_path, trial_times=trial_times, is_example=is_example)
        self._subject_retrival(trial_times=trial_times, trial_answers=trial_answers, is_example=is_example)
        show_nothing(win=self.win, min_time=0.5, max_time=0.5)

        if not trial_answers.get(StringEnums.RETRIVAL_SUCCESS):
            return trial_answers

        retrival_report_list = self._subject_report_retrival_success(trial_times=trial_times,
                                                                     trial_answers=trial_answers, is_example=is_example)
        show_nothing(win=self.win, min_time=0.5, max_time=0.5)

        if retrival_report_list is not None and len(retrival_report_list) > 0:
            random.shuffle(retrival_report_list)

        for question in retrival_report_list:
            trial_answers[question] = self._show_question(category=question, trial_times=trial_times, is_example=is_example)

        return trial_answers

    def _show_object(self, image_path: Path, trial_times: dict, is_example: bool = False):
        """display the object image on screen for 2 seconds, record OBJECT_APPEAR timestamp, and send SHOW_OBJECT_IN_TEST_TRIAL trigger"""
        img = visual.ImageStim(self.win, image=image_path, size=(0.4, 0.4), pos=(0, 0))
        img.draw()

        if not is_example:
            trial_times[TimeAttribute.OBJECT_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_OBJECT_IN_TEST_TRIAL)
        self.win.flip()
        core.wait(2.0)

    def _subject_retrival(self, trial_times: dict, trial_answers: dict, is_example: bool = False):
        """show blank screen for up to 3 seconds; stops early if subject presses any arrow key.
           saves RETRIVAL_TIME to trial_times.
           returns True if subject pressed a key, False if timed out."""
        text = visual.TextStim(self.win, text="+", font=StringEnums.ARIAL_FONT, pos=(0, 0),
                               height=BindingAndTestEnums.TEXT_HEIGHT, languageStyle='rtl', wrapWidth=1.8)
        text.draw()

        if not is_example:
            trial_times[TimeAttribute.OBJECT_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            trial_times[TimeAttribute.START_RETRIVAL_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.START_RETRIVAL_TIME)

        self.win.flip()
        keys = event.waitKeys(maxWait=3.0)
        if not is_example:
            trial_times[TimeAttribute.RETRIVAL_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,pulse_number=ParallelPortEnums.ANSWER_ON_RETRIVAL_TIME)
        trial_answers[StringEnums.RETRIVAL_SUCCESS] = keys is not None

    def _subject_report_retrival_success(self, trial_times: dict, trial_answers: dict, is_example: bool = False) -> list:
        """show 3 options for what the subject remembers (color / scene / both).
           options are displayed at arrow key positions:
               up=nothing, left=color, right=scene, down=both
           saves RETRIVAL_REPORT_TIME to trial_times.
           return: list of remembered categories ([Features.COLORS], [Features.SCENES],
                   [Features.COLORS, Features.SCENES], or [] for nothing)"""

        for key, option in BindingAndTestEnums.RETRIVAL_OPTION.items():
            visual.TextStim(self.win, text=option[StringEnums.TEXT], pos=option[StringEnums.LOCATION],
                            height=BindingAndTestEnums.TEXT_HEIGHT, languageStyle='rtl', font=StringEnums.ARIAL_FONT).draw()

        if not is_example:
            trial_times[TimeAttribute.RETRIVAL_QUESTION_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_RETRIVAL_QUESTION)

        self.win.flip()
        remember_choose = event.waitKeys(keyList=list(BindingAndTestEnums.RETRIVAL_OPTION.keys()))[0]

        if not is_example:
            trial_times[TimeAttribute.RETRIVAL_REPORT_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.ANSWER_RETRIVAL_QUESTION)

        trial_answers[StringEnums.RETRIVAL_REPORT_COLOR] = Features.COLORS in BindingAndTestEnums.RETRIVAL_OPTION[remember_choose][StringEnums.LIST]
        trial_answers[StringEnums.RETRIVAL_REPORT_SCENE] = Features.SCENES in BindingAndTestEnums.RETRIVAL_OPTION[remember_choose][StringEnums.LIST]

        return BindingAndTestEnums.RETRIVAL_OPTION[remember_choose][StringEnums.LIST]

    def _show_question(self, category: str, trial_times: dict, is_example: bool = False):
        """ask subject to choose the correct feature for a category:
            input: category: the feature category to ask about (e.g., Colors, Scenes)
                   trial_times: dict to store timing data
            output: the feature name the subject selected
            1. get all possible features for this category and shuffle them
            2. display the features as words on screen
            3. wait for subject to choose and return the answer"""
        question_answers = list(Features.CATEGORY_TO_FEATURES[category].keys())
        random.shuffle(question_answers)
        self._show_words_arrow_locations(words=question_answers, trial_times=trial_times, category=category, is_example=is_example)
        answer = self._subject_choose(question_answers=question_answers, category=category, trial_times=trial_times, is_example=is_example)
        show_nothing(win=self.win, min_time=1.0, max_time=1.0)
        return answer

    def _show_words_arrow_locations(self, words: list, trial_times: dict, category: str, is_example: bool = False):
        """display feature words at arrow key positions (up, left, right) and record timing"""
        positions = BindingAndTestEnums.FEATURE_QUESTION_POSITIONS
        texts = [visual.TextStim(self.win, text=HebrewEnums.TRANSLATE.get(word), pos=pos, height=BindingAndTestEnums.TEXT_HEIGHT,
                                 languageStyle="rtl", font=StringEnums.ARIAL_FONT)
                 for word, pos in zip(words, positions)]

        for text in texts:
            text.draw()

        if not is_example:
            trial_times[f'{category}_{StringEnums.QUESTION_APPEAR}'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,
                                  pulse_number=ParallelPortEnums.CATEGORY_ANSWERS_SHOW_TO_PULSE_CODE[category])

        self.win.flip()

    def _subject_choose(self, question_answers: list, category: str, trial_times: dict, is_example: bool = False):
        """wait for subject to press arrow key and return the corresponding feature answer"""
        keyboard_answer = event.waitKeys(keyList=list(BindingAndTestEnums.ARROW_TO_LOCATION.keys()))[0]

        if not is_example:
            trial_times[f'{category}_{TimeAttribute.ANSWER_TIME}'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,
                                  pulse_number=ParallelPortEnums.CATEGORY_QUESTION_ANSWER_TO_PULSE_CODE[category])

        answer = question_answers[BindingAndTestEnums.ARROW_TO_LOCATION[keyboard_answer]]
        return answer

    def _write_subject_answers(self, object_path: Path, subject_answer: dict, trial_times: dict):
        """save subject's answers and timing data to self.subject_answers dict"""
        object_name = object_path.stem
        trial_answer = {}
        for category in self.categories:
            trial_answer[category] = subject_answer.get(category)
        self.subject_answers[f"{StringEnums.TRIAL}_{len(self.subject_answers) + 1}"] = {
            object_name: trial_answer,
            StringEnums.RETRIVAL_SUCCESS: subject_answer.get(StringEnums.RETRIVAL_SUCCESS),
            StringEnums.RETRIVAL_REPORT_COLOR: subject_answer.get(StringEnums.RETRIVAL_REPORT_COLOR),
            StringEnums.RETRIVAL_REPORT_SCENE: subject_answer.get(StringEnums.RETRIVAL_REPORT_SCENE),
            StringEnums.TRAIL_TIMES: trial_times,
        }

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files"""
        subject_answer_folder = f"{Paths.SAVE_DATA_FOLDER}subject_{self.subject_id}/{StringEnums.SUBJECT_ANSWER}/"
        Path(subject_answer_folder).mkdir(parents=True, exist_ok=True)

        with open(f'{subject_answer_folder}subject_{self.subject_id}_{time}_{StringEnums.SUBJECT_ANSWER}.json', 'w') as f:
            json.dump(self.subject_answers, f)

        subject_answer_df = self.convert_answer_to_df()
        subject_answer_df.to_csv(f'{subject_answer_folder}subject_{self.subject_id}_{time}_{StringEnums.SUBJECT_ANSWER}.csv')

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        temp_save_path = f'{Paths.SAVE_TEMP_FOLDER}subject_{self.subject_id}/'

        Path(temp_save_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'{temp_save_path}subject_{self.subject_id}_subject_answers_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.subject_answers, f)

        subject_answer_df = self.convert_answer_to_df()
        subject_answer_df.to_csv(f'{temp_save_path}subject_{self.subject_id}_subject_answers_trial_{trial}_{curr_time}.csv')

    def convert_answer_to_df(self):
        """convert self.subject_answers dict to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in self.subject_answers.items():
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            retrival_success = trial_data.get(StringEnums.RETRIVAL_SUCCESS)
            retrival_report_color = trial_data.get(StringEnums.RETRIVAL_REPORT_COLOR)
            retrival_report_scene = trial_data.get(StringEnums.RETRIVAL_REPORT_SCENE)
            skip_keys = [StringEnums.TRAIL_TIMES, StringEnums.RETRIVAL_SUCCESS,
                         StringEnums.RETRIVAL_REPORT_COLOR, StringEnums.RETRIVAL_REPORT_SCENE]
            for obj, features in trial_data.items():
                if obj not in skip_keys:
                    row = {
                        StringEnums.SUBJECT: self.subject_id,
                        StringEnums.TRIAL: trial_index,
                        Features.OBJECT: obj,
                        Features.COLORS: features.get(Features.COLORS),
                        Features.SCENES: features.get(Features.SCENES),
                        StringEnums.RETRIVAL_SUCCESS: retrival_success,
                        StringEnums.RETRIVAL_REPORT_COLOR: retrival_report_color,
                        StringEnums.RETRIVAL_REPORT_SCENE: retrival_report_scene,
                    }
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)

