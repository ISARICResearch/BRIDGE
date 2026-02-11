from contextvars import copy_context
from datetime import date, datetime
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bridge.callbacks import generate


@pytest.mark.parametrize(
    "n_clicks, json_data, selected_version_data, selected_language_data, checked_presets, crf_name, output_files,"
    "browser_info, expected_output",
    [
        (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            ("", None, None, None, None, None),
        ),
        (
            1,
            "{}",
            None,
            None,
            None,
            None,
            None,
            None,
            ("", None, None, None, None, None),
        ),
    ],
)
def test_on_generate_click_no_action(
    n_clicks,
    json_data,
    selected_version_data,
    selected_language_data,
    checked_presets,
    crf_name,
    output_files,
    browser_info,
    expected_output,
):
    output = get_output_on_generate_click(
        n_clicks,
        json_data,
        selected_version_data,
        selected_language_data,
        checked_presets,
        crf_name,
        output_files,
        browser_info,
    )

    assert output == expected_output


@pytest.mark.parametrize(
    "selected_language_data, browser_info, expected_output",
    [
        (
            {"selected_language": "English"},
            "Chrome/139.0.0.0 Safari/537.36",
            (
                "",
                "UEsDBBQAAAAAANJmQVvCdv2k",
                "UEsDBBQAAAAAANJmQVvCdv2k",
                "UEsDBBQAAAAAANJmQVvCdv2k",
                "UEsDBBQAAAAAANJmQVvCdv2k",
                "UEsDBBQAAAAAANJmQVvCdv2k",
            ),
        ),
        (
            {"selected_language": "French"},
            "Safari/537.36",
            (
                "",
                "UEsDBBQAAAAAANJmQVvCdv2k",
                None,
                None,
                None,
                None,
            ),
        ),
    ],
)
@mock.patch("bridge.callbacks.generate.dcc.send_bytes")
@mock.patch("bridge.callbacks.generate.paper_word.df_to_word")
@mock.patch("bridge.callbacks.generate.paper_crf.generate_completion_guide")
@mock.patch("bridge.callbacks.generate.paper_crf.generate_paperlike_pdf")
@mock.patch("bridge.callbacks.generate._generate_crf")
@mock.patch("bridge.callbacks.generate.datetime")
@mock.patch("bridge.callbacks.generate.get_crf_name", return_value="test_crf")
@mock.patch("bridge.callbacks.generate.get_trigger_id", return_value="crf_generate")
def test_on_generate_click(
    _mock_trigger_id,
    _mock_crf_name,
    mock_date,
    mock_crf_csv,
    mock_paperlike_pdf,
    mock_guide_pdf,
    mock_review_word,
    mock_send_bytes,
    selected_language_data,
    browser_info,
    expected_output,
):
    mock_date.today.return_value = datetime(2025, 9, 30)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    n_clicks = 1
    json_data = (
        "{" '"columns":["Form"],' '"index":[0],' '"data":[["presentation"]]' "}"
    )  # This isn't being used, but needs to be readable
    selected_version_data = {"selected_version": "v1.1.2"}
    checked_presets = [[], [], [], [], []]
    crf_name = "test"
    output_files = [
        "redcap_xml",
        "redcap_csv",
        "paper_like",
        "paper_word",
    ]
    mock_pdf = b"%PDF-1.4\n%\x93\x8c\x8b\x9e ReportLab Generated PDF document https://www.reportlab.com\n"
    data = {
        "Variable / Field Name": ["subjid", "inclu_disease", "inclu_consentdes"],
        "Form Name": ["presentation", "presentation", "presentation"],
        "Field Type": ["text", "radio", "descriptive"],
        "Field Label": [
            "Participant Identification Number (PIN)",
            "Suspected or confirmed infection",
            '<div class=""rich-text-field-label""><h5 style=""text-align: center;""><span style=""color: #236fa1;"">Consent:</span></h5></div>',
        ],
    }
    df = pd.DataFrame.from_dict(data)

    mock_crf_csv.return_value = df
    mock_paperlike_pdf.return_value = mock_pdf
    mock_guide_pdf.return_value = mock_pdf
    mock_send_bytes.return_value = "UEsDBBQAAAAAANJmQVvCdv2k"
    mock_review_word.return_value = b"PK\x03\x04\x14\x00\x00\x00\x08"

    output = get_output_on_generate_click(
        n_clicks,
        json_data,
        selected_version_data,
        selected_language_data,
        checked_presets,
        crf_name,
        output_files,
        browser_info,
    )
    assert output == expected_output


@pytest.mark.parametrize(
    "n_clicks, json_data, selected_version_data, selected_language_data, checked_presets, crf_name, output_files,"
    "browser_info, expected_output",
    [
        (
            1,
            '{"columns":["Form"], "index":[0], "data":[["presentation"]]}',
            None,
            None,
            None,
            None,
            None,
            None,
            ("", None, None, None, None, None),
        ),
    ],
)
@mock.patch("bridge.callbacks.generate.get_trigger_id", return_value="crf_not_generate")
def test_on_generate_click_wrong_trigger_id(
    _mock_trigger_id,
    n_clicks,
    json_data,
    selected_version_data,
    selected_language_data,
    checked_presets,
    crf_name,
    output_files,
    browser_info,
    expected_output,
):
    output = get_output_on_generate_click(
        n_clicks,
        json_data,
        selected_version_data,
        selected_language_data,
        checked_presets,
        crf_name,
        output_files,
        browser_info,
    )

    assert output == expected_output


def get_output_on_generate_click(
    n_clicks,
    json_data,
    selected_version_data,
    selected_language_data,
    checked_presets,
    crf_name,
    output_files,
    browser_info,
):
    def run_callback():
        return generate.on_generate_click(
            n_clicks,
            json_data,
            selected_version_data,
            selected_language_data,
            checked_presets,
            crf_name,
            output_files,
            browser_info,
        )

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


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

    df_output = generate._custom_alignment(df_datadicc)
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

    df_output = generate._generate_crf(df_datadicc)

    assert_frame_equal(df_output, df_expected)
