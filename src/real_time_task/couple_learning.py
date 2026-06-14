from datetime import datetime
import pandas as pd
import psychopy
from src.enums import Features, Paths, StringEnums, TimeAttribute, RealTimeTaskTriggers, RealTimeTaskEnums, RealTimeInstruction, Instruction
import random
from pathlib import Path
from psychopy import visual, core, parallel, event
from PIL import Image as PILImage
import json
from src.tools.utils import send_to_parallel_port, show_fixation, show_instruction
from src.tools.break_game import BreakGame


class CoupleLearning:

    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list,
                 subject_id: str, verb_list: list):
        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.categories = categories
        self.verb_list = verb_list
        self.answers = {}
        self.block_counter = 0
        self.verb_to_feature = {}
        self.verb_to_image = {}
        self._create_verb_to_feature_dict()

    def _create_verb_to_feature_dict(self) -> None:
        all_verbs = self.verb_list + RealTimeTaskEnums.EXAMPLE_VERB_LIST
        self.verb_to_feature = {verb: {} for verb in all_verbs}
        self.verb_to_image = {verb: {} for verb in all_verbs}
        for category in self.categories:
            self._assign_category(category)

    def _assign_category(self, category: str) -> None:
        all_images = self._flatten_images(category)
        pool = self._balanced_pool(all_images, len(self.verb_list))
        for verb, (feature, img) in zip(self.verb_list, pool):
            self.verb_to_feature[verb][category] = feature
            self.verb_to_image[verb][category] = img
        for verb in RealTimeTaskEnums.EXAMPLE_VERB_LIST:
            feature, img = random.choice(all_images)
            self.verb_to_feature[verb][category] = feature
            self.verb_to_image[verb][category] = img

    def _flatten_images(self, category: str) -> list:
        return [(feature, img)
                for feature, imgs in Features.CATEGORY_TO_FEATURES[category].items()
                for img in imgs]

    def _balanced_pool(self, all_images: list, n: int) -> list:
        m = len(all_images)
        pool = all_images * (n // m) + all_images[:n % m]
        random.shuffle(pool)
        return pool

    def run_examples(self) -> None:
        show_instruction(win=self.win, instruction=RealTimeInstruction.COUPLE_LEARNING_INSTRUCTION)
        for verb in RealTimeTaskEnums.EXAMPLE_VERB_LIST:
            show_fixation(win=self.win, min_time=0.5, max_time=1.5)
            self._show_verb(verb=verb, trial_times={}, is_example=True)
            show_fixation(win=self.win, min_time=0.5, max_time=1.5)
            for category in self.categories:
                self._show_category_to_verb(verb=verb, category=category, trial_times={}, is_example=True)
        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)

    def run_block(self) -> None:
        shuffled_verbs = self.verb_list.copy()
        random.shuffle(shuffled_verbs)
        for trial_index, verb in enumerate(shuffled_verbs):
            trial_times = {
                'block_index': self.block_counter,
                'trial_index_in_block': trial_index,
            }
            trial_num = self.block_counter * len(self.verb_list) + trial_index + 1

            show_fixation(win=self.win, min_time=0.5, max_time=1.5)
            self._show_verb(verb=verb, trial_times=trial_times)
            show_fixation(win=self.win, min_time=0.5, max_time=1.5)
            for category in self.categories:
                self._show_category_to_verb(verb=verb, category=category, trial_times=trial_times)

            self._write_answers(verb=verb, trial_num=trial_num, trial_times=trial_times)
            self._temp_save(trial_num=trial_num)
        self.block_counter += 1

    def _show_verb(self, verb: str, trial_times: dict, is_example: bool = False):
        verb_stim = visual.TextStim(self.win, text=verb, pos=(0, 0), height=0.1, color='white',
                                    font=StringEnums.ARIAL_FONT, languageStyle='rtl')
        verb_stim.draw()
        self.win.flip()
        if not is_example:
            trial_times[TimeAttribute.VERB_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.LEARNING_VERB_TO_TRIGGER[verb])
        core.wait(1.5)

    def _show_category_to_verb(self, verb: str, category: str, trial_times: dict, is_example: bool = False) -> None:
        feature_image_path = self.verb_to_image[verb][category]
        if category == Features.COLORS:
            img = visual.ImageStim(self.win, image=str(feature_image_path), size=(0.33, 0.33), units='height', pos=(0, 0))
        else:
            pil_img = PILImage.open(str(feature_image_path))
            w, h = pil_img.size
            aspect = w / h
            size = (aspect * 0.6, 0.6) if aspect <= 1 else (0.6, 0.6 / aspect)
            img = visual.ImageStim(self.win, image=str(feature_image_path), size=size)
        img.draw()
        self.win.flip()
        if not is_example:
            trial_times[f"img_path_{category}"] = str(feature_image_path)
            trial_times[f"feature_appear_{category}"] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            image_stem = Path(feature_image_path).stem
            pulse = RealTimeTaskTriggers.LEARNING_IMAGE_TO_TRIGGER.get(image_stem, RealTimeTaskTriggers.SHOW_FEATURE)
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=pulse)
        event.clearEvents()
        core.wait(2.0)
        keys = event.waitKeys(maxWait=3.0, keyList=['up'])
        if not is_example:
            trial_times[f"response_{category}"] = keys[0] if keys else 'timeout'
            trial_times[f"answer_time_{category}"] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=RealTimeTaskTriggers.ANSWER_FEATURE)

    def _write_answers(self, verb: str, trial_num: int, trial_times: dict):
        self.answers[trial_num] = {
            verb: {category: self.verb_to_feature[verb][category] for category in self.categories},
            StringEnums.TRAIL_TIMES: trial_times
        }

    def save_subject(self, time: str):
        save_folder = f"{Paths.RT_SAVE_DATA_FOLDER}subject_{self.subject_id}/"
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        with open(f'{save_folder}subject_{self.subject_id}_{time}_{StringEnums.TRUE_ANSWERS}.json', 'w') as f:
            json.dump(self.answers, f)
        self.convert_answer_to_df().to_csv(
            f'{save_folder}subject_{self.subject_id}_{time}_{StringEnums.TRUE_ANSWERS}.csv')

    def _temp_save(self, trial_num: int):
        temp_path = f'{Paths.RT_SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'{temp_path}true_answers_trial_{trial_num}_{curr_time}.json', 'w') as f:
            json.dump(self.answers, f)
        self.convert_answer_to_df().to_csv(f'{temp_path}true_answers_trial_{trial_num}_{curr_time}.csv')

    def convert_answer_to_df(self):
        rows = []
        for trial_num, trial_data in self.answers.items():
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            for verb, features in trial_data.items():
                if verb != StringEnums.TRAIL_TIMES:
                    row = {StringEnums.SUBJECT: self.subject_id, StringEnums.TRIAL: trial_num, 'verb': verb}
                    row.update(features)
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)
