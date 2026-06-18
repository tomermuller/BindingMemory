from psychopy import visual, event, parallel
from src.enums import Instruction, StringEnums, ExperimentType, RealTimeTaskEnums, \
    RealTimeInstruction
from src.tools.break_game import BreakGame
from src.tools.functional_localizer import FunctionalLocalizer
from src.real_time_task.couple_learning import CoupleLearning
from src.real_time_task.retrival_couple import RetrivalCouple
from datetime import datetime
from src.tools.utils import show_instruction, get_subject_info


class RealTimeTask:
    def __init__(self, subject_id: str, use_parallel_port: bool = True):
        """initialize the experiment with a subject ID, psychopy window, parallel port, and timestamp"""
        self.subject_id = subject_id
        self.win = visual.Window(fullscr=True)
        self.parallel_port = parallel.ParallelPort(address=0x5EFC) if use_parallel_port else None
        self.time = datetime.now().strftime(StringEnums.MINUTE_FORMAT)

    def main(self):
        """run the experiment:
                    1. general settings (hide mouse)
                    2. welcome instruction
                    3. first stage - functional localizer
                    4. second stage - binding learning + test phase (5 blocks)
                    5. save unified combined CSV
                    6. third stage - partial retrieval test
                    7. goodbye instruction"""
        self._general_setting()
        show_instruction(win=self.win, instruction=RealTimeInstruction.WELLCOME)
        categories = ["animacy"]
        self._functional_localizer(categories=categories)
        self._main_task(categories=categories)
        show_instruction(win=self.win, instruction=Instruction.GOODBYE, time=10)

    @staticmethod
    def _general_setting():
        """set setting for experiment:
            1. disappear the mouse"""
        event.Mouse(visible=False)

    def _functional_localizer(self, categories: list):
        """the first part of the experiment:
            1. show the instruction to the first part
            2. init and call run func of FunctionalLocalizer"""
        show_instruction(win=self.win, instruction=Instruction.FIRST_PHASE_INSTRUCTION)
        functional_localizer = FunctionalLocalizer(categories=categories, win=self.win,
                                                   parallel_port=self.parallel_port, subject_id=self.subject_id,
                                                   exp=ExperimentType.REAL_TIME)
        functional_localizer.run()
        functional_localizer.save_results(time=self.time)
        show_instruction(win=self.win, instruction=Instruction.FIRST_PHASE_END, call_experimenter=True)


    def _main_task(self, categories: list):
        couple_learning = CoupleLearning(win=self.win, parallel_port=self.parallel_port,
                                         categories=categories, subject_id=self.subject_id,
                                         verb_list=RealTimeTaskEnums.VERB_LIST)
        retrival_couple = RetrivalCouple(win=self.win, parallel_port=self.parallel_port,
                                         subject_id=self.subject_id,
                                         verb_list=RealTimeTaskEnums.VERB_LIST, categories=categories)
        self._main_task_example(couple_learning=couple_learning, retrival_couple=retrival_couple)

        for block_idx in range(RealTimeTaskEnums.NUMBER_OF_BLOCKS):
            show_instruction(win=self.win, instruction=(
                        Instruction.START_X_BLOCK + str(block_idx + 1) + "/" + str(RealTimeTaskEnums.NUMBER_OF_BLOCKS)))

            couple_learning.run_block()
            #BreakGame(win=self.win, parallel_port=self.parallel_port).run()
            couple_learning.run_block()
            BreakGame(win=self.win, parallel_port=self.parallel_port).run()
            retrival_couple.run_block()

        couple_learning.save_subject(self.time)
        retrival_couple.save_subject(self.time)

    def _main_task_example(self, couple_learning: CoupleLearning, retrival_couple: RetrivalCouple):
        couple_learning.run_examples()
        BreakGame(win=self.win, parallel_port=self.parallel_port).run_example()
        retrival_couple.run_examples()
        show_instruction(win=self.win, instruction=Instruction.FINISH_EXAMPLES)


if __name__ == '__main__':
    subject, use_parallel = get_subject_info()
    if subject != "-1":
        task = RealTimeTask(subject_id=subject, use_parallel_port=use_parallel)
        task.main()
