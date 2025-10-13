import json
from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from pandas.testing import assert_frame_equal

from bridge.callbacks import tree

TRIGGER_NONE = None
CHECKED_VARIABLES_NONE = None
CURRENT_DATADICC_SAVED_NONE = None
GROUPED_PRESETS_NONE = None
SELECTED_VERSION_DATA_NONE = None
SELECTED_LANGUAGE_DATA_NONE = None


def test_get_checked_template_list():
    grouped_presets_dict = {
        'ARChetype Disease CRF': ['Covid', 'Dengue', 'Mpox', 'H5Nx'],
        'ARChetype Syndromic CRF': ['ARI'],
        'Recommended Outcomes': ['Dengue'],
        'Score': ['CharlsonCI'],
        'UserGenerated': ['Oropouche']
    }
    checked_values_list = [['Covid'], ['ARI'], [], [], []]
    output = tree.get_checked_template_list(grouped_presets_dict,
                                            checked_values_list)
    expected = [
        ['ARChetype Disease CRF', 'Covid'],
        ['ARChetype Syndromic CRF', 'ARI']
    ]
    assert output == expected


@pytest.fixture
def df_mock_list():
    data = {
        'Disease':
            [
                'Adenovirus',
                'Bacterial infection',
                'Dengue',
                'Enterovirus',
                'HSV',
                'Lassa fever',
                'Measles',
                'Mpox',
                'Nipah',
                'Oropouche',
            ],
        'Selected':
            [
                1, 0, 1, 1, 1, 0, 0, 0, 0, 1,
            ],
        'preset_ARChetype Disease CRF_Covid':
            [
                0, '  1 ', 1, 1, 0, 0, 0, 1, 0, 0,
            ],
    }
    df_mock_list = pd.DataFrame.from_dict(data)
    return df_mock_list


