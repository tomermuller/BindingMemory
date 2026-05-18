from psychopy import parallel, visual
from src.binding_task.enums.Enums import StringEnums, ParallelPortEnums, Instruction
from src.binding_task.utils import show_instruction, send_to_parallel_port, show_fixation, show_nothing

THREE_MINUTES = 180

win = visual.Window(fullscr=True)
parallel_port = parallel.ParallelPort(address=0x5EFC)
show_instruction(win=win, instruction=Instruction.REST_RECORD)
send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.START_RECORD_REST)
show_fixation(win=win, min_time=THREE_MINUTES, max_time=THREE_MINUTES)
send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.REST_NO_FIXATION)
show_nothing(win=win, min_time=THREE_MINUTES, max_time=THREE_MINUTES)
