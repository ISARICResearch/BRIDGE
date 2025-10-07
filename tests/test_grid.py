from contextvars import copy_context
from unittest import mock

import numpy as np
import pandas as pd

from bridge.callbacks import grid


def test_display_checked_in_grid_checked_empty():
    checked = []
    current_datadicc_saved = ('{"columns":["Form", "Variable"],'
                              '"index":[0, 1],'
                              '"data":[["presentation", "inclu_disease"]]}')

    (output_column_defs,
     output_row_defs,
     output_variables_json) = get_output_display_checked_in_grid(checked,
                                                                 current_datadicc_saved)

    expected_column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                            {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

    expected_row_defs = [{'options': '', 'question': ''},
                         {'options': '', 'question': ''}]

    expected_variables_json = '{"columns":[],"index":[],"data":[]}'

    assert output_column_defs == expected_column_defs
    assert output_row_defs == expected_row_defs
    assert output_variables_json == expected_variables_json


@mock.patch('bridge.callbacks.grid.arc.generate_daily_data_type')
@mock.patch('bridge.callbacks.grid.arc.get_variable_order')
@mock.patch('bridge.callbacks.grid.arc.add_transformed_rows')
@mock.patch('bridge.callbacks.grid.arc.get_select_units')
@mock.patch('bridge.callbacks.grid.arc.get_include_not_show')
def test_display_checked_in_grid(mock_include_not_show,
                                 mock_select_units,
                                 mock_add_transformed_rows,
                                 mock_variable_order,
                                 mock_daily_data_type):
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
        ],
        'Section': [
            None,
            'INCLUSION CRITERIA',
            'INCLUSION CRITERIA',
            'ONSET & PRESENTATION',
        ],
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_disease_otherl3',
            'pres_onsetdate',
        ],
        'Type': [
            'text',
            'user_list',
            'text',
            'date_dmy',
        ],
        'Question': [
            'Participant Identification Number (PIN)',
            'Suspected infection',
            'Specify other Suspected infection',
            'Onset date of earliest symptom',
        ],
        'Answer Options': [
            None,
            '33, Mpox | 88, Other',
            None,
            None,
        ],
        'Validation': [
            None,
            None,
            None,
            'date_dmy',
        ],
    }
    df_selected_variables = pd.DataFrame.from_dict(data)
    mock_include_not_show.return_value = df_selected_variables
    mock_select_units.return_value = (None, None)
    mock_daily_data_type.return_value = df_selected_variables

    (output_column_defs,
     output_row_defs,
     output_variables_json) = get_output_display_checked_in_grid(checked,
                                                                 current_datadicc_saved)

    expected_column_defs = [{'headerName': "Question", 'field': "Question", 'wrapText': True},
                            {'headerName': "Answer Options", 'field': "Answer Options", 'wrapText': True}]

    expected_row_defs = [{'Answer Options': '',
                          'Form': np.nan,
                          'IsSeparator': True,
                          'Question': 'PRESENTATION',
                          'Section': np.nan,
                          'SeparatorType': 'form',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '________________________________________',
                          'Form': 'presentation',
                          'IsSeparator': False,
                          'Question': 'Participant Identification Number (PIN)',
                          'Section': '',
                          'SeparatorType': np.nan,
                          'Type': 'text',
                          'Validation': '',
                          'Variable': 'subjid'},
                         {'Answer Options': '',
                          'Form': np.nan,
                          'IsSeparator': True,
                          'Question': 'INCLUSION CRITERIA',
                          'Section': np.nan,
                          'SeparatorType': 'section',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '○ Mpox   ○ Other',
                          'Form': 'presentation',
                          'IsSeparator': False,
                          'Question': 'Suspected infection',
                          'Section': 'INCLUSION CRITERIA',
                          'SeparatorType': np.nan,
                          'Type': 'user_list',
                          'Validation': '',
                          'Variable': 'inclu_disease'},
                         {'Answer Options': '________________________________________',
                          'Form': 'presentation',
                          'IsSeparator': False,
                          'Question': 'Specify other Suspected infection',
                          'Section': 'INCLUSION CRITERIA',
                          'SeparatorType': np.nan,
                          'Type': 'text',
                          'Validation': '',
                          'Variable': 'inclu_disease_otherl3'},
                         {'Answer Options': '',
                          'Form': np.nan,
                          'IsSeparator': True,
                          'Question': 'ONSET & PRESENTATION',
                          'Section': np.nan,
                          'SeparatorType': 'section',
                          'Type': np.nan,
                          'Validation': np.nan,
                          'Variable': np.nan},
                         {'Answer Options': '[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]',
                          'Form': 'presentation',
                          'IsSeparator': False,
                          'Question': 'Onset date of earliest symptom',
                          'Section': 'ONSET & PRESENTATION',
                          'SeparatorType': np.nan,
                          'Type': 'date_dmy',
                          'Validation': 'date_dmy',
                          'Variable': 'pres_onsetdate'}]

    expected_variables_json = (
        '{"columns":["Form","Section","Variable","Type","Question","Answer Options","Validation"],'
        '"index":[0,1,2,3],'
        '"data":['
        '["presentation","","subjid","text","Participant Identification Number (PIN)","",""],'
        '["presentation","INCLUSION CRITERIA","inclu_disease","user_list","Suspected infection","33, Mpox | 88, Other",""],'
        '["presentation","INCLUSION CRITERIA","inclu_disease_otherl3","text","Specify other Suspected infection","",""],'
        '["presentation","ONSET & PRESENTATION","pres_onsetdate","date_dmy","Onset date of earliest symptom","","date_dmy"]]}')

    assert output_column_defs == expected_column_defs
    assert output_row_defs == expected_row_defs
    assert output_variables_json == expected_variables_json


def get_output_display_checked_in_grid(checked_variables,
                                       current_datadicc):
    def run_callback(checked,
                     current_datadicc_saved):
        return grid.display_checked_in_grid(checked,
                                            current_datadicc_saved)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        checked_variables,
        current_datadicc,
    )

    return output
