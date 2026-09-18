# -- IMPORTS --

# -- Standard libraries --
from pathlib import Path

# -- 3rd party libraries --
import pandas as pd
import pytest
from dash import html

# -- Internal libraries --
from bridge.utils.crf import (
    CRFTemplateMetadataModalContent,
    DocumentationCRFTemplateMetadataModalSection,
    GovernanceCRFTemplateMetadataModalSection,
    OverviewCRFTemplateMetadataModalSection,
    ScientificScopeCRFTemplateMetadataModalSection,
)


@pytest.fixture(scope="module")
def ccpuk_hantavirus_data_dictionary_2026_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath(
        "assets", "ccpuk-hantavirus-data-dictionary-2026-05-15.csv"
    )


@pytest.fixture(scope="module")
def ccpuk_hantavirus_data_dictionary_2026(
    ccpuk_hantavirus_data_dictionary_2026_filepath,
) -> pd.DataFrame:
    return pd.read_csv(ccpuk_hantavirus_data_dictionary_2026_filepath)


@pytest.fixture(scope="module")
def arc_1_2_2__english__paperlike_crf_details_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath(
        "assets", "arc-1.2.2-en-paperlike-details.csv"
    )


@pytest.fixture(scope="module")
def arc_1_2_2__english__paperlike_crf_details(
    arc_1_2_2__english__paperlike_crf_details_filepath,
) -> pd.DataFrame:
    return pd.read_csv(arc_1_2_2__english__paperlike_crf_details_filepath)


@pytest.fixture(scope="module")
def arc_1_2_2__english__supplemental_phrases_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath(
        "assets", "arc-1.2.2-en-supplemental-phrases.csv"
    )


@pytest.fixture(scope="module")
def arc_1_2_2__english__supplemental_phrases(
    arc_1_2_2__english__supplemental_phrases_filepath,
) -> pd.DataFrame:
    return pd.read_csv(arc_1_2_2__english__supplemental_phrases_filepath)


