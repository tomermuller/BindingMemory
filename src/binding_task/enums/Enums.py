from pathlib import Path

class TaskManage:
    NUMBER_OF_TRIALS_PER_FEATURE = 70
    NUMBER_OF_BLOCKS = 5
    NUMBER_OF_BINDING_TRIALS = 45


class Paths:
    OBJECT_EXAMPLE_FORK = "features/object example/fork.png"
    OBJECT_EXAMPLE_ROBOT = "features/object example/robot.png"
    BINDING_EXAMPLE = "features/binding_photos/example.png"
    SAVE_DATA_FOLDER = "subject_answer/final_data/"
    SAVE_TEMP_FOLDER = "subject_answer/temp/"

    OBJECTS_PATH = "features/objects"
    BINDING_PHOTOS_FOLDER = "features/binding_photos/"

    COLOR_PROBE_PATH = "features/probes/color probe.jpeg"
    SCENE_PROBE_PATH = "features/probes/scene probe.jpeg"

    COLORS_IMAGE_PATH = 'features/colors/{}_image.png'
    SCENE_IMAGE_PATH = 'features/scenes/{}_image.png'

    OBJECT_PATH = 'features/objects/{}.png'


class StringEnums:
    Y = 'y'
    N = 'n'
    FEATURE = 'feature'
    WORD_QUESTION = 'word_question'
    USER_ANSWER = 'user_answer'
    IS_RIGHT = 'is_right'
    TRIAL_INDEX = 'trial_index'
    TRAIL_TIMES = 'trial_times'
    SUBJECT = 'subject'
    MINUTE_FORMAT = "%m-%d-%Y_%H-%M"
    MILI_SEC_FORMAT = "%Y-%m-%d_%H-%M-%S.%f"
    RIGHT = "right"
    LEFT = "left"
    UP = "up"
    DOWN = "down"
    KEY_OPTIONS_FUNCTIONAL_LOCALIZER = [RIGHT, LEFT]
    ARIAL_FONT = "Arial"
    TRUE_ANSWERS = "true_answers"
    SUBJECT_ANSWER = "subject_answer"
    QUESTION_APPEAR = "question_appear"
    TRIAL = "trial"
    OBJECTS = "objects"
    BLOCK = "block"
    RETRIVAL_SUCCESS = "retrival_success"
    BOTH_CORRECT = "both_correct"
    RETRIVAL_REPORT_COLOR = "retrival_report_color"
    RETRIVAL_REPORT_SCENE = "retrival_report_scene"
    TEXT = "text"
    LIST = "list"
    LOCATION = "location"
    IS_REMEMBER = "is_remember"
    PROBE = "probe"
    SUBJECT_ID = "subject_id"
    DAY = "day"
    EXPERIMENT_TITLE = "remember_experiment"
    FIVE_MINUTES = 300


class Features:
    OBJECT = "object"
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
        RED: Path(Paths.COLORS_IMAGE_PATH.format(RED)),
        GREEN: Path(Paths.COLORS_IMAGE_PATH.format(GREEN)),
        YELLOW: Path(Paths.COLORS_IMAGE_PATH.format(YELLOW))
    }

    SCENE_TO_IMAGE = {LIVING_ROOM: Path(Paths.SCENE_IMAGE_PATH.format(LIVING_ROOM)),
                      BATHROOM: Path(Paths.SCENE_IMAGE_PATH.format(BATHROOM)),
                      KITCHEN: Path(Paths.SCENE_IMAGE_PATH.format(KITCHEN))}


    IMAGE_TO_FEATURE = {Path(Paths.COLORS_IMAGE_PATH.format(RED)): RED,
                        Path(Paths.COLORS_IMAGE_PATH.format(GREEN)): GREEN,
                        Path(Paths.COLORS_IMAGE_PATH.format(YELLOW)): YELLOW,
                        Path(Paths.SCENE_IMAGE_PATH.format(BATHROOM)): BATHROOM,
                        Path(Paths.SCENE_IMAGE_PATH.format(LIVING_ROOM)): LIVING_ROOM,
                        Path(Paths.SCENE_IMAGE_PATH.format(KITCHEN)): KITCHEN}

    CATEGORY_TO_FEATURES = {SCENES: SCENE_TO_IMAGE, COLORS: COLOR_TO_IMAGE}

    FEATURE_TO_WORDS = {BLUE: [BLUE],
                        GREEN: [GREEN],
                        YELLOW: [YELLOW],
                        RED: [RED],
                        LIVING_ROOM: [LIVING_ROOM],
                        BATHROOM: [BATHROOM],
                        KITCHEN: [KITCHEN]}

    PROBE_TO_PATH = {COLORS: Paths.COLOR_PROBE_PATH,
                     SCENES: Paths.SCENE_PROBE_PATH}


