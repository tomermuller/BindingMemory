from pathlib import Path

class StringEnums:
    NUMBER_OF_TRIALS_PER_FEATURE = 4
    Y = 'y'
    N = 'n'
    FEATURE = 'feature'
    WORD_QUESTION = 'word_question'
    USER_ANSWER = 'user_answer'
    IS_RIGHT = 'is_right'
    TRIAL_INDEX = 'trial_index'
    TRAIL_TIMES = 'trial_times'
    SUBJECT = 'subject'
    MINUTE_FORMAT = "%m/%d/%Y %I:%M"
    MILI_SEC_FORMAT = "%Y-%m-%d_%H-%M-%S.%f"
    TRUE = "true"
    WRONG = "wrong"
    RIGHT = "right"
    LEFT = "left"
    KEY_OPTIONS_FUNCTIONAL_LOCALIZER = [RIGHT, LEFT]


class Features:
    SCENES = 'scenes'
    COLORS = 'colors'
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    LIVING_ROOM = 'living_room'
    BATHROOM = 'bathroom'
    KITCHEN = 'kitchen'
    FUNCTIONAL_LOCALIZER_EXAMPLES = [(YELLOW, YELLOW, True),
                                     (LIVING_ROOM, KITCHEN, False)]

    ALL_CATEGORIES = [COLORS, SCENES]


    COLOR_TO_RGBA = {RED: (255,0,0), BLUE : (0,0,255), GREEN : (0,255,0), YELLOW : (255,255,0)}

    COLOR_TO_IMAGE = {
        RED: Path(f'features/colors/{RED}_image.png'),
        GREEN: Path(f'features/colors/{GREEN}_image.png'),
        YELLOW: Path(f'features/colors/{YELLOW}_image.png')
    }

    SCENE_TO_IMAGE = {LIVING_ROOM: Path(f"features/scenes/{LIVING_ROOM}_image.png"),
                      BATHROOM: Path(f"features/scenes/{BATHROOM}_image.png"),
                      KITCHEN: Path(f"features/scenes/{KITCHEN}_image.png")}


    IMAGE_TO_FEATURE = {Path(f'features/colors/{RED}_image.png'): RED,
                        Path(f'features/colors/{GREEN}_image.png'): GREEN,
                        Path(f'features/colors/{YELLOW}_image.png'): YELLOW,
                        Path(f'features/scenes/{BATHROOM}_image.png'): BATHROOM,
                        Path(f'features/scenes/{LIVING_ROOM}_image.png'): LIVING_ROOM,
                        Path(f'features/scenes/{KITCHEN}_image.png'): KITCHEN}

    CATEGORY_TO_FEATURES = {SCENES: SCENE_TO_IMAGE, COLORS: COLOR_TO_IMAGE}

    FEATURE_TO_WORDS = {BLUE: [BLUE],
                        GREEN: [GREEN],
                        YELLOW: [YELLOW],
                        RED: [RED],
                        LIVING_ROOM: [LIVING_ROOM],
                        BATHROOM: [BATHROOM],
                        KITCHEN: [KITCHEN]}


class Messages:
    START = "welcome, this study have 2 parts"

    FIRST_PART_MESSAGE = ("in this part you will see 8 repeats features. \n"
                          "after each of them you will see a word and you will need to decide if the word related to "
                          "the feature or not")


class ParallelPortEnums:
    SHOW_RED = 21
    SHOW_GREEN = 23
    SHOW_YELLOW = 24
    STOP_RED = 31
    STOP_GREEN = 33
    STOP_YELLOW = 34

    SHOW_LIVING_ROOM = 41
    SHOW_BATHROOM = 42
    SHOW_KITCHEN = 43
    STOP_LIVING_ROOM = 51
    STOP_BATHROOM = 52
    STOP_KITCHEN = 53

    SHOW_BINDING_TRIALS = 61
    SHOW_ATTENTION_QUESTION = 62
    SHOW_COLOR_QUESTION = 63
    SHOW_SCENE_QUESTION = 64
    SHOW_DIFFICULTY_QUESTION = 65
    SHOW_COLORS_ANSWERS = 66
    SHOW_SCENES_ANSWERS = 67
    SHOW_OBJECT_IN_TEST_TRIAL = 68

    STOP_BINDING_TRIALS = 71
    STOP_ATTENTION_QUESTION = 72
    STOP_COLOR_QUESTION = 73
    STOP_SCENE_QUESTION = 74
    STOP_DIFFICULTY_QUESTION = 75
    STOP_OBJECT_IN_TEST_TRIAL = 78

    ANSWER_ATTENTION_QUESTION = 82
    ANSWER_COLOR_QUESTION = 83
    ANSWER_SCENE_QUESTION = 84
    ANSWER_DIFFICULTY_QUESTION = 85

    START_BREAK = 91
    STOP_BREAK = 92

    FEATURE_SHOW_TO_PULSE_CODE = {Features.GREEN: SHOW_GREEN,
                                  Features.YELLOW: SHOW_YELLOW,
                                  Features.RED: SHOW_RED,
                                  Features.LIVING_ROOM: SHOW_LIVING_ROOM,
                                  Features.BATHROOM: SHOW_BATHROOM,
                                  Features.KITCHEN: SHOW_KITCHEN}

    FEATURE_STOP_TO_PULSE_CODE = {Features.GREEN: STOP_GREEN,
                                  Features.YELLOW: STOP_YELLOW,
                                  Features.RED: STOP_RED,
                                  Features.LIVING_ROOM: STOP_LIVING_ROOM,
                                  Features.BATHROOM: STOP_BATHROOM,
                                  Features.KITCHEN: STOP_KITCHEN}

    CATEGORY_QUESTION_SHOW_TO_PULSE_CODE = {Features.SCENES: SHOW_SCENE_QUESTION,
                                            Features.COLORS: SHOW_COLOR_QUESTION}

    CATEGORY_QUESTION_STOP_TO_PULSE_CODE = {Features.SCENES: STOP_SCENE_QUESTION,
                                            Features.COLORS: STOP_COLOR_QUESTION}

    CATEGORY_ANSWERS_SHOW_TO_PULSE_CODE = {Features.SCENES: SHOW_SCENES_ANSWERS,
                                            Features.COLORS: SHOW_COLORS_ANSWERS}

    CATEGORY_QUESTION_ANSWER_TO_PULSE_CODE = {Features.SCENES: ANSWER_SCENE_QUESTION,
                                            Features.COLORS: ANSWER_COLOR_QUESTION}


