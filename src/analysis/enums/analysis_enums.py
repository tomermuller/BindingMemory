from pathlib import Path


class Paths:
    DATA_ROOT   = "/Volumes/CENSORLAB$/Tomer Muller/data"
    OUTPUT_ROOT = "/Volumes/CENSORLAB$/Tomer Muller/preprocessed"
    SESSIONS = ["experiment", "baseline", "end"]
    META_DATA_FOLDER = "META DATA"


class StageEnum:
    FL = 'fl'
    BL = 'bl'
    TP = 'tp'


class MetadataConfig:
    FL_ANCHORS  = frozenset({11, 12, 13, 16, 17, 18})
    FL_WITHIN   = frozenset({31, 32})
    BL_ANCHOR   = 41
    BL_WITHIN   = frozenset({43, 44})
    TP_ANCHOR   = 51
    TP_WITHIN   = frozenset({53, 54, 55, 56, 61, 62, 66, 67})
    PR_ANCHOR   = 71
    PR_WITHIN   = frozenset({73, 74})
    SHOW_COLORS = 61
    SHOW_SCENES = 66

    TRIGGER_TO_FEATURE = {
        11: 'red', 12: 'green', 13: 'yellow',
        16: 'living_room', 17: 'bathroom', 18: 'kitchen',
    }

    FL_CSV_FOLDER       = 'functional_localizer'
    COMBINED_CSV_FOLDER = 'combined_data'
    FL_SORT_COL         = 'trial_index'
    BL_SORT_COL         = 'binding_trial'
    TEST_TRIAL_COL      = 'test_trial'

    STAGE_COL     = 'stage'
    TRIAL_NUM_COL = 'trial_num'
    FL_PREFIX     = 'fl_'
    BL_PREFIX     = 'bl_'
    TP_PREFIX     = 'tp_'

    FL_FEATURE_COL        = 'fl_feature'
    FL_FEATURE_APPEAR_COL = 'fl_feature_appear'
    TP_FIRST_Q_COL        = 'tp_first_question'
    COLORS_STR            = 'colors'
    SCENES_STR            = 'scenes'

    TIMESTAMP_FMT   = "%Y-%m-%d_%H-%M-%S.%f"
    TIMESTAMP_MAX_S = 1.0

    FL_COLS = ['trial_index', 'feature', 'word_question', 'user_answer', 'is_right', 'feature_appear']
    BL_COLS = ['block', 'object', 'binding_trial', 'binding_trial_in_block',
               'colors', 'scenes', 'difficulty', 'binding_object_appear']
    TP_COLS = ['block', 'object', 'binding_trial', 'colors', 'scenes', 'difficulty',
               'test_trial', 'subject_color', 'subject_scene',
               'color_correct', 'scene_correct', 'both_correct',
               'color_rt_ms', 'scene_rt_ms', 'first_question', 'test_object_appear']


class PreproArgs:
    RESAMPLE = 1000
    TMIN = -0.4
    TMAX = 5
    BASELINE = None
    DROP_ICA = ['eye blink', 'muscle artifact', 'channel noise']


class ParallelPortDict:
    EVENT_DICT = {
        'show_red': 11,
        'show_green': 12,
        'show_yellow': 13,
        'show_living_room': 16,
        'show_bathroom': 17,
        'show_kitchen': 18,
        'show_attention_question': 31,
        'answer_attention_question': 32,
        'show_binding_trials': 41,
        'show_difficulty_question': 43,
        'answer_difficulty_question': 44,
        'show_object_in_test_trial': 51,
        'start_retrieval_time': 53,
        'answer_on_retrieval_time': 54,
        'show_retrieval_question': 55,
        'answer_retrieval_question': 56,
        'show_colors_answers': 61,
        'answer_color_question': 62,
        'show_scenes_answers': 66,
        'answer_scene_question': 67,
        'show_probe': 71,
        'show_partial_retrival_remember_question': 73,
        'answer_partial_retrival_remember_question': 74,
    }

