from psychopy import visual, event, parallel
from src.enums import Features, Instruction, StringEnums, MemoryStrategyEnums
from src.binding_no_localizer_task.config import NoLocalizerConfig
from src.binding_no_localizer_task.encoding_binding import EncodingBinding
from src.binding_no_localizer_task.retrieval_binding import RetrievalBinding, PartialRetrievalBinding
from src.tools.break_game import BreakGame
from datetime import datetime
from src.tools.utils import show_instruction, get_subject_info
from pathlib import Path
import pandas as pd


class BindingNoLocalizerTask:
    def __init__(self, subject_id: str, use_parallel_port: bool = True):
        """initialize the experiment with a subject ID, psychopy window, parallel port (None if disabled), and timestamp.
           blocks, trials, objects and save folders come from NoLocalizerConfig"""
        self.subject_id = subject_id
        self.config = NoLocalizerConfig
        self.win = visual.Window(fullscr=True)
        self.parallel_port = parallel.ParallelPort(address=0x5EFC) if use_parallel_port else None
        self.time = datetime.now().strftime(StringEnums.MINUTE_FORMAT)
        self.category = Features.BINDING_CATEGORIES

    def main(self):
        """run the experiment: welcome, binding learning + test blocks, combined CSV,
           partial retrieval test, memory strategy questionnaire, goodbye"""
        event.Mouse(visible=False)
        show_instruction(win=self.win, instruction=Instruction.WELLCOME)
        binding, test = self._learning_and_test_stage()
        self._save_unified_file_for_all_data(binding=binding, test=test)
        self._partial_retrival_stage()
        self._ask_memory_strategy()
        show_instruction(win=self.win, instruction=Instruction.GOODBYE, time=10)

    def _learning_and_test_stage(self):
        """init binding learning and test phase, run examples and all blocks, save results"""
        show_instruction(win=self.win, instruction=Instruction.SECOND_PHASE_INSTRUCTION)
        binding = EncodingBinding(win=self.win, parallel_port=self.parallel_port, categories=self.category,
                                  subject_id=self.subject_id)
        test = RetrievalBinding(win=self.win, parallel_port=self.parallel_port, categories=self.category,
                                objects=binding.objects, subject_id=self.subject_id)
        self._run_examples(binding=binding, test=test)
        for block_idx in range(self.config.NUMBER_OF_BLOCKS):
            self._block_learning_and_test(binding=binding, test=test, block=block_idx)
        self._save_learning_and_test(binding=binding, test=test)
        return binding, test

    def _run_examples(self, binding: EncodingBinding, test: RetrievalBinding):
        """run binding, break game and test examples"""
        binding.run_examples()
        BreakGame(win=self.win, parallel_port=self.parallel_port).run_example()
        test.run_examples()
        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)

    def _save_learning_and_test(self, binding: EncodingBinding, test: RetrievalBinding):
        """save binding and test results and show end-of-stage instruction"""
        binding.save_subject(time=self.time)
        test.save_subject_answer(time=self.time)
        show_instruction(win=self.win, instruction=Instruction.SECOND_PHASE_END, call_experimenter=True)

    def _block_learning_and_test(self, binding: EncodingBinding, test: RetrievalBinding, block: int):
        """run one block: block instruction, binding learning, break game, test phase"""
        show_instruction(win=self.win, instruction=(Instruction.START_X_BLOCK + str(block + 1) + "/" + str(self.config.NUMBER_OF_BLOCKS)))
        binding.run_block(block_index=block)
        BreakGame(win=self.win, parallel_port=self.parallel_port).run()
        show_instruction(win=self.win, instruction=Instruction.BEFORE_TEST_PHASE)
        test.run_block(block_index=block)

    def _partial_retrival_stage(self):
        """run partial retrieval test on the objects correctly retrieved in the test phase"""
        show_instruction(win=self.win, instruction=Instruction.THIRD_STAGE_INSTRUCTION)
        partial_retrival = PartialRetrievalBinding(win=self.win, parallel_port=self.parallel_port,
                                                   categories=self.category, subject_id=self.subject_id)
        partial_retrival.run_examples()
        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)
        partial_retrival.run()
        partial_retrival.save_subject_answer(time=self.time)

    def _ask_memory_strategy(self) -> None:
        """show memory strategy sliders until all are rated and a key is pressed, then save"""
        event.Mouse(visible=True)
        title, labels, sliders = self._build_strategy_ui()
        confirm = visual.TextStim(self.win, text="לחץ על כל מקש לאישור", pos=(0, -0.85),
                                  font=StringEnums.ARIAL_FONT, languageStyle='rtl')
        while not self._draw_strategy_frame(title, labels, sliders, confirm):
            pass
        self._save_strategy(dict(zip(self._strategy_questions(), [s.rating for s in sliders])))

    def _draw_strategy_frame(self, title, labels, sliders, confirm) -> bool:
        """draw one frame of the strategy UI, return True when all rated and a key was pressed"""
        for stim in [title, *labels, *sliders]:
            stim.draw()
        all_rated = all(s.rating is not None for s in sliders)
        if all_rated:
            confirm.draw()
        confirmed = all_rated and bool(event.getKeys())
        self.win.flip()
        return confirmed

    @staticmethod
    def _strategy_questions() -> list:
        """memory strategy questions, in display order"""
        return [MemoryStrategyEnums.VISUALIZATION_MEMORY, MemoryStrategyEnums.SEMANTIC_MEMORY,
                MemoryStrategyEnums.ASSOCIATION_MEMORY]

    def _build_strategy_ui(self):
        """build title, question labels and 1-10 sliders for the memory strategy questionnaire"""
        title = visual.TextStim(self.win, text=MemoryStrategyEnums.TITLE, pos=(0, 0.9),
                                height=0.06, languageStyle='rtl', font=StringEnums.ARIAL_FONT)
        labels, sliders = [], []
        for q, y in zip(self._strategy_questions(), [0.55, 0.0, -0.55]):
            labels.append(visual.TextStim(self.win, text=q, pos=(0, y + 0.15), height=0.05,
                                          languageStyle='rtl', font=StringEnums.ARIAL_FONT))
            sliders.append(visual.Slider(self.win, ticks=range(1, 11), labels=['1', '10'],
                                         granularity=1, style='rating', pos=(0, y), size=(1.2, 0.07)))
        return title, labels, sliders

    def _save_strategy(self, ratings: dict) -> None:
        """save memory strategy ratings to CSV"""
        save_path = Path(f"{self.config.SAVE_DATA_FOLDER}subject_{self.subject_id}/strategy/")
        save_path.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([ratings]).to_csv(save_path / f"strategy_{self.subject_id}.csv", index=False)

    def _save_unified_file_for_all_data(self, binding: EncodingBinding, test: RetrievalBinding):
        """save one combined CSV with one row per binding trial, merging binding and test data"""
        test_by_object = self._create_test_lookup(test)
        rows = [self._build_row(binding_trial, binding_data, test_by_object, binding.difficulty_ratings)
                for binding_trial, binding_data in binding.answers.items()]
        self._save_combined_csv([row for row in rows if row])

    @staticmethod
    def _create_test_lookup(test: RetrievalBinding):
        """create lookup dict {object_name: {trial_key, answers, times}} from test answers"""
        test_by_object = {}
        for trial_key, trial_data in test.subject_answers.items():
            test_times = trial_data.get(StringEnums.TRAIL_TIMES, {})
            for obj, answers in trial_data.items():
                if obj != StringEnums.TRAIL_TIMES:
                    test_by_object[obj] = {'trial_key': trial_key, 'answers': answers, 'times': test_times}
        return test_by_object

    def _build_row(self, binding_trial, binding_data, test_by_object, difficulty_ratings):
        """build one flat CSV row for a binding trial merged with its test results, or None if no object entry"""
        binding_times = binding_data.get(StringEnums.TRAIL_TIMES, {})
        for obj, features in binding_data.items():
            if obj == StringEnums.TRAIL_TIMES:
                continue
            test_data = test_by_object.get(obj, {})
            row = self._create_base_row(obj, binding_trial, features, difficulty_ratings)
            row.update(self._create_test_row(test_data, test_data.get('answers', {}), features, test_data.get('times', {})))
            row.update({f'binding_{k}': v for k, v in binding_times.items()})
            row.update({f'test_{k}': v for k, v in test_data.get('times', {}).items()})
            return row
        return None

    def _calc_trial_indices(self, binding_trial):
        """convert a global trial number to (block, trial_in_block) indices"""
        trials_per_block = self.config.NUMBER_OF_TRIALS // self.config.NUMBER_OF_BLOCKS
        return (binding_trial - 1) // trials_per_block, (binding_trial - 1) % trials_per_block

    def _create_base_row(self, obj, binding_trial, features, difficulty_ratings):
        """build the binding half of a CSV row (subject, trial position, shown features, difficulty)"""
        block, trial_in_block = self._calc_trial_indices(binding_trial)
        return {
            'subject': self.subject_id,
            'block': block,
            'object': obj,
            'binding_trial': binding_trial,
            'binding_trial_in_block': trial_in_block,
            Features.COLORS: features.get(Features.COLORS),
            Features.SCENES: features.get(Features.SCENES),
            'difficulty': difficulty_ratings.get(binding_trial),
        }

    def _create_test_row(self, test_data, test_answers, features, test_times):
        """build the test half of a CSV row (subject answers, correctness, RT, question order)"""
        color_correct = test_answers.get(Features.COLORS) == features.get(Features.COLORS)
        scene_correct = test_answers.get(Features.SCENES) == features.get(Features.SCENES)
        first_q, color_order, scene_order = self._get_question_order(test_times)
        return {
            'test_trial': test_data.get('trial_key'),
            'subject_color': test_answers.get(Features.COLORS),
            'subject_scene': test_answers.get(Features.SCENES),
            'color_correct': color_correct,
            'scene_correct': scene_correct,
            'both_correct': color_correct and scene_correct,
            'color_rt_ms': self._calc_response_time(test_times, Features.COLORS),
            'scene_rt_ms': self._calc_response_time(test_times, Features.SCENES),
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
            return int((datetime.strptime(end, fmt) - datetime.strptime(start, fmt)).total_seconds() * 1000)
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
        save_path = Path(f'{self.config.SAVE_DATA_FOLDER}subject_{self.subject_id}/combined_data')
        save_path.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(save_path / f'subject_{self.subject_id}_{self.time}_combined.csv', index=False)


if __name__ == '__main__':
    subject, use_parallel = get_subject_info()
    if subject != "-1":
        task = BindingNoLocalizerTask(subject_id=subject, use_parallel_port=use_parallel)
        task.main()
