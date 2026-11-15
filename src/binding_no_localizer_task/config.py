from pathlib import Path

from src.enums import Features, Paths

_TASK_FOLDER = Path(__file__).parent
_FEATURES = _TASK_FOLDER / 'features'


class NoLocalizerConfig:
    """settings of the binding no localizer task.
       trials per block (NUMBER_OF_TRIALS / NUMBER_OF_BLOCKS) must divide by the features per category (2),
       and OBJECTS_PATH must hold NUMBER_OF_TRIALS objects"""
    NUMBER_OF_BLOCKS = 8
    NUMBER_OF_TRIALS = 128
    OBJECTS_PATH = _TASK_FOLDER / 'objects'
    OBJECTS_EXTENSION = '.jpg'
    BINDING_PHOTOS_FOLDER = _TASK_FOLDER / 'binding_photos'
    SAVE_DATA_FOLDER = "subject_answer/no_localizer/final_data/"
    SAVE_TEMP_FOLDER = "subject_answer/no_localizer/temp/"
    PARTIAL_RETRIEVAL_MAX_OBJECTS = 30  # partial retrieval asks about at most this many correct objects (all of them if fewer)

    # object coloring (pixels, for 800x800 object images)
    OUTLINE_BREAK_RADIUS = 2  # breaks in the lines up to ~2x this are sealed first, so thin parts (horns, roots) count as enclosed
    OUTLINE_GAP_RADIUS = 6  # white areas narrower than ~2x this (outline breaks, gaps between legs) count as narrow, not as inside/outside
    OUTLINE_LINE_RADIUS = 3  # dark areas thinner than ~2x this are kept as outline, thicker ones are colored
    OUTLINE_BORDER_WIDTH = 2  # black border drawn around the object and around every colored thick dark area
    # background seen through the object (enclosed by its lines) that must stay transparent:
    # object name -> (x, y) pixels in the object image, one point inside each such hole
    TRANSPARENT_HOLES = {'animate_39': [(479, 545)],  # giraffe: between the legs
                         'animate_32': [(579, 287)],  # snake: inside the loop
                         'inanimate_01': [(534, 352)],  # belt: inside the loop
                         'inanimate_11': [(407, 247)]}  # scarf: above the crossing

    COLOR_TO_IMAGE = {Features.RED: [_FEATURES / 'colors' / f'{Features.RED}_image.png'],
                      Features.YELLOW: [_FEATURES / 'colors' / f'{Features.YELLOW}_image.png']}
    SCENE_TO_IMAGE = {Features.KITCHEN: [_FEATURES / 'scenes' / f'{Features.KITCHEN}_image.png'],
                      Features.LIVING_ROOM: [_FEATURES / 'scenes' / f'{Features.LIVING_ROOM}_image.png']}
    CATEGORY_TO_FEATURES = {Features.COLORS: COLOR_TO_IMAGE, Features.SCENES: SCENE_TO_IMAGE}

    # (object, color RGBA, scene images) of the binding examples
    BINDING_EXAMPLES = [(Path(Paths.OBJECT_EXAMPLE_FORK), Features.COLOR_TO_RGBA[Features.YELLOW], SCENE_TO_IMAGE[Features.KITCHEN]),
                        (Path(Paths.OBJECT_EXAMPLE_ROBOT), Features.COLOR_TO_RGBA[Features.RED], SCENE_TO_IMAGE[Features.LIVING_ROOM])]
