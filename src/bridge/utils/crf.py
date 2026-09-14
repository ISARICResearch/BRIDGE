__all__ = [
    "clean_crf_metadata",
    "CRFTemplateMetadataModalContent",
    "DocumentationCRFTemplateMetadataModalSection",
    "get_approvers",
    "get_author_and_institutions",
    "get_contact",
    "get_keywords",
    "get_research_questions",
    "get_resources",
    "get_crf_name",
    "get_crf_template_metadata_modal_content",
    "get_crf_template_metadata_modal_documentation",
    "get_crf_template_metadata_modal_governance",
    "get_crf_template_metadata_modal_overview",
    "get_crf_template_metadata_modal_scientific_scope",
    "get_selected_crf_presets",
    "GovernanceCRFTemplateMetadataModalSection",
    "OverviewCRFTemplateMetadataModalSection",
    "ScientificScopeCRFTemplateMetadataModalSection",
]


# -- IMPORTS --

# -- Standard libraries --
import re
import typing
from collections import OrderedDict
from dataclasses import dataclass
from itertools import chain

# -- 3rd party libraries --
import pandas as pd

# -- Internal libraries --
from bridge.utils.logger import setup_logger


logger = setup_logger(__name__)


NOT_AVAILABLE_TYPE = typing.Literal["Not available"]


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


def get_research_questions(
    research_questions_raw: str, /, *, delim: str = ";"
) -> tuple[str]:
    """:py:class:`tuple` : Returns a tuple of research questions for the Scientific Scope section.

    Parameters
    ----------
    research_questions_raw : str
        A raw delimiter-separated (the delimiter defaulting to ``";"``) string
        containing research questions.

    delim : str, default=";"
        Optional delimiter for the questions inside the string, defaulting to
        ``";"``.

    Returns
    -------
    tuple
        A tuple of research questions.

    Examples
    --------
    >>> research_questions_raw = '(1) characterise the clinical epidemiology of chikungunya, including presenting signs and symptoms, disease course, and outcomes;   (2) enable comparative clinical epidemiology across diseases, populations, and geographic regions;  (3) identify risk factors associated with disease presentation, progression, and outcomes;   (4) describe clinical management practices, including variations in approaches to care; (5) describe diagnostic approaches and results used in both routine clinical practice and research settings. '
    >>> get_research_questions(research_questions_raw)  # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    ('Characterise the clinical epidemiology of chikungunya, including presenting signs and symptoms, disease course, and outcomes',
     'Enable comparative clinical epidemiology across diseases, populations, and geographic regions',
     'Identify risk factors associated with disease presentation, progression, and outcomes',
     'Describe clinical management practices, including variations in approaches to care',
     'Describe diagnostic approaches and results used in both routine clinical practice and research settings.')
    """
    return tuple(
        map(
            lambda s: str.capitalize(re.sub(r"(\s+)?\(\d+\)(\s+)?", "", s)).strip(),
            research_questions_raw.split(delim),
        )
    )


