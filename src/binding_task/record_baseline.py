from psychopy import parallel, visual, core
from src.enums import ParallelPortEnums, Instruction
from src.tools.utils import show_instruction, send_to_parallel_port, show_fixation, show_nothing, get_subject_info

subject, use_parallel = get_subject_info()
if subject != "-1":
    win = visual.Window(fullscr=True)
    parallel_port = parallel.ParallelPort(address=0x5EFC) if use_parallel else None
    show_instruction(win=win, instruction=Instruction.REST_RECORD)

    send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.REST_FIXATION_START)
    show_fixation(win=win, min_time=ParallelPortEnums.REST_DURATION, max_time=ParallelPortEnums.REST_DURATION)
    send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.REST_FIXATION_END)

    core.wait(1.0)

    send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.REST_NO_FIXATION_START)
    show_nothing(win=win, min_time=ParallelPortEnums.REST_DURATION, max_time=ParallelPortEnums.REST_DURATION)
    send_to_parallel_port(parallel_port=parallel_port, pulse_number=ParallelPortEnums.REST_NO_FIXATION_END)
