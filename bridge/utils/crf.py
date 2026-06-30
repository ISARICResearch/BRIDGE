__all__ = [
    "get_crf_name",
    "get_selected_crf_presets",
]


# -- IMPORTS --

# -- Standard libraries --
from bridge.utils.logger import setup_logger

# -- 3rd party libraries --

# -- Internal libraries --


logger = setup_logger(__name__)


def get_selected_crf_presets(
    grouped_presets: dict[str, list[str]], checked_values: list[bool]
) -> tuple[tuple[str, str]]:
    """:py:class:`tuple` : A tuple of selected CRF presets organised by section name.

    .. note:: A tuple is returned to keep the output immutable.

    Parameters
    ----------
    grouped_presets : dict
        A dict of CRF presets/templates keyed by section name.

    checked_values : list
        A list of boolean indicators of CRF preset checked values / selectors.

    Returns
    -------
    tuple
        A tuple of tuples composed of section name and selected CRF preset name.
    """
    flattened_grouped_presets = [
        (k, v) for k, values in grouped_presets.items() for v in values
    ]

    return tuple(
        preset
        for preset, preset_checked in zip(flattened_grouped_presets, checked_values)
        if preset_checked
    )


def get_crf_name(
    crf_name: str | list | None,
    checked_values: list[bool],
    grouped_presets: dict[str, list[str]] | None = None,
) -> str:
    """:py:class:`str` : The name of a selected CRF preset.

    Parameters
    ----------
    crf_name : str
        The CRF preset name or list of names, which could be null, to check
        against.

    checked_values : list
        A list of bools indicating CRF preset selections/checks - this will be
        an ordered list as long as the total number of CRF preset options in
        all sections.

    grouped_presets : dict
        A dict of CRF preset names keyed by section name.

    Returns
    -------
    str
        The selected CRF preset name.
    """
    if crf_name:
        if isinstance(crf_name, list):
            crf_name = crf_name[0]
    else:
        crf_name = get_selected_crf_presets(grouped_presets, checked_values)[0][1]
    logger.info(f"crf_name: {crf_name}")

    return crf_name
