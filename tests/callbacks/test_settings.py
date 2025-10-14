from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict

from bridge.callbacks import settings


@pytest.mark.parametrize(
    "version, expected_output",
    [
        (None, dash.no_update),
        ({'selected_version': 'v1.1.1'}, 'v1.1.1'),
    ]
)
def test_update_input_version(version, expected_output):
    def run_callback(data):
        return settings.update_input_version(data)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        version,
    )
    assert output == expected_output


@pytest.mark.parametrize(
    "language, expected_output",
    [
        (None, dash.no_update),
        ({'selected_language': 'English'}, 'English'),
    ]
)
def test_update_input_language(language, expected_output):
    def run_callback(data):
        return settings.update_input_language(data)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        language,
    )
    assert output == expected_output


def test_update_output_files_store():
    def run_callback(data):
        return settings.update_output_files_store(data)

    checked_values = [
        'redcap_xml',
        'redcap_csv',
        'paper_like'
    ]

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        checked_values,
    )
    assert output == checked_values


@pytest.mark.parametrize(
    "version_data, expected_output",
    [
        (None,
         (dash.no_update, dash.no_update)),
        ({'selected_version': 'v1.1.1'},
         (['Mock DropdownMenuItem', 'Mock DropdownMenuItem'], ['English', 'French'])),
    ]
)
@mock.patch('bridge.callbacks.settings.dbc.DropdownMenuItem', return_value='Mock DropdownMenuItem')
@mock.patch('bridge.callbacks.settings.ArcApiClient.get_arc_language_list_version',
            return_value=['English', 'French'])
def test_update_language_available_for_version(mock_language_list,
                                               mock_dropdown,
                                               version_data,
                                               expected_output):
    def run_callback(selected_version_data):
        return settings.update_language_available_for_version(selected_version_data)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        version_data,
    )
    assert output == expected_output


@pytest.mark.parametrize(
    "trigger, clicks_version, clicks_language, crf_ready, selected_version, selected_language, language_list, expected_output",
    [
        (None, [None, None, None], [None, None], True, None, None, [],
         (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
          dash.no_update, dash.no_update, dash.no_update)),
        (None, [None, 1, None, None], [None, None], False, None, None, [],
         (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
          False, dash.no_update, dash.no_update)),
    ]
)
def test_store_data_for_selected_version_language_no_action(trigger,
                                                            clicks_version,
                                                            clicks_language,
                                                            crf_ready,
                                                            selected_version,
                                                            selected_language,
                                                            language_list,
                                                            expected_output):
    output = get_output_store_data_for_selected_version_language(trigger,
                                                                 clicks_version,
                                                                 clicks_language,
                                                                 crf_ready,
                                                                 selected_version,
                                                                 selected_language,
                                                                 language_list)
    assert output == expected_output


@pytest.fixture
def mock_language_data_return_value():
    data = {
        'Form': ['presentation', 'presentation'],
        'Section': ['INCLUSION CRITERIA', 'DEMOGRAPHICS'],
        'Variable': ['inclu_disease', 'demog_country'],
    }
    df = pd.DataFrame.from_dict(data)
    return (
        df,
        'sha1234',
        [{'version': 'presets'}],
        ['version', 'accordion', 'items'],
        ['version', 'ulist', 'variable', 'choices'],
        ['version', 'multilist', 'variable', 'choices'],
    )


@pytest.mark.parametrize(
    "clicks_version, clicks_language, crf_ready, selected_version, selected_language, language_list, expected_output",
    [
        ([None, 1, None, None],
         [None, None, None],
         False,
         {'selected_version': 'v1.1.1'},
         {'selected_language': 'French'},
         ['English', 'French'],
         (
                 {'selected_version': 'v1.1.0'},  # trigger index = 0
                 {'selected_language': 'English'},
                 {'commit': 'sha1234'},
                 ['version', 'accordion', 'items'],
                 [{'version': 'presets'}],
                 '{"columns":["Form","Section","Variable"],"index":[0,1],'
                 '"data":[["presentation","INCLUSION CRITERIA","inclu_disease"]'
                 ',["presentation","DEMOGRAPHICS","demog_country"]]}',
                 True,
                 ['version', 'ulist', 'variable', 'choices'],
                 ['version', 'multilist', 'variable', 'choices']
         )),
        ([None, 1, None, None],
         [None, None, None],
         False,
         {'selected_version': 'v1.1.0'},
         {'selected_language': 'English'},
         ['English', 'French'],
         (dash.no_update,
          dash.no_update,
          dash.no_update,
          dash.no_update,
          dash.no_update,
          dash.no_update,
          False,
          dash.no_update,
          dash.no_update)),
    ]
)
@mock.patch('bridge.callbacks.settings.Language.get_version_language_related_data')
@mock.patch('bridge.callbacks.settings.arc_core.get_arc_versions',
            return_value=(['v1.1.0', 'v1.1.1', 'v1.1.2'], 'v1.1.2'))