@pytest.fixture(scope="module")
def arc_1_4_0__crf_metadata() -> pd.DataFrame:
    return pd.read_csv(
        Path(__file__).parent.joinpath("assets", "arc-1.4.0-crf-metadata.csv")
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata() -> pd.DataFrame:
    return pd.read_csv(
        Path(__file__).parent.joinpath("assets", "arc-1.6.0-crf-metadata.csv")
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_content__overview__chikungunya() -> (
    OverviewCRFTemplateMetadataModalSection
):
    return OverviewCRFTemplateMetadataModalSection(
        description=(
            "A standardised ISARIC Case Report Form (CRF) for chikungunya, "
            "developed to harmonise clinical data collection in hospitalised "
            "patients during the acute phase of infection. It was produced "
            "through the ISARIC CRF development pipeline, using an existing "
            "dengue CRF as a template, variables extracted from "
            "expert-submitted study instruments and from the systematic review "
            "by Rama et al. (2024), and refined by international public "
            "consultation (15 experts across 11 countries). The CRF comprises "
            "a Presentation Form, a Daily Form, and an Outcome Form, and is "
            "available via ISARIC BRIDGE, which automatically generates a "
            "paper CRF, completion guide, and REDCap database file for "
            "deployment across diverse settings."
        ),
        metadata=(
            ("Study type", "Observational"),
            ("Version", "v1.0"),
            ("Publication date", "01/05/2026"),
        ),
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_tab__overview__chikungunya() -> html.Div:
    return html.Div(
        [
            html.Section(
                children=[
                    html.H3(children="Description", className="section-title"),
                    html.P(
                        children=(
                            "A standardised ISARIC Case Report Form (CRF) for "
                            "chikungunya, developed to harmonise clinical data "
                            "collection in hospitalised patients during the acute "
                            "phase of infection. It was produced through the ISARIC "
                            "CRF development pipeline, using an existing dengue CRF "
                            "as a template, variables extracted from expert-submitted "
                            "study instruments and from the systematic review by Rama "
                            "et al. (2024), and refined by international public "
                            "consultation (15 experts across 11 countries). The CRF "
                            "comprises a Presentation Form, a Daily Form, and an "
                            "Outcome Form, and is available via ISARIC BRIDGE, which "
                            "automatically generates a paper CRF, completion guide, "
                            "and REDCap database file for deployment across "
                            "diverse settings."
                        ),
                        className="section-text",
                    ),
                ],
                className="section",
            ),
            html.Section(
                children=[
                    html.H3(children="CRF metadata", className="section-title"),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    html.Span(
                                        children="Study type",
                                        className="metadata-label",
                                    ),
                                    html.Div(
                                        children="Observational",
                                        className="metadata-value",
                                    ),
                                ],
                                className="metadata-item",
                            ),
                            html.Div(
                                children=[
                                    html.Span(
                                        children="Version", className="metadata-label"
                                    ),
                                    html.Div(
                                        children="v1.0", className="metadata-value"
                                    ),
                                ],
                                className="metadata-item",
                            ),
                            html.Div(
                                children=[
                                    html.Span(
                                        children="Publication date",
                                        className="metadata-label",
                                    ),
                                    html.Div(
                                        children="01/05/2026",
                                        className="metadata-value",
                                    ),
                                ],
                                className="metadata-item",
                            ),
                        ],
                        className="metadata-grid",
                    ),
                ],
                className="section",
            ),
            html.Section(
                children=[
                    html.H3(children="Study population", className="section-title"),
                    html.Div(
                        [
                            html.Div(
                                children=[
                                    html.Div(
                                        children="Target population",
                                        className="population-label",
                                    ),
                                    html.Div(
                                        children="Hospitalised adults during the acute phase of chikungunya infection.",
                                        className="population-value",
                                    ),
                                ],
                                className="population-item first",
                            ),
                            html.Div(
                                children=[
                                    html.Div(
                                        children="Inclusion criteria",
                                        className="population-label",
                                    ),
                                    html.Div(
                                        children="Hospitalised individuals with suspected or laboratory-confirmed acute chikungunya virus infection.",
                                        className="population-value",
                                    ),
                                ],
                                className="population-item",
                            ),
                            html.Div(
                                children=[
                                    html.Div(
                                        children="Exclusion criteria",
                                        className="population-label",
                                    ),
                                    html.Div(
                                        children="Alternative confirmed diagnosis;",
                                        className="population-value",
                                    ),
                                ],
                                className="population-item",
                            ),
                        ]
                    ),
                ],
                className="section",
            ),
        ]
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_content__scientific_scope__chikungunya() -> (
    OverviewCRFTemplateMetadataModalSection
):
    return ScientificScopeCRFTemplateMetadataModalSection(
        research_questions=(
            "Characterise the clinical epidemiology of chikungunya, including presenting signs and symptoms, disease course, and outcomes",
            "Enable comparative clinical epidemiology across diseases, populations, and geographic regions",
            "Identify risk factors associated with disease presentation, progression, and outcomes",
            "Describe clinical management practices, including variations in approaches to care",
            "Describe diagnostic approaches and results used in both routine clinical practice and research settings.",
        ),
        syndrome="Acute febrile illness",
        pathogens=(
            "Chikungunya virus (CHIKV) - an alphavirus transmitted by Aedes aegypti and Aedes albopictus.",
        ),
        setting="Hospital",
        geographic_scope="Global",
        syndrome_definition="Not available",
        target_population="Hospitalised adults during the acute phase of chikungunya infection.",
        inclusion_criteria="Hospitalised individuals with suspected or laboratory-confirmed acute chikungunya virus infection.",
        exclusion_criteria="Alternative confirmed diagnosis;",
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_tab__scientific_scope__chikungunya() -> html.Div:
    return html.Div(
        [
            html.Section(
                children=[
                    html.H3(children="Clinical context", className="section-title"),
                    html.Div(
                        [
                            html.Div(
                                children=[
                                    html.Div(
                                        children=[
                                            html.Div(
                                                children="Syndrome",
                                                className="scope-label",
                                            ),
                                            html.Div(
                                                children="Acute febrile illness",
                                                className="scope-value",
                                            ),
                                        ],
                                        className="scope-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                children="Pathogen / agent",
                                                className="scope-label",
                                            ),
                                            html.Div(
                                                children=html.Div(
                                                    children=[
                                                        html.Span(
                                                            children="Chikungunya virus (CHIKV) - an alphavirus transmitted by Aedes aegypti and Aedes albopictus.",
                                                            className="pathogen-chip",
                                                        )
                                                    ],
                                                    className="pathogen-list",
                                                ),
                                                className="scope-value",
                                            ),
                                        ],
                                        className="scope-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                children="Setting",
                                                className="scope-label",
                                            ),
                                            html.Div(
                                                children="Hospital",
                                                className="scope-value",
                                            ),
                                        ],
                                        className="scope-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                children="Geographic scope",
                                                className="scope-label",
                                            ),
                                            html.Div(
                                                children="Global",
                                                className="scope-value",
                                            ),
                                        ],
                                        className="scope-item",
                                    ),
                                ],
                                className="scope-grid",
                            ),
                            html.Div(
                                children=[
                                    html.Span(
                                        children="Syndrome definition",
                                        className="definition-label",
                                    ),
                                    "Not available",
                                ],
                                className="definition-block",
                            ),
                        ]
                    ),
                ],
                className="section",
            ),
            html.Section(
                children=[
                    html.H3(children="Research questions", className="section-title"),
                    html.Ol(
                        children=[
                            html.Li(
                                "Characterise the clinical epidemiology of chikungunya, including presenting signs and symptoms, disease course, and outcomes"
                            ),
                            html.Li(
                                "Enable comparative clinical epidemiology across diseases, populations, and geographic regions"
                            ),
                            html.Li(
                                "Identify risk factors associated with disease presentation, progression, and outcomes"
                            ),
                            html.Li(
                                "Describe clinical management practices, including variations in approaches to care"
                            ),
                            html.Li(
                                "Describe diagnostic approaches and results used in both routine clinical practice and research settings."
                            ),
                        ],
                        className="research-list",
                    ),
                ],
                className="section",
            ),
        ]
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_content__governance_and_contributors__chikungunya() -> (
    GovernanceCRFTemplateMetadataModalSection
):
    return GovernanceCRFTemplateMetadataModalSection(
        authors=(
            ("Anastasiia Demidova", (1,)),
            ("Aileen Chang", (2,)),
            ("Viviane Boaventura", (3,)),
            ("Hugh Watson", (4, 5)),
            ("Lubaba Sharin", (6,)),
            ("Perkell Collie", (7,)),
            ("Anastasia Kiseleva", (4,)),
            ("Lilit Davtian", (5,)),
            ("Jan Wu", (7,)),
            ("Veronika Rogozhina", (8,)),
            ("Elena Piatenko", (9,)),
            ("Anastasiia Chernyavskaya", (4,)),
            ("Sara Duque Vallejo", (10,)),
            ("Esteban Garcia-Gallo", (10,)),
            ("Dhruv Darji", (10,)),
            ("Tom Edinburgh", (10,)),
            ("Laura Merson", (11,)),
            ("Daniel Munblit", (1, 4)),
            ("Expert Working Group", (12,)),
        ),
        approvers=(
            "Aileen Chang",
            "Viviane S B de Oliveira",
            "Josephine Bourner",
            "Hugh Watson",
            "Lubaba Sharin)",
        ),
        affiliations=(
            "Care in Long Term Conditions Division, Florence Nightingale Faculty of Nursing, Midwifery and Palliative Care, King's College London, London, UK",
            "Department of Medicine, George Washington University, Washington, DC, USA",
            "Precision Medicine and Public Health Laboratory, Gonçalo Moniz Institute, Fiocruz Bahia, Oswaldo Cruz Foundation, Fiocruz",
            "Department of Paediatrics and Paediatric Infectious Diseases, Institute of Child's Health, Sechenov First Moscow State Medical University, Moscow, Russia",
            "Federal Scientific and Clinical Center for Children and Adolescents, Federal Medical-Biological Agency (FMBA) of Russia, Moscow, Russia",
            "Dhaka Hospital, International Centre for Diarrheal Disease Research, Bangladesh (icddr,b), Dhaka, Bangladesh",
            "American Canadian School of Medicine, Picard, Dominica",
            "Clinical Pathophysiology Laboratory, Veltischev Research and Clinical Institute for Pediatrics and Pediatric Surgery, Pirogov Russian National Research Medical University, 2, Taldomskaya Street, 125412 Moscow, Russia",
            "Nassau University Medical Center, NY, USA",
            "ISARIC, Pandemic Sciences Institute, University of Oxford, UK",
            "Public Health Department, Institut Pasteur de Dakar, Dakar, Senegal",
            "N/A",
        ),
        contact=("Anastasiia Demidova", "anastasiia.demidova@kcl.ac.uk"),
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_tab__governance_and_contributors__chikungunya() -> (
    html.Div
):
    return html.Div(
        [
            html.Section(
                children=[
                    html.H3(children="Contributors", className="section-title"),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    html.H4(
                                        children="Authors", className="paper-subtitle"
                                    ),
                                    html.Div(
                                        children="19 people", className="paper-count"
                                    ),
                                    html.Div(
                                        children=[
                                            html.Span(
                                                [
                                                    "Anastasiia Demidova",
                                                    html.Sup(
                                                        children="1",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Aileen Chang",
                                                    html.Sup(
                                                        children="2",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Viviane Boaventura",
                                                    html.Sup(
                                                        children="3",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Hugh Watson",
                                                    html.Sup(
                                                        children="4,5",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Lubaba Sharin",
                                                    html.Sup(
                                                        children="6",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Perkell Collie",
                                                    html.Sup(
                                                        children="7",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Anastasia Kiseleva",
                                                    html.Sup(
                                                        children="4",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Lilit Davtian",
                                                    html.Sup(
                                                        children="5",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Jan Wu",
                                                    html.Sup(
                                                        children="7",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Veronika Rogozhina",
                                                    html.Sup(
                                                        children="8",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Elena Piatenko",
                                                    html.Sup(
                                                        children="9",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Anastasiia Chernyavskaya",
                                                    html.Sup(
                                                        children="4",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Sara Duque Vallejo",
                                                    html.Sup(
                                                        children="10",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Esteban Garcia-Gallo",
                                                    html.Sup(
                                                        children="10",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Dhruv Darji",
                                                    html.Sup(
                                                        children="10",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Tom Edinburgh",
                                                    html.Sup(
                                                        children="10",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Laura Merson",
                                                    html.Sup(
                                                        children="11",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Daniel Munblit",
                                                    html.Sup(
                                                        children="1,4",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                            ", ",
                                            html.Span(
                                                [
                                                    "Expert Working Group",
                                                    html.Sup(
                                                        children="12",
                                                        className="author-sup",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="author-line",
                                    ),
                                ],
                                className="paper-subsection",
                            ),
                            html.Div(
                                children=[
                                    html.H4(
                                        children="Approvers", className="paper-subtitle"
                                    ),
                                    html.Div(
                                        children="5 people", className="paper-count"
                                    ),
                                    html.Div(
                                        children="Aileen Chang, Viviane S B de Oliveira, Josephine Bourner, Hugh Watson, Lubaba Sharin)",
                                        className="approver-line",
                                    ),
                                ],
                                className="paper-subsection",
                            ),
                        ],
                        className="paper-columns",
                    ),
                ],
                className="section",
            ),
            html.Section(
                children=[
                    html.H3(children="Affiliations", className="section-title"),
                    html.Div(
                        [
                            html.Div(
                                children="12 affiliations", className="paper-count"
                            ),
                            html.Div(
                                children=[
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="1",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Care in Long Term Conditions Division, Florence Nightingale Faculty of Nursing, Midwifery and Palliative Care, King's College London, London, UK"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="2",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Department of Medicine, George Washington University, Washington, DC, USA"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="3",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Precision Medicine and Public Health Laboratory, Gonçalo Moniz Institute, Fiocruz Bahia, Oswaldo Cruz Foundation, Fiocruz"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="4",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Department of Paediatrics and Paediatric Infectious Diseases, Institute of Child's Health, Sechenov First Moscow State Medical University, Moscow, Russia"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="5",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Federal Scientific and Clinical Center for Children and Adolescents, Federal Medical-Biological Agency (FMBA) of Russia, Moscow, Russia"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="6",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Dhaka Hospital, International Centre for Diarrheal Disease Research, Bangladesh (icddr,b), Dhaka, Bangladesh"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="7",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "American Canadian School of Medicine, Picard, Dominica"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="8",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Clinical Pathophysiology Laboratory, Veltischev Research and Clinical Institute for Pediatrics and Pediatric Surgery, Pirogov Russian National Research Medical University, 2, Taldomskaya Street, 125412 Moscow, Russia"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="9",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Nassau University Medical Center, NY, USA"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="10",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "ISARIC, Pandemic Sciences Institute, University of Oxford, UK"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="11",
                                                className="affiliation-number",
                                            ),
                                            html.Span(
                                                "Public Health Department, Institut Pasteur de Dakar, Dakar, Senegal"
                                            ),
                                        ],
                                        className="affiliation-item",
                                    ),
                                    html.Div(
                                        children=[
                                            html.Sup(
                                                children="12",
                                                className="affiliation-number",
                                            ),
                                            html.Span("N/A"),
                                        ],
                                        className="affiliation-item",
                                    ),
                                ],
                                className="affiliation-list",
                            ),
                        ]
                    ),
                ],
                className="section",
            ),
            html.Div(className="governance-divider"),
            html.Section(
                children=[
                    html.H3(children="Correspondence", className="section-title"),
                    html.Div(
                        children=[
                            html.Span(
                                children="Anastasiia Demidova",
                                style={"fontWeight": "600"},
                            ),
                            " - ",
                            html.A(
                                children="anastasiia.demidova@kcl.ac.uk",
                                className="correspondence-email",
                                href="mailto:anastasiia.demidova@kcl.ac.uk",
                            ),
                        ],
                        className="correspondence",
                    ),
                ],
                className="section",
            ),
        ]
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_content__documentation_and_discoverability__chikungunya() -> (
    DocumentationCRFTemplateMetadataModalSection
):
    return DocumentationCRFTemplateMetadataModalSection(
        keywords=(
            "chikungunya",
            "CHIKV",
            "arbovirus",
            "case report form",
            "CRF",
            "ISARIC",
            "BRIDGE",
            "ARC",
            "harmonised data collection",
            "clinical characterisation",
            "outbreak preparedness",
            "REDCap",
            "acute infection",
        ),
        resources=(
            "https://isaric.org/resources/data/case-report-forms/",
            "https://bridge.isaric.org/",
            "https://github.com/ISARICResearch/ARC",
            "www.isaric.org",
        ),
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_tab__documentation_and_discoverability__chikungunya() -> (
    html.Div
):
    return html.Div(
        [
            html.Section(
                children=[
                    html.H3(children="Keywords", className="section-title"),
                    html.Div(
                        children=[
                            html.Span(children="chikungunya", className="keyword"),
                            html.Span(children="CHIKV", className="keyword"),
                            html.Span(children="arbovirus", className="keyword"),
                            html.Span(children="case report form", className="keyword"),
                            html.Span(children="CRF", className="keyword"),
                            html.Span(children="ISARIC", className="keyword"),
                            html.Span(children="BRIDGE", className="keyword"),
                            html.Span(children="ARC", className="keyword"),
                            html.Span(
                                children="harmonised data collection",
                                className="keyword",
                            ),
                            html.Span(
                                children="clinical characterisation",
                                className="keyword",
                            ),
                            html.Span(
                                children="outbreak preparedness", className="keyword"
                            ),
                            html.Span(children="REDCap", className="keyword"),
                            html.Span(children="acute infection", className="keyword"),
                        ],
                        className="keyword-container",
                    ),
                ],
                className="section",
            ),
            html.Section(
                children=[
                    html.H3(children="Resources", className="section-title"),
                    html.Div(
                        children=[
                            html.A(
                                children=[
                                    html.Div(children="↗", className="resource-icon"),
                                    html.Div(
                                        [
                                            html.Div(
                                                children="https://isaric.org/resources/data/case-report-forms/",
                                                className="resource-url",
                                            )
                                        ]
                                    ),
                                ],
                                className="resource-link",
                                href="https://isaric.org/resources/data/case-report-forms/",
                                target="_blank",
                            ),
                            html.A(
                                children=[
                                    html.Div(children="↗", className="resource-icon"),
                                    html.Div(
                                        [
                                            html.Div(
                                                children="https://bridge.isaric.org/",
                                                className="resource-url",
                                            )
                                        ]
                                    ),
                                ],
                                className="resource-link",
                                href="https://bridge.isaric.org/",
                                target="_blank",
                            ),
                            html.A(
                                children=[
                                    html.Div(children="↗", className="resource-icon"),
                                    html.Div(
                                        [
                                            html.Div(
                                                children="https://github.com/ISARICResearch/ARC",
                                                className="resource-url",
                                            )
                                        ]
                                    ),
                                ],
                                className="resource-link",
                                href="https://github.com/ISARICResearch/ARC",
                                target="_blank",
                            ),
                            html.A(
                                children=[
                                    html.Div(children="↗", className="resource-icon"),
                                    html.Div(
                                        [
                                            html.Div(
                                                children="www.isaric.org",
                                                className="resource-url",
                                            )
                                        ]
                                    ),
                                ],
                                className="resource-link",
                                href="www.isaric.org",
                                target="_blank",
                            ),
                        ],
                        className="resource-list",
                    ),
                ],
                className="section",
            ),
        ]
    )


@pytest.fixture(scope="module")
def arc_1_6_0__crf_metadata_modal_content__chikungunya(
    arc_1_6_0__crf_metadata_modal_content__overview__chikungunya,
    arc_1_6_0__crf_metadata_modal_content__scientific_scope__chikungunya,
    arc_1_6_0__crf_metadata_modal_content__governance_and_contributors__chikungunya,
    arc_1_6_0__crf_metadata_modal_content__documentation_and_discoverability__chikungunya,
) -> CRFTemplateMetadataModalContent:
    return CRFTemplateMetadataModalContent(
        title="ARChetype Disease CRF | Chikungunya",
        overview_section=arc_1_6_0__crf_metadata_modal_content__overview__chikungunya,
        scientific_scope_section=arc_1_6_0__crf_metadata_modal_content__scientific_scope__chikungunya,
        governance_section=arc_1_6_0__crf_metadata_modal_content__governance_and_contributors__chikungunya,
        documentation_section=arc_1_6_0__crf_metadata_modal_content__documentation_and_discoverability__chikungunya,
    )
