import json
import random
from pathlib import Path
from datetime import datetime
import pandas as pd
import psychopy
from psychopy import visual, core, event, parallel
from tasks.binding_task.enums.Enums import StringEnums, ParallelPortEnums, Features, Instruction, TimeAttribute
from tasks.binding_task.utils import shuffle_trials, show_nothing, show_fixation, show_instruction, send_to_parallel_port

"""
IMPORTANT: the categories input to the builder is what will determine what categories will be
            and the features are determine by the dict Features.CATEGORY_TO_FEATURES
"""

class FunctionalLocalizer:

    def __init__(self, categories: list, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort,
                 subject_id: str, time: str) -> None:
        """input: categories: list of the categories show in the functional localizer
                  win: window of psychopy.visual.window.Window to show all the features on it.
                  parallel_port: parallel port of psychopy.parallel.ParallelPort that will send all the pulses
                  subject_id: id of the subject of the trial
                  time: time of the start of the experiment
            1. save as the attribute of the class all the inputs
            2. init the correction score of the attention questions
            3. create dict between the categories given as input to theirs features
            4. create all the trials of the functional localizer, multiply the feature by the const
               NUMBER_OF_TRIALS_PER_FEATURE and shuffle those trials
            5. create dict between features to theirs image path"""

        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.time = time
        self.correctness_score = []

        self.category_to_features = {category: Features.CATEGORY_TO_FEATURES[category] for category in categories}
        self.all_trials = [key for category in self.category_to_features.values() for key in category.keys()] * StringEnums.NUMBER_OF_TRIALS_PER_FEATURE
        self.all_trials = shuffle_trials(items=self.all_trials, max_consecutive=2)

        self.feature_to_image_file = {key: value for category in self.category_to_features.values() for key, value in category.items()}

    def run(self):
        """run the functional localizer:
            1. run the examples
            2. run all the trials and for each trial:
                a. show features
                b. show attention question
                c. give 1-3 seconds break to next feature
                d. give break each 50 features
            3. save the attention questions results"""

        self._run_examples()

        for trial_index, trial_feature in enumerate(self.all_trials):
            trial_times = {}
            self._fixation_and_show_feature(trial_feature=trial_feature, trial_times=trial_times)
            self._attention_question(trial_index=trial_index, trial_feature=trial_feature, trial_times=trial_times)
            self._temp_save(trial=trial_index)
            show_nothing(win=self.win, min_time=1.0, max_time=3.0)
            if (trial_index + 1) % 50 == 0:
                show_instruction(win=self.win, instruction=Instruction.BREAK)

        self._save_results()

    def _run_examples(self):
        """Run 2 example trials to familiarize the subject with the task."""
        for (feature, word_question, is_true) in Features.FUNCTIONAL_LOCALIZER_EXAMPLES:
            self._fixation_and_show_feature(trial_feature=feature, trial_times= {})
            self._show_attention_question(word_question=word_question, trial_times={})
            self._get_subject_answer(is_true=is_true, trial_times={})
            show_nothing(win=self.win, min_time=1.0, max_time=3.0)

        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)

    def _fixation_and_show_feature(self, trial_feature: str, trial_times: dict):
        """show the feature in 1 trial:
            1. show fixation for 1 second
            2. show nothing for 1 to 2 seconds
            3. show the feature for 1 seconds
            4. give break for 1 to 2 features"""
        show_fixation(win=self.win, min_time=1.0, max_time=1.0)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)
        self._show_feature(trial_feature=trial_feature, trial_times=trial_times)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)

    def _show_feature(self, trial_feature: str, trial_times: dict = None):
        """display the feature image on screen for 1 second and record timing"""
        img = visual.ImageStim(self.win, image=str(self.feature_to_image_file[trial_feature]), size=1)
        img.draw()

        trial_times[TimeAttribute.FEATURE_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.FEATURE_SHOW_TO_PULSE_CODE[trial_feature])
        self.win.flip()
        core.wait(1.0)

        # after this function finished, there is a call to show nothing
        trial_times[TimeAttribute.FEATURE_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.FEATURE_STOP_TO_PULSE_CODE[trial_feature])

    def _attention_question(self, trial_index: int, trial_feature: str, trial_times: dict = None):
        """ 1. flip a coin for true or false word
            2. get the word by the flip results.
            3. show the attention question.
            4. received the answer from subject and update the correctness score"""
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

    def _show_attention_question(self, word_question: str, trial_times: dict)-> None:
        """show the attention question:
            1. create the word and the option to choose
            2. show the subject"""
        text = visual.TextStim(self.win, text=word_question)
        true_text = visual.TextStim(self.win, text=StringEnums.TRUE, pos=(0.5, -0.4))
        false_text = visual.TextStim(self.win, text=StringEnums.WRONG, pos=(-0.5, -0.4))
        for stim in [text, true_text, false_text]:
            stim.draw()

        trial_times[TimeAttribute.QUESTION_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_ATTENTION_QUESTION)
        self.win.flip()

    def _get_subject_answer(self, is_true: bool, trial_times: dict)-> tuple:
        """wait for subject answer and check if correct"""

        user_answer = event.waitKeys(keyList=StringEnums.KEY_OPTIONS_FUNCTIONAL_LOCALIZER)[0]
        trial_times[TimeAttribute.ANSWER_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.ANSWER_ATTENTION_QUESTION)

        if (is_true and user_answer == StringEnums.RIGHT) or (not is_true and user_answer == StringEnums.LEFT):
            is_right = True
        else:
            is_right = False
            show_instruction(win=self.win, instruction=Instruction.MISTAKE, time= 3.0)

        return is_right, user_answer

    def _update_subject_score(self, trial_feature: str, is_right: bool, word_question: str, user_answer: str, trial_index: int, trial_times: dict = None):
        """append trial data to correctness_score list"""
        trial_data = {StringEnums.FEATURE: trial_feature, StringEnums.WORD_QUESTION: word_question, StringEnums.USER_ANSWER: user_answer,
                      StringEnums.IS_RIGHT: is_right, StringEnums.TRIAL_INDEX: trial_index, StringEnums.TRAIL_TIMES: trial_times or {}}
        self.correctness_score.append(trial_data)

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        Path('subject_answer/temp').mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'subject_answer/temp/subject_{self.subject_id}_functional_localizer_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.correctness_score, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'subject_answer/temp/subject_{self.subject_id}_functional_localizer_trial_{trial}_{curr_time}.csv')

    def _save_results(self):
        """save final results to JSON and CSV files"""
        Path(f'subject_answer/subject_{self.subject_id}_{self.time}/function_localizer_stage.json').parent.mkdir(parents=True, exist_ok=True)
        with open(f'subject_answer/subject_{self.subject_id}_{self.time}/function_localizer_stage.json', 'w') as f:
            json.dump(self.correctness_score, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'subject_answer/subject_{self.subject_id}_{self.time}/function_localizer_stage.csv')

    def convert_answer_to_df(self):
        """convert correctness_score list to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in enumerate(self.correctness_score):
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            row = {
                StringEnums.SUBJECT: self.subject_id,
                StringEnums.TRIAL_INDEX: trial_index,
                StringEnums.FEATURE: trial_data[StringEnums.FEATURE],
                StringEnums.WORD_QUESTION: trial_data[StringEnums.WORD_QUESTION],
                StringEnums.USER_ANSWER: trial_data[StringEnums.USER_ANSWER],
                StringEnums.IS_RIGHT: trial_data[StringEnums.IS_RIGHT]
            }
            row.update(trial_times)
            rows.append(row)
        return pd.DataFrame(rows)

