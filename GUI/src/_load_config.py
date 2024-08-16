import json
from .validation import examples as pipelines, ValidationError, TranslationError, Pipeline


def load_settings(path: str, **pipes: Pipeline) -> dict:
    """
    Load the compile-time settings from a JSON file.

    Parameters
    ----------
    path: str
        The path to the JSON file. Is expected to exist, and be a valid JSON file.
    **pipes: Pipeline
        The pipelines to load settings for - any settings not specified will be removed from the output.

        The settings for the

    Returns
    -------
    dict[str, Any]
        The output JSON dictionary.
    """
    with open(path) as config:
        configuration = json.loads(config.read())
    valid_file = f"""Make sure that:
    "size" matches {pipelines.survey_size},
    "init_dwell" matches {pipelines.dwell_time},
    "engine_type" matches {pipelines.engine_type},
    "microscope" matches {pipelines.any_bool},
    "cluster_colour" matches {pipelines.colour}
    "marker_colour" matches {pipelines.colour}
    "histogram_outline" matches {pipelines.colour}
    "pattern_colour" matches {pipelines.colour}
    "finished_colour" matches {pipelines.colour}
    
    Any other keys are from individual pages, and they should match those expected pipelines."""
    remove = set()
    for k, v in configuration.items():
        chosen_pipe = pipes.get(k)
        if chosen_pipe is None:
            remove.add(k)
            continue
        try:
            chosen_pipe.validate(v)
            configuration[k] = chosen_pipe.translate(v)
        except (ValidationError, TranslationError) as err:
            raise AttributeError(f"JSON configuration file invalid at {k = }. \n{valid_file}") from err
    return {k: v for k, v in configuration.items() if k not in remove}