class HebrewEnums:
    RED = 'אדום'
    BLUE = 'כחול'
    GREEN = 'ירוק'
    YELLOW = 'צהוב'
    LIVING_ROOM = 'סלון'
    BATHROOM = 'שירותים'
    KITCHEN = 'מטבח'
    TRANSLATE = {
        Features.RED: RED,
        Features.BLUE: BLUE,
        Features.GREEN: GREEN,
        Features.YELLOW: YELLOW,
        Features.LIVING_ROOM: LIVING_ROOM,
        Features.BATHROOM: BATHROOM,
        Features.KITCHEN: KITCHEN
    }

    NOTHING = 'כלום'
    COLOR = 'צבע'
    SCENE = 'חדר'
    BOTH = 'צבע וחדר'
    TRUE = "נכון"
    WRONG = "לא נכון"
    REMEMBER = "זוכר"
    NOT_REMEMBER = "לא זוכר"


class ParallelPortEnums:

    # general
    START_RECORD_BASELINE = 1

    # functional localizer parallel port numbers
    SHOW_RED = 11
    SHOW_GREEN = 12
    SHOW_YELLOW = 13

    SHOW_LIVING_ROOM = 16
    SHOW_BATHROOM = 17
    SHOW_KITCHEN = 18

    SHOW_ATTENTION_QUESTION = 31
    ANSWER_ATTENTION_QUESTION = 32

    # binding learning parallel port numbers
    SHOW_BINDING_TRIALS = 41
    SHOW_DIFFICULTY_QUESTION = 43
    ANSWER_DIFFICULTY_QUESTION = 44

    # test phase parallel port numbers
    SHOW_OBJECT_IN_TEST_TRIAL = 51
    START_RETRIVAL_TIME = 53
    ANSWER_ON_RETRIVAL_TIME = 54
    SHOW_RETRIVAL_QUESTION = 55
    ANSWER_RETRIVAL_QUESTION = 56

    SHOW_COLORS_ANSWERS = 61
    ANSWER_COLOR_QUESTION = 62
    SHOW_SCENES_ANSWERS = 66
    ANSWER_SCENE_QUESTION = 67

    FEATURE_SHOW_TO_PULSE_CODE = {Features.GREEN: SHOW_GREEN,
                                  Features.YELLOW: SHOW_YELLOW,
                                  Features.RED: SHOW_RED,
                                  Features.LIVING_ROOM: SHOW_LIVING_ROOM,
                                  Features.BATHROOM: SHOW_BATHROOM,
                                  Features.KITCHEN: SHOW_KITCHEN}

    CATEGORY_ANSWERS_SHOW_TO_PULSE_CODE = {Features.SCENES: SHOW_SCENES_ANSWERS,
                                            Features.COLORS: SHOW_COLORS_ANSWERS}

    CATEGORY_QUESTION_ANSWER_TO_PULSE_CODE = {Features.SCENES: ANSWER_SCENE_QUESTION,
                                            Features.COLORS: ANSWER_COLOR_QUESTION}

    # partial retrieval phase parallel port numbers
    SHOW_PROBE = 71
    SHOW_PARTIAL_RETRIVAL_REMEMBER_QUESTION = 73
    ANSWER_PARTIAL_RETRIVAL_REMEMBER_QUESTION = 74