def get_author_and_institutions(
    authors_and_institutions_raw: str,
    /,
    *,
    author_and_institutions_sep: str = "|",
    author_institutions_delim: str = "/",
    authors_delim: str = ";",
) -> tuple[dict[str, tuple[str]], tuple[str]]:
    """:py:class:`tuple` : Returns a pair of tuples for the Governance & Contributors section, consisting of an ordered map of authors and author-affiliated institutions, and a tuple of all affiliated institutions.

    Parameters
    ----------
    authors_and_institutions_raw : str
        A raw string of authors and author-affiliated institutions in the format:
        ::

           Author #1 name | Author #1 institution #1 / Author #1 institution #2; Author #2 name | Author #2 institution #1 ...

    author_and_institutions_sep : str, default="|"
        Optional separator of an author name from the list of their
        (affiliated) institutions, defaults to ``"|"``.

    author_institutions_delim : str, default="/"
        Optional delimiter of an author's institutions, defaults to ``"/"``.

    authors_delim : str, default=";"
        Optional delimiter of authors, defaults to ``";"``.

    Returns
    -------
    tuple
        A pair consisting of (1) ordered dict of authors and author-affiliated
        institutions, and a tuple of all affiliated institutions in order.

    Examples
    --------
    >>> authors_and_institutions_raw = "Anastasiia Demidova | King's College London; Aileen Chang | ISARIC; Viviane S B de Oliveira | ISARIC; Josephine Bourner | ISARIC; Hugh Watson | ISARIC; Lubaba Sharin | ISARIC; Perkell Collie | ISARIC; Anastasia Kiseleva | ISARIC; Lilit Davtian | ISARIC; Jan Wu | ISARIC; Anastasiia Chernavskaya | ISARIC; Sara Duque Vallejo | ISARIC; Esteban Garcia-Gallo | ISARIC / Pandemic Sciences Institute, University of Oxford / Universidad Federal Bahia, Salvador, Brazil"
    >>> get_authors_and_institutions(authors_and_institutions_raw) # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    OrderedDict([('Anastasiia Demidova', (1,)),
                 ('Aileen Chang', (2,)),
                 ('Viviane S B de Oliveira', (2,)),
                 ('Josephine Bourner', (2,)),
                 ('Hugh Watson', (2,)),
                 ('Lubaba Sharin', (2,)),
                 ('Perkell Collie', (2,)),
                 ('Anastasia Kiseleva', (2,)),
                 ('Lilit Davtian', (2,)),
                 ('Jan Wu', (2,)),
                 ('Anastasiia Chernavskaya', (2,)),
                 ('Sara Duque Vallejo', (2,)),
                 ('Esteban Garcia-Gallo', (2, 3, 4))])
    """
    authors_and_institutions_map = OrderedDict(
        [
            author.strip(),
            tuple(map(str.strip, institutions.split(author_institutions_delim))),
        ]
        for author, institutions in map(
            lambda s: s.split(author_and_institutions_sep),
            authors_and_institutions_raw.split(authors_delim),
        )
    )
    ordered_institutions = tuple(
        map(
            str.strip,
            dict.fromkeys(chain.from_iterable(authors_and_institutions_map.values())),
        )
    )

    return tuple(
        tuple(
            [
                author,
                tuple(
                    [
                        ordered_institutions.index(institution) + 1
                        for institution in institutions
                    ]
                ),
            ]
        )
        for author, institutions in authors_and_institutions_map.items()
    ), ordered_institutions


def get_approvers(
    approvers_raw: str,
    /,
    *,
    approvers_prefix_sep: str = ":",
    approvers_delim: str = ",",
) -> tuple[str]:
    """:py:class:`tuple` : Returns a tuple of approvers for the Governance & Contributors section.

    Parameters
    ----------
    approvers_raw : str
        A delimiter-separated (the delimiter defaulting to ``";"``) string
        containing a list of study approvers.

    approvers_delim : str, default=";"
        Optional delimiter for the approver names inside the string, defaulting
        to ``","``.

    Returns
    -------
    tuple
        A tuple of approver names.

    Examples
    --------
    >>> approvers_raw = 'ISARIC chikungunya CRF management committee: Aileen Chang, Viviane S B de Oliveira, Josephine Bourner, Hugh Watson, Lubaba Sharin)'
    >>> get_approvers(approvers_raw). # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    ('Aileen Chang',
     'Viviane S B de Oliveira',
     'Josephine Bourner',
     'Hugh Watson',
     'Lubaba Sharin)')
    """
    return tuple(
        map(
            str.strip,
            approvers_raw.split(approvers_prefix_sep)[-1].split(approvers_delim),
        )
    )


