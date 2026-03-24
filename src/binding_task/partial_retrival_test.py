from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import psychopy
from psychopy import parallel, visual, core, event
import random

from src.binding_task.enums.Enums import Features, Paths, StringEnums, BindingAndTestEnums, \
    ParallelPortEnums, TimeAttribute
from src.binding_task.test_phase import TestPhase
from src.binding_task.utils import show_nothing, send_to_parallel_port


class PartialRetrivalTest(TestPhase):
    def __init__(self, win: psychopy.visual.window.Window, parallel_port: parallel.ParallelPort, categories: list,
                 subject_id: str):
        """*** IMPORTANT: loads only objects that were correctly retrieved in both color and scene
                          during the test phase (from combined_data CSV). ***

            input: win: psychopy window to display stimuli on
                   parallel_port: psychopy parallel port for sending EEG triggers
                   categories: list of feature categories (e.g., Colors, Scenes)
                   subject_id: subject identifier
            1. load correct objects from the most recent combined_data CSV
            2. call super().__init__ with the correct objects as a single block"""
        correct_objects = self._load_correct_objects(subject_id)
        super().__init__(win=win, parallel_port=parallel_port, categories=categories,
                         objects=[correct_objects], subject_id=subject_id)

    def run_example(self):
        """run 2 example trials using the fork and robot example objects"""
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_FORK), trial_times={}, is_example=True)
        self.run_test(image_path=Path(Paths.OBJECT_EXAMPLE_ROBOT), trial_times={}, is_example=True)

    def run(self):
        """run all partial retrieval trials:
            1. send START_PARTIAL_RETRIVAL trigger
            2. for each trial: run test, write answers, temp save"""
        send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.START_PARTIAL_RETRIVAL)
        for trial_index, object_path in enumerate(self.blocks[0]):
            trial_times = {}
            subject_answer = self.run_test(image_path=object_path, trial_times=trial_times)
            self._write_subject_answers(object_path=object_path, subject_answer=subject_answer, trial_times=trial_times)
            self._temp_save(trial=trial_index)

    def run_test(self, image_path: Path, trial_times: dict, is_example: bool = False):
        """run a single partial retrieval trial:
            input: image_path: path to the object image
                   trial_times: dict to store timing data
                   is_example: if True, skip EEG triggers
            output: dict of subject answers including probe category, retrieval success, and feature answer
            1. randomly select a probe category (color or scene)
            2. show probe image for 1 second
            3. show object image for 2 seconds
            4. show retrieval prompt (subject presses key when they remember, or times out after 3s)
            5. blank screen for 0.5 seconds
            6. ask subject whether they remember (remember / don't remember)
            7. if remembered: ask subject to choose the feature for the probe category"""
        retrival_category = random.choice(self.categories)
        trial_answers = {StringEnums.PROBE: retrival_category}

        self._show_probe(retrival_category=retrival_category, trial_times=trial_times, is_example=is_example)
        self._show_object(image_path=image_path, trial_times=trial_times, is_example=is_example)
        self._subject_retrival(trial_times=trial_times, trial_answers=trial_answers, is_example=is_example)
        show_nothing(win=self.win, min_time=0.5, max_time=0.5)

        is_remember = self._subject_report_retrival_success(trial_times=trial_times, trial_answers=trial_answers,
                                                            is_example=is_example)
        if is_remember:
            trial_answers[retrival_category] = self._show_question(category=retrival_category,
                                                                   trial_times=trial_times, is_example=is_example)

        return trial_answers

    def _show_probe(self, retrival_category: str, trial_times: dict, is_example: bool = False):
        """display the probe image (color or scene cue) for 1 second:
            input: retrival_category: the category to probe (Colors or Scenes)
                   trial_times: dict to store timing data
                   is_example: if True, skip EEG triggers
            records PROBE_APPEAR and PROBE_DISAPPEAR timestamps and sends SHOW_PROBE / STOP_PROBE triggers"""
        retrival_probe = Features.PROBE_TO_PATH[retrival_category]
        img = visual.ImageStim(self.win, image=retrival_probe, size=(0.4, 0.4), pos=(0, 0))
        img.draw()

        if not is_example:
            trial_times[TimeAttribute.PROBE_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.SHOW_PROBE)

        self.win.flip()
        core.wait(1.0)

        if not is_example:
            trial_times[TimeAttribute.PROBE_DISAPPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port, pulse_number=ParallelPortEnums.STOP_PROBE)

    def _subject_report_retrival_success(self, trial_times: dict, trial_answers: dict, is_example: bool = False) -> bool:
        """show remember / don't remember options (left/right arrow keys):
            records RETRIVAL_QUESTION_APPEAR and RETRIVAL_REPORT_TIME timestamps,
            sends SHOW_PARTIAL_RETRIVAL_REMEMBER_QUESTION and ANSWER_PARTIAL_RETRIVAL_REMEMBER_QUESTION triggers.
            saves IS_REMEMBER to trial_answers.
            output: True if subject pressed remember, False otherwise"""
        for key, option in BindingAndTestEnums.RETRIVAL_OPTION_BONUS.items():
            visual.TextStim(self.win, text=option[StringEnums.TEXT], pos=option[StringEnums.LOCATION], height=0.1,
                            languageStyle='rtl', font=StringEnums.ARIAL_FONT).draw()

        if not is_example:
            trial_times[TimeAttribute.RETRIVAL_QUESTION_APPEAR] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,
                                  pulse_number=ParallelPortEnums.SHOW_PARTIAL_RETRIVAL_REMEMBER_QUESTION)

        self.win.flip()
        remember_choose = event.waitKeys(keyList=list(BindingAndTestEnums.RETRIVAL_OPTION_BONUS.keys()))[0]

        if not is_example:
            trial_times[TimeAttribute.RETRIVAL_REPORT_TIME] = datetime.now().strftime(StringEnums.MILI_SEC_FORMAT)[:-3]
            send_to_parallel_port(parallel_port=self.parallel_port,
                                  pulse_number=ParallelPortEnums.ANSWER_PARTIAL_RETRIVAL_REMEMBER_QUESTION)

        self.win.flip()
        is_remember = BindingAndTestEnums.RETRIVAL_OPTION_BONUS[remember_choose][StringEnums.IS_REMEMBER]
        trial_answers[StringEnums.IS_REMEMBER] = is_remember
        return is_remember

    def _write_subject_answers(self, object_path: Path, subject_answer: dict, trial_times: dict):
        """save subject's answers for a trial to self.subject_answers:
            stores probe category, is_remember, feature answer (or None if not remembered),
            retrieval success, and trial times"""
        object_name = object_path.stem
        probe = subject_answer.get(StringEnums.PROBE)
        self.subject_answers[f"{StringEnums.TRIAL}_{len(self.subject_answers) + 1}"] = {
            object_name: {
                StringEnums.PROBE: probe,
                StringEnums.IS_REMEMBER: subject_answer.get(StringEnums.IS_REMEMBER),
                StringEnums.SUBJECT_ANSWER: subject_answer.get(probe),  # feature chosen, or None if not remembered
            },
            StringEnums.RETRIVAL_SUCCESS: subject_answer.get(StringEnums.RETRIVAL_SUCCESS),
            StringEnums.TRAIL_TIMES: trial_times,
        }

    def convert_answer_to_df(self):
        """convert self.subject_answers dict to pandas DataFrame with one row per trial"""
        rows = []
        for trial_index, trial_data in self.subject_answers.items():
            trial_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            retrival_success = trial_data.get(StringEnums.RETRIVAL_SUCCESS)
            skip_keys = [StringEnums.TRAIL_TIMES, StringEnums.RETRIVAL_SUCCESS]
            for obj, obj_data in trial_data.items():
                if obj not in skip_keys:
                    row = {
                        StringEnums.SUBJECT: self.subject_id,
                        StringEnums.TRIAL: trial_index,
                        Features.OBJECT: obj,
                        StringEnums.PROBE: obj_data.get(StringEnums.PROBE),
                        StringEnums.RETRIVAL_SUCCESS: retrival_success,
                        StringEnums.IS_REMEMBER: obj_data.get(StringEnums.IS_REMEMBER),
                        StringEnums.SUBJECT_ANSWER: obj_data.get(StringEnums.SUBJECT_ANSWER),
                    }
                    row.update(trial_times)
                    rows.append(row)
        return pd.DataFrame(rows)

    def save_subject_answer(self, time):
        """save final subject answers to JSON and CSV files in subject_answer/final_data/subject_<id>/partial_retrival/"""
        save_folder = f"{Paths.SAVE_DATA_FOLDER}subject_{self.subject_id}/partial_retrival/"
        Path(save_folder).mkdir(parents=True, exist_ok=True)

        with open(f'{save_folder}subject_{self.subject_id}_{time}_partial_retrival.json', 'w') as f:
            json.dump(self.subject_answers, f)

        self.convert_answer_to_df().to_csv(
            f'{save_folder}subject_{self.subject_id}_{time}_partial_retrival.csv', index=False)

    @staticmethod
    def _load_correct_objects(subject_id: str) -> list:
        """load object paths that were correctly retrieved in both color and scene from the most recent combined_data CSV:
            output: list of Path objects for correctly retrieved objects"""
        combined_data_path = Path(Paths.SAVE_DATA_FOLDER) / f"subject_{subject_id}" / "combined_data"
        csv_files = sorted(combined_data_path.glob("*.csv"), key=lambda f: f.stat().st_mtime)
        df = pd.read_csv(csv_files[-1])
        only_correct = df[df[StringEnums.BOTH_CORRECT] == True]
        return [Path(Paths.OBJECT_PATH.format(obj)) for obj in only_correct[Features.OBJECT].tolist()]
