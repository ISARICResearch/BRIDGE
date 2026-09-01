# -- IMPORTS --

# -- Standard libraries --
from contextvars import copy_context
from unittest import mock

# -- 3rd party libraries --
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

# -- Internal libraries --
from bridge.utils.crf import (
    clean_crf_metadata,
    DocumentationCRFTemplateMetadataSection,
    get_selected_crf_presets,
    get_crf_name,
    GovernanceCRFTemplateMetadataSection,
    OverviewCRFTemplateMetadataSection,
    ScientificScopeCRFTemplateMetadataSection,
)


@pytest.mark.parametrize(
    "grouped_presets, checked_values, expected_output",
    [
        (
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            [True, False, False, False, False, False],
            (("test_section1", "test_option1__first_selected"),),
        ),
        (
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3__second_selected",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            [True, False, True, False, False, False],
            (
                ("test_section1", "test_option1__first_selected"),
                ("test_section1", "test_option3__second_selected"),
            ),
        ),
        (
            {
                "test_section1": [
                    "test_option1",
                    "test_option2__first_selected",
                    "test_option3",
                ],
                "test_section2": [
                    "test_option4",
                    "test_option5__second_selected",
                    "test_option6",
                ],
            },
            [False, True, False, False, True, False],
            (
                ("test_section1", "test_option2__first_selected"),
                ("test_section2", "test_option5__second_selected"),
            ),
        ),
    ],
)
@mock.patch("bridge.utils.crf.logger")
def test_get_selected_crf_presets(
    _mock_logger, grouped_presets, checked_values, expected_output
):
    received_output = get_selected_crf_presets(grouped_presets, checked_values)

    assert expected_output == received_output


@pytest.mark.parametrize(
    "name, checked, grouped_presets, expected_output",
    [
        (["name1", "name2", "name3"], [], None, "name1"),
        (
            None,
            [True, False, False, False, False, False],
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            "test_option1__first_selected",
        ),
        (
            None,
            [True, False, False, True, False, False],
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": [
                    "test_option4__first_selected",
                    "test_option5",
                    "test_option6",
                ],
            },
            "test_option1__first_selected",
        ),
    ],
)
@mock.patch("bridge.utils.crf.logger")
def test_get_crf_name(_mock_logger, name, checked, grouped_presets, expected_output):
    def run_callback(crf_name, checked_values, grouped_presets):
        return get_crf_name(
            crf_name, checked_values, grouped_presets=(grouped_presets or None)
        )

    ctx = copy_context()
    output = ctx.run(run_callback, name, checked, grouped_presets)
    assert output == expected_output


@pytest.mark.parametrize(
    "crf_metadata, expected_output",
    [
        # An example case where no cleaning is required
        (
            pd.DataFrame().assign(
                A=["A1", "A2", "A3"], B=["B1", "B2", "B3"], C=["C1", "C2", "C3"]
            ),
            pd.DataFrame().assign(
                A=["A1", "A2", "A3"], B=["B1", "B2", "B3"], C=["C1", "C2", "C3"]
            ),
        ),
        # An example case where cleaning is required
        (
            pd.DataFrame().assign(
                A=["A1", "Fake A2", "A3"],
                B=["Example B1", "B2", "B3"],
                C=["C1", "C2", "C3@example.org"],
            ),
            pd.DataFrame().assign(
                A=["A1", "Unknown", "A3"],
                B=["Unknown", "B2", "B3"],
                C=["C1", "C2", "Unknown"],
            ),
        ),
    ],
)
def test_clean_crf_metadata(crf_metadata, expected_output):
    received_output = clean_crf_metadata(crf_metadata)
    assert_frame_equal(received_output, expected_output)


class TestOverviewCRFTemplateMetadataSection:
    def test_overview_crf_template_metadata_section(self):
        expected_data = {
            "section_name": "test_section_name",
            "description": "test_description",
            "metadata": (
                ("test_metadata_key1", "test_metadata_key1_value"),
                ("test_metadata_key2", "test_metadata_key2_value"),
            ),
        }
        test_section = OverviewCRFTemplateMetadataSection(
            section_name="test_section_name",
            description="test_description",
            metadata=(
                ("test_metadata_key1", "test_metadata_key1_value"),
                ("test_metadata_key2", "test_metadata_key2_value"),
            ),
        )
        assert test_section.section_name == expected_data["section_name"]
        assert test_section.description == expected_data["description"]
        assert test_section.metadata == expected_data["metadata"]
        assert hash(test_section) == hash(
            OverviewCRFTemplateMetadataSection(**expected_data)
        )


