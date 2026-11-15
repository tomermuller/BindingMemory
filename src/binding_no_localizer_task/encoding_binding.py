import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from psychopy import visual, core, event
from scipy import ndimage
from src.binding_task.binding_learning import BindingLearning
from src.binding_no_localizer_task.config import NoLocalizerConfig
from src.enums import BindingAndTestEnums, Features, StringEnums, Instruction
from src.tools.utils import show_instruction, show_nothing, shuffle_trials


class EncodingBinding(BindingLearning):
    """binding learning of the no localizer task: same trial flow as BindingLearning,
       with blocks, trials, objects and save folders from NoLocalizerConfig"""

    def run_examples(self):
        """run example trials: show each unified example object for 3 seconds and ask difficulty question"""
        for (example_object, color, scene) in NoLocalizerConfig.BINDING_EXAMPLES:
            example_path = self._save_unified_object(example_object, color, scene, file_name='example.png')
            visual.ImageStim(self.win, image=str(example_path), size=1).draw()
            self.win.flip()
            core.wait(3.0)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            show_instruction(win=self.win, instruction=Instruction.DIFFICULT_QUESTION, time=0)
            event.waitKeys(keyList=BindingAndTestEnums.DIFFICULT_RANGE)
            show_nothing(win=self.win, min_time=3.0, max_time=3.0)

    def run_block(self, block_index: int):
        """run all trials in a block: binding stimulus, blank screen, difficulty rating, temp save"""
        trials_per_block = NoLocalizerConfig.NUMBER_OF_TRIALS // NoLocalizerConfig.NUMBER_OF_BLOCKS
        for trial_index in range(trials_per_block):
            trial_times = dict()
            self._show_binding_learning(block_index=block_index, trial_index=trial_index, trial_times=trial_times)
            show_nothing(win=self.win, min_time=1.0, max_time=2.0)
            trial_num = block_index * trials_per_block + trial_index + 1
            self._ask_difficulty_rating(trial_num=trial_num, trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def _get_binding_object(self, block_index: int, trial_index: int, trial_times: dict):
        """create and save the unified object of a trial, write its correct answers, return its path"""
        object_image = self.objects[block_index][trial_index]
        color = Features.COLOR_TO_RGBA[self.blocks[block_index][Features.COLORS][trial_index]]
        scene = NoLocalizerConfig.SCENE_TO_IMAGE[self.blocks[block_index][Features.SCENES][trial_index]]
        file_name = f"{StringEnums.BLOCK}_{block_index}_{StringEnums.TRIAL}_{trial_index}.png"
        binding_photo_path = self._save_unified_object(object_image, color, scene, file_name=file_name)

        trials_per_block = NoLocalizerConfig.NUMBER_OF_TRIALS // NoLocalizerConfig.NUMBER_OF_BLOCKS
        trial_num = block_index * trials_per_block + trial_index + 1
        self._write_answers(phase_index=block_index, trial_index=trial_index, trial_times=trial_times, trial_num=trial_num)
        return binding_photo_path

    def _save_unified_object(self, object_image, color, scene_images: list, file_name: str) -> Path:
        """create the unified object on the first scene image and save it to BINDING_PHOTOS_FOLDER"""
        NoLocalizerConfig.BINDING_PHOTOS_FOLDER.mkdir(parents=True, exist_ok=True)
        save_path = NoLocalizerConfig.BINDING_PHOTOS_FOLDER / file_name
        unified_object = self._create_unified_object(object_image=object_image, color=color, scene_image=scene_images[0])
        unified_object.save(save_path)
        unified_object.close()
        return save_path

    @staticmethod
    def _color_object(input_path, color):
        """color the object: all object pixels get the color, background is transparent, and a black outline is drawn
           from the thin dark lines plus a border around the object and around every thick dark area"""
        rgb = np.asarray(Image.open(input_path).convert('RGB')).astype(int)
        object_mask = EncodingBinding._object_mask(not_white=rgb.min(axis=2) < 225, object_name=Path(input_path).stem)
        dark = rgb.max(axis=2) < 50
        thick_dark = ndimage.binary_opening(dark, structure=EncodingBinding._disk(NoLocalizerConfig.OUTLINE_LINE_RADIUS)) & object_mask
        outline = (dark & ~thick_dark) | EncodingBinding._border(object_mask) | EncodingBinding._border(thick_dark)
        colored = np.zeros((*rgb.shape[:2], 4), dtype=np.uint8)
        colored[object_mask] = (*color, 255)
        colored[object_mask & outline] = (0, 0, 0, 255)
        return Image.fromarray(colored)

    @staticmethod
    def _object_mask(not_white: np.ndarray, object_name: str) -> np.ndarray:
        """object = everything except the outside background. wide white areas (a disk fits) touching the border
           are outside, other wide areas are the object's inside (unless listed in TRANSPARENT_HOLES).
           narrow white areas (gaps between legs, outline breaks) are outside only if they touch the outside and not the inside"""
        pad = NoLocalizerConfig.OUTLINE_GAP_RADIUS + 1
        white = np.pad(~EncodingBinding._seal_line_breaks(not_white), pad, constant_values=True)
        wide = ndimage.binary_opening(white, structure=EncodingBinding._disk(NoLocalizerConfig.OUTLINE_GAP_RADIUS))
        wide_labels, _ = ndimage.label(wide)
        outside_wide = np.isin(wide_labels, np.unique(wide_labels[0])) & wide
        outside_wide |= EncodingBinding._transparent_holes(wide_labels, object_name, pad)
        outside = outside_wide | EncodingBinding._outside_narrow(narrow=white & ~wide, outside_wide=outside_wide, inside_wide=wide & ~outside_wide)
        return ~outside[pad:-pad, pad:-pad]

    @staticmethod
    def _seal_line_breaks(not_white: np.ndarray) -> np.ndarray:
        """close tiny breaks in the drawing lines (OUTLINE_BREAK_RADIUS), padded so lines at the image edge are kept"""
        radius = NoLocalizerConfig.OUTLINE_BREAK_RADIUS
        pad = radius + 1
        return ndimage.binary_closing(np.pad(not_white, pad), structure=EncodingBinding._disk(radius))[pad:-pad, pad:-pad]

    @staticmethod
    def _outside_narrow(narrow: np.ndarray, outside_wide: np.ndarray, inside_wide: np.ndarray) -> np.ndarray:
        """narrow white areas that touch the outside wide area and do not touch any inside wide area"""
        labels, _ = ndimage.label(narrow)
        touches = lambda area: np.unique(labels[ndimage.binary_dilation(area) & narrow])
        outside_ids = np.setdiff1d(touches(outside_wide), touches(inside_wide))
        return np.isin(labels, outside_ids[outside_ids > 0])

    @staticmethod
    def _transparent_holes(wide_labels: np.ndarray, object_name: str, pad: int) -> np.ndarray:
        """mask of the wide white areas that contain a TRANSPARENT_HOLES point of this object"""
        hole_ids = [wide_labels[y + pad, x + pad] for x, y in NoLocalizerConfig.TRANSPARENT_HOLES.get(object_name, [])]
        return np.isin(wide_labels, [hole_id for hole_id in hole_ids if hole_id])

    @staticmethod
    def _border(mask: np.ndarray) -> np.ndarray:
        """inner border of the mask, OUTLINE_BORDER_WIDTH pixels wide"""
        return mask & ~ndimage.binary_erosion(mask, structure=EncodingBinding._disk(NoLocalizerConfig.OUTLINE_BORDER_WIDTH))

    @staticmethod
    def _disk(radius: int) -> np.ndarray:
        """boolean disk structuring element of the given radius"""
        y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
        return x * x + y * y <= radius * radius

    def _get_objects(self) -> list:
        """get all objects from OBJECTS_PATH, shuffle them and divide them equally into blocks"""
        objects = sorted(NoLocalizerConfig.OBJECTS_PATH.glob(f'*{NoLocalizerConfig.OBJECTS_EXTENSION}'))
        random.shuffle(objects)
        n = len(objects) // NoLocalizerConfig.NUMBER_OF_BLOCKS
        return [objects[i * n:(i + 1) * n] for i in range(NoLocalizerConfig.NUMBER_OF_BLOCKS)]

    def _create_blocks(self, categories: list):
        """create {block_index: {category: shuffled features}} with each feature repeated equally per block"""
        blocks = defaultdict(dict)
        for category in categories:
            features_of_category = list(NoLocalizerConfig.CATEGORY_TO_FEATURES[category].keys())
            repeats = NoLocalizerConfig.NUMBER_OF_TRIALS // (len(features_of_category) * NoLocalizerConfig.NUMBER_OF_BLOCKS)
            for block_index in range(NoLocalizerConfig.NUMBER_OF_BLOCKS):
                blocks[block_index][category] = shuffle_trials(items=features_of_category * repeats, max_consecutive=2)
        return blocks

    def save_subject(self, time):
        """save final subject data (answers, difficulty ratings) to JSON and CSV files"""
        true_answer_folder = f"{NoLocalizerConfig.SAVE_DATA_FOLDER}subject_{self.subject_id}/{StringEnums.TRUE_ANSWERS}/"
        Path(true_answer_folder).mkdir(parents=True, exist_ok=True)
        file_prefix = f'{true_answer_folder}subject_{self.subject_id}_{time}'
        self._write_files(json_path=f'{file_prefix}_{StringEnums.TRUE_ANSWERS}.json',
                          difficulty_path=f'{file_prefix}_difficulty.json',
                          csv_path=f'{file_prefix}_{StringEnums.TRUE_ANSWERS}.csv')

    def _temp_save(self, trial: int):
        """save temporary backup after each trial for crash recovery"""
        temp_save_path = f'{NoLocalizerConfig.SAVE_TEMP_FOLDER}subject_{self.subject_id}/'
        Path(temp_save_path).mkdir(parents=True, exist_ok=True)
        curr_time = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
        file_prefix = f'{temp_save_path}true_answers_trial_{trial}_{curr_time}'
        self._write_files(json_path=f'{file_prefix}.json', difficulty_path=f'{file_prefix}_difficulty.json',
                          csv_path=f'{file_prefix}.csv')

    def _write_files(self, json_path: str, difficulty_path: str, csv_path: str):
        """write answers JSON, difficulty ratings JSON and answers CSV"""
        with open(json_path, 'w') as f:
            json.dump(self.answers, f)
        with open(difficulty_path, 'w') as f:
            json.dump(self.difficulty_ratings, f)
        self.convert_answer_to_df().to_csv(csv_path)