class Instruction:
    WELLCOME = ("ברוך הבא/ה לניסוי!\n"
                "הניסוי מורכב מ3 שלבים:\n\n"
                "1.שלב התמונות החוזרות- צבעים וחדרים.\n"
                "2.שלב הלמידה והמבחן.\n"
                "3.שלב המבחן החלקי.\n\n"
                "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")

    BASELINE = ("אך קודם, ב5 דקות הקרובות אנחנו נקליט את גלי המוח שלך במצב מנוחה\n"
                "אנא השתדל להתמקד ב + שיופיע על המסך. לאחר מכן יתחיל הניסוי\n\n"
                "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")


    FIRST_PHASE_INSTRUCTION = ("\n\nבשלב הראשון תראה/י תמונות החוזרות על עצמן."
                               "\n\nאחרי כל תמונה תופיע מילה."
                               "\n\n באמצעות מקשי החצים במקלדת תצטרך לבחור האם המילה מתארת את התמונה או לא."
                               "\n\nאך לפני הנה 2 דוגמאות:"
                               "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")

    SECOND_PHASE_INSTRUCTION = ("כעת השלב השני מחולק לכ 5 בלוקים. כל בלוק מורכב מ2 חלקים שביניהם משחקון.\n"
                                "תחילה תראה אובייקטים בצבע בחדר ואחר כך תצטרך לענות באיזה צבע וחדר הופיע כל אובייקט.\n"
                                "אך לפני הנה 2 דוגמאות:\n"
                                "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")

    THIRD_STAGE_INSTRUCTION = ("ברוך הבא לחלק השלישי בניסוי!\n"
                               "בחלק הזה בתחילת כל סיבוב יופיע סימון של צבע או חדר\n"
                               "תצטרכ/י לענות רק עבור הסימון שיופיע.\n"
                               "אך לפני הנה 2 דוגמאות:\n"
                               "(אנא לחץ/י על כל כפתור כדי להתחיל את הדוגמאות)")

    BREAK_GAME_INSTRUCTION = ("להלן משחקון של דקה וחצי: המלבן המשתנה.\n"
                              "כל כמה שניות המלבן יהפוך להיות כהה או בהיר יותר ויחזור למצב ההתחלה.\n"
                              "עליך לספור כמה פעמים המלבן הופך להיות בהיר יותר מאשר מצבו בהתחלה.\n"
                              "אנא לחץ/י על כל כפתור כדי להתחיל.")

    BREAK_GAME_EXAMPLE_INSTRUCTION = ("להלן משחקון של כ10 שניות: המלבן המשתנה.\n"
                              "כל כמה שניות המלבן יהפוך להיות כהה או בהיר יותר ויחזור למצב ההתחלה.\n"
                              "עליך לספור כמה פעמים המלבן הופך להיות בהיר יותר מאשר מצבו בהתחלה.\n"
                              "אנא לחץ/י על כל כפתור כדי להתחיל.")

    MISTAKE = "טעות! שים לב עליך לבחור האם המילה מתארת את התמונה שראית"

    FIRST_PHASE_END = ("כל הכבוד! סיימת את השלב הראשון בניסוי.\n"
                       "לחץ/י על כל כפתור כדי להמשיך לשלב הבא. ")

    SECOND_PHASE_END = ("כל הכבוד! סיימת את השלב השני בניסוי.\n"
                        "לחץ/י על כל כפתור כדי להמשיך לשלב הבא. ")

    START_X_BLOCK = "לחץ על כל מקש על מנת להתחיל את הבלוק ה "

    DIFFICULT_QUESTION = ("עד כמה קשה היה לך לזכור את הצבע והחדר של האובייקט?\n"
                         "5 (קשה) – 1 (קל)")

    BREAK_GAME_QUESTION = "כמה פעמים המלבן הפך לבהיר יותר?"

    BREAK_GAME_FINISH = ("סיימת את המשחקון. ברוך הבא לשלב המבחן.\n"
                         "לחץ/י על כל כפתור כדי להתחיל")

    FINISH_EXAMPLES = ("סיימת את הדוגמאות! כעת מתחיל השלב האמיתי.\n"
                       "אנא לחץ/י על כל כפתור כדי להתחיל בניסוי.")

    BREAK = "הפסקה!\n אנא לחץ/י על כל כפתור כאשר אתה מוכן לחזור לניסוי."

    GOODBYE = "תודה רבה על השתתפותך בניסוי. נא לקרוא למריץ הניסוי. ניתן לשאול אותו/ה שאלות על הניסויֿ"


