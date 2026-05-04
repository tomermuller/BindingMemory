import json
import random
from pathlib import Path
from datetime import datetime
import pandas as pd
import psychopy
from psychopy import visual, core, event, parallel
from src.binding_task.enums.Enums import StringEnums, ParallelPortEnums, Features, Instruction, TimeAttribute, \
    HebrewEnums, Paths, TaskManage, BindingAndTestEnums
from src.binding_task.utils import shuffle_trials, show_nothing, show_fixation, show_instruction, send_to_parallel_port, compute_avg_scene_color

class FunctionalLocalizer:

    def __init__(self, categories: list, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort,
                 subject_id: str) -> None:
        """*** IMPORTANT: the categories input determines what categories will be shown.
                          features are determined by Features.CATEGORY_TO_FEATURES ***

            input: categories: list of the categories to show in the functional localizer
                   win: psychopy window to display stimuli on
                   parallel_port: psychopy parallel port for sending EEG triggers
                   subject_id: id of the subject
            1. save all inputs as class attributes
            2. init correctness_score list for storing attention question results
            3. build category_to_features dict from the given categories
            4. build all_trials by repeating each feature NUMBER_OF_TRIALS_PER_FEATURE times and shuffling
            5. build feature_to_image_file dict mapping each feature to its image path"""

        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.correctness_score = []

        self.category_to_features = {category: Features.CATEGORY_TO_FEATURES[category] for category in categories}
        self.all_trials = [key for category in self.category_to_features.values() for key in category.keys()] * TaskManage.NUMBER_OF_TRIALS_PER_FEATURE
        self.all_trials = shuffle_trials(items=self.all_trials, max_consecutive=2)

        self.feature_to_image_file = {key: value for category in self.category_to_features.values() for key, value in category.items()}
        self.avg_scene_color = compute_avg_scene_color()
        self.scene_frame = visual.Rect(self.win, width=1, height=1, fillColor=self.avg_scene_color, lineColor=None)

    def run(self):
        """run the functional localizer:
            1. run the examples
            2. run all trials
            3. show a rest break instruction every 50 trials"""

        self._run_examples()

        for trial_index, trial_feature in enumerate(self.all_trials):
            self._run_trial(trial_index=trial_index, trial_feature=trial_feature)
            if (trial_index + 1) % 50 == 0:
                show_instruction(win=self.win, instruction=Instruction.BREAK)

    def _run_examples(self):
        """Run 2 example trials to familiarize the subject with the task."""
        for (feature, word_question, is_true) in Features.FUNCTIONAL_LOCALIZER_EXAMPLES:
            self._fixation_and_show_feature(trial_feature=feature, trial_times={}, is_example=True)
            self._show_attention_question(word_question=word_question, trial_times={}, is_example=True)
            self._get_subject_answer(is_true=is_true, trial_times={}, is_example=True)
            show_nothing(win=self.win, min_time=1.0, max_time=3.0)

        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)

    def _run_trial(self, trial_index: int, trial_feature: str):
        """run a single trial:
            1. show fixation and feature image
            2. show attention question and get subject answer
            3. temp save
            4. blank screen for 1-3 seconds"""
        trial_times = {}
        self._fixation_and_show_feature(trial_feature=trial_feature, trial_times=trial_times)
        self._attention_question(trial_index=trial_index, trial_feature=trial_feature, trial_times=trial_times)
        self._temp_save(trial=trial_index)
        show_nothing(win=self.win, min_time=1.0, max_time=3.0)

    def _fixation_and_show_feature(self, trial_feature: str, trial_times: dict, is_example: bool = False):
        """show fixation cross then feature image with blank screens between:
            1. show fixation for 1 second
            2. blank screen for 1 to 2 seconds
            3. show the feature image for 1.5 second
            4. blank screen for 1 to 2 seconds"""
        show_fixation(win=self.win, min_time=1.0, max_time=1.0)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)
        self._show_feature(trial_feature=trial_feature, trial_times=trial_times, is_example=is_example)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)

    def _show_feature(self, trial_feature: str, trial_times: dict = None, is_example: bool = False):
        """display the feature image on screen for 1.5 seconds and record timing.
            color features are displayed at size 0.5, all other features at size 1."""
        if trial_feature in Features.COLOR_TO_IMAGE:
            self.scene_frame.draw()
            size = 0.5
        else:
            size = 1
        img = visual.ImageStim(self.win, image=str(self.feature_to_image_file[trial_feature]), size=size)
        img.draw()

        if not is_example:
            trial_times[TimeAttribute.FEATURE_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.FEATURE_SHOW_TO_PULSE_CODE[trial_feature])

        self.win.flip()
        core.wait(1.5)

        # after this function finished, there is a call to show nothing
        if not is_example:
            trial_times[TimeAttribute.FEATURE_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]

    def _attention_question(self, trial_index: int, trial_feature: str, trial_times: dict):
        """run the attention question for a single trial:
            1. randomly decide whether to show a true or false word
            2. pick the word based on the decision
            3. display the attention question screen
            4. get subject answer and save the result to correctness_score"""
        is_true = random.choice([True, False])
        word_question = self._get_word_question(is_true=is_true, trial_feature=trial_feature)
        self._show_attention_question(word_question=word_question, trial_times=trial_times)
        is_right, user_answer = self._get_subject_answer(is_true=is_true, trial_times=trial_times)
        self._update_subject_score(trial_feature=trial_feature, is_right=is_right, word_question=word_question,
                                   user_answer=user_answer, trial_index=trial_index, trial_times=trial_times)

    def _get_word_question(self, is_true: bool, trial_feature: str) -> str:
        """if is_true: return the word of the photo
            else: return word of another feature from the same category"""
        if is_true:
            word_question = random.choice(Features.FEATURE_TO_WORDS[trial_feature])
        else:
            category = [cat for cat, features in self.category_to_features.items() if trial_feature in features][0]
            other_features = [f for f in self.category_to_features[category].keys() if f != trial_feature]
            feature_question = random.choice(other_features)
            word_question = random.choice(Features.FEATURE_TO_WORDS[feature_question])

        return word_question

    def _show_attention_question(self, word_question: str, trial_times: dict, is_example: bool = False)-> None:
        """display the attention question screen:
            - center: the word to judge (translated to Hebrew)
            - bottom-right: correct option (נכון)
            - bottom-left: incorrect option (לא נכון)
            records QUESTION_APPEAR timestamp and sends SHOW_ATTENTION_QUESTION trigger"""
        stims = [visual.TextStim(self.win, text=HebrewEnums.TRANSLATE.get(word_question), font=StringEnums.ARIAL_FONT, languageStyle='rtl')]
        for option in BindingAndTestEnums.ATTENTION_QUESTION_OPTIONS.values():
            stims.append(visual.TextStim(self.win, text=option[StringEnums.TEXT], pos=option[StringEnums.LOCATION],
                                         font=StringEnums.ARIAL_FONT, languageStyle='rtl'))
        for stim in stims:
            stim.draw()

        if not is_example:
            trial_times[TimeAttribute.QUESTION_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_ATTENTION_QUESTION)
        self.win.flip()

    def _get_subject_answer(self, is_true: bool, trial_times: dict, is_example: bool = False)-> tuple:
        """wait for subject to press right (correct) or left (incorrect) and evaluate the answer:
            - right key = subject says the word matches the image
            - left key  = subject says the word does not match the image
            records ANSWER_TIME timestamp and sends ANSWER_ATTENTION_QUESTION trigger
            if wrong: shows a mistake instruction for 3 seconds
            output: (is_right: bool, user_answer: str)"""

        user_answer = event.waitKeys(keyList=StringEnums.KEY_OPTIONS_FUNCTIONAL_LOCALIZER)[0]
        if not is_example:
            trial_times[TimeAttribute.ANSWER_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.ANSWER_ATTENTION_QUESTION)

        if (is_true and user_answer == StringEnums.RIGHT) or (not is_true and user_answer == StringEnums.LEFT):
            is_right = True
        else:
            is_right = False
            show_instruction(win=self.win, instruction=Instruction.MISTAKE, time= 3.0)

        return is_right, user_answer

    def _update_subject_score(self, trial_feature: str, is_right: bool, word_question: str, user_answer: str, trial_index: int, trial_times: dict):
        """append trial data to correctness_score list"""
        trial_data = {StringEnums.FEATURE: trial_feature, StringEnums.WORD_QUESTION: word_question,
                      StringEnums.USER_ANSWER: user_answer, StringEnums.IS_RIGHT: is_right,
                      StringEnums.TRIAL_INDEX: trial_index, StringEnums.TRAIL_TIMES: trial_times}
        self.correctness_score.append(trial_data)

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        temp_save_path = f'{Paths.SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_save_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]

        with open(f'{temp_save_path}functional_localizer_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.correctness_score, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'{temp_save_path}functional_localizer_trial_{trial}_{curr_time}.csv')

    def save_results(self, time):
        """save final results to JSON and CSV files"""
        functional_localizer_folder = f"{Paths.SAVE_DATA_FOLDER}subject_{self.subject_id}/functional_localizer/"
        Path(functional_localizer_folder).mkdir(parents=True, exist_ok=True)

        with open(f'{functional_localizer_folder}subject_{self.subject_id}_{time}_function_localizer_stage.json', 'w') as f:
            json.dump(self.correctness_score, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'{functional_localizer_folder}subject_{self.subject_id}_{time}_function_localizer_stage.csv')

    def convert_answer_to_df(self):
        """convert correctness_score list to pandas DataFrame with one row per trial"""
        rows = []
        for trial_data in self.correctness_score:
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            row = {
                StringEnums.SUBJECT: self.subject_id,
                StringEnums.TRIAL_INDEX: trial_data[StringEnums.TRIAL_INDEX],
                StringEnums.FEATURE: trial_data[StringEnums.FEATURE],
                StringEnums.WORD_QUESTION: trial_data[StringEnums.WORD_QUESTION],
                StringEnums.USER_ANSWER: trial_data[StringEnums.USER_ANSWER],
                StringEnums.IS_RIGHT: trial_data[StringEnums.IS_RIGHT]
            }
            row.update(trial_times)
            rows.append(row)
        return pd.DataFrame(rows)

