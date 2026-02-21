from psychopy import visual, event, parallel, gui
from src.binding_task.enums.Enums import Features, BindingAndTestEnums, Instruction, StringEnums
from src.binding_task.binding_learning import BindingLearning
from src.binding_task.functional_localizer import FunctionalLocalizer
from src.binding_task.test_phase import TestPhase
from datetime import datetime
from src.binding_task.break_game import BreakGame
from src.binding_task.utils import show_instruction
from pathlib import Path
import pandas as pd


def get_subject_id() -> str:
    """open Gui window to get subject ID and return it"""
    info = {'Subject ID': ''}
    dlg = gui.DlgFromDict(dictionary=info, title='Experiment')
    if dlg.OK:
        return info['Subject ID']
    else:
        return "-1"


class BindingTask:
    def __init__(self, subject_id: str):
        self.subject_id = subject_id
        self.win = visual.Window(fullscr=True)
        self.parallel_port = parallel.ParallelPort(address=0x0378)
        self.time = datetime.now().strftime(StringEnums.MINUTE_FORMAT)

    def main(self):
        """run the experiment:
            1. set the screen and psychopy window to experiment
            2. call first stage
            3. call second stage"""
        self._general_setting()
        show_instruction(win=self.win, instruction=Instruction.WELLCOME)
        self._first_stage()
        binding, test = self._second_stage()
        self._save_unified_file_for_all_data(binding=binding, test=test)
        show_instruction(win=self.win, instruction=Instruction.GOODBYE, time=10)

    @staticmethod
    def _general_setting():
        """set setting for experiment:
            1. disappear the mouse"""

        event.Mouse(visible=False)

    def _first_stage(self):
        """the first part of the experiment:
            1. show the instruction to the first part
            2. init and call run func of FunctionalLocalizer"""

        show_instruction(win=self.win, instruction=Instruction.FIRST_PHASE_INSTRUCTION)
        functional_localizer = FunctionalLocalizer(categories=Features.ALL_CATEGORIES, win=self.win, time=self.time,
                                                   parallel_port=self.parallel_port, subject_id=self.subject_id)
        functional_localizer.run()

    def _second_stage(self):
        """the second part of the experiment:
        1. show the instruction to the second part
        2. init binding_learning and test_phase classes
        3. call examples
        4. run all the blocks
        5. save the results"""

        show_instruction(win=self.win, instruction=Instruction.SECOND_PHASE_INSTRUCTION)
        binding = BindingLearning(win=self.win, parallel_port=self.parallel_port, categories=Features.ALL_CATEGORIES,
                                  subject_id=self.subject_id)
        test = TestPhase(win=self.win, parallel_port=self.parallel_port, categories=Features.ALL_CATEGORIES,
                         objects=binding.objects, subject_id=self.subject_id)

        binding.run_examples()
        test.run_example()

        for block_idx in range(BindingAndTestEnums.NUMBER_OF_BLOCKS):
            self._block_learning_and_test(binding=binding, test=test, block=block_idx)

        binding.save_subject(time=self.time)
        test.save_subject_answer(time=self.time)

        return binding, test

    def _block_learning_and_test(self, binding: BindingLearning, test: TestPhase, block: int):
        """run one block of the second stage:
             1. show instruction to the block
             2. call binding_learning.run_phase for show the binding
             3. create and show and break game
             4. run test_phase.run_phase for the tests on the binding"""

        show_instruction(win=self.win, instruction=Instruction.START_X_BLOCK + str(block) + "/5")
        binding.run_block(block_index=block)
        break_game = BreakGame(win=self.win)
        break_game.run()
        test.run_phase(block)

    def _save_unified_file_for_all_data(self, binding: BindingLearning, test: TestPhase):
        """Save a single combined CSV with one row per binding trial, merging binding and test data.
           Input:  binding - BindingLearning object holding binding.answers and binding.difficulty_ratings
                   test    - TestPhase object holding test.subject_answers
           Steps:
               1. Build a flat lookup dict {object_name -> test results} via _create_test_lookup
               2. Iterate over every binding trial in binding.answers
               3. For each trial build one merged row via _build_row
               4. Write all rows to CSV via _save_combined_csv
           Output: CSV file at subject_answer/final_data/subject_<id>/subject_<id>_<time>_combined.csv"""
        rows = []
        test_by_object = self._create_test_lookup(test)

        for binding_trial, binding_data in binding.answers.items():
            row = self._build_row(binding_trial, binding_data, test_by_object, binding.difficulty_ratings)
            if row:
                rows.append(row)

        self._save_combined_csv(rows)

    @staticmethod
    def _create_test_lookup(test: TestPhase):
        """create lookup dict for test answers by object name:
           Input: TestPhase object of the experiment
           Output:{chair: {trail_number: trial_4,
                           answers: {colors: yellow, scenes: kitchen},
                            times: {object appear: 14:00:05}, ....},
                   closet: ...."""
        test_by_object = {}
        for trial_key, trial_data in test.subject_answers.items():
            test_times = trial_data.get('trial_times', {})
            for obj, answers in trial_data.items():
                if obj != 'trial_times':
                    test_by_object[obj] = {'trial_key': trial_key, 'answers': answers, 'times': test_times}
        return test_by_object

    def _build_row(self, binding_trial, binding_data, test_by_object, difficulty_ratings):
        """Build one flat dict (CSV row) for a single binding trial by merging binding and test data.
           Input:  binding_trial      - global trial number (int), e.g. 7
                   binding_data       - dict with one object entry + 'trial_times',
                                        e.g. {'cup': {'Colors': 'red', 'Scenes': 'kitchen'}, 'trial_times': {...}}
                   test_by_object     - lookup dict {object_name -> {trial_key, answers, times}}
                                        as returned by _create_test_lookup
                   difficulty_ratings - dict {trial_in_block -> difficulty rating}
           Steps:
               1. Extract binding timing data from binding_data
               2. Find the object entry in binding_data (skip 'trial_times' key)
               3. Compute block and trial_in_block indices via _calc_trial_indices
               4. Look up test results for this object from test_by_object
               5. Build base binding columns via _create_base_row
               6. Add test correctness / RT / order columns via _create_test_row
               7. Append prefixed raw timestamps from both phases (binding_<key>, test_<key>)
           Output: flat dict ready to become one CSV row, or None if binding_data had no object entry"""
        binding_times = binding_data.get(StringEnums.TRAIL_TIMES, {})

        for obj, features in binding_data.items():
            if obj == StringEnums.TRAIL_TIMES:
                continue

            block, trial_in_block = self._calc_trial_indices(binding_trial)
            test_data = test_by_object.get(obj, {})
            test_answers = test_data.get('answers', {})
            test_times = test_data.get('times', {})

            row = self._create_base_row(obj, block, binding_trial, trial_in_block, features, difficulty_ratings)
            row.update(self._create_test_row(test_data, test_answers, features, test_times))
            row.update({f'binding_{k}': v for k, v in binding_times.items()})
            row.update({f'test_{k}': v for k, v in test_times.items()})
            return row
        return None

    @staticmethod
    def _calc_trial_indices(binding_trial):
        """Convert a global trial number to (block, trial_in_block) indices."""
        trials_per_block = BindingAndTestEnums.NUMBER_OF_BINDING_TRIALS // BindingAndTestEnums.NUMBER_OF_BLOCKS
        block = (binding_trial - 1) // trials_per_block
        trial_in_block = (binding_trial - 1) % trials_per_block
        return block, trial_in_block

    def _create_base_row(self, obj, block, binding_trial, trial_in_block, features, difficulty_ratings):
        """Build the binding half of a CSV row (subject identity, trial position, shown features, difficulty)"""
        return {
            'subject': self.subject_id,
            'block': block,
            'object': obj,
            'binding_trial': binding_trial,
            'binding_trial_in_block': trial_in_block,
            Features.COLORS: features.get(Features.COLORS),
            Features.SCENES: features.get(Features.SCENES),
            'difficulty': difficulty_ratings.get(trial_in_block),
        }

    def _create_test_row(self, test_data, test_answers, features, test_times):
        """Build the test half of a CSV row (subject answers, correctness, RT, question order).
           Input:  test_data    - lookup entry for this object {trial_key, answers, times}
                   test_answers - dict of subject's test answers, e.g. {'Colors': 'blue', 'Scenes': 'kitchen'}
                   features     - dict of correct features shown in binding (used to compute correctness)
                   test_times   - timing dict from the test trial (used for RT and order)
           Steps:
               1. Compare test_answers vs features for Colors and Scenes to get color_correct / scene_correct
               2. Calculate RT in ms for each category via _calc_response_time
               3. Determine which question was presented first via _get_question_order
           Output: dict with keys: test_trial, subject_color, subject_scene,
                                   color_correct, scene_correct, both_correct,
                                   color_rt_ms, scene_rt_ms,
                                   first_question, color_question_order, scene_question_order"""
        color_correct = test_answers.get(Features.COLORS) == features.get(Features.COLORS)
        scene_correct = test_answers.get(Features.SCENES) == features.get(Features.SCENES)
        color_rt = self._calc_response_time(test_times, Features.COLORS)
        scene_rt = self._calc_response_time(test_times, Features.SCENES)
        first_q, color_order, scene_order = self._get_question_order(test_times)

        return {
            'test_trial': test_data.get('trial_key'),
            'subject_color': test_answers.get(Features.COLORS),
            'subject_scene': test_answers.get(Features.SCENES),
            'color_correct': color_correct,
            'scene_correct': scene_correct,
            'both_correct': color_correct and scene_correct,
            'color_rt_ms': color_rt,
            'scene_rt_ms': scene_rt,
            'first_question': first_q,
            'color_question_order': color_order,
            'scene_question_order': scene_order,
        }

    @staticmethod
    def _calc_response_time(test_times, category):
        """calculate response time in ms for a category"""
        start = test_times.get(f'{category}_question_appear')
        end = test_times.get(f'{category}_answer_time')
        if not start or not end:
            return None
        try:
            fmt = StringEnums.MILI_SEC_FORMAT[:-3]
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            return int(delta.total_seconds() * 1000)
        except ValueError:
            return None

    @staticmethod
    def _get_question_order(test_times):
        """determine which question was asked first"""
        color_q = test_times.get(f'{Features.COLORS}_question_appear', '')
        scene_q = test_times.get(f'{Features.SCENES}_question_appear', '')
        if not color_q or not scene_q:
            return None, None, None
        first_q = Features.COLORS if color_q < scene_q else Features.SCENES
        return first_q, 1 if first_q == Features.COLORS else 2, 1 if first_q == Features.SCENES else 2

    def _save_combined_csv(self, rows):
        """save rows to combined CSV file"""
        df = pd.DataFrame(rows)
        save_path = Path(f'subject_answer/final_data/subject_{self.subject_id}')
        save_path.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path / f'subject_{self.subject_id}_{self.time}_combined.csv', index=False)

if __name__ == '__main__':
    subject = get_subject_id()
    if subject!= "-1":
        task = BindingTask(subject_id=subject)
        task.main()

