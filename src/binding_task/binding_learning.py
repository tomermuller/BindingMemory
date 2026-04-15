from datetime import datetime

import numpy as np
import pandas as pd
import psychopy
from PIL import Image, ImageDraw
from src.binding_task.enums.Enums import (ParallelPortEnums, BindingAndTestEnums, Features, Paths, StringEnums,
                                          Instruction, TimeAttribute, TaskManage)
import random
from pathlib import Path
from psychopy import visual, core, parallel, event
import json
from src.binding_task.utils import show_instruction, send_to_parallel_port, show_fixation, show_nothing, shuffle_trials
from collections import defaultdict

class BindingLearning:
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list, subject_id: str):
        """*** IMPORTANT: the categories input determines what categories will be shown.
                          features are determined by Features.CATEGORY_TO_FEATURES ***

            input: categories: list of feature categories to use in the binding task (e.g. Colors, Scenes)
                   win: psychopy window to display stimuli on
                   parallel_port: psychopy parallel port for sending EEG triggers
                   subject_id: subject id
            1. save all inputs as class attributes
            2. init answers dict for storing correct color/scene per trial
            3. create list of all objects divided into blocks
            4. create all binding learning blocks (shuffled feature sequences per category per block)
            5. init difficulty_ratings dict"""
        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.answers = {}
        self.objects = self._get_objects()
        self.blocks = self._create_blocks(categories=categories)
        self.difficulty_ratings = {}

    def run_examples(self):
        """run example trials to familiarize the subject with the binding task:
            1. for each example in BINDING_EXAMPLES (object, color, scene):
                a. create a unified object (colored object on scene background)
                b. save to temporary file
                c. display on screen for 3 seconds
                d. show blank screen for 1-2 second before next example
                e. ask difficulty question
                f. show blank screen for 3 second before next example"""
        for (example_object, color, scene) in BindingAndTestEnums.BINDING_EXAMPLES:
            unified_object = self._create_unified_object(object_image=example_object, color=color, scene_image=scene)
            Path(Paths.BINDING_EXAMPLE).parent.mkdir(parents=True, exist_ok=True)
            unified_object.save(Paths.BINDING_EXAMPLE)
            unified_object.close()

            img = visual.ImageStim(self.win, image=Paths.BINDING_EXAMPLE, size=1)
            img.draw()
            self.win.flip()
            core.wait(3.0)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            show_instruction(win=self.win, instruction=Instruction.DIFFICULT_QUESTION, time=0)
            rating = event.waitKeys(keyList=BindingAndTestEnums.DIFFICULT_RANGE)[0]
            show_nothing(win=self.win, min_time=3.0, max_time=3.0)

    def run_block(self, block_index: int):
        """run all trials in a single block of the binding learning phase:
            input: block_index: index of the current block (0 to NUMBER_OF_BLOCKS-1)
            1. send START_BINDING_LEARNING_BLOCK trigger
            2. for each trial in the block:
                a. show binding learning stimulus (fixation + colored object on scene)
                b. blank screen for 1-2 seconds
                c. ask difficulty rating (1-5)
                d. temp save"""

        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.START_BINDING_LEARNING_BLOCK)

        trials_per_block = TaskManage.NUMBER_OF_BINDING_TRIALS // TaskManage.NUMBER_OF_BLOCKS
        for trial_index in range(trials_per_block):
            trial_times = dict()
            self._show_binding_learning(block_index=block_index, trial_index=trial_index, trial_times=trial_times)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            trial_num = block_index * trials_per_block + trial_index + 1
            self._ask_difficulty_rating(trial_num=trial_num, trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def _show_binding_learning(self, block_index: int, trial_index: int, trial_times: dict):
        """show a single binding learning trial:
            input: block_index: current block index
                   trial_index: current trial index within the block
                   trial_times: dict to store timing data for this trial
            1. show fixation cross for 1 second
            2. blank screen for 1-2 seconds
            3. show binding object (colored object on scene) for 3 seconds,
               recording OBJECT_APPEAR and sending SHOW_BINDING_TRIALS trigger
            4. record FEATURE_DISAPPEAR timestamp and send STOP_BINDING_TRIALS trigger"""
        show_fixation(win=self.win, min_time=1.0, max_time=1.0)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)
        self._show_binding_object(block_index=block_index, trail_index=trial_index, trial_times=trial_times)

        # after this function end there is a call to show nothing
        trial_times[TimeAttribute.FEATURE_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.STOP_BINDING_TRIALS)

    def _ask_difficulty_rating(self, trial_num: int, trial_times: dict):
        """ask the subject to rate how hard it was to remember the object (1=easy, 5=hard):
            1. show difficulty question and record DIFFICULTY_QUESTION_APPEAR timestamp
            2. send SHOW_DIFFICULTY_QUESTION trigger
            3. wait for key press (1-5)
            4. record DIFFICULTY_ANSWER_TIME timestamp and send ANSWER_DIFFICULTY_QUESTION trigger
            5. save rating to difficulty_ratings keyed by global trial_num"""
        show_instruction(win=self.win, instruction=Instruction.DIFFICULT_QUESTION, time=0)
        trial_times[TimeAttribute.DIFFICULTY_QUESTION_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_DIFFICULTY_QUESTION)

        rating = event.waitKeys(keyList=BindingAndTestEnums.DIFFICULT_RANGE)[0]
        trial_times[TimeAttribute.DIFFICULTY_ANSWER_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.ANSWER_DIFFICULTY_QUESTION)

        self.difficulty_ratings[trial_num] = int(rating)

    def _show_binding_object(self, block_index: int, trail_index: int, trial_times: dict):
        """display the binding object on screen:
            input: block_index: current block index
                   trail_index: current trial index within the block
                   trial_times: dict to store timing data
            1. get the binding object image path (creates the unified object)
            2. create ImageStim and draw on screen
            3. record object_appear time
            4. send parallel port signal for SHOW_BINDING_TRIALS
            5. show window and wait 3 seconds"""
        binding_object_path = self._get_binding_object(block_index=block_index, trial_index=trail_index, trial_times=trial_times)
        img = visual.ImageStim(self.win, image=str(binding_object_path), size=1)
        img.draw()

        trial_times[TimeAttribute.OBJECT_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_BINDING_TRIALS)
        self.win.flip()
        core.wait(3.0)

    def _get_binding_object(self, block_index: int, trial_index: int, trial_times: dict):
        """create and save the binding object for a trial:
            input: block_index: current block index
                   trial_index: current trial index
                   trial_times: dict to store timing data
            output: path to the saved binding object image
            1. get the object image path for this trial
            2. get the color (RGBA) and scene for this trial from blocks
            3. create unified object (colored object on scene background)
            4. save to features/binding_photos/trial_{trial_index}.png
            5. write answers (correct color and scene) for this trial"""
        binding_photo_path = f"{Paths.BINDING_PHOTOS_FOLDER}{StringEnums.BLOCK}_{block_index}_{StringEnums.TRIAL}_{trial_index}.png"
        object_image = self.objects[block_index][trial_index]
        color = Features.COLOR_TO_RGBA[self.blocks[block_index][Features.COLORS][trial_index]]
        scene = Features.SCENE_TO_IMAGE[self.blocks[block_index][Features.SCENES][trial_index]]
        unified_object = self._create_unified_object(object_image=object_image, color=color, scene_image=scene)
        unified_object.save(binding_photo_path)
        unified_object.close()

        trials_per_block = TaskManage.NUMBER_OF_BINDING_TRIALS // TaskManage.NUMBER_OF_BLOCKS
        trial_num = block_index * trials_per_block + trial_index + 1
        self._write_answers(phase_index=block_index, trial_index=trial_index, trial_times=trial_times, trial_num=trial_num)
        return binding_photo_path

    def _create_unified_object(self, object_image, color, scene_image):
        """create a unified image of a colored object pasted onto a scene background:
            input: object_image: path to the object PNG
                   color: RGBA tuple to apply to the object
                   scene_image: path to the scene background image
            1. color the object pixels using the given RGBA color
            2. resize the colored object to 40% of the scene dimensions
            3. open the scene image and paste the object centered on it
            output: PIL Image (scene with object — caller is responsible for saving)"""
        colored_object = self._color_object(object_image, color)
        scene_image = Image.open(scene_image)
        colored_object = colored_object.resize((int(scene_image.width * 0.4), int(scene_image.height * 0.4)))
        x = (scene_image.width - colored_object.width) // 2
        y = (scene_image.height - colored_object.height) // 2

        scene_image.paste(colored_object, (x, y), colored_object)
        return scene_image

    @staticmethod
    def _color_object(input_path, color):
        """color the object in the color input:
            flood-fills background transparent from all 4 corners with a threshold to catch
            near-white pixels, preserves dark outlines (r,g,b < 50), and colors all remaining
            pixels with the given color at alpha 210"""
        image = Image.open(input_path).convert('RGBA')
        width, height = image.size

        for corner in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
            ImageDraw.floodfill(image, corner, (0, 0, 0, 0), thresh=30)

        pixels = image.load()
        for i in range(width):
            for j in range(height):
                r, g, b, a = pixels[i, j]
                if a == 0:
                    continue
                elif r < 50 and g < 50 and b < 50:
                    continue
                else:
                    pixels[i, j] = (*color, 210)

        return image

    def _write_answers(self, phase_index: int, trial_index: int, trial_times: dict, trial_num: int):
        """save the correct answers (color, scene) for a trial to self.answers"""
        color_name = self.blocks[phase_index][Features.COLORS][trial_index]
        scene_name = self.blocks[phase_index][Features.SCENES][trial_index]
        object_name = Path(self.objects[phase_index][trial_index]).stem

        self.answers[trial_num] = {object_name: {Features.COLORS: color_name, Features.SCENES: scene_name},
                                   StringEnums.TRAIL_TIMES: trial_times}

    @staticmethod
    def _get_objects() -> list:
        """get all objects for the experiment and divide them into phases:
            output: list of lists, where each inner list contains object paths for one phase
            1. get all PNG files from the features/objects folder
            2. sort the files for consistency
            3. shuffle randomly to randomize object order across subjects
            4. divide into NUMBER_OF_PHASES equal groups
            5. return list structure: [[phase1_objects], [phase2_objects], ...]"""

        objects = sorted(list(Path(Paths.OBJECTS_PATH).glob('*.png')))
        real_objects = []
        for one_object in objects:
            if "_" not in one_object.name:
                real_objects.append(one_object)

        random.shuffle(real_objects)
        n = len(real_objects) // TaskManage.NUMBER_OF_BLOCKS
        return [real_objects[i * n:(i + 1) * n] for i in range(TaskManage.NUMBER_OF_BLOCKS)]

    @staticmethod
    def _create_blocks(categories: list):
        """create the blocks of the experiment:
            input: categories: list of feature categories (e.g., Colors, Scenes)
            output: dict mapping block_index to dict of category -> shuffled feature list
            1. for each category, calculate how many times each feature should repeat per phase
               (total trials / number of features / number of blocks)
            2. for each block, create a list of features repeated the calculated number of times
            3. shuffle the features list to avoid more than 2 consecutive same features
            4. return dict structure: {block_index: {category: [feature1, feature2, ...]}}"""
        blocks = defaultdict(dict)
        for category in categories:
            number_of_features = len(Features.CATEGORY_TO_FEATURES[category])
            number_of_feature_repeats_in_block = int(TaskManage.NUMBER_OF_BINDING_TRIALS / (number_of_features * TaskManage.NUMBER_OF_BLOCKS))

            features_of_category = Features.CATEGORY_TO_FEATURES[category].keys()
            for block_index in range(TaskManage.NUMBER_OF_BLOCKS):
                block_category_features = list(features_of_category) * number_of_feature_repeats_in_block
                block_category_features = shuffle_trials(items=block_category_features, max_consecutive=2)
                blocks[block_index][category] = block_category_features

        return blocks

    def save_subject(self, time):
        """save final subject data (answers, difficulty ratings) to JSON and CSV files"""
        true_answer_folder = f"{Paths.SAVE_DATA_FOLDER}subject_{self.subject_id}/{StringEnums.TRUE_ANSWERS}/"
        Path(true_answer_folder).mkdir(parents=True, exist_ok=True)

        with open(f'{true_answer_folder}subject_{self.subject_id}_{time}_{StringEnums.TRUE_ANSWERS}.json', 'w') as f:
            json.dump(self.answers, f)

        with open(f'{true_answer_folder}subject_{self.subject_id}_{time}_difficulty.json', 'w') as f:
            json.dump(self.difficulty_ratings, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'{true_answer_folder}subject_{self.subject_id}_{time}_{StringEnums.TRUE_ANSWERS}.csv')

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        temp_save_path = f'{Paths.SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_save_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]

        with open(f'{temp_save_path}true_answers_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.answers, f)

        with open(f'{temp_save_path}true_answers_trial_{trial}_{curr_time}_difficulty.json', 'w') as f:
            json.dump(self.difficulty_ratings, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'{temp_save_path}true_answers_trial_{trial}_{curr_time}.csv')

    def convert_answer_to_df(self):
        """convert self.answers dict to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in self.answers.items():
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            for obj, features in trial_data.items():
                if obj != StringEnums.TRAIL_TIMES:
                    row = {
                        StringEnums.SUBJECT: self.subject_id,
                        StringEnums.TRIAL: trial_index,
                        Features.OBJECT: obj,
                        Features.COLORS: features.get(Features.COLORS),
                        Features.SCENES: features.get(Features.SCENES)
                    }
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)