@mock.patch('bridge.callbacks.modals.arc_translations.get_translations', return_value={'other': 'Other'})
@mock.patch('bridge.callbacks.tree.ArcApiClient.get_dataframe_arc_list_version_language', return_value=[])
def test_update_for_template_options_ulist_checked_otherl2(mock_list,
                                                           mock_get_translations,
                                                           df_mock_list):
    mock_list.return_value = df_mock_list
    version = 'v1.1.2'
    language = 'English'
    ulist_variable_choices = []
    multilist_variable_choices = []
    checked_key = 'preset_ARChetype Disease CRF_Covid'
    data = {
        'Variable': ['inclu_disease', 'inclu_disease_otherl2'],
        'Type': ['user_list', 'dropdown'],
        'List': ['inclusion_Diseases', None],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    df_output, ulist_output, multilist_output = tree.update_for_template_options(version,
                                                                                 language,
                                                                                 df_current_datadicc,
                                                                                 ulist_variable_choices,
                                                                                 multilist_variable_choices,
                                                                                 checked_key=checked_key)
    ulist_expected = [['inclu_disease', [
        ['1', 'Adenovirus', 0],
        ['2', 'Bacterial infection', 1],
        ['3', 'Dengue', 1],
        ['4', 'Enterovirus', 1],
        ['5', 'HSV', 0],
        ['6', 'Lassa fever', 0],
        ['7', 'Measles', 0],
        ['8', 'Mpox', 1],
        ['9', 'Nipah', 0],
        ['10', 'Oropouche', 0],
    ]]]
    multilist_expected = []
    data = {
        'Variable': ['inclu_disease', 'inclu_disease_otherl2'],
        'Type': ['user_list', 'dropdown'],
        'List': ['inclusion_Diseases', None],
        'Answer Options': [
            '2, Bacterial infection | 3, Dengue | 4, Enterovirus | 8, Mpox |  88, Other',
            '1, Adenovirus | 5, HSV | 6, Lassa fever | 7, Measles | 9, Nipah | 10, Oropouche |  88, Other'
        ],
    }
    df_expected = pd.DataFrame.from_dict(data)

    assert_frame_equal(df_output, df_expected)
    assert ulist_output == ulist_expected
    assert multilist_output == multilist_expected


@mock.patch('bridge.callbacks.modals.arc_translations.get_translations', return_value={'other': 'Other'})
@mock.patch('bridge.callbacks.tree.ArcApiClient.get_dataframe_arc_list_version_language', return_value=[])
def test_update_for_template_options_multilist_selected(mock_list,
                                                        mock_get_translations,
                                                        df_mock_list):
    mock_list.return_value = df_mock_list
    version = 'v1.1.2'
    language = 'English'
    ulist_variable_choices = []
    multilist_variable_choices = []
    data = {
        'Variable': ['inclu_disease'],
        'Type': ['multi_list'],
        'List': ['inclusion_Diseases'],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    df_output, ulist_output, multilist_output = tree.update_for_template_options(version,
                                                                                 language,
                                                                                 df_current_datadicc,
                                                                                 ulist_variable_choices,
                                                                                 multilist_variable_choices)
    ulist_expected = []
    multilist_expected = [
        ['inclu_disease', [
            ['1', 'Adenovirus', 1],
            ['2', 'Bacterial infection', 0],
            ['3', 'Dengue', 1],
            ['4', 'Enterovirus', 1],
            ['5', 'HSV', 1],
            ['6', 'Lassa fever', 0],
            ['7', 'Measles', 0],
            ['8', 'Mpox', 0],
            ['9', 'Nipah', 0],
            ['10', 'Oropouche', 1],
        ]]]
    data = {
        'Variable': ['inclu_disease'],
        'Type': ['multi_list'],
        'List': ['inclusion_Diseases'],
        'Answer Options': ['1, Adenovirus | 3, Dengue | 4, Enterovirus | 5, HSV | 10, Oropouche |  88, Other'],
    }
    df_expected = pd.DataFrame.from_dict(data)

    assert_frame_equal(df_output, df_expected)
    assert ulist_output == ulist_expected
    assert multilist_output == multilist_expected


@pytest.fixture
def df_mock_list_multilist():
    data = {
        'Race':
            [
                'Aboriginal/First Nations/Indigenous',
                'Arab',
                'Black or African Descent',
                'Brown (Mixed/Multiracial)',
                'East Asian (incl. Brazilian Yellow/Amarelo)',
                'Latin American or Hispanic',
                'South Asian',
                'South-East Asian',
                'West Asian',
                'White',
            ],
        'Selected':
            [
                0, 1, 0, 1, 0, 1, 1, 0, 0, 1,
            ],
    }
    df_mock_list = pd.DataFrame.from_dict(data)
    return df_mock_list


@mock.patch('bridge.callbacks.modals.arc_translations.get_translations', return_value={'other': 'Other'})
@mock.patch('bridge.callbacks.tree.ArcApiClient.get_dataframe_arc_list_version_language', return_value=[])
def test_update_for_template_options_ulist_multilist(mock_list,
                                                     mock_get_translations,
                                                     df_mock_list,
                                                     df_mock_list_multilist):
    mock_list.side_effect = [df_mock_list, df_mock_list_multilist]
    version = 'v1.1.2'
    language = 'English'
    ulist_variable_choices = []
    multilist_variable_choices = []
    data = {
        'Variable': ['inclu_disease', 'demog_race'],
        'Type': ['user_list', 'multi_list'],
        'List': ['inclusion_Diseases', 'demographics_Race'],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    df_output, ulist_output, multilist_output = tree.update_for_template_options(version,
                                                                                 language,
                                                                                 df_current_datadicc,
                                                                                 ulist_variable_choices,
                                                                                 multilist_variable_choices)
    ulist_expected = [
        ['inclu_disease', [
            ['1', 'Adenovirus', 1],
            ['2', 'Bacterial infection', 0],
            ['3', 'Dengue', 1],
            ['4', 'Enterovirus', 1],
            ['5', 'HSV', 1],
            ['6', 'Lassa fever', 0],
            ['7', 'Measles', 0],
            ['8', 'Mpox', 0],
            ['9', 'Nipah', 0],
            ['10', 'Oropouche', 1],
        ]]]
    multilist_expected = [
        ['demog_race',
         [['1', 'Aboriginal/First Nations/Indigenous', 0],
          ['2', 'Arab', 1],
          ['3', 'Black or African Descent', 0],
          ['4', 'Brown (Mixed/Multiracial)', 1],
          ['5', 'East Asian (incl. Brazilian Yellow/Amarelo)', 0],
          ['6', 'Latin American or Hispanic', 1],
          ['7', 'South Asian', 1],
          ['8', 'South-East Asian', 0],
          ['9', 'West Asian', 0],
          ['10', 'White', 1],
          ]]]
    data = {
        'Variable': ['inclu_disease', 'demog_race'],
        'Type': ['user_list', 'multi_list'],
        'List': ['inclusion_Diseases', 'demographics_Race'],
        'Answer Options': [
            '1, Adenovirus | 3, Dengue | 4, Enterovirus | 5, HSV | 10, Oropouche |  88, Other',
            '2, Arab | 4, Brown (Mixed/Multiracial) | 6, Latin American or Hispanic | 7, South Asian | 10, White |  88, Other'
        ],
    }
    df_expected = pd.DataFrame.from_dict(data)

    assert_frame_equal(df_output, df_expected)
    assert ulist_output == ulist_expected
    assert multilist_output == multilist_expected


def get_output_update_tree_items_and_stores(trigger,
                                            checked_variables,
                                            upload_crf_ready,
                                            current_datadicc_saved,
                                            grouped_presets_dict,
                                            selected_version_data,
                                            selected_language_data):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return tree.update_tree_items_and_stores(checked_variables,
                                                 upload_crf_ready,
                                                 current_datadicc_saved,
                                                 grouped_presets_dict,
                                                 selected_version_data,
                                                 selected_language_data)

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


def test_update_tree_items_and_stores_upload_crf_ready():
    upload_crf_ready = True
    output = get_output_update_tree_items_and_stores(TRIGGER_NONE,
                                                     CHECKED_VARIABLES_NONE,
                                                     upload_crf_ready,
                                                     CURRENT_DATADICC_SAVED_NONE,
                                                     GROUPED_PRESETS_NONE,
                                                     SELECTED_VERSION_DATA_NONE,
                                                     SELECTED_LANGUAGE_DATA_NONE)
    expected = (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    assert output == expected


@pytest.mark.parametrize(
    "trigger, checked_variables",
    [
        (None, [['Covid'], [], [], []]),
        ([{'prop_id': '{"index":"ARChetype Disease CRF","type":"template_check"}.value', 'value': []}],
         [[], [], [], []]),
    ]

)
@mock.patch('bridge.callbacks.tree.html.Div', return_value=['Just for checking'])
@mock.patch('bridge.callbacks.tree.arc_tree.get_tree_items')
def test_update_tree_items_and_stores_no_update(mock_get_tree_items,
                                                mock_html_div,
                                                trigger,
                                                checked_variables):
    upload_crf_ready = False
    current_datadicc_saved = '{"columns":["Form"], "index":[0], "data":[["presentation"]]}'
    selected_version_data = {'selected_version': 'v1.1.2'}
    selected_language_data = {'selected_language': 'English'}

    output = get_output_update_tree_items_and_stores(trigger,
                                                     checked_variables,
                                                     upload_crf_ready,
                                                     current_datadicc_saved,
                                                     GROUPED_PRESETS_NONE,
                                                     selected_version_data,
                                                     selected_language_data)
    expected = (
        ['Just for checking'],
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    assert output == expected


@pytest.mark.parametrize(
    "trigger, checked_variables",
    [
        ([{'prop_id': '{"index":"ARChetype Disease CRF","type":"template_check"}.value', 'value': []}],
         [['Covid'], [], [], []]),
    ]

)
@mock.patch('bridge.callbacks.tree.update_for_template_options')
@mock.patch('bridge.callbacks.tree.get_checked_template_list', return_value=[['ARChetype Disease CRF', 'Covid']])
@mock.patch('bridge.callbacks.tree.logger')
@mock.patch('bridge.callbacks.tree.html.Div', return_value=['Just for checking'])
@mock.patch('bridge.callbacks.tree.arc_tree.get_tree_items')
def test_update_tree_items_and_stores(mock_get_tree_items,
                                      mock_html_div,
                                      mock_logger,
                                      mock_template_list,
                                      mock_update_for_template,
                                      trigger,
                                      checked_variables):
    upload_crf_ready = False
    current_datadicc_saved = '{"columns":["Form"], "index":[0], "data":[["presentation"]]}'
    grouped_presets_dict = {'ARChetype Disease CRF': ['Covid', 'Dengue', 'Mpox', 'H5Nx'],
                            'ARChetype Syndromic CRF': ['ARI']}
    selected_version_data = {'selected_version': 'v1.1.2'}
    selected_language_data = {'selected_language': 'English'}

    mock_ulist = [['inclu_disease', [
        ['1', 'Adenovirus', 0],
        ['2', 'Bacterial infection', 1],
        ['10', 'Oropouche', 0]]]]
    mock_multilist = [
        ['inclu_disease', [
            ['1', 'Adenovirus', 1],
            ['2', 'Bacterial infection', 0]]]]
    mock_data = {
        'Variable': ['inclu_disease'],
        'Type': ['multi_list'],
        'List': ['inclusion_Diseases'],
        'Answer Options': ['1, Adenovirus | 3, Dengue | 4, Enterovirus | 5, HSV | 10, Oropouche |  88, Other'],
    }
    df_mock = pd.DataFrame.from_dict(mock_data)

    mock_update_for_template.return_value = (
        df_mock,
        mock_ulist,
        mock_multilist,
    )

    (output_tree_items,
     output_json,
     output_ulist,
     output_multilist) = get_output_update_tree_items_and_stores(trigger,
                                                                 checked_variables,
                                                                 upload_crf_ready,
                                                                 current_datadicc_saved,
                                                                 grouped_presets_dict,
                                                                 selected_version_data,
                                                                 selected_language_data)

    assert output_tree_items == ['Just for checking']
    assert output_json == str(df_mock.to_json(date_format='iso', orient='split'))
    assert output_ulist == json.dumps(mock_ulist)
    assert output_multilist == json.dumps(mock_multilist)
