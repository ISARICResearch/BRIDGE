from contextvars import copy_context
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from statsmodels.compat.pandas import assert_frame_equal

from bridge.callbacks import grid

FOCUSED_CELL_INDEX = 0


@mock.patch("bridge.callbacks.grid._get_focused_cell_index", return_value=0)
def test_display_checked_in_grid_checked_empty(_mock_focused_cell_index):
    checked = []
    current_datadicc_saved = (
        '{"columns":["Form", "Variable"],'
        '"index":[0, 1],'
        '"data":[["some_data", "for_the_mock"]]}'
    )
    selected_version_data = {"selected_version": "v1.1.2"}
    (
        output_row_data_list,
        output_variables_json,
        focused_cell_run_callback,
        focused_cell_index,
    ) = get_output_display_checked_in_grid(
        checked, current_datadicc_saved, FOCUSED_CELL_INDEX, selected_version_data
    )

    expected_row_data_list = []
    expected_variables_json = '{"columns":[],"index":[],"data":[]}'

    assert output_row_data_list == expected_row_data_list
    assert output_variables_json == expected_variables_json


@mock.patch("bridge.callbacks.grid._get_focused_cell_index", return_value=0)
@mock.patch("bridge.callbacks.grid._create_new_row_list")
@mock.patch("bridge.callbacks.grid._create_selected_dataframe")
def test_display_checked_in_grid(
    mock_selected_dataframe, mock_new_row_list, _mock_focused_index
):
    checked = ["not_empty"]
    current_datadicc_saved = (
        '{"columns":["Form", "Variable"],'
        '"index":[0, 1],'
        '"data":[["some_data", "for_the_mock"]]}'
    )
    selected_version_data = {"selected_version": "v1.1.2"}
    data = {
        "Variable": [
            "some_more_data",
        ],
    }
    df_selected = pd.DataFrame(data)
    mock_selected_dataframe.return_value = df_selected
    mock_new_row_list.return_value = [
        {
            "Question": "some dummy data",
            "Type": "number",
        },
        {
            "Question": "some more dummy data",
            "Type": "radio",
        },
        {
            "Question": "some group dummy data (to be dropped)",
            "Type": "group",
        },
    ]

    (
        output_row_data_list,
        output_variables_json,
        focused_cell_run_callback,
        focused_cell_index,
    ) = get_output_display_checked_in_grid(
        checked, current_datadicc_saved, FOCUSED_CELL_INDEX, selected_version_data
    )

    expected_row_data_list = [
        {
            "Question": "some dummy data",
            "Type": "number",
        },
        {
            "Question": "some more dummy data",
            "Type": "radio",
        },
    ]
    expected_variables_json = (
        '{"columns":["Variable"],"index":[0],"data":[["some_more_data"]]}'
    )

    assert output_row_data_list == expected_row_data_list
    assert output_variables_json == expected_variables_json


def get_output_display_checked_in_grid(
    checked_variables, current_datadicc, focused_cell, version_data
):
    def run_callback(
        checked, current_datadicc_saved, focused_cell_index, selected_version_data
    ):
        return grid.display_checked_in_grid(
            checked, current_datadicc_saved, focused_cell_index, selected_version_data
        )

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        checked_variables,
        current_datadicc,
        focused_cell,
        version_data,
    )

    return output


