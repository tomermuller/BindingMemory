from psychopy import parallel, visual
from src.binding_task.enums.Enums import StringEnums, ParallelPortEnums, Instruction
from src.binding_task.utils import show_instruction, send_to_parallel_port, show_fixation

win = visual.Window(fullscr=True)
parallel_port = parallel.ParallelPort(address=0x5EFC)
show_instruction(win=win, instruction=Instruction.BASELINE)
send_to_parallel_port(parallel_port=parallel_port,pulse_number=ParallelPortEnums.START_RECORD_BASELINE)
show_fixation(win=win, min_time=StringEnums.FIVE_MINUTES, max_time=StringEnums.FIVE_MINUTES)