def get_contact(
    contact_firstname: str, contact_lastname: str, contact_email: str
) -> tuple[str, str]:
    """:py:class:`tuple` : A pair consisting of the study contact name and email.

    Parameters
    ----------
    contact_firstname: str
        The contact first name.

    contact_lastname : str
        The contact last name.

    contact_email : str
        The contact email.

    Returns
    -------
    tuple
        A pair consisting of the contact name and email.

    Examples
    --------
    >>> get_contact("John", "Smith", "jsmith@example.com")  # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    (John Smith', jsmith@example.com')
    """
    return f"{contact_firstname} {contact_lastname}", contact_email


def get_keywords(keywords_raw: str, /, *, keywords_delim: str = ";") -> tuple[str]:
    """:py:class:`tuple` : Returns a tuple of keywords for the Documentation & Discoverability section.

    Parameters
    ----------
    keywords_raw : str
        A delimiter-separated (the delimiter defaulting to ``";"``) string
        containing a list of study keywords.

    keywords_delim : str, default=";"
        Optional delimiter for the keywords inside the string, defaulting
        to ``";"``.

    Returns
    -------
    tuple
        A tuple of keywords.

    Examples
    --------
    >>> keywords_raw = 'chikungunya; CHIKV; arbovirus; case report form; CRF; ISARIC; BRIDGE; ARC; harmonised data collection; clinical characterisation; outbreak preparedness; REDCap; acute infection    '
    >>> get_keywords(keywords_raw). # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    ('Aileen Chang',
     'Viviane S B de Oliveira',
     'Josephine Bourner',
     'Hugh Watson',
     'Lubaba Sharin)')
    """
    return tuple(map(str.strip, keywords_raw.split(keywords_delim)))


def get_resources(
    resources_raw: str,
    /,
    *,
    resource_name_url_sep: str = ": ",
    resource_delim: str = "·",
) -> tuple[str]:
    """:py:class:`tuple` : Returns a tuple of resource name and URL pairs for the Documentation & Discoverability section.

    Parameters
    ----------
    resources_raw : str
        A delimiter-separated (the delimiter defaulting to ``"·"``) string
        of resource names and URLs.

    resource_name_url_sep : str, default=": "
        Optional separator between the resource name and the URL, defaults
        to ``": "``.

    resource_delim: str, default="·"
        Optional delimiter of the resource name and URL pairs, defaults to
        ``"·"``.

    Returns
    -------
    tuple
        A tuple of pairs, each pair consisting of a resource name and URL.

    Examples
    --------
    >>> resources_raw = 'ISARIC CRFs: https://isaric.org/resources/data/case-report-forms/   · BRIDGE: https://bridge.isaric.org/   · ARC variable library: https://github.com/ISARICResearch/ARC · ISARIC: www.isaric.org · '
    >>> get_resources(resources_raw). # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    ('Aileen Chang',
     'Viviane S B de Oliveira',
     'Josephine Bourner',
     'Hugh Watson',
     'Lubaba Sharin)')
    """
    return tuple(
        [
            tuple(map(str.strip, s.split(resource_name_url_sep)))
            for s in resources_raw.strip().strip(resource_delim).split(resource_delim)
        ]
    )


@dataclass(eq=True, frozen=True)
class OverviewCRFTemplateMetadataModalSection:
    """A dataclass implementation of the project overview section of a CRF template metadata modal content."""

    section_name = "Overview"

    description: str | NOT_AVAILABLE_TYPE
    metadata: tuple[tuple[str, str]] | NOT_AVAILABLE_TYPE


@dataclass(eq=True, frozen=True)
class ScientificScopeCRFTemplateMetadataModalSection:
    """A dataclass implementation of the scientific scope section of CRF template metadata modal content."""

    section_name = "Scientific Scope"

    research_questions: tuple[str] | NOT_AVAILABLE_TYPE
    syndrome: str | NOT_AVAILABLE_TYPE
    pathogens: tuple[str] | NOT_AVAILABLE_TYPE
    setting: str | NOT_AVAILABLE_TYPE
    geographic_scope: str | NOT_AVAILABLE_TYPE
    syndrome_definition: str | NOT_AVAILABLE_TYPE
    target_population: str | NOT_AVAILABLE_TYPE
    inclusion_criteria: str | NOT_AVAILABLE_TYPE
    exclusion_criteria: str | NOT_AVAILABLE_TYPE


