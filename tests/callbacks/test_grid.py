from contextvars import copy_context
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from statsmodels.compat.pandas import assert_frame_equal

from bridge.callbacks import grid


@mock.patch("bridge.callbacks.grid._get_focused_cell_index", return_value=0)
@mock.patch("bridge.callbacks.grid._checked_updates_for_units")
def test_display_checked_in_grid_checked_empty(
    _mock_checked_updates, _mock_focused_cell_index
):
    checked = []
    _mock_checked_updates = []
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
        checked, current_datadicc_saved, 0, selected_version_data
    )

    expected_row_data_list = []
    expected_variables_json = '{"columns":[],"index":[],"data":[]}'

    assert output_row_data_list == expected_row_data_list
    assert output_variables_json == expected_variables_json


@mock.patch("bridge.callbacks.grid._get_focused_cell_index", return_value=0)
@mock.patch("bridge.callbacks.grid._create_new_row_list")
@mock.patch("bridge.callbacks.grid._create_selected_dataframe")
@mock.patch("bridge.callbacks.grid._checked_updates_for_units", return_value=[])
def test_display_checked_in_grid(
    _mock_checked_updates,
    mock_selected_dataframe,
    mock_new_row_list,
    _mock_focused_index,
):
    checked = ["not_empty"]
    _mock_checked_updates.return_value = ["not_empty"]
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
        checked, current_datadicc_saved, 0, selected_version_data
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
    "focused_cell_index, expected_output",
    [
        (None, None),
        (0, 0),
    ],
)
@mock.patch("bridge.callbacks.grid._get_latest_checked_variable")
def test_get_focused_cell_index_no_action(
    _mock_latest_checked, focused_cell_index, expected_output
):
    row_data = []
    checked = []
    output = grid._get_focused_cell_index(row_data, focused_cell_index, checked)
    if expected_output:
        assert output == expected_output
    else:
        assert not output


