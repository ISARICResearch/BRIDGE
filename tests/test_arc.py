from unittest import mock

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from bridge.arc import arc


@mock.patch('bridge.arc.arc.ArcApiClient.get_dataframe_arc_list_version_language')
@mock.patch('bridge.arc.arc.get_translations')
def test_get_list_content(mock_get_translations,
                          mock_list):
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
