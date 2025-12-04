from contextvars import copy_context
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from bridge.callbacks import grid

FOCUSED_CELL_INDEX = 0


@mock.patch('bridge.callbacks.grid.get_focused_cell_index', return_value=0)
def test_display_checked_in_grid_checked_empty(mock_focused_cell_index):
    checked = []
    current_datadicc_saved = ('{"columns":["Form", "Variable"],'
                              '"index":[0, 1],'
                              '"data":[["presentation", "inclu_disease"]]}')

    (output_row_defs,
     output_variables_json,
     focused_cell_run_callback,
     focused_cell_index) = get_output_display_checked_in_grid(checked,
                                                              current_datadicc_saved,
                                                              FOCUSED_CELL_INDEX)

    expected_row_defs = []
    expected_variables_json = '{"columns":[],"index":[],"data":[]}'

    assert output_row_defs == expected_row_defs
    assert output_variables_json == expected_variables_json


@mock.patch('bridge.callbacks.grid.get_focused_cell_index', return_value=0)
@mock.patch('bridge.callbacks.grid.arc_core.get_variable_order')
@mock.patch('bridge.callbacks.grid.arc_core.add_transformed_rows')
@mock.patch('bridge.callbacks.grid.arc_core.get_select_units')
@mock.patch('bridge.callbacks.grid.arc_core.get_include_not_show')
def test_display_checked_in_grid(mock_include_not_show,
                                 mock_select_units,
                                 mock_add_transformed_rows,
                                 mock_variable_order,
                                 mock_focused_cell_index):
    checked = ['inclu_disease']
    current_datadicc_saved = ('{"columns":["Form", "Variable", "Dependencies"],'
                              '"index":[0, 1, 2],'
                              '"data":[["presentation", "inclu_disease", "[subjid]"]]}')

    data = {
        'Form': [
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
        ],
        'Section': [
            None,
            'INCLUSION CRITERIA',
            'INCLUSION CRITERIA',
            'INCLUSION CRITERIA',
            'ONSET & PRESENTATION',
            'DEMOGRAPHICS',
        ],
        'Variable': [
            'subjid',
            'inclu_consentdes',
            'inclu_disease',
            'inclu_disease_otherl3',
            'pres_onsetdate',
            'demog_height_cm',
        ],
        'Type': [
            'text',
            'descriptive',
            'user_list',
            'text',
            'date_dmy',
            'number',
        ],
        'Question': [
            'Participant Identification Number (PIN)',
            'Consent:',
            'Suspected infection',
            'Specify other Suspected infection',
            'Onset date of earliest symptom',
            'Height (cm)',
        ],
        'Answer Options': [
            None,
            None,
            '33, Mpox | 88, Other',
            None,
            None,
            None,
        ],
        'Validation': [
            None,
            None,
            None,
            None,
            'date_dmy',
            'number',
        ],
    }
    delete_this_variables_with_units = [
        'demog_height_cm',
        'demog_height_in',
    ]
    df_selected_variables = pd.DataFrame.from_dict(data)
    mock_include_not_show.return_value = df_selected_variables
    mock_add_transformed_rows.return_value = df_selected_variables
    mock_select_units.return_value = (pd.DataFrame(),
                                      delete_this_variables_with_units)

    (output_row_defs,
     output_variables_json,
     focused_cell_run_callback,
     focused_cell_index) = get_output_display_checked_in_grid(checked,
                                                              current_datadicc_saved,
                                                              FOCUSED_CELL_INDEX)

    expected_row_defs = [{'Answer Options': '',
                          'Form': np.nan,
                          'IsDescriptive': np.nan,
                          'IsSeparator': True,
                          'Question': 'PRESENTATION',
                          'Section': np.nan,
                          'SeparatorType': 'form',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '________________________________________',
                          'Form': 'presentation',
                          'IsDescriptive': np.nan,
                          'IsSeparator': False,
                          'Question': 'Participant Identification Number (PIN)',
                          'Section': '',
                          'SeparatorType': np.nan,
                          'Type': 'text',
                          'Validation': '',
                          'Variable': 'subjid'},
                         {'Answer Options': '',
                          'Form': np.nan,
                          'IsDescriptive': np.nan,
                          'IsSeparator': True,
                          'Question': 'INCLUSION CRITERIA',
                          'Section': np.nan,
                          'SeparatorType': 'section',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '',
                          'Form': 'presentation',
                          'IsDescriptive': True,
                          'IsSeparator': False,
                          'Question': 'Consent:',
                          'Section': 'INCLUSION CRITERIA',
                          'SeparatorType': np.nan,
                          'Type': 'descriptive',
                          'Validation': '',
                          'Variable': 'inclu_consentdes'},
                         {'Answer Options': '○ Mpox   ○ Other',
                          'Form': 'presentation',
                          'IsDescriptive': np.nan,
                          'IsSeparator': False,
                          'Question': 'Suspected infection',
                          'Section': 'INCLUSION CRITERIA',
                          'SeparatorType': np.nan,
                          'Type': 'user_list',
                          'Validation': '',
                          'Variable': 'inclu_disease'},
                         {'Answer Options': '________________________________________',
                          'Form': 'presentation',
                          'IsDescriptive': np.nan,
                          'IsSeparator': False,
                          'Question': 'Specify other Suspected infection',
                          'Section': 'INCLUSION CRITERIA',
                          'SeparatorType': np.nan,
                          'Type': 'text',
                          'Validation': '',
                          'Variable': 'inclu_disease_otherl3'},
                         {'Answer Options': '',
                          'Form': np.nan,
                          'IsDescriptive': np.nan,
                          'IsSeparator': True,
                          'Question': 'ONSET & PRESENTATION',
                          'Section': np.nan,
                          'SeparatorType': 'section',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]',
                          'Form': 'presentation',
                          'IsDescriptive': np.nan,
                          'IsSeparator': False,
                          'Question': 'Onset date of earliest symptom',
                          'Section': 'ONSET & PRESENTATION',
                          'SeparatorType': np.nan,
                          'Type': 'date_dmy',
                          'Validation': 'date_dmy',
                          'Variable': 'pres_onsetdate'}]

    expected_variables_json = (
        '{"columns":["Form","Section","Variable","Type","Question","Answer Options","Validation"],'
        '"index":[0,1,2,3,4],'
        '"data":['
        '["presentation","","subjid","text","Participant Identification Number (PIN)","",""],'
        '["presentation","INCLUSION CRITERIA","inclu_consentdes","descriptive","Consent:","",""],'
        '["presentation","INCLUSION CRITERIA","inclu_disease","user_list","Suspected infection","33, Mpox | 88, Other",""],'
        '["presentation","INCLUSION CRITERIA","inclu_disease_otherl3","text","Specify other Suspected infection","",""],'
        '["presentation","ONSET & PRESENTATION","pres_onsetdate","date_dmy","Onset date of earliest symptom","","date_dmy"]]}')

    assert output_row_defs == expected_row_defs
    assert output_variables_json == expected_variables_json


