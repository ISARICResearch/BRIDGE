import json
from contextvars import copy_context

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bridge.callbacks.save import get_checked_data_for_list, on_save_click


@pytest.fixture
def list_type():
    return 'Ulist'


@pytest.fixture
def checked_variables():
    return ['inclu_disease', 'demog_country']


@pytest.fixture
def df_list(list_type):
    data = ('[["inclu_disease", [[1, "Adenovirus", 0], [2, "Alice in Wonderland Syndrome", 1], [3, "Mpox", 0]]], '
            '["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 1], [3, "Finland", 1]]], '
            '["medi_antifungagent", [[1, "Amphotericin", 0], [2, "Clotrimazole", 0]]]]')
    df = pd.DataFrame(json.loads(data), columns=['Variable', 'Ulist'])
    return df


def test_get_checked_data_for_list(df_list, checked_variables, list_type):
    data_expected = {
        'inclu_disease': 'Alice in Wonderland Syndrome',
        'demog_country': 'Estonia|Finland',
    }
    df_expected = pd.DataFrame.from_dict(data_expected, orient='index').reset_index()
    df_expected.columns = ['Variable', f'{list_type} Selected']
    df_result = get_checked_data_for_list(df_list, checked_variables, list_type)
    assert_frame_equal(df_expected, df_result)


@pytest.mark.parametrize(
    "n_clicks, checked_variables, current_datadicc_saved, selected_version_data, selected_language_data, crf_name, ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        (None, None, pd.DataFrame(), None, None, None, None, None, ('', None)),
        (None, checked_variables, pd.DataFrame(), None, None, None, None, None, ('', None)),
        (1, None, pd.DataFrame(), None, None, None, None, None, ('', None)),
    ]
)
def test_on_save_click(n_clicks,
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
        return on_save_click(n_clicks, checked_variables, current_datadicc_saved, selected_version_data,
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
