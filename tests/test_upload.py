import json
from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from pandas.testing import assert_frame_equal

import bridge.callbacks.upload as upload


@pytest.mark.parametrize(
    "upload_filename, upload_contents, expected_output",
    [
        (None, None, (dash.no_update, dash.no_update)),
        ('template_test_v1_1_2_English_2025-09-16.csv', None,
         ({'upload_version': 'v1.1.2'}, {'upload_language': 'English'},)),
    ]
)
def test_on_upload_crf(upload_filename, upload_contents, expected_output):
    def run_callback(filename, contents):
        return upload.on_upload_crf(filename, contents)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        upload_filename,
        upload_contents,
    )
    assert output == expected_output


@mock.patch('bridge.callbacks.upload.logger')
def test_on_upload_crf_exception(mock_logger):
    with pytest.raises(AttributeError):
        upload.on_upload_crf('template_English_2025-09-16.csv', None)


@mock.patch('bridge.callbacks.upload.arc.get_translations', return_value={'other': 'Other'})
def test_update_for_upload_list_selected(mock_get_translations):
    data = {
        'Form': ['presentation', 'presentation'],
        'Section': ['INCLUSION CRITERIA', 'DEMOGRAPHICS'],
        'Variable': ['inclu_disease', 'demog_country'],
        'Answer Options': [None, None]
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    data = {
        'Variable': ['inclu_disease', 'demog_country'],
        'Ulist Selected': ['Adenovirus|Andes virus infection (hantavirus)', 'Aland Islands'],
        'Multilist Selected': [None, None],
    }
    df_list_upload = pd.DataFrame.from_dict(data)
    list_variable_choices = ('[["inclu_disease", '
                             '[[1, "Adenovirus", 0],[2, "Andes virus infection (hantavirus)", 0],[3, "Argentine haemorrhagic fever (Junin virus)", 0]]], '
                             '["demog_country", '
                             '[[1, "Afghanistan", 0],[2, "Aland Islands", 0]]]]')
    list_type = 'Ulist'
    language = 'English'
    (df_datadicc, list_variable_choices_updated) = upload.update_for_upload_list_selected(df_datadicc, df_list_upload,
                                                                                          list_variable_choices,
                                                                                          list_type, language)

    data = {
        'Form': ['presentation', 'presentation'],
        'Section': ['INCLUSION CRITERIA', 'DEMOGRAPHICS'],
        'Variable': ['inclu_disease', 'demog_country'],
        'Answer Options': ['1, Adenovirus | 2, Andes virus infection (hantavirus) | 88, Other',
                           '2, Aland Islands | 88, Other'],
    }
    df_datadicc_expected = pd.DataFrame.from_dict(data)
    assert_frame_equal(df_datadicc, df_datadicc_expected)

    list_variable_choices_expected = (
        '[["inclu_disease", '
        '[[1, "Adenovirus", 1], [2, "Andes virus infection (hantavirus)", 1], [3, "Argentine haemorrhagic fever (Junin virus)", 0], "88, Other"]], '
        '["demog_country", '
        '[[1, "Afghanistan", 0], [2, "Aland Islands", 1], "88, Other"]]]')

    assert list_variable_choices_updated == list_variable_choices_expected


def test_load_upload_arc_version_language_not_triggered():
    trigger = None
    upload_version_data = None
    upload_language_data = None
    selected_version_data = None
    selected_language_data = None

    output = get_output_load_upload_arc_version_language(trigger, upload_version_data, upload_language_data,
                                                         selected_version_data, selected_language_data)

    assert output == (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                      False, None, dash.no_update, dash.no_update)


@pytest.fixture
def triggered_trigger():
    trigger = [{'prop_id': 'upload-version-store.data', 'value': {'upload_version': 'v1.1.2'}}, {
        'prop_id': 'upload-language-store.data', 'value': {'upload_language': 'English'}}]
    return trigger


def test_load_upload_arc_version_language_no_update(triggered_trigger):
    upload_version_data = {'upload_version': 'v1.1.2'}
    upload_language_data = {'upload_language': 'English'}
    selected_version_data = {'selected_version': 'v1.1.2'}
    selected_language_data = {'selected_language': 'English'}

    output = get_output_load_upload_arc_version_language(triggered_trigger, upload_version_data, upload_language_data,
                                                         selected_version_data, selected_language_data)

    assert output == (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                      True, None, dash.no_update, dash.no_update)


@mock.patch('bridge.callbacks.upload.logger')
@mock.patch('bridge.callbacks.upload.Language.get_version_language_related_data')
def test_load_upload_arc_version_language_json_error(mock_error, mock_logger, triggered_trigger):
    mock_error.return_value = (None, None, None, None, None, None)
    mock_error.side_effect = json.JSONDecodeError('msg', '', 1)

    upload_version_data = {'upload_version': 'v1.1.2'}
    upload_language_data = {'upload_language': 'English'}
    selected_version_data = {'selected_version': 'v1.1.3'}
    selected_language_data = {'selected_language': 'English'}

    output = get_output_load_upload_arc_version_language(triggered_trigger, upload_version_data, upload_language_data,
                                                         selected_version_data, selected_language_data)

    assert output == (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                      False, None, dash.no_update, dash.no_update)


@mock.patch('bridge.callbacks.upload.logger')
@mock.patch('bridge.callbacks.upload.Language.get_version_language_related_data')
def test_load_upload_arc_version_language(mock_error, mock_logger, triggered_trigger):
    data = {
        'Form': ['presentation', 'presentation'],
        'Section': ['INCLUSION CRITERIA', 'DEMOGRAPHICS'],
        'Variable': ['inclu_disease', 'demog_country'],
    }
    df_upload_version = pd.DataFrame.from_dict(data)
    version_commit = 'abc123'
    version_grouped_presets = {'ARChetype Disease CRF': ['Covid', 'Dengue', 'Mpox', 'H5Nx'],
                               'ARChetype Syndromic CRF': ['ARI'], 'Recommended Outcomes': ['Dengue'],
                               'Score': ['CharlsonCI'], 'UserGenerated': ['Oropouche']}
    version_accordion_items = ['Some accordian items']
    version_ulist_variable_choices = 'Some ulist variable choices'
    version_multilist_variable_choices = 'Some multilist variable choices'

    mock_error.return_value = (df_upload_version, version_commit, version_grouped_presets, version_accordion_items,
                               version_ulist_variable_choices, version_multilist_variable_choices)

    upload_version_data = {'upload_version': 'v1.1.2'}
    upload_language_data = {'upload_language': 'Finnish'}
    selected_version_data = {'selected_version': 'v1.1.3'}
    selected_language_data = {'selected_language': 'English'}

    output = get_output_load_upload_arc_version_language(triggered_trigger, upload_version_data, upload_language_data,
                                                         selected_version_data, selected_language_data)

    assert output == (
        {'selected_version': 'v1.1.2'},
        {'selected_language': 'Finnish'},
        {'commit': version_commit},
        version_accordion_items,
        version_grouped_presets,
        df_upload_version.to_json(date_format='iso', orient='split'),
        True,
        None,
        version_ulist_variable_choices,
        version_multilist_variable_choices,
    )


def get_output_load_upload_arc_version_language(trigger,
                                                upload_version_data,
                                                upload_language_data,
                                                selected_version_data,
                                                selected_language_data):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return upload.load_upload_arc_version_language(upload_version_data,
                                                       upload_language_data,
                                                       selected_version_data,
                                                       selected_language_data)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


def test_update_output_upload_crf_not_triggered():
    trigger = None
    upload_crf_ready = None
    upload_version_data = None
    upload_language_data = None
    upload_crf_contents = None
    upload_version_lang_datadicc_saved = None
    upload_version_lang_ulist_saved = None
    upload_version_lang_multilist_saved = None

    output = get_output_update_output_upload_crf(trigger,
                                                 upload_crf_ready,
                                                 upload_version_data,
                                                 upload_language_data,
                                                 upload_crf_contents,
                                                 upload_version_lang_datadicc_saved,
                                                 upload_version_lang_ulist_saved,
                                                 upload_version_lang_multilist_saved)

    assert output == (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)


@mock.patch('bridge.callbacks.upload.html.Div', return_value=None)
@mock.patch('bridge.callbacks.upload.update_for_upload_list_selected')
@mock.patch('bridge.callbacks.upload.arc.get_tree_items', return_value={})
def test_update_output_upload_crf(mock_get_tree_items, mock_update_for_upload_list, mock_html_div):
    data = {
        'Form': ['here is some mock output'],
        'Answer Options': ['because it is tested elsewhere'],
    }
    df_mock = pd.DataFrame.from_dict(data)
    list_mock = ['Some', ['mock', 'output', 'list']]
    mock_update_for_upload_list.return_value = (df_mock, list_mock)

    trigger = [{'prop_id': 'upload-crf-ready.data', 'value': True}]
    upload_crf_ready = True
    upload_version_data = {'upload_version': 'v1.1.2'}
    upload_language_data = {'upload_language': 'English'}
    upload_crf_contents = 'data:text/csv;base64,VmFyaWFibGUsVWxpc3QgU2VsZWN0ZWQsTXVsdGlsaXN0IFNlbGVjdGVkCmRlbW9nX2NvdW50cnksQWZnaGFuaXN0YW58QWxhbmQgSXNsYW5kc3xBbGJhbmlhLAo='
    upload_version_lang_datadicc_saved = '{"columns":["Form","Section","Variable"], "index":[0], "data":[["presentation", "DEMOGRAPHICS", "demog_country"]]}'
    upload_version_lang_ulist_saved = None
    upload_version_lang_multilist_saved = None

    output = get_output_update_output_upload_crf(trigger,
                                                 upload_crf_ready,
                                                 upload_version_data,
                                                 upload_language_data,
                                                 upload_crf_contents,
                                                 upload_version_lang_datadicc_saved,
                                                 upload_version_lang_ulist_saved,
                                                 upload_version_lang_multilist_saved)

    expected = (
        None,
        df_mock.to_json(date_format='iso', orient='split'),
        list_mock,
        list_mock,
        None,
    )
    assert output == expected


def get_output_update_output_upload_crf(trigger,
                                        upload_crf_ready,
                                        upload_version_data,
                                        upload_language_data,
                                        upload_crf_contents,
                                        upload_version_lang_datadicc_saved,
                                        upload_version_lang_ulist_saved,
                                        upload_version_lang_multilist_saved):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return upload.update_output_upload_crf(upload_crf_ready,
                                               upload_version_data,
                                               upload_language_data,
                                               upload_crf_contents,
                                               upload_version_lang_datadicc_saved,
                                               upload_version_lang_ulist_saved,
                                               upload_version_lang_multilist_saved)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output
