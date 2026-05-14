from pathlib import Path


class Paths:
    DATA_ROOT   = "/Volumes/CENSORLAB$/Tomer Muller/data"
    OUTPUT_ROOT = "/Volumes/CENSORLAB$/Tomer Muller/preprocessed"
    SESSIONS    = ["experiment", "baseline"]


class FilterParams:
    L_FREQ      = 0.1    # high-pass cut-off (Hz)
    H_FREQ      = 40.0   # low-pass cut-off  (Hz)
    NOTCH_FREQ  = 50.0   # power-line noise  (Hz, EU standard)
    RESAMPLE_HZ = 256    # downsample target (Hz)


class ICAParams:
    N_COMPONENTS = 25
    METHOD       = "fastica"
    RANDOM_STATE = 42
    FIT_L_FREQ   = 1.0   # high-pass used only for ICA fitting


class EpochParams:
    TMIN     = -0.2       # epoch start relative to trigger (s)
    TMAX     = 1.0        # epoch end   relative to trigger (s)
    BASELINE = (None, 0)  # baseline correction window


class TriggerCodes:
    BINDING_TRIAL = 1
    TEST_TRIAL    = 2
    PARTIAL_TEST  = 3

    EVENT_ID = {
        "binding_trial": BINDING_TRIAL,
        "test_trial":    TEST_TRIAL,
        "partial_test":  PARTIAL_TEST,
    }


class RejectCriteria:
    HARD_AMPLITUDE  = 150e-6   # hard threshold before AutoReject (V)
    FLAT_THRESHOLD  = 0.5e-6   # channel std below this → flat channel (V)
    NOISY_Z_SCORE   = 3        # channel std z-score above this → noisy channel


class FrequencyBands:
    DELTA = (0.5, 4.0)
    THETA = (4.0, 8.0)
    ALPHA = (8.0, 13.0)
    BETA  = (13.0, 30.0)
    GAMMA = (30.0, 40.0)

    ALL = {
        "delta": DELTA,
        "theta": THETA,
        "alpha": ALPHA,
        "beta":  BETA,
        "gamma": GAMMA,
    }


class ChannelGroups:
    FRONTAL   = ["Fp1", "Fp2", "F3", "F4", "Fz", "F7", "F8"]
    CENTRAL   = ["C3", "C4", "Cz"]
    PARIETAL  = ["P3", "P4", "Pz", "P7", "P8"]
    OCCIPITAL = ["O1", "O2", "Oz"]
    TEMPORAL  = ["T7", "T8", "TP9", "TP10"]

    ALL = {
        "frontal":   FRONTAL,
        "central":   CENTRAL,
        "parietal":  PARIETAL,
        "occipital": OCCIPITAL,
        "temporal":  TEMPORAL,
    }


class FileFormat:
    PREPROCESSED_SUFFIX = "-epo.fif"
    SUBJECT_FOLDER_PREFIX = "subject "


class StageEnum:
    FL = 'fl'
    BL = 'bl'
    TP = 'tp'


class MetadataConfig:
    FL_ANCHORS  = frozenset({11, 12, 13, 16, 17, 18})
    FL_WITHIN   = frozenset({31, 32})
    BL_ANCHOR   = 41
    BL_WITHIN   = frozenset({42, 43, 44})
    TP_ANCHOR   = 51
    TP_WITHIN   = frozenset({53, 54, 55, 56, 61, 62, 66, 67})
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
        'stop_binding_trials': 42,
        # what is 42 and 41?
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
    }

    PREPRO_ARGS = {
        'resample': 1000,
        'tmin': -0.4,
        'tmax': 5,
        'baseline': None,
        'drop ica': ['eye blink', 'muscle artifact', 'channel noise']
    }
