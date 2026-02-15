from datetime import datetime

import pandas as pd
import psychopy
from PIL import Image, ImageDraw
from tasks.binding_task.enums.Enums import (ParallelPortEnums, BindingAndTestEnums, Features, Paths, StringEnums,
                                            Instruction, TimeAttribute)
import random
from pathlib import Path
from psychopy import visual, core, parallel, event
import json
from tasks.binding_task.utils import show_instruction, send_to_parallel_port
from utils import show_fixation, show_nothing, shuffle_trials
from collections import defaultdict

"""
IMPORTANT: the categories input to the builder is what will determine what categories will be
            and the features are determine by the dict Features.CATEGORY_TO_FEATURES
"""


class BindingLearning:
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list, subject_id: str):
        """input: categories: list of the categories show in the functional localizer
                   win: window of psychopy.visual.window.Window to show all the functional localizers.
                  parallel_port: parallel port of psychopy.parallel.ParallelPort that will send all the pulses
                  subject_id: subject id of the subject
                1. save as the attribute of the class all the inputs
                2. init the answers dict of the attention questions
                3. create a list of all the objects in the experiment
                4. create the all the blocks of the second stage"""
        self.win = win
        self.parallel_port = parallel_port
        self.subject_id = subject_id
        self.features_trials = {}
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
        for example_object, color, scene in BindingAndTestEnums.BINDING_EXAMPLES:
            unified_object = self._create_unified_object(object_image=example_object, color=color, scene_image=scene)
            unified_object.save(Paths.BINDING_EXAMPLE)
            unified_object.close()

            img = visual.ImageStim(self.win, image=Paths.BINDING_EXAMPLE, size=1)
            img.draw()
            self.win.flip()
            core.wait(3.0)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            show_instruction(win=self.win, instruction=Instruction.DIFFICULT_QUESTION)
            rating = event.waitKeys(keyList=[BindingAndTestEnums.DIFFICULT_RANGE])[0]
            show_nothing(win=self.win, min_time=3.0, max_time=3.0)

    def run_block(self, block_index: int):
        """run all trials in a single block of the binding learning phase:
            input: block_index: index of the current block (0 to NUMBER_OF_BLOCKS-1)
            output: returns the block data for the given block_index
            1. for each trial in the block:
                a. show the binding learning stimulus (fixation + object)
                b. show blank screen for 1-2 seconds
                c. ask difficulty rating (1-5)
                d. save temporary backup of answers"""
        for trial_index in range(BindingAndTestEnums.NUMBER_OF_BINDING_TRIALS // BindingAndTestEnums.NUMBER_OF_BLOCKS):
            trial_times = dict()
            self._show_binding_learning(block_index=block_index, trial_index=trial_index, trial_times=trial_times)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            self._ask_difficulty_rating(trial_index=trial_index, trial_times=trial_times)
            self._temp_save(trial=trial_index)

        return self.blocks[block_index]

    def _show_binding_learning(self, block_index: int, trial_index: int, trial_times: dict):
        """show a single binding learning trial:
            input: block_index: current block index
                   trial_index: current trial index within the block
                   trial_times: dict to store timing data for this trial
            1. show fixation cross for 1 second
            2. show blank screen for 1-2 seconds
            3. show the binding object (colored object on scene) for 3 seconds
            4. record object_disappear time and send parallel port signal"""
        show_fixation(win=self.win, min_time=1.0, max_time=1.0)
        show_nothing(win=self.win, min_time=1.0, max_time=2.0)
        self._show_binding_object(block_index=block_index, trail_index=trial_index, trial_times=trial_times)

        # after this function end there is a call to show nothing
        trial_times[TimeAttribute.FEATURE_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.STOP_BINDING_TRIALS)

    def _ask_difficulty_rating(self, trial_index: int, trial_times: dict):
        """Ask the subject to rate how hard it is to remember (1-5)."""
        show_instruction(win=self.win, instruction=Instruction.DIFFICULT_QUESTION)
        trial_times['difficulty_question_appear'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_DIFFICULTY_QUESTION)

        rating = event.waitKeys(keyList=[BindingAndTestEnums.DIFFICULT_RANGE])[0]
        trial_times['difficulty_answer_time'] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.ANSWER_DIFFICULTY_QUESTION)

        self.difficulty_ratings[trial_index] = int(rating)
        self.answers[len(self.answers)][StringEnums.TRAIL_TIMES] = trial_times

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
        object_image = self.objects[block_index][trial_index]
        color = Features.COLOR_TO_RGBA[self.blocks[block_index][Features.COLORS][trial_index]]
        scene = Features.SCENE_TO_IMAGE[self.blocks[block_index][Features.SCENES][trial_index]]
        unified_object = self._create_unified_object(object_image=object_image, color=color, scene_image=scene)
        unified_object.save(f"features/binding_photos/trial_{trial_index}.png")
        unified_object.close()

        self._write_answers(phase_index=block_index, trial_index=trial_index, trial_times=trial_times)
        return f"features/binding_photos/trial_{trial_index}.png"

    def _create_unified_object(self, object_image, color, scene_image):
        """create and save the unified object for a trial:
        Inputs: object_image: ImageStim object
        color: color
        scene_image: scene image path
        1. color the object in the color input
        2. paste the object in the scene input"""
        colored_object = self._color_object(object_image, color)
        colored_object = colored_object.resize((400, 300))
        scene_image = Image.open(scene_image)
        x = (scene_image.width - colored_object.width) // 2
        y = (scene_image.height - colored_object.height) // 2

        scene_image.paste(colored_object, (x, y), colored_object)
        return scene_image

    @staticmethod
    def _color_object(input_path, color):
        """color the object in the color input"""
        image = Image.open(input_path).convert('RGBA')

        ImageDraw.floodfill(image, (0, 0), (0, 0, 0, 0))
        pixels = image.load()
        for i in range(image.width):
            for j in range(image.height):
                r, g, b, a = pixels[i, j]
                if a == 0:
                    continue
                elif r < 50 and g < 50 and b < 50:
                    continue
                else:
                    pixels[i, j] = (*color, 210)

        return image

    def _write_answers(self, phase_index: int, trial_index: int, trial_times: dict):
        """save the correct answers (color, scene) for a trial to self.answers"""
        color_name = self.blocks[phase_index][Features.COLORS][trial_index]
        scene_name = self.blocks[phase_index][Features.SCENES][trial_index]
        object_name = str(self.objects[phase_index][trial_index]).split(".png")[0].split("objects/")[1]

        self.answers[len(self.answers) + 1] = {object_name: {Features.COLORS: color_name, Features.SCENES: scene_name},
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

        objects = sorted(list(Path(f'features/objects').glob('*.png')))
        random.shuffle(objects)
        n = len(objects) // BindingAndTestEnums.NUMBER_OF_BLOCKS
        return [objects[i * n:(i + 1) * n] for i in range(BindingAndTestEnums.NUMBER_OF_BLOCKS)]

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
            number_of_feature_repeats_in_block = int(BindingAndTestEnums.NUMBER_OF_BINDING_TRIALS / (number_of_features * BindingAndTestEnums.NUMBER_OF_BLOCKS))

            features_of_category = Features.CATEGORY_TO_FEATURES[category].keys()
            for block_index in range(BindingAndTestEnums.NUMBER_OF_BLOCKS):
                block_category_features = list(features_of_category) * number_of_feature_repeats_in_block
                block_category_features = shuffle_trials(items=block_category_features, max_consecutive=2)
                blocks[block_index][category] = block_category_features

        return blocks

    def save_subject(self, time):
        """save final subject data (answers, difficulty ratings) to JSON and CSV files"""
        Path(f'subject_answer/final_data/subject_{self.subject_id}/true_answers').mkdir(parents=True, exist_ok=True)

        with open(f'subject_answer/final_data/subject_{self.subject_id}/true_answers/subject_{self.subject_id}_{time}.json', 'w') as f:
            json.dump(self.answers, f)

        with open(f'subject_answer/final_data/subject_{self.subject_id}/true_answers//subject_{self.subject_id}_{time}_difficulty.json', 'w') as f:
            json.dump(self.difficulty_ratings, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'subject_answer/final_data/subject_{self.subject_id}/true_answers/subject_{self.subject_id}_{time}.csv')

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        with open(f'subject_answer/temp/subject_{self.subject_id}_true_answers_trial_{trial}_{curr_time}.json', 'w') as f:
            json.dump(self.answers, f)

        with open(f'subject_answer/temp/subject_{self.subject_id}_true_answers_trial_{trial}_{curr_time}_difficulty.json', 'w') as f:
            json.dump(self.difficulty_ratings, f)

        answer_df = self.convert_answer_to_df()
        answer_df.to_csv(f'subject_answer/temp/subject_{self.subject_id}_true_answers_trial_{trial}_{curr_time}.csv')

    def convert_answer_to_df(self):
        """convert self.answers dict to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in self.answers.items():
            trial_times = trial_data.get('trial_times', {})
            for obj, features in trial_data.items():
                if obj != 'trial_times':
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

