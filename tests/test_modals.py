from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
from dash._callback_context import context_value
from dash._utils import AttributeDict
from pandas.testing import assert_frame_equal

from bridge.callbacks import modals


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
    submit_n_clicks = None
    cancel_n_clicks = None
    current_datadicc_saved = None
    modal_title = None
    checked_options = None
    checked = None
    ulist_variable_choices_saved = None
    multilist_variable_choices_saved = None
    selected_version_data = None
    selected_language_data = None
    output = get_output_on_modal_button_click(trigger,
                                              submit_n_clicks,
                                              cancel_n_clicks,
                                              current_datadicc_saved,
                                              modal_title,
                                              checked_options,
                                              checked,
                                              ulist_variable_choices_saved,
                                              multilist_variable_choices_saved,
                                              selected_version_data,
                                              selected_language_data)
    expected = (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@mock.patch('bridge.callbacks.modals.get_trigger_id', return_value='nothing_modal')
def test_on_modal_button_click_wrong_trigger(mock_trigger_id):
    submit_n_clicks = None
    cancel_n_clicks = None
    current_datadicc_saved = None
    modal_title = None
    checked_options = None
    checked = None
    ulist_variable_choices_saved = None
    multilist_variable_choices_saved = None
    selected_version_data = None
    selected_language_data = None
    output = get_output_on_modal_button_click(mock_trigger_id,
                                              submit_n_clicks,
                                              cancel_n_clicks,
                                              current_datadicc_saved,
                                              modal_title,
                                              checked_options,
                                              checked,
                                              ulist_variable_choices_saved,
                                              multilist_variable_choices_saved,
                                              selected_version_data,
                                              selected_language_data)
    expected = (dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@mock.patch('bridge.callbacks.modals.get_trigger_id', return_value='modal_cancel')
def test_on_modal_button_click_modal_cancel(mock_trigger_id):
    submit_n_clicks = None
    cancel_n_clicks = None
    current_datadicc_saved = None
    modal_title = None
    checked_options = None
    checked = None
    ulist_variable_choices_saved = None
    multilist_variable_choices_saved = None
    selected_version_data = None
    selected_language_data = None
    output = get_output_on_modal_button_click(mock_trigger_id,
                                              submit_n_clicks,
                                              cancel_n_clicks,
                                              current_datadicc_saved,
                                              modal_title,
                                              checked_options,
                                              checked,
                                              ulist_variable_choices_saved,
                                              multilist_variable_choices_saved,
                                              selected_version_data,
                                              selected_language_data)
    expected = (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


def get_output_on_modal_button_click(trigger,
                                     submit_n_clicks,
                                     cancel_n_clicks,
                                     current_datadicc_saved,
                                     modal_title,
                                     checked_options,
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
                                            checked_options,
                                            checked,
                                            ulist_variable_choices_saved,
                                            multilist_variable_choices_saved,
                                            selected_version_data,
                                            selected_language_data)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output
