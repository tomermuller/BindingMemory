from pathlib import Path
import json

import pandas as pd
import psychopy
from psychopy import parallel

from src.binding_task.enums.Enums import Features, Paths, StringEnums
from src.binding_task.test_phase import TestPhase
from src.binding_task.utils import shuffle_trials


class SecondDayTask(TestPhase):
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort,
                 categories: list, subject_id: str):
        """*** IMPORTANT: loads objects from the most recent partial_retrival CSV saved on day 1. ***

            input: win: psychopy window to display stimuli on
                   parallel_port: psychopy parallel port (unused, no triggers sent)
                   categories: list of feature categories (e.g., Colors, Scenes)
                   subject_id: subject identifier
            1. load objects from the most recent partial_retrival CSV (shuffled, max 1 consecutive)
            2. call super().__init__ with the objects as a single block"""
        objects_by_block = self._load_partial_retrival_objects(subject_id)
        super().__init__(win=win, parallel_port=parallel_port, categories=categories,
                         objects=objects_by_block, subject_id=subject_id)

    def run_example(self):
        """run 2 example trials using the fork and robot example objects"""
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_FORK), trial_times={}, is_example=True)
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_ROBOT), trial_times={}, is_example=True)

    def run(self):
        """run all second day test trials:
            for each trial: run test, write answers, temp save"""
        for trial_index, object_path in enumerate(self.blocks[0]):
            trial_times = {}
            subject_answer = self.run_test(image_path=object_path, trial_times=trial_times)
            self._write_subject_answers(object_path=object_path, subject_answer=subject_answer,
                                        trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files in subject_answer/final_data/subject_<id>/second_day/"""
        save_folder = f"{Paths.SAVE_DATA_FOLDER}subject_{self.subject_id}/second_day/"
        Path(save_folder).mkdir(parents=True, exist_ok=True)

        with open(f'{save_folder}subject_{self.subject_id}_{time}_second_day.json', 'w') as f:
            json.dump(self.subject_answers, f)

        self.convert_answer_to_df().to_csv(
            f'{save_folder}subject_{self.subject_id}_{time}_second_day.csv', index=False)

    @staticmethod
    def _load_partial_retrival_objects(subject_id: str) -> list:
        """load object paths from the most recent partial_retrival CSV, shuffled with max 1 consecutive repeat:
            output: list containing one block (list of shuffled Path objects)"""
        partial_retrival_folder = Path(Paths.SAVE_DATA_FOLDER) / f"subject_{subject_id}" / "partial_retrival"
        csv_files = sorted(partial_retrival_folder.glob("*.csv"), key=lambda f: f.stat().st_mtime)
        df = pd.read_csv(csv_files[-1])
        object_paths = [Path(Paths.OBJECT_PATH.format(obj)) for obj in df[Features.OBJECT].tolist()]
        return [shuffle_trials(object_paths, max_consecutive=1)]
