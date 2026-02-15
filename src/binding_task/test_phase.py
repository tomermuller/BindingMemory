import json
import pandas as pd
import psychopy
from psychopy import visual, event, parallel, core
import random
from pathlib import Path
from datetime import datetime
from src.binding_task.enums.Enums import Features, BindingAndTestEnums, ParallelPortEnums, Paths, StringEnums
from src.binding_task.utils import show_nothing, send_to_parallel_port, shuffle_trials

class TestPhase:
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list,
                 objects: dict, subject_id: str) -> None:
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
        self.run_test(image_path= Path(Paths.OBJECT_EXAMPLE_FORK), trial_times={})
        self.run_test(image_path= Path(Paths.OBJECT_EXAMPLE_ROBOT), trial_times={})

    def run_phase(self, block_index: int):
        """run all test trials in a single block:
            input: block_index: index of the current block
            1. for each trial in the block:
                a. run the test (show object, ask questions)
                b. write subject answers to self.subject_answers
                c. save temporary backup"""
        for trial_index in range(BindingAndTestEnums.NUMBER_OF_BINDING_TRIALS // BindingAndTestEnums.NUMBER_OF_BLOCKS):
            trial_times = {}
            subject_answer = self.run_test(image_path=self.blocks[block_index][trial_index], trial_times=trial_times)
            self._write_subject_answers(object_path=self.blocks[block_index][trial_index], subject_answer=subject_answer, trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def run_test(self, image_path: Path, trial_times: dict):
        """run a single test trial:
            input: image_path: path to the object image
                   trial_times: dict to store timing data
            output: dict of subject answers {category: answer}
            1. show object image for 3 seconds
            3. for each category (randomized order), ask subject to choose the feature"""
        trial_questions = list(self.categories)
        random.shuffle(trial_questions)
        trial_answers = {}

        self._show_object(image_path=image_path, trial_times=trial_times)

        for question in trial_questions:
            trial_answers[question] = self._show_question(category=question, trial_times=trial_times)

        return trial_answers

    def _show_object(self, image_path: Path, trial_times: dict):
        """display the object image on screen for 3 seconds and record timing, after that show nothing for 3 seconds"""
        img = visual.ImageStim(self.win, image=image_path, size=(0.4, 0.4), pos=(0, 0))
        img.draw()

        trial_times['object_appear'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_OBJECT_IN_TEST_TRIAL)
        self.win.flip()

        core.wait(3.0)

        trial_times['object_disappear'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.STOP_OBJECT_IN_TEST_TRIAL)
        show_nothing(win=self.win, min_time=3.0, max_time=3.0)

    def _show_question(self, category: str, trial_times: dict):
        """ask subject to choose the correct feature for a category:
            input: category: the feature category to ask about (e.g., Colors, Scenes)
                   trial_times: dict to store timing data
            output: the feature name the subject selected
            1. get all possible features for this category and shuffle them
            2. display the features as words on screen
            3. wait for subject to choose and return the answer"""
        question_answers = list(Features.CATEGORY_TO_FEATURES[category].keys())
        random.shuffle(question_answers)
        self._show_words_arrow_locations(words=question_answers, trial_times=trial_times, category=category)
        answer = self._subject_choose(question_answers=question_answers, category=category, trial_times=trial_times)
        show_nothing(win=self.win, min_time=2.0, max_time=2.0)
        return answer

    def _show_words_arrow_locations(self, words: list, trial_times: dict, category: str):
        """display feature words at arrow key positions (up, left, right) and record timing"""
        positions = [(0, 0.45), (-0.45, 0), (0.45, 0)]
        texts = [visual.TextStim(self.win, text=word, pos=pos, height=0.1)
                 for word, pos in zip(words, positions)]

        for text in texts:
            text.draw()

        trial_times[f'{category}_question_appear'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port,
                              pulse_number=ParallelPortEnums.CATEGORY_ANSWERS_SHOW_TO_PULSE_CODE[category])

        self.win.flip()

    def _subject_choose(self, question_answers: list, category: str, trial_times: dict):
        """wait for subject to press arrow key and return the corresponding feature answer"""
        keyboard_answer = event.waitKeys(keyList=['up', 'left', 'right'])[0]

        trial_times[f'{category}_answer_time'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port,
                              pulse_number=ParallelPortEnums.CATEGORY_QUESTION_ANSWER_TO_PULSE_CODE[category])

        answer = question_answers[BindingAndTestEnums.ARROW_TO_LOCATION[keyboard_answer]]
        return answer

    def _write_subject_answers(self, object_path: Path, subject_answer: dict, trial_times: dict):
        """save subject's answers and timing data to self.subject_answers dict"""
        #object_name = str(object_path).split(".png")[0].split("objects/")[1]
        object_name = object_path.stem
        trial_answer = {}
        for category in self.categories:
            trial_answer[category] = subject_answer[category]
        self.subject_answers[f"trial_{len(self.subject_answers) + 1}"] = {object_name: trial_answer, 'trial_times': trial_times}

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files"""
        Path(f'subject_answer/final_data/subject_{self.subject_id}/subject_answers').mkdir(parents=True, exist_ok=True)

        with open(f'subject_answer/final_data/subject_{self.subject_id}/subject_answers/subject_{self.subject_id}_{time}.json', 'w') as f:
            json.dump(self.subject_answers, f)

        subject_answer_df = self.convert_answer_to_df()
        subject_answer_df.to_csv(f'subject_answer/final_data/subject_{self.subject_id}/subject_answers/subject_{self.subject_id}_{time}.csv')

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        Path('subject_answer/temp').mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'subject_answer/temp/subject_{self.subject_id}_subject_answers_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.subject_answers, f)

        subject_answer_df = self.convert_answer_to_df()
        subject_answer_df.to_csv(f'subject_answer/temp/subject_{self.subject_id}_subject_answers_trial_{trial}_{curr_time}.csv')

    def convert_answer_to_df(self):
        """convert self.subject_answers dict to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in self.subject_answers.items():
            trial_times = trial_data.get('trial_times', {})
            for obj, features in trial_data.items():
                if obj not in ['trial_times']:
                    row = {
                        'subject': self.subject_id,
                        'trial': trial_index,
                        'object': obj,
                        Features.COLORS: features.get(Features.COLORS),
                        Features.SCENES: features.get(Features.SCENES)
                    }
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)

