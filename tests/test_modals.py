import io
import json
from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from pandas.testing import assert_frame_equal

from bridge.callbacks import modals

SUBMIT_N_CLICKS_NONE = None
CANCEL_N_CLICKS_NONE = None
CURRENT_DATADICC_SAVED_NONE = None
MODAL_TITLE_NONE = None
MODAL_OPTIONS_CHECKED_NONE = None
CHECKED_NONE = None
ULIST_VARIABLE_CHOICES_SAVED_NONE = None
MULTILIST_VARIABLE_CHOICES_SAVED_NONE = None
SELECTED_VERSION_DATA_NONE = None
SELECTED_LANGUAGE_DATA_NONE = None


def test_determine_list_variable_choices():
    data = {
        'cod': [1, 15, 33],
        'Option': ['Adenovirus', 'HSV', 'Mpox'],
    }
    df_list_options_checked = pd.DataFrame.from_dict(data)
    data = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_disease_otherl2',
            'demog_country'
        ],
        'Answer Options': [
            '',
            '2, Andes virus',
            '',
            '',
        ]
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    other_text = 'Other'
    variable_submitted = 'inclu_disease'
    variable_choices_list = [
        ["inclu_disease",
         [
             [1, "Adenovirus", 0],
             [2, "Andes virus", 0],
             [15, "HSV", 0],
             [33, "Mpox", 0]
         ]],
        ["inclu_disease_otherl2",
         [
             [1, "Made this up", 0],
         ]],
        ["demog_country",
         [
             [1, "Afghanistan", 0],
             [2, "Aland Islands", 0]
         ]]
    ]
    df_output, list_output = modals.determine_list_variable_choices(variable_choices_list,
                                                                    variable_submitted,
                                                                    df_list_options_checked,
                                                                    df_datadicc,
                                                                    other_text)

    list_expected = [
        ['inclu_disease',
         [
             [1, 'Adenovirus', 1],
             [2, 'Andes virus', 0],
             [15, 'HSV', 1],
             [33, 'Mpox', 1]
         ]],
        ['inclu_disease_otherl2',
         [
             [1, 'Made this up', 0]
         ]],
        ['demog_country',
         [
             [1, 'Afghanistan', 0],
             [2, 'Aland Islands', 0]
         ]]
    ]
    data = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_disease_otherl2',
            'demog_country'
        ],
        'Answer Options': [
            '',
            '1, Adenovirus | 15, HSV | 33, Mpox | 88, Other',
            '2, Andes virus | 88, Other',
            '',
        ]
    }
    df_expected = pd.DataFrame.from_dict(data)

    assert list_output == list_expected
    assert_frame_equal(df_output, df_expected)


def test_on_modal_button_click_not_triggered():
    trigger = None
    output = get_output_on_modal_button_click(trigger,
                                              SUBMIT_N_CLICKS_NONE,
                                              CANCEL_N_CLICKS_NONE,
                                              CURRENT_DATADICC_SAVED_NONE,
                                              MODAL_TITLE_NONE,
                                              MODAL_OPTIONS_CHECKED_NONE,
                                              CHECKED_NONE,
                                              ULIST_VARIABLE_CHOICES_SAVED_NONE,
                                              MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
                                              SELECTED_VERSION_DATA_NONE,
                                              SELECTED_LANGUAGE_DATA_NONE)
    expected = (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@mock.patch('bridge.callbacks.modals.get_trigger_id', return_value='nothing_modal')
def test_on_modal_button_click_wrong_trigger(mock_trigger_id):
    output = get_output_on_modal_button_click(mock_trigger_id,
                                              SUBMIT_N_CLICKS_NONE,
                                              CANCEL_N_CLICKS_NONE,
                                              CURRENT_DATADICC_SAVED_NONE,
                                              MODAL_TITLE_NONE,
                                              MODAL_OPTIONS_CHECKED_NONE,
                                              CHECKED_NONE,
                                              ULIST_VARIABLE_CHOICES_SAVED_NONE,
                                              MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
                                              SELECTED_VERSION_DATA_NONE,
                                              SELECTED_LANGUAGE_DATA_NONE)
    expected = (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@mock.patch('bridge.callbacks.modals.get_trigger_id', return_value='modal_cancel')
def test_on_modal_button_click_modal_cancel(mock_trigger_id):
    output = get_output_on_modal_button_click(mock_trigger_id,
                                              SUBMIT_N_CLICKS_NONE,
                                              CANCEL_N_CLICKS_NONE,
                                              CURRENT_DATADICC_SAVED_NONE,
                                              MODAL_TITLE_NONE,
                                              MODAL_OPTIONS_CHECKED_NONE,
                                              CHECKED_NONE,
                                              ULIST_VARIABLE_CHOICES_SAVED_NONE,
                                              MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
                                              SELECTED_VERSION_DATA_NONE,
                                              SELECTED_LANGUAGE_DATA_NONE)
    expected = (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@pytest.mark.parametrize(
    "ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        ('[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
         '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
         (False,
          '{"columns":["Form","Variable"],"index":[0,1],"data":[["presentation","inclu_disease"],["presentation","inclu_disease"]]}',
          '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
          '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
          ['Just for checking'])),
        ('[["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 1], [3, "Finland", 1]]]]',
         '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
         (False,
          dash.no_update,
          dash.no_update,
          dash.no_update,
          dash.no_update)),
    ]
)
@mock.patch('bridge.callbacks.modals.html.Div', return_value=['Just for checking'])
@mock.patch('bridge.callbacks.modals.arc.get_tree_items', return_value={})
@mock.patch('bridge.callbacks.modals.determine_list_variable_choices')
@mock.patch('bridge.callbacks.modals.arc.get_translations', return_value={'other': 'Other'})
@mock.patch('bridge.callbacks.modals.get_trigger_id', return_value='modal_submit')
def test_on_modal_button_click_modal_submit(mock_trigger_id,
                                            mock_get_translations,
                                            mock_list_choices,
                                            mock_get_tree_items,
                                            mock_html_div,
                                            ulist_variable_choices_saved,
                                            multilist_variable_choices_saved,
                                            expected_output):
    submit_n_clicks = None
    cancel_n_clicks = None
    current_datadicc_saved = '{"columns":["Form", "Variable"], "index":[0, 1], "data":[["presentation", "inclu_disease"]]}'
    df_current_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient='split')
    modal_title = 'Suspected or confirmed infection [inclu_disease]'
    modal_options_checked = ['33_Mpox ', '1_Adenovirus', '10_Dengue ']
    checked = []
    selected_version_data = {'selected_version': 'v1.1.1'}
    selected_language_data = {'selected_language': 'English'}

    mock_list_choices.return_value = (df_current_datadicc, json.loads(ulist_variable_choices_saved))

    output = get_output_on_modal_button_click(mock_trigger_id,
                                              submit_n_clicks,
                                              cancel_n_clicks,
                                              current_datadicc_saved,
                                              modal_title,
                                              modal_options_checked,
                                              checked,
                                              ulist_variable_choices_saved,
                                              multilist_variable_choices_saved,
                                              selected_version_data,
                                              selected_language_data)

    assert output == expected_output


