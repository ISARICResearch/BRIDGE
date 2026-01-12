from unittest import mock

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from bridge.arc import arc_core


def test_add_required_datadicc_columns():
    data = {
        "Section": [
            "INCLUSION CRITERIA",
            "CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing",
        ],
        "Variable": [
            "inclu_disease",
            "comor_chrcardiac_chf",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    df_new_columns = pd.DataFrame.from_dict(
        {
            "Sec": [
                "inclu",
                "comor",
            ],
            "vari": [
                "disease",
                "chrcardiac",
            ],
            "mod": [
                None,
                "chf",
            ],
            "Sec_name": [
                "INCLUSION CRITERIA",
                "CO-MORBIDITIES AND RISK FACTORS",
            ],
            "Expla": [
                None,
                " Existing prior to this current illness and is ongoing",
            ],
        }
    )
    df_expected = df_datadicc.join(df_new_columns)
    df_output = arc_core.add_required_datadicc_columns(df_datadicc)
    assert_frame_equal(df_output, df_expected)


@mock.patch("bridge.arc.arc_core.logger")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_arc_version_list")
def test_get_arc_versions(mock_get_versions, mock_logger):
    version_list = ["v1.0.0", "v1.1.0", "v1.1.1", "v1.1.2", "v1.1.3"]
    mock_get_versions.return_value = version_list

    (version_list_output, latest_version_output) = arc_core.get_arc_versions()

    assert version_list_output == version_list
    assert latest_version_output == "v1.1.3"


def test_get_variable_order():
    data = {
        "Sec": [
            "inclu",
            "inclu",
            "comor",
            "adsym",
        ],
        "vari": [
            "disease",
            "case",
            "chrcardiac",
            "resp",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    list_expected = [
        "inclu_disease",
        "inclu_case",
        "comor_chrcardiac",
        "adsym_resp",
    ]
    list_output = arc_core.get_variable_order(df_current_datadicc)
    assert list_output == list_expected


@mock.patch("bridge.arc.arc_core.logger")
@mock.patch("bridge.arc.arc_core.get_dependencies")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_dataframe_arc_sha")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_arc_version_sha")
def test_get_arc(mock_sha, mock_arc, mock_dependencies, mock_logger):
    sha_str = "sha123"
    mock_sha.return_value = sha_str

    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Question": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
        "preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff": [
            1,
            1,
            0,
        ],
        "preset_ARChetype Disease CRF_Dengue": [
            0,
            1,
            0,
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    mock_arc.return_value = df_datadicc

    data_dependencies = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Dependencies": [
            "[[subjid]]",
            "[subjid]",
            "[inclu_testreason, subjid]",
        ],
    }
    df_dependencies = pd.DataFrame.from_dict(data_dependencies)
    mock_dependencies.return_value = df_dependencies

    data_expected = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Question": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
        "preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff": [
            1,
            1,
            0,
        ],
        "preset_ARChetype Disease CRF_Dengue": [
            0,
            1,
            0,
        ],
        "Dependencies": [
            "[[subjid]]",
            "[subjid]",
            "[inclu_testreason, subjid]",
        ],
        "Branch": [
            "",
            "",
            "",
        ],
        "Question_english": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    preset_expected = [
        ["ARChetype Disease CRF", "Covid Adding Some Extra Stuff"],
        ["ARChetype Disease CRF", "Dengue"],
    ]

    version = "v1.1.1"
    (df_output, preset_output, commit_output) = arc_core.get_arc(version)

    assert_frame_equal(df_output, df_expected)
    assert preset_output == preset_expected
    assert commit_output == sha_str


def test_get_dependencies():
    data = {
        "Variable": [
            "subjid",
            "inclu_consent_date",
            "readm_prev_site",
            "treat_an",
            "treat_another",
            "medi_something",
            "medi_somethingunits",
        ],
        "Skip Logic": [
            np.nan,
            "[inclu_consent]='1'",
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[treat_dailydata]='1'",
            "[treat_dailydata]='1'",
            "[medi_treat()]='1'",
            "[medi_treat()]='1'",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        "Variable": [
            "subjid",
            "inclu_consent_date",
            "readm_prev_site",
            "treat_an",
            "treat_another",
            "medi_something",
            "medi_somethingunits",
        ],
        "Skip Logic": [
            np.nan,
            "[inclu_consent]='1'",
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[treat_dailydata]='1'",
            "[treat_dailydata]='1'",
            "[medi_treat()]='1'",
            "[medi_treat()]='1'",
        ],
        "Dependencies": [
            ["subjid"],
            ["inclu_consent", "subjid"],
            ["readm_prev", "readm_prev", "readm_prev", "subjid"],
            ["treat_dailydata", "subjid", "treat_another"],
            ["treat_dailydata", "subjid"],
            ["medi_treat", "subjid", "medi_somethingunits"],
            ["medi_treat", "subjid"],
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    df_output = arc_core.get_dependencies(df_datadicc)
    assert_frame_equal(df_output, df_expected)


def test_set_select_units():
    data = {
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
        ],
        "select units": [
            True,
            False,
            False,
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    data_expected = {
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
        ],
        "select units": [
            True,
            True,
            True,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    df_output = arc_core.set_select_units(df_current_datadicc)
    assert_frame_equal(df_output, df_expected)


def test_extract_parenthesis_content():
    text = "Neutrophils (select units)"
    output_str = arc_core.extract_parenthesis_content(text)
    expected_str = "select units"
    assert output_str == expected_str


def test_extract_parenthesis_content_multiple_brackets():
    text = "Neutrophils (AB) (CD) (EF) (select units)"
    output_str = arc_core.extract_parenthesis_content(text)
    expected_str = "select units"
    assert output_str == expected_str


def test_get_include_not_show():
    data = [
        "demog_age",
        "demog_sex",
        "demog_outcountry",
        "demog_country",
    ]
    selected_variables = pd.Series(data, name="Variable")
    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_disease_otherl3",
            "demog_age",
            "demog_age_units",
            "demog_sex",
            "demog_outcountry",
            "demog_country_otherl3",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        "Variable": [
            "demog_age",
            "demog_age_units",
            "demog_sex",
            "demog_outcountry",
            "demog_country_otherl3",
        ]
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc_core.get_include_not_show(selected_variables, df_current_datadicc)
    assert_frame_equal(df_output, df_expected)


@mock.patch("bridge.arc.arc_core.set_select_units")
@mock.patch(
    "bridge.arc.arc_core.extract_parenthesis_content", return_value="select units"
)
def test_get_select_units(mock_extract_parenthesis, mock_set_units):
    data = [
        "demog_height",
        "demog_height_cm",
        "demog_height_in",
    ]
    selected_variables = pd.Series(data, name="Variable")
    data = {
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Question": [
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
        ],
        "Question_english": [
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
        ],
        "Minimum": [
            np.nan,
            0,
            0,
        ],
        "Maximum": [
            np.nan,
            250,
            98,
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
        ],
        "mod": [None, "cm", "in"],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    df_units = pd.DataFrame.from_dict(
        {
            "select units": [
                True,
                True,
                True,
            ]
        }
    )
    df_mock_set_units = df_current_datadicc.join(df_units)
    mock_set_units.return_value = df_mock_set_units

    data_expected = {
        "Variable": [
            "demog_height",
            "demog_height_units",
        ],
        "Question": [
            "Height ",
            "Height (select units)",
        ],
        "Question_english": [
            "Height (cm)",
            "Height (cm)",
        ],
        "Minimum": [
            0,
            np.nan,
        ],
        "Maximum": [
            250,
            np.nan,
        ],
        "Sec": [
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
        ],
        "mod": [
            "cm",
            "cm",
        ],
        "select units": [
            True,
            True,
        ],
        "count": [
            2,
            2,
        ],
        "Answer Options": [
            None,
            "1,select units | 2,select units",
        ],
        "Type": [
            "text",
            "radio",
        ],
        "Validation": [
            "number",
            None,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        "demog_height_cm",
        "demog_height_in",
    ]

    (df_output, list_output) = arc_core.get_select_units(
        selected_variables, df_current_datadicc
    )

    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected


def test_add_transformed_rows():
    data = {
        "Variable": [
            "demog_height",
            "comor_unlisted",
        ],
    }
    df_selected_variables = pd.DataFrame.from_dict(data)
    data = {
        "Variable": [
            "demog_height",
            "comor_unlisted",
            "comor_unlisted_0item",
            "test_var_0item",
        ],
        "Sec": [
            "demog",
            "comor",
            "comor",
            "test",
        ],
        "vari": [
            "height",
            "unlisted",
            "unlisted",
            "var",
        ],
    }
    df_arc_var_units_selected = pd.DataFrame.from_dict(data)

    variable_order = [
        "demog_height",
        "test_var_0item",
        "comor_unlisted",
    ]

    data_expected = {
        "Variable": [
            "demog_height",
            "test_var_0item",
            "comor_unlisted",
            "comor_unlisted_0item",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc_core.add_transformed_rows(
        df_selected_variables, df_arc_var_units_selected, variable_order
    )

    assert_frame_equal(df_output, df_expected)


def test_custom_alignment():
    data = {
        "Variable / Field Name": [
            "text_field",
            "user_list_field",
            "radio_field",
            "radio_three_fields_over_40",
            "descriptive_field",
            "date_dmy_field",
            "checkbox_four_fields_under_40",
            "checkbox_field",
        ],
        "Field Type": [
            "text",
            "user_list",
            "radio",
            "radio",
            "descriptive",
            "date_dmy",
            "checkbox",
            "checkbox",
        ],
        "Choices, Calculations, OR Slider Labels": [
            None,
            "33, Mpox  | 88, Other",
            "1, Yes | 0, No | 99, Unknown",
            "1, Yeeeeeeees | 0, Nooooooo | 99, Unknown",
            None,
            None,
            "1, A | 2, B | 3, C | 4, D | 88, E",
            "1, Hunting | 2, Preparing | 88, Other",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    df_custom_aligment = pd.DataFrame.from_dict(
        {
            "Custom Alignment": [
                np.nan,
                np.nan,
                "RH",
                np.nan,
                np.nan,
                np.nan,
                np.nan,
                "RH",
            ],
        }
    )
    df_expected = df_datadicc.join(df_custom_aligment)

    df_output = arc_core._custom_alignment(df_datadicc)
    assert_frame_equal(df_output, df_expected)


def test_generate_crf():
    data = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "outcome",
        ],
        "Section": [
            None,
            "INCLUSION CRITERIA",
            "INCLUSION CRITERIA",
            "ONSET & PRESENTATION",
            "CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing",
            "RE-ADMISSION AND PREVIOUS PIN",
            "INTERVENTIONS: Record interventions given or prescribed from day of presentation to day of discharge.",
        ],
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_consent_date",
            "pres_firstsym",
            "comor_unlisted",
            "readm_prev_num",
            "inter_ivfluid_start",
        ],
        "Type": [
            "text",
            "user_list",
            "date_dmy",
            "multi_list",
            "list",
            "number",
            "datetime_dmy",
        ],
        "Question": [
            "Participant Identification Number (PIN)",
            "Suspected or confirmed infection",
            "Date of consent",
            "Symptom(s) during first 24 hours of illness (select all that apply)",
            "Other relevant comorbidity(s)",
            "Total number of previous admissions for this infection",
            "Date first IV fluid started",
        ],
        "Answer Options": [
            None,
            "33, Mpox  | 88, Other",
            None,
            "35, Fever | 54, Mucosal lesion | 69, Skin lesion | 88, Other",
            "1, Yes | 0, No | 99, Unknown",
            None,
            None,
        ],
        "Validation": [
            None,
            None,
            "date_dmy",
            None,
            None,
            "number",
            "datetime_dmy",
        ],
        "Minimum": [
            None,
            None,
            None,
            None,
            None,
            1,
            None,
        ],
        "Maximum": [
            None,
            None,
            "today",
            None,
            None,
            None,
            "today",
        ],
        "Skip Logic": [
            None,
            None,
            "[inclu_consent]='1'",
            None,
            None,
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[inter_ivfluid] ='1'",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        "Variable / Field Name": [
            "subjid",
            "inclu_disease",
            "inclu_consent_date",
            "pres_firstsym",
            "comor_unlisted",
            "readm_prev_num",
            "inter_ivfluid_start",
        ],
        "Form Name": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "outcome",
        ],
        "Section Header": [
            np.nan,
            "INCLUSION CRITERIA",
            np.nan,
            "ONSET & PRESENTATION",
            "CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing",
            "RE-ADMISSION AND PREVIOUS PIN",
            "INTERVENTIONS: Record interventions given or prescribed from day of presentation to day of discharge.",
        ],
        "Field Type": [
            "text",
            "radio",
            "text",
            "checkbox",
            "radio",
            "text",
            "text",
        ],
        "Field Label": [
            "Participant Identification Number (PIN)",
            "Suspected or confirmed infection",
            "Date of consent",
            "Symptom(s) during first 24 hours of illness (select all that apply)",
            "Other relevant comorbidity(s)",
            "Total number of previous admissions for this infection",
            "Date first IV fluid started",
        ],
        "Choices, Calculations, OR Slider Labels": [
            "",
            "33, Mpox  | 88, Other",
            "",
            "35, Fever | 54, Mucosal lesion | 69, Skin lesion | 88, Other",
            "1, Yes | 0, No | 99, Unknown",
            "",
            "",
        ],
        "Field Note": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Text Validation Type OR Show Slider Number": [
            "",
            "",
            "date_dmy",
            "",
            "",
            "number",
            "datetime_dmy",
        ],
        "Text Validation Min": [
            "",
            "",
            "",
            "",
            "",
            1,
            "",
        ],
        "Text Validation Max": [
            "",
            "",
            "today",
            "",
            "",
            "",
            "today",
        ],
        "Identifier?": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Branching Logic (Show field only if...)": [
            "",
            "",
            "[inclu_consent]='1'",
            "",
            "",
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[inter_ivfluid] ='1'",
        ],
        "Required Field?": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Custom Alignment": [
            "",
            "RH",
            "",
            "",
            "RH",
            "",
            "",
        ],
        "Question Number (surveys only)": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Matrix Group Name": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Matrix Ranking?": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        "Field Annotation": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc_core.generate_crf(df_datadicc)

    assert_frame_equal(df_output, df_expected)