@dataclass(eq=True, frozen=True)
class GovernanceCRFTemplateMetadataModalSection:
    """A dataclass implementation of the governance section of CRF template metadata modal content."""

    section_name = "Governance & Contributors"

    authors: tuple[tuple[str, tuple[int]]] | NOT_AVAILABLE_TYPE
    approvers: tuple[str] | NOT_AVAILABLE_TYPE
    affiliations: tuple[str] | NOT_AVAILABLE_TYPE
    contact: tuple[str, str] | NOT_AVAILABLE_TYPE


@dataclass(eq=True, frozen=True)
class DocumentationCRFTemplateMetadataModalSection:
    """A dataclass implementation of the documentation section of CRF template metadata modal content."""

    section_name = "Documentation & Discoverability"

    keywords: tuple[str] | NOT_AVAILABLE_TYPE
    links: tuple[tuple[str, str]] | NOT_AVAILABLE_TYPE


@dataclass(eq=True, frozen=True)
class CRFTemplateMetadataModalContent:
    """A dataclass implementation of a CRF template metadata modal content."""

    title: str

    overview_section: OverviewCRFTemplateMetadataModalSection
    scientific_scope_section: ScientificScopeCRFTemplateMetadataModalSection
    governance_section: GovernanceCRFTemplateMetadataModalSection
    documentation_section: DocumentationCRFTemplateMetadataModalSection


def get_crf_template_metadata_modal_overview(
    template_metadata: pd.Series,
) -> OverviewCRFTemplateMetadataModalSection:
    """:py:class:`OverviewCRFTemplateMetadataModalSection` : The Overview section content of the CRF template metadata modal.

    Parameters
    ----------
    template_metadata : pandas.Series
        The CRF template metadata.

    Returns
    -------
    OverviewCRFTemplateMetadataModalSection
        The Overview section content of the CRF template metadata modal.
    """
    tm = template_metadata

    description = tm.get("Description", "Not available")
    metadata = [
        (
            "Study type",
            tm.get("Study type", "Not available"),
        ),
        (
            "Version",
            tm.get("Version", "Not available"),
        ),
        (
            "Publication date",
            tm.get("Date of publication/release", "Not known"),
        ),
    ]

    return OverviewCRFTemplateMetadataModalSection(
        description=description,
        metadata=metadata,
    )


def get_crf_template_metadata_modal_scientific_scope(
    template_metadata: pd.Series,
) -> ScientificScopeCRFTemplateMetadataModalSection:
    """:py:class:`ScientificScopeCRFTemplateMetadataModalSection` : The Scientific Scope section content of the CRF template metadata modal.

    Parameters
    ----------
    template_metadata : pandas.Series
        The CRF template metadata.

    Returns
    -------
    ScientificScopeCRFTemplateMetadataModalSection
        The Scientific Scope section of the CRF template metadata modal.
    """
    tm = template_metadata

    research_questions = (
        get_research_questions(tm["Research_questions"])
        if tm.get("Research questions")
        else "Not available"
    )
    syndrome = tm.get("Syndrome / clinical presentation", "Not available")
    pathogens = tuple(tm.get("Pathogen or agent", ["Not available"]))
    setting = tm.get("Setting", "Not available")
    geographic_scope = tm.get("Geographic scope", "Not available")
    syndrome_definition = tm.get("Syndrome definition", "Not available")
    target_population = tm.get("Target population", "Not available")
    inclusion_criteria = tm.get("Inclusion Criteria", "Not available")
    exclusion_criteria = tm.get("Exclusion Criteria", "Not available")

    return ScientificScopeCRFTemplateMetadataModalSection(
        research_questions=research_questions,
        syndrome=syndrome,
        pathogens=pathogens,
        setting=setting,
        geographic_scope=geographic_scope,
        syndrome_definition=syndrome_definition,
        target_population=target_population,
        inclusion_criteria=inclusion_criteria,
        exclusion_criteria=exclusion_criteria,
    )