class TestScientificScopeCRFTemplateMetadataSection:
    def test_scientific_scope_crf_template_metadata_section(self):
        expected_data = {
            "research_questions": (
                "test_research_question1",
                "test_research_question2",
            ),
            "syndrome": "test_syndrome",
            "pathogens": (
                "test_pathogen1",
                "test_pathogen2",
            ),
            "setting": "test_setting",
            "geographic_scope": "test_geographic_scope",
            "syndrome_definition": "test_syndrome_definition",
            "target_population": "test_target_population",
            "inclusion_criteria": "test_inclusion_criteria",
            "exclusion_criteria": "test_exclusion_criteria",
        }
        test_section = ScientificScopeCRFTemplateMetadataSection(
            research_questions=(
                "test_research_question1",
                "test_research_question2",
            ),
            syndrome="test_syndrome",
            pathogens=(
                "test_pathogen1",
                "test_pathogen2",
            ),
            setting="test_setting",
            geographic_scope="test_geographic_scope",
            syndrome_definition="test_syndrome_definition",
            target_population="test_target_population",
            inclusion_criteria="test_inclusion_criteria",
            exclusion_criteria="test_exclusion_criteria",
        )
        assert test_section.research_questions == expected_data["research_questions"]
        assert test_section.syndrome == expected_data["syndrome"]
        assert test_section.pathogens == expected_data["pathogens"]
        assert test_section.setting == expected_data["setting"]
        assert test_section.geographic_scope == expected_data["geographic_scope"]
        assert test_section.syndrome_definition == expected_data["syndrome_definition"]
        assert test_section.target_population == expected_data["target_population"]
        assert test_section.inclusion_criteria == expected_data["inclusion_criteria"]
        assert test_section.exclusion_criteria == expected_data["exclusion_criteria"]
        assert hash(test_section) == hash(
            ScientificScopeCRFTemplateMetadataSection(**expected_data)
        )


class TestGovernanceCRFTemplateMetadataSection:
    def test_governance_crf_template_metadata_section(self):
        expected_data = {
            "authors": (
                "test_author1",
                "test_author2",
            ),
            "approvers": (
                "test_approver1",
                "test_approver2",
            ),
            "affiliations": (
                "test_affiliation1",
                "test_affiliation2",
            ),
            "contacts": (
                ("test_contact1_name", "test_contact1_email"),
                ("test_contact2_name", "test_contact2_email"),
            ),
        }
        test_section = GovernanceCRFTemplateMetadataSection(
            authors=(
                "test_author1",
                "test_author2",
            ),
            approvers=(
                "test_approver1",
                "test_approver2",
            ),
            affiliations=(
                "test_affiliation1",
                "test_affiliation2",
            ),
            contacts=(
                ("test_contact1_name", "test_contact1_email"),
                ("test_contact2_name", "test_contact2_email"),
            ),
        )
        assert test_section.authors == expected_data["authors"]
        assert test_section.approvers == expected_data["approvers"]
        assert test_section.affiliations == expected_data["affiliations"]
        assert test_section.contacts == expected_data["contacts"]
        assert hash(test_section) == hash(
            GovernanceCRFTemplateMetadataSection(**expected_data)
        )


class TestDocumentationCRFTemplateMetadataSection:
    def test_documentation_crf_template_metadata_section(self):
        expected_data = {
            "keywords": (
                "test_keyword1",
                "test_keyword2",
            ),
            "links": (
                ("test_link1", "test_link1_url"),
                ("test_link2", "test_link2_url"),
            ),
        }
        test_section = DocumentationCRFTemplateMetadataSection(
            keywords=(
                "test_keyword1",
                "test_keyword2",
            ),
            links=(
                ("test_link1", "test_link1_url"),
                ("test_link2", "test_link2_url"),
            ),
        )
        assert test_section.keywords == expected_data["keywords"]
        assert test_section.links == expected_data["links"]
        assert hash(test_section) == hash(
            DocumentationCRFTemplateMetadataSection(**expected_data)
        )