class BreakGameEnums:
    GAME_DURATION = 100  # seconds
    CHANGE_INTERVAL = 10  # seconds
    BASE_BRIGHTNESS = 0.5
    TRIAL_CHANGE = 0.2
    ANSWER_KEY_LIST = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

class BindingAndTestEnums:
    TEXT_HEIGHT = 0.07

    BINDING_EXAMPLES  = zip([Path(Paths.OBJECT_EXAMPLE_FORK), Path(Paths.OBJECT_EXAMPLE_ROBOT)],
                            [Features.COLOR_TO_RGBA[Features.YELLOW], Features.COLOR_TO_RGBA[Features.RED]],
                            [Features.SCENE_TO_IMAGE[Features.KITCHEN], Features.SCENE_TO_IMAGE[Features.LIVING_ROOM]])

    DIFFICULT_RANGE = ["1", "2", "3", "4", "5"]
    ARROW_TO_LOCATION = {StringEnums.UP: 0, StringEnums.LEFT: 1, StringEnums.RIGHT: 2}

    RETRIVAL_OPTION = {
        StringEnums.LEFT: {
            StringEnums.TEXT: HebrewEnums.COLOR,
            StringEnums.LIST: [Features.COLORS],
            StringEnums.LOCATION: (-0.45, 0)
        },
        StringEnums.RIGHT: {
            StringEnums.TEXT: HebrewEnums.SCENE,
            StringEnums.LIST: [Features.SCENES],
            StringEnums.LOCATION: (0.45, 0)
        },
        StringEnums.DOWN: {
            StringEnums.TEXT: HebrewEnums.BOTH,
            StringEnums.LIST: [Features.COLORS, Features.SCENES],
            StringEnums.LOCATION: (0, -0.45)
        },
    }

    ATTENTION_QUESTION_OPTIONS = {
        StringEnums.RIGHT: {StringEnums.TEXT: HebrewEnums.TRUE,  StringEnums.LOCATION: (0.5, -0.4)},
        StringEnums.LEFT:  {StringEnums.TEXT: HebrewEnums.WRONG, StringEnums.LOCATION: (-0.5, -0.4)},
    }

    FEATURE_QUESTION_POSITIONS = [(0, 0.45), (-0.45, 0), (0.45, 0)]

    RETRIVAL_OPTION_BONUS = {
        StringEnums.LEFT: {
            StringEnums.TEXT: HebrewEnums.NOT_REMEMBER,
            StringEnums.IS_REMEMBER: False,
            StringEnums.LOCATION: (-0.45, 0)
        },
        StringEnums.RIGHT: {
            StringEnums.TEXT: HebrewEnums.REMEMBER,
            StringEnums.IS_REMEMBER: True,
            StringEnums.LOCATION: (0.45, 0)
        }
    }


class TimeAttribute:
    FEATURE_APPEAR = "feature_appear"
    FEATURE_DISAPPEAR = "feature_disappear"
    QUESTION_APPEAR = "question_appear"
    ANSWER_TIME = "answer_time"
    OBJECT_APPEAR = "object_appear"
    OBJECT_DISAPPEAR = "object_disappear"
    DIFFICULTY_QUESTION_APPEAR = "difficulty_question_appear"
    DIFFICULTY_ANSWER_TIME = "difficulty_answer_time"
    RETRIVAL_TIME = "retrival_time"
    RETRIVAL_QUESTION_APPEAR = "retrival_question_appear"
    RETRIVAL_REPORT_TIME = "retrival_report_time"
    PROBE_APPEAR = "probe_appear"
    PROBE_DISAPPEAR = "probe_disappear"
    START_RETRIVAL_TIME = "start_retrival_time"