def get_output_on_modal_button_click(trigger,
                                     submit_n_clicks,
                                     cancel_n_clicks,
                                     current_datadicc_saved,
                                     modal_title,
                                     modal_options_checked,
                                     checked,
                                     ulist_variable_choices_saved,
                                     multilist_variable_choices_saved,
                                     selected_version_data,
                                     selected_language_data):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return modals.on_modal_button_click(submit_n_clicks,
                                            cancel_n_clicks,
                                            current_datadicc_saved,
                                            modal_title,
                                            modal_options_checked,
                                            checked,
                                            ulist_variable_choices_saved,
                                            multilist_variable_choices_saved,
                                            selected_version_data,
                                            selected_language_data)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


@pytest.mark.parametrize(
    "selected, ulist_variable_choices_saved, multilist_variable_choices_saved, is_open, current_datadicc_saved, expected_output",
    [
        ([], None, None, False, None,
         (False, '', '', '', '', {"display": "none"}, {"display": "none"}, [], [], [])),
    ]
)
def test_display_selected_nothing_selected(selected,
                                           ulist_variable_choices_saved,
                                           multilist_variable_choices_saved,
                                           is_open,
                                           current_datadicc_saved,
                                           expected_output):
    output = get_output_display_selected(selected,
                                         ulist_variable_choices_saved,
                                         multilist_variable_choices_saved,
                                         is_open,
                                         current_datadicc_saved)
    assert output == expected_output


@mock.patch('bridge.callbacks.modals.dbc.ListGroupItem', return_value=['List group item'])
@pytest.mark.parametrize(
    "selected, ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        (['inclu_disease'],
         '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
         '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
         (True,
          'This is the question [inclu_disease]',
          'This is the definition',
          'This is the completion guideline',
          'This is the branch',
          {'maxHeight': '250px', 'overflowY': 'auto', 'padding': '20px'},
          {'display': 'none'},
          [{'label': '1, Adenovirus', 'value': '1_Adenovirus'},
           {'label': '2, Andes virus', 'value': '2_Andes virus'},
           {'label': '10, Dengue', 'value': '10_Dengue'},
           {'label': '33, Mpox ', 'value': '33_Mpox '}],
          ['10_Dengue', '33_Mpox '],
          [])
         ),
        (['inclu_disease'],
         '[["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 0]]]]',
         '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
         (True,
          'This is the question [inclu_disease]',
          'This is the definition',
          'This is the completion guideline',
          'This is the branch',
          {'display': 'none'},
          {'maxHeight': '250px', 'overflowY': 'auto'},
          [],
          [],
          [['List group item']])
         ),
    ]
)
def test_display_selected(mock_list_group_item,
                          selected,
                          ulist_variable_choices_saved,
                          multilist_variable_choices_saved,
                          expected_output):
    is_open = False
    current_datadicc_saved = (
        '{"columns":["Form", "Variable", "Question", "Definition", "Completion Guideline", "Branch", "Answer Options"],'
        '"index":[0, 1, 2, 3, 4, 5, 6],'
        '"data":['
        '["presentation",'
        '"inclu_disease",'
        '"This is the question",'
        '"This is the definition",'
        '"This is the completion guideline",'
        '"This is the branch",'
        '"These are the answer options"]]}')

    output = get_output_display_selected(selected,
                                         ulist_variable_choices_saved,
                                         multilist_variable_choices_saved,
                                         is_open,
                                         current_datadicc_saved)
    assert output == expected_output


def get_output_display_selected(selected,
                                ulist_variable_choices_saved,
                                multilist_variable_choices_saved,
                                is_open,
                                current_datadicc_saved):
    def run_callback():
        return modals.display_selected_in_modal(selected,
                                                ulist_variable_choices_saved,
                                                multilist_variable_choices_saved,
                                                is_open,
                                                current_datadicc_saved)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output