class Instruction:
    WELLCOME = ("ברוך הבא/ה לניסוי!\n"
                "המחקר מורכב מ2 שלבים\n"
                "בשלב הראשון תראה/י תמונות חוזרות על עצמן ותצטרך/י לענות על שאלה אחרי כל תמונה.\n"
                "בשלב השני תראה/י אובייקטים בצבעים ומקומות ותצטרך/י לזכור איזה אובייקט הופיעו היכן ומהו צבעם.")

    FIRST_PHASE_INSTRUCTION = ("\nבשלב הראשון תראה/י תמונות החוזרות על עצמן. אחרי כל תמונה תופיע מילה"
                               "\n ותצטרך/י ללחוץ על המקש החץ שיתאר האם המילה מתארת את התמונה או לא."
                               "\nאך לפני הנה 2 דוגמאות:"
                               "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")
    MISTAKE = "טעות! שים לב עליך לבחור האם המילה מתארת את התמונה שראית"

    FIRST_PHASE_END = ("כל הכבוד! סיימת את השלב הראשון בניסוי.\n"
                       "לחץ/י על כל כפתור כדי להמשיך לשלב הבא. ")

    SECOND_PHASE_INSTRUCTION = ("כעת בשלב השני יופיעו לך 5 בלוקים. כל בלוק מורכב מ2 חלקים שביניהם משחקון.\n"
                                "בחלק הראשון תראה/י אובייקטים בצבע בסצנה ותצטרך/י לזכור אותם.\n"
                                "בחלק השני תצטרך/י להתאים לכל אובייקט באיזה צבע ובאיזו סצנה הוא הופיע.\n"
                                "אך לפני הנה 2 דוגמאות:\n"
                                "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")

    START_X_BLOCK = "לחץ על כל מקש על מנת להתחיל את הבלוק ה "

    DIFFICULT_QUESTION = ("עד כמה קשה היה לך לזכור את הצבע והמיקום של האובייקט?\n"
                         "1 (קל) – 5 (קשה)")

    BREAK_GAME_INSTRUCTION = ("להלן משחקון של דקה וחצי: הריבוע המשתנה.\n"
                              "כל כמה שניות הריבוע יהפוך להיות כהה או בהיר יותר ויחזור למצב ההתחלה.\n"
                              "עליך לספור כמה פעמים הריבוע הופך להיות בהיר יותר מאשר מצבו בהתחלה.\n"
                              "אנא לחץ/י על כל כפתור כדי להתחיל.")

    BREAK_GAME_QUESTION = "כמה פעמים הקיבוע הפך לבהיר יותר?"

    BREAK_GAME_FINISH = ("סיימת את המשחקון. ברוך הבא לשלב המבחן.\n"
                         "לחץ/י על כל כפתור כדי להתחיל")

    FINISH_EXAMPLES = ("סיימת את הדוגמאות! כעת מתחיל השלב האמיתי.\n"
                       "אנא לחץ/י על כל כפתור כדי להתחיל בניסוי.")

    BREAK = "הפסקה!\n אנא לחץ/י על כל כפתור כאשר אתה מוכן לחזור לניסוי."

    GOODBYE = ("תודה רבה על השתתפותך בניסוי. נא לקרוא למריץ הניסוי. ניתן לשאול אותו/ה שאלות על הניסויֿ")


class BreakGameEnums:
    GAME_DURATION = 100  # seconds
    CHANGE_INTERVAL = 10  # seconds
    BASE_BRIGHTNESS = 0.5
    TRIAL_CHANGE = 0.2


class Paths:
    OBJECT_EXAMPLE_FORK = "features/object example/fork.png"
    OBJECT_EXAMPLE_ROBOT = "features/object example/robot.png"
    BINDING_EXAMPLE = "features/binding_photos/example.png"


class BindingAndTestEnums:
    NUMBER_OF_BLOCKS = 5
    NUMBER_OF_BINDING_TRIALS = 45
    BINDING_EXAMPLES  = zip([Path(Paths.OBJECT_EXAMPLE_FORK), Path(Paths.OBJECT_EXAMPLE_ROBOT)],
                            [Features.COLOR_TO_RGBA[Features.YELLOW], Features.COLOR_TO_RGBA[Features.RED]],
                            [Features.SCENE_TO_IMAGE[Features.KITCHEN], Features.SCENE_TO_IMAGE[Features.LIVING_ROOM]])

    DIFFICULT_RANGE = ["1", "2", "3", "4", "5"]
    ARROW_TO_LOCATION = {'up': 0, 'left': 1, 'right': 2}


class TimeAttribute:
    FEATURE_APPEAR = "feature_appear"
    FEATURE_DISAPPEAR = "feature_disappear"
    QUESTION_APPEAR = "question_appear"
    ANSWER_TIME = "answer_time"
    OBJECT_APPEAR = "object_appear"
    OBJECT_DISAPPEAR = "object_disappear"