@mock.patch('bridge.callbacks.settings.get_trigger_id', return_value='{"index":0,"type":"dynamic-version"}')
@mock.patch('bridge.callbacks.settings.logger')
def test_store_data_for_selected_version_language_dynamic_version(mock_logger,
                                                                  mock_trigger_id,
                                                                  mock_versions,
                                                                  mock_language_data,
                                                                  clicks_version,
                                                                  clicks_language,
                                                                  crf_ready,
                                                                  selected_version,
                                                                  selected_language,
                                                                  language_list,
                                                                  expected_output,
                                                                  mock_language_data_return_value):
    mock_language_data.return_value = mock_language_data_return_value

    output = get_output_store_data_for_selected_version_language(mock_trigger_id,
                                                                 clicks_version,
                                                                 clicks_language,
                                                                 crf_ready,
                                                                 selected_version,
                                                                 selected_language,
                                                                 language_list)
    assert output == expected_output


@pytest.mark.parametrize(
    "clicks_version, clicks_language, crf_ready, selected_version, selected_language, language_list, expected_output",
    [
        ([None, None, None, None],
         [None, None, 1],
         False,
         {'selected_version': 'v1.1.1'},
         {'selected_language': 'English'},
         ['English', 'French'],
         (
                 {'selected_version': 'v1.1.1'},
                 {'selected_language': 'French'},  # trigger index = 1
                 {'commit': 'sha1234'},
                 ['version', 'accordion', 'items'],
                 [{'version': 'presets'}],
                 '{"columns":["Form","Section","Variable"],"index":[0,1],'
                 '"data":[["presentation","INCLUSION CRITERIA","inclu_disease"]'
                 ',["presentation","DEMOGRAPHICS","demog_country"]]}',
                 True,
                 ['version', 'ulist', 'variable', 'choices'],
                 ['version', 'multilist', 'variable', 'choices']
         )),
    ]
)
@mock.patch('bridge.callbacks.settings.Language.get_version_language_related_data')
@mock.patch('bridge.callbacks.settings.arc_core.get_arc_versions',
            return_value=(['v1.1.0', 'v1.1.1', 'v1.1.2'], 'v1.1.2'))
@mock.patch('bridge.callbacks.settings.get_trigger_id', return_value='{"index":1,"type":"dynamic-language"}')
@mock.patch('bridge.callbacks.settings.logger')
def test_store_data_for_selected_version_language_dynamic_language(mock_logger,
                                                                   mock_trigger_id,
                                                                   mock_versions,
                                                                   mock_language_data,
                                                                   clicks_version,
                                                                   clicks_language,
                                                                   crf_ready,
                                                                   selected_version,
                                                                   selected_language,
                                                                   language_list,
                                                                   expected_output,
                                                                   mock_language_data_return_value):
    mock_language_data.return_value = mock_language_data_return_value

    output = get_output_store_data_for_selected_version_language(mock_trigger_id,
                                                                 clicks_version,
                                                                 clicks_language,
                                                                 crf_ready,
                                                                 selected_version,
                                                                 selected_language,
                                                                 language_list)
    assert output == expected_output


def get_output_store_data_for_selected_version_language(trigger,
                                                        clicks_version,
                                                        clicks_language,
                                                        crf_ready,
                                                        selected_version,
                                                        selected_language,
                                                        language_list):
    def run_callback(n_clicks_version,
                     n_clicks_language,
                     upload_crf_ready,
                     selected_version_data,
                     selected_language_data,
                     language_list_data):
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return settings.store_data_for_selected_version_language(n_clicks_version,
                                                                 n_clicks_language,
                                                                 upload_crf_ready,
                                                                 selected_version_data,
                                                                 selected_language_data,
                                                                 language_list_data)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        clicks_version,
        clicks_language,
        crf_ready,
        selected_version,
        selected_language,
        language_list
    )

    return output