@pytest.mark.parametrize(
    "row_data, focused_cell_index, checked, expected_output",
    [
        ([], 5, [], 5),
        (
            [
                {
                    "Question": "Another question",
                    "Type": "descriptive",
                    "Variable": "another_variable",
                    "Section": "INCLUSION CRITERIA",
                },
                {
                    "Question": "Consent:",
                    "Type": "descriptive",
                    "Variable": "inclu_consentdes",
                    "Section": "INCLUSION CRITERIA",
                },
            ],
            16,
            [
                "inclu_consentdes",
                "A FAKE UPPERCASE VARIABLE",
                "fake_variable_not_in_row",
            ],
            1,
        ),
        (
            [
                {
                    "Question": "Another question",
                    "Type": "descriptive",
                    "Variable": "another_variable",
                    "Section": "INCLUSION CRITERIA",
                },
                {
                    "Question": "Gender",
                    "Type": "radio",
                    "Variable": "demog_gender",
                    "Section": "DEMOGRAPHICS",
                },
                {
                    "Question": "Country",
                    "Type": "user_list",
                    "Variable": "demog_country",
                    "Section": "DEMOGRAPHICS",
                },
                {
                    "Question": "Consent:",
                    "Type": "descriptive",
                    "Variable": "inclu_consentdes",
                    "Section": "INCLUSION CRITERIA",
                },
            ],
            7,
            ["demog_country", "demog_gender"],
            2,
        ),
        (
            [
                {
                    "Question": "Another question",
                    "Type": "descriptive",
                    "Variable": "another_variable",
                    "Section": "INCLUSION CRITERIA",
                },
                {
                    "Question": "Gender",
                    "Type": "radio",
                    "Variable": "demog_gender",
                    "Section": "DEMOGRAPHICS",
                },
                {
                    "Question": "Country",
                    "Type": "user_list",
                    "Variable": "demog_country",
                    "Section": "DEMOGRAPHICS",
                },
                {
                    "Question": "Consent:",
                    "Type": "descriptive",
                    "Variable": "inclu_consentdes",
                    "Section": "INCLUSION CRITERIA",
                },
            ],
            7,
            ["demog_country", "demog_gender"],
            2,
        ),
    ],
)
def test_get_focused_cell_index(row_data, focused_cell_index, checked, expected_output):
    output = grid._get_focused_cell_index(row_data, focused_cell_index, checked)

    assert output == expected_output


@mock.patch("bridge.arc.arc_core.get_variable_order")
@mock.patch("bridge.arc.arc_core.add_transformed_rows")
@mock.patch("bridge.callbacks.grid._units_transformation")
@mock.patch("bridge.callbacks.grid._get_include_not_show")
def test_create_selected_dataframe(
    _mock_include, mock_units, mock_transformed_rows, _mock_order
):
    data_datadicc = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
            "demog_weight_kg",
        ],
        "Dependencies": [
            ["subjid", "another_variable"],
            ["subjid", "another_variable 2"],
            ["subjid", "another_variable 3"],
            ["subjid", "another_variable 4"],
            ["subjid", "another_variable 5"],
        ],
    }
    df_datadicc = pd.DataFrame(data_datadicc)
    checked = [
        "PRESENTATION-DEMOGRAPHICS-VARI-height-GROUP",
        "demog_height",
        "demog_height_cm",
        "demog_height_in",
    ]
    version = "v1.2.1"

    unit_variables_to_delete = ["demog_height_units", "demog_weight_kg"]
    mock_units.return_value = [df_datadicc, unit_variables_to_delete]
    mock_transformed_rows.return_value = df_datadicc

    data_expected = {
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Dependencies": [
            ["subjid", "another_variable"],
            ["subjid", "another_variable 3"],
            ["subjid", "another_variable 4"],
        ],
    }
    df_expected = pd.DataFrame(data_expected)

    df_output = grid._create_selected_dataframe(df_datadicc, checked, version)

    assert_frame_equal(df_output, df_expected)


