__all__ = [
    "clean_crf_metadata",
    "CRFTemplateMetadataModal",
    "DocumentationCRFTemplateMetadataModalSection",
    "get_crf_name",
    "get_selected_crf_presets",
    "GovernanceCRFTemplateMetadataModalSection",
    "OverviewCRFTemplateMetadataModalSection",
    "ScientificScopeCRFTemplateMetadataModalSection",
]


# -- IMPORTS --

# -- Standard libraries --
import re
from dataclasses import dataclass

# -- 3rd party libraries --
import pandas as pd

# -- Internal libraries --
from bridge.utils.logger import setup_logger


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


def clean_crf_metadata(crf_metadata: pd.DataFrame) -> pd.DataFrame:
    """:py:class:`pandas.DataFrame` : Returns a "clean" version of the incoming CRF metadata dataframe by replacing "dummy" values and text with an appropriate placeholder.

    Any cell values in the original dataframe containing the case-insensitive
    words ``"example"``, ``"fake"`` or domains ``"example.org"``, are replaced
    with the value ``"Unknown"``, as are any null values including empty
    strings.

    Parameters
    ----------
    crf_metadata : pandas.DataFrame
        The original CRF metadata from ARC.

    Returns
    -------
    pandas.DataFrame
        The cleaned CRF metadata.
    """
    return (
        crf_metadata.map(
            lambda s: "Unknown"
            if isinstance(s, str)
            and re.search(r"(dummy|fake|example)", s, flags=re.IGNORECASE)
            else s
        )
        .fillna("Unknown")
        .replace("", "Unknown")
    )


@dataclass(eq=True, frozen=True)
class OverviewCRFTemplateMetadataModalSection:
    """A dataclass implementation of the project overview section of a CRF template metadata modal content."""

    section_name: str
    description: str
    metadata: tuple[tuple[str, str]]


@dataclass(eq=True, frozen=True)
class ScientificScopeCRFTemplateMetadataModalSection:
    """A dataclass implementation of the scientific scope section of CRF template metadata modal content."""

    research_questions: tuple[str]
    syndrome: str
    pathogens: tuple[str]
    setting: str
    geographic_scope: str
    syndrome_definition: str
    target_population: str
    inclusion_criteria: str
    exclusion_criteria: str


@dataclass(eq=True, frozen=True)
class GovernanceCRFTemplateMetadataModalSection:
    """A dataclass implementation of the governance section of CRF template metadata modal content."""

    authors: tuple[tuple[str, tuple[int]]]
    approvers: tuple[str]
    affiliations: tuple[str]
    contacts: tuple[tuple[str, str]]


@dataclass(eq=True, frozen=True)
class DocumentationCRFTemplateMetadataModalSection:
    """A dataclass implementation of the documentation section of CRF template metadata modal content."""

    keywords: tuple[str]
    links: tuple[tuple[str, str]]


@dataclass(eq=True, frozen=True)
class CRFTemplateMetadataModal:
    """A dataclass implementation of a CRF template metadata modal content."""

    title: str
    overview_section: OverviewCRFTemplateMetadataModalSection
    scientific_scope_section: ScientificScopeCRFTemplateMetadataModalSection
    governance_section: GovernanceCRFTemplateMetadataModalSection
    documentation_section: DocumentationCRFTemplateMetadataModalSection