def get_output_display_checked_in_grid(checked_variables,
                                       current_datadicc,
                                       focused_cell):
    def run_callback(checked,
                     current_datadicc_saved,
                     focused_cell_index):
        return grid.display_checked_in_grid(checked,
                                            current_datadicc_saved,
                                            focused_cell_index)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        checked_variables,
        current_datadicc,
        focused_cell,
    )

    return output


@pytest.mark.parametrize(
    "row_data, focused_cell_index, checked, expected_output",
    [
        ([], 5, [], 5),
        ([{'Question': 'Another question', 'Type': 'descriptive', 'Variable': 'another_variable',
           'Section': 'INCLUSION CRITERIA'},
          {'Question': 'Consent:', 'Type': 'descriptive', 'Variable': 'inclu_consentdes',
           'Section': 'INCLUSION CRITERIA'},
          ], 16, ['inclu_consentdes', 'A FAKE UPPERCASE VARIABLE', 'fake_variable_not_in_row'], 1),
        ([{'Question': 'Another question', 'Type': 'descriptive', 'Variable': 'another_variable',
           'Section': 'INCLUSION CRITERIA'},
          {'Question': 'Gender', 'Type': 'radio', 'Variable': 'demog_gender', 'Section': 'DEMOGRAPHICS'},
          {'Question': 'Country', 'Type': 'user_list', 'Variable': 'demog_country', 'Section': 'DEMOGRAPHICS'},
          {'Question': 'Consent:', 'Type': 'descriptive', 'Variable': 'inclu_consentdes',
           'Section': 'INCLUSION CRITERIA'},
          ], 7, ['demog_country', 'demog_gender'], 2),

        ([{'Question': 'Another question', 'Type': 'descriptive', 'Variable': 'another_variable',
           'Section': 'INCLUSION CRITERIA'},
          {'Question': 'Gender', 'Type': 'radio', 'Variable': 'demog_gender', 'Section': 'DEMOGRAPHICS'},
          {'Question': 'Country', 'Type': 'user_list', 'Variable': 'demog_country', 'Section': 'DEMOGRAPHICS'},
          {'Question': 'Consent:', 'Type': 'descriptive', 'Variable': 'inclu_consentdes',
           'Section': 'INCLUSION CRITERIA'},
          ], 7, ['demog_country', 'demog_gender'], 2),
    ]
)
def test_get_focused_cell_index(mocker,
                                row_data,
                                focused_cell_index,
                                checked,
                                expected_output):
    output = grid.get_focused_cell_index(row_data,
                                         focused_cell_index,
                                         checked)

    assert output == expected_output
