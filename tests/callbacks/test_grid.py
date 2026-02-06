from contextvars import copy_context
from unittest import mock

import pandas as pd
import pytest
from statsmodels.compat.pandas import assert_frame_equal

from bridge.callbacks import grid

FOCUSED_CELL_INDEX = 0


@mock.patch("bridge.callbacks.grid.get_focused_cell_index", return_value=0)
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


@mock.patch("bridge.callbacks.grid.get_focused_cell_index", return_value=0)
@mock.patch("bridge.callbacks.grid.create_new_row_list")
@mock.patch("bridge.callbacks.grid.create_selected_dataframe")
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
    output = grid.get_focused_cell_index(row_data, focused_cell_index, checked)

    assert output == expected_output


@mock.patch("bridge.callbacks.grid.arc_core.get_variable_order")
@mock.patch("bridge.callbacks.grid.arc_core.add_transformed_rows")
@mock.patch("bridge.callbacks.grid.arc_core.units_transformation")
@mock.patch("bridge.callbacks.grid.arc_core.get_include_not_show")
def test_create_selected_dataframe(
    _mock_include, mock_units, mock_transformed_rows, mock_order
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

    df_output = grid.create_selected_dataframe(df_datadicc, checked, version)

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

    output_list = grid.create_new_row_list(df_selected)
    assert output_list == expected_list