def get_crf_template_metadata_modal_governance(
    template_metadata: pd.Series,
) -> GovernanceCRFTemplateMetadataModalSection:
    """:py:class:`GovernanceCRFTemplateMetadataModalSection` : The Governors & Contributors section content of the CRF template metadata modal.

    Parameters
    ----------
    template_metadata : pandas.Series
        The CRF template metadata.

    Returns
    -------
    GovernanceCRFTemplateMetadataModalSection
        The Governance & Contributors section of the CRF template metadata modal.
    """
    tm = template_metadata

    authors, affiliations = (
        get_author_and_institutions(tm["Authors"])
        if tm.get("Authors")
        else ("Not available", "Not available")
    )
    approvers = (
        get_approvers(tm["Approvers"]) if tm.get("Approvers") else "Not available"
    )
    contact_name, contact_email = get_contact(
        tm["Contact First Name"],
        tm["Contact Last Name"],
        tm["Contact email"]
        if (
            tm.get("Contact First Name")
            and tm.get("Contact Last Name")
            and tm.get("Contact email")
        )
        else "Not available",
    )

    return GovernanceCRFTemplateMetadataModalSection(
        authors=authors,
        affiliations=affiliations,
        approvers=approvers,
        contact=(contact_name, contact_email),
    )


def get_crf_template_metadata_modal_documentation(
    template_metadata: pd.Series,
) -> DocumentationCRFTemplateMetadataModalSection:
    """:py:class:`DocumentationCRFTemplateMetadataModalSection` : The Documentation & Discoverability section content of the CRF template metadata modal.

    Parameters
    ----------
    template_metadata : pandas.Series
        The CRF template metadata.

    Returns
    -------
    DocumentationCRFTemplateMetadataModalSection
        The Documentation & Discoverability section of the CRF template metadata modal.
    """
    tm = template_metadata

    keywords = get_keywords(tm["Keywords"]) if tm.get("Keywords") else "Not available"
    resources = (
        get_resources(tm["Relevant resources"])
        if tm.get("Relevant resources")
        else "Not available"
    )

    return DocumentationCRFTemplateMetadataModalSection(
        keywords=keywords, resources=resources
    )


def get_crf_template_metadata_modal_content(
    template_metadata: pd.Series,
) -> CRFTemplateMetadataModalContent:
    """:py:class:`bridge.utils.crf.CRFTemplateMetadataModalContent` : Returns CRF template metadata content as a dataclass.

    Parameters
    ----------
    template_metadata : pd.Series
        A specific CRF template metadata as a Pandas series.

    Returns
    -------
    CRFTemplateMetadataModalContent
    """
    tm = template_metadata

    # Get the Overview section content
    overview_section = get_crf_template_metadata_modal_overview(tm)

    # Get the Scientific Scope section content
    scientific_scope_section = get_crf_template_metadata_modal_scientific_scope(tm)

    # Get the Governance & Contributors section content
    governance_section = get_crf_template_metadata_modal_governance(tm)

    # Get the Documentation & Discoverability section content
    documentation_section = get_crf_template_metadata_modal_documentation(tm)

    # Create and return the CRF template metadata modal content
    modal_title = " | ".join(tm["Title of CRF"].split("_"))

    return CRFTemplateMetadataModalContent(
        title=modal_title,
        overview_section=overview_section,
        scientific_scope_section=scientific_scope_section,
        governance_section=governance_section,
        documentation_section=documentation_section,
    )