@mock.patch("bridge.callbacks.grid._get_latest_checked_variable")
def test_get_focused_cell_index(
    mock_latest_checked,
):
    mock_latest_checked.return_value = "demog_height"
    row_data = [
        {"Variable": np.nan},
        {"Variable": "subjid"},
        {"Variable": "demog_height"},
        {"Variable": "demog_height_units"},
    ]
    focused_cell_index = 3
    checked = ["demog_height", "demog_height_cm", "demog_height_in"]
    expected = 2
    output = grid._get_focused_cell_index(row_data, focused_cell_index, checked)
    assert output == expected


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
@mock.patch("bridge.arc.arc_core.get_variable_order")
@mock.patch("bridge.arc.arc_core.add_transformed_rows")
@mock.patch("bridge.callbacks.grid._units_transformation")
@mock.patch("bridge.callbacks.grid._get_include_not_show")
def test_create_selected_dataframe(
    _mock_include,
    mock_units,
    mock_transformed_rows,
    _mock_order,
    dynamic_units_conversion,
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

    df_output = grid._create_selected_dataframe(
        df_datadicc, checked, dynamic_units_conversion
    )

    assert_frame_equal(df_output, df_expected)


def test_create_new_row_list():
    data_selected = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
        ],
        "Section": [
            None,
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
        ],
        "Type": [
            "text",
            "text",
            "radio",
            "descriptive",
            "date_dmy",
        ],
        "Validation": [
            None,
            "number",
            None,
            None,
            "date_dmy",
        ],
        "Answer Options": [
            "Answer A | Answer B",
            "Answer C | Answer D | Answer E",
            "Answer 1 | Answer 2",
            "Answer 3 | Answer 4",
            "Answer 5 | Answer 6 | Answer 7",
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
            "Answer Options": "○ Answer 1   ○ Answer 2",
            "Form": "presentation",
            "IsSeparator": False,
            "Section": "DEMOGRAPHICS",
            "Type": "radio",
            "Validation": None,
        },
        {
            "Answer Options": "",
            "Form": "presentation",
            "IsDescriptive": True,
            "IsSeparator": False,
            "Section": "DEMOGRAPHICS",
            "Type": "descriptive",
            "Validation": None,
        },
        {
            "Answer Options": "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]",
            "Form": "presentation",
            "IsSeparator": False,
            "Section": "DEMOGRAPHICS",
            "Type": "date_dmy",
            "Validation": "date_dmy",
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


@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool")
def test_add_select_units_field_remove_select_units(mock_dynamic_units_bool):
    dynamic_units_conversion = False
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
            "Height",
            "Height",
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
            "Height",
            "Height",
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


def test_extract_parenthesis_content_no_brackets():
    text = "Neutrophils"
    output_str = grid._extract_parenthesis_content(text)
    assert not output_str


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


@mock.patch("bridge.callbacks.grid._get_options")
@mock.patch(
    "bridge.callbacks.grid._assign_units_answer_options", return_value=pd.DataFrame()
)
@mock.patch(
    "bridge.callbacks.grid._create_grid_units_dataframe", return_value=pd.DataFrame()
)
@mock.patch("bridge.callbacks.grid._get_units_language")
@mock.patch("bridge.callbacks.grid._add_select_units_field")
def test_units_transformation_no_data(
    _mock_select_units,
    _mock_language,
    _mock_units_dataframe,
    _mock_answers,
    _mock_options,
):
    selected_variables = pd.Series()
    df_datadicc = pd.DataFrame()
    dynamic_units_conversion = True
    (df_output, list_output) = grid._units_transformation(
        selected_variables, df_datadicc, dynamic_units_conversion
    )
    df_expected = pd.DataFrame()
    list_expected = []
    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected


@mock.patch("bridge.callbacks.grid._get_options", return_value="1, cm | 2, in")
@mock.patch("bridge.callbacks.grid._assign_units_answer_options")
@mock.patch("bridge.callbacks.grid._create_grid_units_dataframe")
@mock.patch("bridge.callbacks.grid._get_units_language", return_value="select units")
@mock.patch("bridge.callbacks.grid._add_select_units_field")
def test_units_transformation(
    mock_select_units,
    _mock_language,
    mock_units_dataframe,
    mock_answers,
    _mock_options,
):
    data = [
        "demog_height",
        "demog_height_units",
        "demog_height_cm",
        "demog_height_in",
    ]
    selected_variables = pd.Series(data, name="Variable")
    df_datadicc = pd.DataFrame()
    dynamic_units_conversion = True  # Not used
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
    mock_answers.return_value = df_units

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
            "Height",
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
            "1, cm | 2, in",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        "demog_height_cm",
        "demog_height_in",
    ]

    (df_output, list_output) = grid._units_transformation(
        selected_variables, df_datadicc, dynamic_units_conversion
    )

    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected


