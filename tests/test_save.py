import json
from contextvars import copy_context
from datetime import date
from datetime import datetime
from unittest import mock

import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from pandas.testing import assert_frame_equal

import bridge.callbacks.save as save


@pytest.fixture
def df_list():
    data = (
        '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Alice in Wonderland Syndrome", 1], [3, "Mpox", 0]]], '
        '["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 1], [3, "Finland", 1]]], '
        '["medi_antifungagent", [[1, "Amphotericin", 0], [2, "Clotrimazole", 0]]]]'
    )
    df = pd.DataFrame(json.loads(data), columns=['Variable', 'Ulist'])
    return df


def test_get_checked_data_for_list(df_list):
    list_type = 'Ulist'
    checked_variables = ['inclu_disease', 'demog_country']
    data_expected = {
        'inclu_disease': 'Alice in Wonderland Syndrome',
        'demog_country': 'Estonia|Finland',
    }
    df_expected = pd.DataFrame.from_dict(data_expected, orient='index').reset_index()
    df_expected.columns = ['Variable', f'{list_type} Selected']
    df_result = save.get_checked_data_for_list(df_list, checked_variables, list_type)
    assert_frame_equal(df_expected, df_result)


@pytest.mark.parametrize(
    "n_clicks, checked_variables, current_datadicc_saved, selected_version_data, selected_language_data, crf_name, ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        (None, None, pd.DataFrame(), None, None, None, None, None, ('', None)),
        (None, ['inclu_disease', 'demog_country'], pd.DataFrame(), None, None, None, None, None, ('', None)),
        (1, None, pd.DataFrame(), None, None, None, None, None, ('', None)),
    ]
)
def test_on_save_click_no_action(n_clicks,
                                 checked_variables,
                                 current_datadicc_saved,
                                 selected_version_data,
                                 selected_language_data,
                                 crf_name,
                                 ulist_variable_choices_saved,
                                 multilist_variable_choices_saved,
                                 expected_output):
    def run_callback(n_clicks, checked_variables, current_datadicc_saved, selected_version_data, selected_language_data,
                     crf_name, ulist_variable_choices_saved, multilist_variable_choices_saved):
        return save.on_save_click(n_clicks, checked_variables, current_datadicc_saved, selected_version_data,
                                  selected_language_data, crf_name, ulist_variable_choices_saved,
                                  multilist_variable_choices_saved)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        n_clicks,
        checked_variables,
        current_datadicc_saved,
        selected_version_data,
        selected_language_data,
        crf_name,
        ulist_variable_choices_saved,
        multilist_variable_choices_saved
    )
    assert output == expected_output


@mock.patch('bridge.callbacks.save.datetime', return_value=datetime(2025, 9, 30))
def test_on_save_click(mock_date):
    mock_date.today.return_value = datetime(2025, 9, 30)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    trigger = {"prop_id": "crf_save.n_clicks"}
    n_clicks = 1
    checked_variables = ['inclu_disease']
    current_datadicc_saved = '{"columns":["Form","Section","Variable"], "index":[0,1,2], "data":[["presentation",null,"subjid"],["presentation","INCLUSION CRITERIA","inclu_disease"],["presentation","ONSET & PRESENTATION","pres_firstsym"]]}'
    selected_version_data = {'selected_version': 'v1.1.2'}
    selected_language_data = {'selected_language': 'English'}
    crf_name = 'test'
    ulist_variable_choices_saved = '[["inclu_disease", [[1, "Adenovirus", 1], [2, "Andes virus infection (hantavirus)", 0]]]]'
    multilist_variable_choices_saved = '[["pres_firstsym", [[1, "Abdominal pain", 1], [2, "Abnormal weight loss", 0]]]]'

    def run_callback(trigger, n_clicks, checked_variables, current_datadicc_saved, selected_version_data,
                     selected_language_data, crf_name, ulist_variable_choices_saved, multilist_variable_choices_saved):
        context_value.set(AttributeDict(**{"triggered_inputs": [trigger]}))

        # TODO
        # mocker.patch('bridge.utils.trigger_id.get_trigger_id', return_value='crf_save')
        # mocker.patch('bridge.utils.crf_name.get_crf_name', return_value='test')

        # with mock.patch('bridge.callbacks.save.datetime') as mock_date:
        return save.on_save_click(n_clicks, checked_variables, current_datadicc_saved, selected_version_data,
                                  selected_language_data, crf_name, ulist_variable_choices_saved,
                                  multilist_variable_choices_saved)

    # TODO: Test these
    # TODO: Need to mock other functions as well
    # mocker.patch('bridge.utils.trigger_id.get_trigger_id', return_value='crf_save')
    # mocker.patch('bridge.utils.crf_name.get_crf_name', return_value='test')
    # get_checked_data_for_list

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        trigger,
        n_clicks,
        checked_variables,
        current_datadicc_saved,
        selected_version_data,
        selected_language_data,
        crf_name,
        ulist_variable_choices_saved,
        multilist_variable_choices_saved,
    )
    assert output[1][
               'content'] == 'VmFyaWFibGUsVWxpc3QgU2VsZWN0ZWQsTXVsdGlsaXN0IFNlbGVjdGVkCmluY2x1X2Rpc2Vhc2UsQWRlbm92aXJ1cywK'
    assert output[1]['filename'] == f'template_{crf_name}_v1_1_2_English_2025-09-30.csv'
