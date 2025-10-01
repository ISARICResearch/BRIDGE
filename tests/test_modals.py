import pandas as pd
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
    df_output, list_output = modals.determine_list_variable_choices(variable_choices_list, variable_submitted,
                                                                    df_list_options_checked,
                                                                    df_datadicc, other_text)

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