@mock.patch("bridge.callbacks.grid._get_options", return_value="1, cm | 2, in")
@mock.patch("bridge.callbacks.grid._assign_units_answer_options")
@mock.patch("bridge.callbacks.grid._create_grid_units_dataframe")
@mock.patch("bridge.callbacks.grid._get_units_language", return_value=None)
@mock.patch("bridge.callbacks.grid._add_select_units_field")
def test_units_transformation_remove_select_units(
    mock_select_units,
    _mock_language,
    mock_units_dataframe,
    mock_answers,
    _mock_options,
):
    data = [
        "demog_height",
        "demog_height_units",
        "demog_height_cm",
        "demog_height_in",
    ]
    selected_variables = pd.Series(data, name="Variable")
    df_datadicc = pd.DataFrame()
    dynamic_units_conversion = True  # Not used
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
    mock_answers.return_value = df_units

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
            "Height",
            "Height",
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
            "1, cm | 2, in",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        "demog_height_cm",
        "demog_height_in",
    ]

    (df_output, list_output) = grid._units_transformation(
        selected_variables, df_datadicc, dynamic_units_conversion
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
            "Height (select units)",
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
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
    expected_str = "select units"
    output_str = grid._get_units_language(df_datadicc, dynamic_units_conversion)
    assert output_str == expected_str


def test_get_units_language_remove_select_units():
    dynamic_units_conversion = False
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
            "Height",
            "Height",
            "Height (cm)",
            "Height (in)",
        ],
        "Question_english": [
            "Height",
            "Height",
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
    output = grid._get_units_language(df_datadicc, dynamic_units_conversion)
    assert not output


@mock.patch("bridge.callbacks.grid._assign_units_answer_options")
def test_create_grid_units_dataframe(_mock_answer_options):
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

    df_output = grid._create_grid_units_dataframe(df_datadicc, selected_variables)

    assert_frame_equal(df_output, df_expected)


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
def test_checked_updates_for_units_no_change(dynamic_units_conversion):
    checked = ["demog_height_cm", "demog_weight_in"]
    data = {
        "Variable": [
            "demog_height_cm",
            "demog_weight_in",
        ],
        "Sec_vari": [
            "demog_height",
            "demog_weight",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    expected = ["demog_height_cm", "demog_weight_in"]
    output = grid._checked_updates_for_units(
        checked, dynamic_units_conversion, df_datadicc
    )
    assert output == expected


@pytest.fixture()
def df_datadicc_new_units():
    data = {
        "Variable": [
            "labs_glucose",
            "labs_glucose_units",
            "labs_glucose_mmoll",
            "labs_glucose_mgdl",
            "labs_glucose_gl",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
            "number",
        ],
        "Sec_vari": [
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    return df_datadicc


@pytest.fixture()
def df_datadicc_old_units():
    data = {
        "Variable": [
            "labs_glucose",
            "labs_glucose_mmoll",
            "labs_glucose_mgdl",
            "labs_glucose_gl",
        ],
        "Question_english": [
            "Random blood glucose (select units)",
            "Random blood glucose (mmol/L)",
            "Random blood glucose (mg/dL)",
            "Random blood glucose (g/L)",
        ],
        "Sec_vari": [
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    return df_datadicc


def test_checked_updates_for_units_all_units_checked_dynamic_units_false(
    df_datadicc_new_units,
):
    checked = [
        "labs_glucose_units",
        "labs_glucose_mmoll",
        "labs_glucose_mgdl",
        "labs_glucose_gl",
    ]
    dynamic_units_conversion = False
    expected = [
        "labs_glucose",
        "labs_glucose_mmoll",
        "labs_glucose_mgdl",
        "labs_glucose_gl",
    ]
    output = grid._checked_updates_for_units(
        checked, dynamic_units_conversion, df_datadicc_new_units
    )
    assert output == expected


def test_checked_updates_for_units_all_units_checked_dynamic_units_true(
    df_datadicc_old_units,
):
    checked = [
        "labs_glucose",
        "labs_glucose_mmoll",
        "labs_glucose_mgdl",
        "labs_glucose_gl",
    ]
    dynamic_units_conversion = True
    expected = [
        "labs_glucose",
        "labs_glucose_mmoll",
        "labs_glucose_mgdl",
        "labs_glucose_gl",
    ]
    output = grid._checked_updates_for_units(
        checked, dynamic_units_conversion, df_datadicc_old_units
    )
    assert output == expected


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
def test_checked_updates_for_units_two_units(
    dynamic_units_conversion, df_datadicc_new_units, df_datadicc_old_units
):
    checked = [
        "labs_glucose_mmoll",
        "labs_glucose_gl",
    ]

    expected = [
        "labs_glucose_mmoll",
        "labs_glucose_gl",
        "labs_glucose",
    ]

    if not dynamic_units_conversion:
        output = grid._checked_updates_for_units(
            checked, dynamic_units_conversion, df_datadicc_new_units
        )
    else:
        output = grid._checked_updates_for_units(
            checked, dynamic_units_conversion, df_datadicc_old_units
        )

    assert output == expected


@pytest.mark.parametrize(
    "dynamic_units_conversion",
    [
        True,
        False,
    ],
)
def test_checked_updates_for_units_one_unit(
    dynamic_units_conversion, df_datadicc_new_units, df_datadicc_old_units
):
    checked = [
        "labs_glucose_mgdl",
    ]

    expected = [
        "labs_glucose_mgdl",
    ]

    if not dynamic_units_conversion:
        output = grid._checked_updates_for_units(
            checked, dynamic_units_conversion, df_datadicc_old_units
        )
    else:
        output = grid._checked_updates_for_units(
            checked, dynamic_units_conversion, df_datadicc_old_units
        )

    assert output == expected


def test_get_latest_checked_variable_single_checked():
    checked = ["a_single_variable"]
    df_row_data = pd.DataFrame()  # Not used
    expected = "a_single_variable"
    output = grid._get_latest_checked_variable(checked, df_row_data)
    assert output == expected


def test_get_latest_checked_variable_multiple_checked_not_in_row_data():
    checked = [
        "demog_height",
        "demog_height_cm",
        "demog_height_in",
    ]
    data = {
        "Variable": [
            "demog_height",
        ],
    }
    df_row_data = pd.DataFrame(data)
    expected = "demog_height"
    output = grid._get_latest_checked_variable(checked, df_row_data)
    assert output == expected


def test_get_latest_checked_variable_multiple_checked_in_row_data():
    checked = [
        "PRESENTATION-DEMOGRAPHICS-VARI-healthcare-GROUP",
        "demog_healthcare",
        "demog_healthcare_ptfacing",
        "demog_healthcare_expbiosample",
    ]
    data = {
        "Variable": [
            "demog_healthcare_expbiosample",
        ],
    }
    df_row_data = pd.DataFrame(data)
    expected = "demog_healthcare_expbiosample"
    output = grid._get_latest_checked_variable(checked, df_row_data)
    assert output == expected


def test_get_latest_checked_variable_multiple_checked_plus_header():
    checked = [
        "nborn_motherpin",
        "nborn_motherincl",
        "NEONATE-NEONATE DETAILS",
    ]
    data = {
        "Variable": [
            "nborn_motherpin",
            "nborn_motherincl",
            "NEONATE-NEONATE DETAILS",
        ],
    }
    df_row_data = pd.DataFrame(data)
    expected = "nborn_motherincl"
    output = grid._get_latest_checked_variable(checked, df_row_data)
    assert output == expected


def test_get_options_dynamic_false():
    dynamic_units_conversion = False
    data = {
        "Answer Options": [
            "1, mmol/L",
            "3, g/L",
        ],
    }
    df_matching_rows = pd.DataFrame(data)

    expected = "1, mmol/L | 3, g/L"
    output = grid._get_options(df_matching_rows, dynamic_units_conversion)

    assert output == expected


def test_get_options_dynamic_true():
    dynamic_units_conversion = True
    data = {
        "Question": [
            "Random blood glucose (mmol/L)",
            "Random blood glucose (g/L)",
        ],
    }
    df_matching_rows = pd.DataFrame(data)

    expected = "1, mmol/L | 2, g/L"
    output = grid._get_options(df_matching_rows, dynamic_units_conversion)

    assert output == expected


def test_assign_units_answer_options_dynamic_false():
    dynamic_units_conversion = False
    data = {
        "Variable": [
            "labs_glucose",
            "labs_glucose_units",
            "labs_glucose_mmoll",
            "labs_glucose_mgdl",
            "labs_glucose_gl",
        ],
        "Sec_vari": [
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
            "labs_glucose",
        ],
        "Answer Options": [
            None,
            "1, mmol/L | 2, mg/dL | 3, g/L",
            None,
            None,
            None,
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    data_units = {
        "Variable": [
            "labs_glucose_mmoll",
            "labs_glucose_gl",
        ],
        "Question": [
            "Random blood glucose (mmol/L)",
            "Random blood glucose (g/L)",
        ],
    }
    df_units = pd.DataFrame.from_dict(data_units)

    data_expected = {
        "Variable": [
            "labs_glucose_mmoll",
            "labs_glucose_gl",
        ],
        "Question": [
            "Random blood glucose (mmol/L)",
            "Random blood glucose (g/L)",
        ],
        "Answer Options": [
            "1, mmol/L",
            "3, g/L",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = grid._assign_units_answer_options(
        df_datadicc, df_units, dynamic_units_conversion
    )
    assert_frame_equal(df_output, df_expected)


def test_assign_units_answer_options_dynamic_true():
    dynamic_units_conversion = True
    df_datadicc = pd.DataFrame()  # Not used
    data = {
        "Mock Data": [
            "some made up data",
        ],
    }
    df_units = pd.DataFrame.from_dict(data)

    df_output = grid._assign_units_answer_options(
        df_datadicc, df_units, dynamic_units_conversion
    )
    assert_frame_equal(df_output, df_units)
