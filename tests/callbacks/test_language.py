import json
from unittest import mock

import pandas as pd
from pandas.testing import assert_frame_equal

from bridge.callbacks.language import Language


@mock.patch('bridge.callbacks.language.arc_translations.get_arc_translation')
def test_get_dataframe_arc_language(mock_translation):
    version = 'v1.0.0'
    language = 'Finnish'
    data = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_disease_otherl2',
            'demog_country'
        ],
    }
    df_mock = pd.DataFrame.from_dict(data)

    mock_translation.return_value = df_mock
    df_result = Language(version, language).get_dataframe_arc_language(pd.DataFrame())
    assert_frame_equal(df_result, df_mock)


@mock.patch('bridge.callbacks.language.dbc.AccordionItem')
@mock.patch('bridge.callbacks.language.arc_lists.get_multi_list_content')
@mock.patch('bridge.callbacks.language.arc_lists.get_user_list_content')
@mock.patch('bridge.callbacks.language.arc_core.get_variable_order')
@mock.patch('bridge.callbacks.language.arc_core.add_transformed_rows')
@mock.patch('bridge.callbacks.language.arc_lists.get_list_content')
@mock.patch('bridge.callbacks.language.Language.get_dataframe_arc_language')
@mock.patch('bridge.callbacks.language.arc_core.add_required_datadicc_columns')
@mock.patch('bridge.callbacks.language.arc_core.get_arc')
def test_get_version_language_related_data(mock_get_arc,
                                           mock_add_required_data,
                                           mock_get_dataframe_arc_language,
                                           mock_get_list_content,
                                           mock_add_transformed_rows,
                                           mock_get_variable_order,
                                           mock_get_user_list_content,
                                           mock_get_multi_list_content,
                                           mock_accordian):
    version = 'v1.0.0'
    language = 'Finnish'
    data = {
        'Form': ['presentation', 'presentation'],
        'Section': ['INCLUSION CRITERIA', 'DEMOGRAPHICS'],
        'Variable': ['inclu_disease', 'demog_country'],
    }
    df_version = pd.DataFrame.from_dict(data)
    presets = [
        ['ARChetype Disease CRF', 'Covid'],
        ['ARChetype Disease CRF', 'Dengue'],
        ['ARChetype Disease CRF', 'Mpox'],
        ['UserGenerated', 'Oropouche']
    ]
    commit = 'sha123'
    df_list = pd.DataFrame()
    list_variable_choices = []
    variable_order = []
    ulist_variable_choices = [
        ['inclu_disease', [
            ['1', 'Adenovirus'],
            ['2', 'Bacterial infection'],
            ['3', 'Dengue'],
        ]]]
    multilist_variable_choices = [
        ['demog_race',
         [['2', 'Arab'],
          ['3', 'Black or African Descent'],
          ]]]
    accordian = ['Just for testing']

    mock_get_arc.return_value = (df_version,
                                 presets,
                                 commit)
    mock_add_required_data.return_value = df_version
    mock_get_dataframe_arc_language.return_value = df_version
    mock_get_list_content.return_value = (
        df_list,
        list_variable_choices,
    )
    mock_add_transformed_rows.return_value = df_version
    mock_get_variable_order.return_value = variable_order
    mock_get_user_list_content.return_value = (
        df_list,
        ulist_variable_choices,
    )
    mock_get_multi_list_content.return_value = (
        df_list,
        multilist_variable_choices,
    )
    mock_accordian.return_value = accordian

    (df_output,
     output_commit,
     output_presets,
     output_accordian,
     output_ulist,
     output_multilist) = Language(version, language).get_version_language_related_data()

    expected_presets = {
        'ARChetype Disease CRF': ['Covid', 'Dengue', 'Mpox'],
        'UserGenerated': ['Oropouche'],
    }
    expected_accordian = [accordian, accordian]

    assert_frame_equal(df_output, df_version)
    assert output_commit == commit
    assert output_presets == expected_presets
    assert output_accordian == expected_accordian
    assert output_ulist == json.dumps(ulist_variable_choices)
    assert output_multilist == json.dumps(multilist_variable_choices)
