from unittest import mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bridge.callbacks import tree


def test_get_checked_template_list():
    grouped_presets_dict = {
        'ARChetype Disease CRF': ['Covid', 'Dengue', 'Mpox', 'H5Nx'],
        'ARChetype Syndromic CRF': ['ARI'],
        'Recommended Outcomes': ['Dengue'],
        'Score': ['CharlsonCI'], 'UserGenerated': ['Oropouche']
    }
    checked_values_list = [['Covid'], ['ARI'], [], [], []]
    output = tree.get_checked_template_list(grouped_presets_dict,
                                            checked_values_list)
    expected = [['ARChetype Disease CRF', 'Covid'], ['ARChetype Syndromic CRF', 'ARI']]
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


@mock.patch('bridge.callbacks.modals.arc.get_translations', return_value={'other': 'Other'})
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
        ['10', 'Oropouche', 0]]]]
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


@mock.patch('bridge.callbacks.modals.arc.get_translations', return_value={'other': 'Other'})
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
            ['10', 'Oropouche', 1]]]]
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
