from contextvars import copy_context
from unittest import mock

import pandas as pd
import pytest

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