def test_create_new_row_list():
    data_selected = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
        ],
        "Section": [
            None,
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
        ],
        "Type": [
            "text",
            "text",
            "radio",
        ],
        "Validation": [
            None,
            "number",
            None,
        ],
        "Answer Options": [
            "Answer A | Answer B",
            "",
            "",
        ],
    }
    df_selected = pd.DataFrame.from_dict(data_selected)

    expected_list = [
        {
            "Answer Options": "",
            "IsSeparator": True,
            "Question": "PRESENTATION",
            "SeparatorType": "form",
        },
        {
            "Answer Options": "________________________________________",
            "Form": "presentation",
            "IsSeparator": False,
            "Section": None,
            "Type": "text",
            "Validation": None,
        },
        {
            "Answer Options": "",
            "IsSeparator": True,
            "Question": "DEMOGRAPHICS",
            "SeparatorType": "section",
        },
        {
            "Answer Options": "________________________________________",
            "Form": "presentation",
            "IsSeparator": False,
            "Section": "DEMOGRAPHICS",
            "Type": "text",
            "Validation": "number",
        },
        {
            "Answer Options": "○",
            "Form": "presentation",
            "IsSeparator": False,
            "Section": "DEMOGRAPHICS",
            "Type": "radio",
            "Validation": None,
        },
    ]

    output_list = grid._create_new_row_list(df_selected)
    assert output_list == expected_list


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool")
def test_add_select_units_field(mock_dynamic_units_bool, dynamic_units_conversion):
    mock_dynamic_units_bool.return_value = dynamic_units_conversion
    data = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
        ],
        "Question_english": [
            "Height (select units)",
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    # Adjust the input to reflect what is in ARC for the different versions
    if dynamic_units_conversion:
        df_datadicc = df_datadicc.drop(
            df_datadicc[df_datadicc["Variable"] == "demog_height_units"].index
        )
        del df_datadicc["Validation"]

    data_expected = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
        ],
        "Question_english": [
            "Height (select units)",
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
        ],
        "select units": [
            True,
            False,
            True,
            True,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    # Adjust the output to reflect what is in ARC for the different versions
    if dynamic_units_conversion:
        df_expected = df_expected.drop(
            df_expected[df_expected["Variable"] == "demog_height_units"].index
        )
        del df_expected["Validation"]

    df_output = grid._add_select_units_field(df_datadicc, dynamic_units_conversion)
    assert_frame_equal(df_output, df_expected)


def test_extract_parenthesis_content():
    text = "Neutrophils (select units)"
    output_str = grid._extract_parenthesis_content(text)
    expected_str = "select units"
    assert output_str == expected_str


def test_extract_parenthesis_content_multiple_brackets():
    text = "Neutrophils (AB) (CD) (EF) (select units)"
    output_str = grid._extract_parenthesis_content(text)
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

    df_output = grid._get_include_not_show(selected_variables, df_current_datadicc)
    assert_frame_equal(df_output, df_expected)


@mock.patch("bridge.callbacks.grid._create_units_dataframe")
@mock.patch("bridge.callbacks.grid._get_units_language", return_value="select units")
@mock.patch("bridge.callbacks.grid._add_select_units_field")
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool")
def test_units_transformation(
    _mock_bool, mock_select_units, _mock_language, mock_units_dataframe
):
    data = [
        "demog_height",
        "demog_height_units",
        "demog_height_cm",
        "demog_height_in",
    ]
    selected_variables = pd.Series(data, name="Variable")
    df_datadicc = pd.DataFrame()
    version = "v1.1.2"
    mock_select_units.return_value = pd.DataFrame()
    data = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "Type": [
            "number",
            "number",
        ],
        "Question": [
            "Height (cm)",
            "Height (in)",
        ],
        "Validation": [
            "number",
            "number",
        ],
        "Minimum": [
            0,
            0,
        ],
        "Maximum": [
            250,
            98,
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
            "in",
        ],
        "count": [
            2,
            2,
        ],
    }
    df_units = pd.DataFrame.from_dict(data)
    mock_units_dataframe.return_value = df_units
    data_expected = {
        "Variable": [
            "demog_height",
            "demog_height_units",
        ],
        "Type": [
            "text",
            "radio",
        ],
        "Question": [
            "Height ",
            "Height (select units)",
        ],
        "Validation": [
            "number",
            None,
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
        "count": [
            2,
            2,
        ],
        "Answer Options": [
            None,
            "1,cm | 2,in",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        "demog_height_cm",
        "demog_height_in",
    ]

    (df_output, list_output) = grid._units_transformation(
        selected_variables, df_datadicc, version
    )

    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
def test_get_units_language(dynamic_units_conversion):
    data = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
        ],
        "Question": [
            "Height(select units)",
            "Height(select units)",
            "Height(select cm)",
            "Height(select in)",
        ],
        "Question_english": [
            "Height(select units)",
            "Height(select units)",
            "Height(select cm)",
            "Height(select in)",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    # Adjust the input to reflect what is in ARC for the different versions
    if dynamic_units_conversion:
        df_datadicc = df_datadicc.drop(
            df_datadicc[df_datadicc["Variable"] == "demog_height_units"].index
        )
    expected_str = "select units"
    output_str = grid._get_units_language(df_datadicc, dynamic_units_conversion)
    assert output_str == expected_str


def test_create_units_dataframe():
    data_datadicc = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "select units": [
            True,
            False,
            True,
            True,
        ],
        "mod": [
            None,
            "units",
            "cm",
            "in",
        ],
        "Sec": [
            "demog",
            "demog",
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data_datadicc)
    data_selected = [
        "demog_height",
        "demog_height_units",
        "demog_height_cm",
        "demog_height_in",
    ]
    selected_variables = pd.Series(data_selected, name="Variable")
    data_expected = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "select units": [
            True,
            True,
        ],
        "mod": [
            "cm",
            "in",
        ],
        "Sec": [
            "demog",
            "demog",
        ],
        "vari": [
            "height",
            "height",
        ],
        "count": [
            2,
            2,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = grid._create_units_dataframe(df_datadicc, selected_variables)

    assert_frame_equal(df_output, df_expected)
