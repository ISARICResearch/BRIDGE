from unittest import mock

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from bridge.arc import arc


@pytest.fixture
def translation_dict():
    translation_dict = {
        'any_additional': 'Any additional',
        'other': 'Other',
        'other_agent': 'other agents administered',
        'select': 'Select',
        'select_additional': 'Select additional',
        'specify': 'Specify',
        'specify_other': 'Specify other',
        'specify_other_infection': 'Specify other infection',
        'units': 'Units'
    }
    return translation_dict


@mock.patch('bridge.arc.arc.ArcApiClient.get_dataframe_arc_list_version_language')
@mock.patch('bridge.arc.arc.get_translations')
def test_get_list_content(mock_get_translations,
                          mock_list,
                          translation_dict):
    data = {
        'Condition': [
            'Asplenia',
            'Dementia',
            'Hemiplegia',
            'Leukemia',
            'Obesity',
        ],

    }
    df_mock_list = pd.DataFrame(data)

    mock_get_translations.return_value = translation_dict
    mock_list.return_value = df_mock_list

    version = 'v1.1.1'
    language = 'English'
    data = {
        'Variable': [
            'comor_unlisted',
        ],
        'Type': [
            'list',
        ],
        'List': [
            'conditions_Comorbidities',
        ],
        'Answer Options': [
            '1, Yes | 0, No | 99, Unknown',
        ],
        'Question': [
            'Other relevant information',
        ],
        'Question_english': [
            'Other relevant information',
        ],
        'Sec': [
            'comor',
        ],
        'vari': [
            'unlisted',
        ],

    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        'Variable': [
            'comor_unlisted',
            'comor_unlisted_0item',
            'comor_unlisted_0otherl2',
            'comor_unlisted_0addi',
            'comor_unlisted_1item',
            'comor_unlisted_1otherl2',
            'comor_unlisted_1addi',
            'comor_unlisted_2item',
            'comor_unlisted_2otherl2',
            'comor_unlisted_2addi',
            'comor_unlisted_3item',
            'comor_unlisted_3otherl2',
            'comor_unlisted_3addi',
            'comor_unlisted_4item',
            'comor_unlisted_4otherl2',
        ],
        'Type': [
            'list',
            'dropdown',
            'text',
            'radio',
            'dropdown',
            'text',
            'radio',
            'dropdown',
            'text',
            'radio',
            'dropdown',
            'text',
            'radio',
            'dropdown',
            'text',
        ],
        'List': [
            'conditions_Comorbidities',
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
        'Answer Options': [
            '1, Yes | 0, No | 99, Unknown',
            '1, Asplenia | 2, Dementia | 3, Hemiplegia | 4, Leukemia | 5, Obesity | 88, Other',
            None,
            '1, Yes | 0, No | 99, Unknown',
            '1, Asplenia | 2, Dementia | 3, Hemiplegia | 4, Leukemia | 5, Obesity | 88, Other',
            None,
            '1, Yes | 0, No | 99, Unknown',
            '1, Asplenia | 2, Dementia | 3, Hemiplegia | 4, Leukemia | 5, Obesity | 88, Other',
            None,
            '1, Yes | 0, No | 99, Unknown',
            '1, Asplenia | 2, Dementia | 3, Hemiplegia | 4, Leukemia | 5, Obesity | 88, Other',
            None,
            '1, Yes | 0, No | 99, Unknown',
            '1, Asplenia | 2, Dementia | 3, Hemiplegia | 4, Leukemia | 5, Obesity | 88, Other',
            None,
        ],
        'Question': [
            'Other relevant information',
            ' Select other relevant information',
            ' Specify other relevant information',
            ' Any additional other relevant information ?',
            '> Select additional other relevant information 2',
            '> Specify other relevant information 2',
            '> Any additional other relevant information ?',
            '-> Select additional other relevant information 3',
            '-> Specify other relevant information 3',
            '-> Any additional other relevant information ?',
            '>-> Select additional other relevant information 4',
            '>-> Specify other relevant information 4',
            '>-> Any additional other relevant information ?',
            '->-> Select additional other relevant information 5',
            '->-> Specify other relevant information 5',
        ],
        'Question_english': ['Other relevant information'] * 15,
        'Sec': ['comor'] * 15,
        'vari': ['unlisted'] * 15,
        'Validation': [
            np.nan,
            'autocomplete',
            np.nan,
            np.nan,
            'autocomplete',
            np.nan,
            np.nan,
            'autocomplete',
            np.nan,
            np.nan,
            'autocomplete',
            np.nan,
            np.nan,
            'autocomplete',
            np.nan,
        ],
        'Maximum': [np.nan] * 15,
        'Minimum': [np.nan] * 15,
        'mod': [
            np.nan,
            '0item',
            '0otherl2',
            '0addi',
            '1item',
            '1otherl2',
            '1addi',
            '2item',
            '2otherl2',
            '2addi',
            '3item',
            '3otherl2',
            '3addi',
            '4item',
            '4otherl2',
        ],
        'Skip Logic': [
            np.nan,
            "[comor_unlisted]=\'1\'",
            "[comor_unlisted_0item]=\'88\'",
            "[comor_unlisted]=\'1\'",
            "[comor_unlisted_0addi]=\'1\'",
            "[comor_unlisted_1item]=\'88\'",
            "[comor_unlisted_0addi]=\'1\'",
            "[comor_unlisted_1addi]=\'1\'",
            "[comor_unlisted_2item]=\'88\'",
            "[comor_unlisted_1addi]=\'1\'",
            "[comor_unlisted_2addi]=\'1\'",
            "[comor_unlisted_3item]=\'88\'",
            "[comor_unlisted_2addi]=\'1\'",
            "[comor_unlisted_3addi]=\'1\'",
            "[comor_unlisted_4item]=\'88\'",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        ['comor_unlisted',
         [[1, 'Asplenia'],
          [2, 'Dementia'],
          [3, 'Hemiplegia'],
          [4, 'Leukemia'],
          [5, 'Obesity'],
          ]],
    ]

    (df_output,
     list_output) = arc.get_list_content(df_current_datadicc,
                                         version,
                                         language)

    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected


@mock.patch('bridge.arc.arc.ArcApiClient.get_dataframe_arc_list_version_language')
@mock.patch('bridge.arc.arc.get_translations')
def test_get_list_data(mock_get_translations,
                       mock_list,
                       translation_dict):
    data = {
        'Disease': [
            'Adenovirus',
            'Dengue',
            'Enterovirus',
            'HSV',
            'Mpox',
        ],
        'Selected': [
            0,
            0,
            0,
            0,
            1,
        ],

    }
    df_mock_list = pd.DataFrame(data)

    mock_get_translations.return_value = translation_dict
    mock_list.return_value = df_mock_list

    version = 'v1.1.1'
    language = 'English'
    list_type = 'user_list'
    data = {
        'Variable': [
            'inclu_disease',
        ],
        'Type': [
            'user_list',
        ],
        'List': [
            'inclusion_Diseases',
        ],
        'Question': [
            'Suspected or confirmed infection',
        ],
        'Sec': [
            'inclu',
        ],
        'vari': [
            'disease',
        ],

    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    list_choices_expected = [
        ['inclu_disease', [
            [1, 'Adenovirus', 0],
            [2, 'Dengue', 0],
            [3, 'Enterovirus', 0],
            [4, 'HSV', 0],
            [5, 'Mpox', 1],
        ]]]
    dict1 = {
        'Variable': 'inclu_disease',
        'Type': 'user_list',
        'List': 'inclusion_Diseases',
        'Question': 'Suspected or confirmed infection',
        'Sec': 'inclu',
        'vari': 'disease',
        'Answer Options': '5, Mpox | 88, Other',
    }
    series1 = pd.Series(dict1, name=0)
    dict2 = {
        'Variable': 'inclu_disease_otherl3',
        'Type': 'text',
        'List': None,
        'Question': 'Specify other Suspected or confirmed infection',
        'Sec': 'inclu',
        'vari': 'disease',
        'Answer Options': None,
        'Maximum': None,
        'Minimum': None,
        'Skip Logic': "[inclu_disease]='88'",
        'mod': 'otherl3',
    }
    series2 = pd.Series(dict2, name=0)
    all_rows_expected = [
        series1,
        series2,
    ]

    (list_choices_output,
     all_rows_output) = arc.get_list_data(df_current_datadicc,
                                          version,
                                          language,
                                          list_type)

    assert list_choices_output == list_choices_expected
    assert_series_equal(all_rows_output[0], all_rows_expected[0])
    assert_series_equal(all_rows_output[1], all_rows_expected[1])


@mock.patch('bridge.arc.arc.set_select_units')
@mock.patch('bridge.arc.arc.extract_parenthesis_content', return_value='select units')
def test_get_select_units(mock_extract_parenthesis,
                          mock_set_units):
    data = [
        'demog_height',
        'demog_height_cm',
        'demog_height_in',
    ]
    selected_variables = pd.Series(data, name='Variable')
    data = {
        'Variable': [
            'demog_height',
            'demog_height_cm',
            'demog_height_in',
        ],
        'Question': [
            'Height (select units)',
            'Height (cm)',
            'Height (in)',
        ],
        'Question_english': [
            'Height (select units)',
            'Height (cm)',
            'Height (in)',
        ],
        'Minimum': [
            np.nan,
            0,
            0,
        ],
        'Maximum': [
            np.nan,
            250,
            98,
        ],
        'Sec': [
            'demog',
            'demog',
            'demog',
        ],
        'vari': [
            'height',
            'height',
            'height',
        ],
        'mod': [
            None,
            'cm',
            'in'
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    df_units = pd.DataFrame.from_dict({
        'select units': [
            True,
            True,
            True,
        ]})
    df_mock_set_units = df_current_datadicc.join(df_units)
    mock_set_units.return_value = df_mock_set_units

    data_expected = {
        'Variable': [
            'demog_height',
            'demog_height_units',
        ],
        'Question': [
            'Height ',
            'Height (select units)',
        ],
        'Question_english': [
            'Height (cm)',
            'Height (cm)',
        ],
        'Minimum': [
            0,
            np.nan,
        ],
        'Maximum': [
            250,
            np.nan,
        ],
        'Sec': [
            'demog',
            'demog',
        ],
        'vari': [
            'height',
            'height',
        ],
        'mod': [
            'cm',
            'cm',
        ],
        'select units': [
            True,
            True,
        ],
        'count': [
            2,
            2,
        ],
        'Answer Options': [
            None,
            '1,select units | 2,select units',
        ],
        'Type': [
            'text',
            'radio',
        ],
        'Validation': [
            'number',
            None,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    list_expected = [
        'demog_height_cm',
        'demog_height_in',
    ]

    (df_output,
     list_output) = arc.get_select_units(selected_variables,
                                         df_current_datadicc)

    assert_frame_equal(df_output, df_expected)
    assert list_output == list_expected
