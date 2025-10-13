from unittest import mock

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from bridge.arc import arc


def test_add_required_datadicc_columns():
    data = {
        'Section': [
            'INCLUSION CRITERIA',
            'CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing',
        ],
        'Variable': [
            'inclu_disease',
            'comor_chrcardiac_chf',
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    df_new_columns = pd.DataFrame.from_dict({
        'Sec': [
            'inclu',
            'comor',
        ],
        'vari': [
            'disease',
            'chrcardiac',
        ],
        'mod': [
            None,
            'chf',
        ],
        'Sec_name': [
            'INCLUSION CRITERIA',
            'CO-MORBIDITIES AND RISK FACTORS',
        ],
        'Expla': [
            None,
            ' Existing prior to this current illness and is ongoing',
        ],
    })
    df_expected = df_datadicc.join(df_new_columns)
    df_output = arc.add_required_datadicc_columns(df_datadicc)
    assert_frame_equal(df_output, df_expected)


@mock.patch('bridge.arc.arc._process_skip_logic')
@mock.patch('bridge.arc.arc.ArcApiClient.get_dataframe_arc_version_language')
def test_get_arc_translation(mock_arc,
                             mock_skip_logic):
    version = 'v1.1.1'
    language = 'English'
    data = {
        'Variable': [
            'subjid',
            'inclu_reason',
        ],
        'Form': [
            'presentation',
            'presentation',
        ],
        'Section': [
            np.nan,
            'INCLUSION CRITERIA',
        ],
        'Question': [
            'Participant Identification Number (PIN)',
            'Is the suspected or confirmed infection the reason for hospital admission?',
        ],
        'Answer Options': [
            np.nan,
            '1, Yes | 0, No | 99, Unknown',
        ],
        'Definition': [
            'The Participant Identification Number or PIN.',
            'Suspected infection with the pathogen of interest if the reason for the hospital admission.',
        ],
        'Completion Guideline': [
            'Write the Participant Identification Number (PIN).',
            'Indicate \'Yes\' if suspected or confirmed infection with the pathogen of interest.',
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    data_not_english = {
        'Variable': [
            'subjid',
            'inclu_reason',
        ],
        'Form': [
            'presentation_translated',
            'presentation_translated',
        ],
        'Section': [
            np.nan,
            'INCLUSION CRITERIA TRANSLATED',
        ],
        'Question': [
            'Participant Identification Number (PIN)',
            'Is the suspected or confirmed infection the reason for hospital admission (translated)?',
        ],
        'Answer Options': [
            np.nan,
            '1, Joo | 0, Ei | 99, Jattipotti',
        ],
        'Definition': [
            'Le Participant Identification Number or PIN.',
            'Suspected infection with the pathogen of interest if the reason for the hospital admission (translated).',
        ],
        'Completion Guideline': [
            'Kirjoita osallistujan tunnistenumero (PIN-koodi).',
            'Indicate \'Yes\' if suspected or confirmed infection with the pathogen of interest (translated).',
        ],
    }
    df_not_english = pd.DataFrame.from_dict(data_not_english)
    branch_logic = '[Some branch logic]'

    mock_arc.side_effect = [df_current_datadicc, df_not_english]
    mock_skip_logic.return_value = branch_logic

    df_extra_columns = pd.DataFrame.from_dict({
        'Question_english': [
            'Participant Identification Number (PIN)',
            'Is the suspected or confirmed infection the reason for hospital admission?',
        ],
        'Branch': [
            branch_logic,
            branch_logic,
        ],
    })

    df_expected = df_not_english.join(df_extra_columns)

    df_output = arc.get_arc_translation(language,
                                        version,
                                        df_current_datadicc)

    assert_frame_equal(df_output, df_expected)


@pytest.mark.parametrize(
    "skip_logic_column, variables_expected, values_expected, comparison_operators_expected, logical_operators_expected",
    [
        ("[inclu_testreason]='88'", ['inclu_testreason'], ['88'], ['='], []),
        ("[inclu_testreason]=88.0", ['inclu_testreason'], [88.0], ['='], []),
        ("[inclu_testreason]=88", ['inclu_testreason'], [88], ['='], []),
        (np.nan, [], [], [], []),
    ]
)
def test_extract_logic_components(skip_logic_column,
                                  variables_expected,
                                  values_expected,
                                  comparison_operators_expected,
                                  logical_operators_expected):
    (variables_output,
     values_output,
     comparison_operators_output,
     logical_operators_output) = arc._extract_logic_components(skip_logic_column)

    assert variables_output == variables_expected
    assert values_output == values_expected
    assert comparison_operators_output == comparison_operators_expected
    assert logical_operators_output == logical_operators_expected


@mock.patch('bridge.arc.arc._extract_logic_components')
def test_process_skip_logic(mock_extract):
    mock_extract.return_value = (
        ['inclu_testreason'],
        ['88'],
        ['='],
        [],
    )
    data_series = {
        'Skip Logic': ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        'Variable': [
            'inclu_testreason',
        ],
        'Question': [
            'Reason why the patient was tested',
        ],
        'Answer Options': [
            ' 1, Symptomatic | 2, Asymptomatic | 3, Not tested | 99, Unknown | 88, Other',
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = '(Reason why the patient was tested = Other)  '
    output = arc._process_skip_logic(row, df_current_datadicc)
    assert output == expected


@mock.patch('bridge.arc.arc._extract_logic_components')
def test_process_skip_logic_no_answers(mock_extract):
    mock_extract.return_value = (
        ['inclu_testreason'],
        ['88'],
        ['='],
        [],
    )
    data_series = {
        'Skip Logic': ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        'Variable': [
            'inclu_testreason',
        ],
        'Question': [
            'Reason why the patient was tested',
        ],
        'Answer Options': [
            np.nan,
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = '(Reason why the patient was tested = 88)  '
    output = arc._process_skip_logic(row, df_current_datadicc)
    assert output == expected


@mock.patch('bridge.arc.arc._extract_logic_components')
def test_process_skip_logic_index_error(mock_extract):
    mock_extract.return_value = (
        ['inclu_testreason_index_error'],
        ['88'],
        ['='],
        [],
    )
    data_series = {
        'Skip Logic': ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        'Variable': [
            'inclu_testreason',
        ],
        'Question': [
            'Reason why the patient was tested',
        ],
        'Answer Options': [
            np.nan,
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = 'Variable not found getARCTranslation'
    output = arc._process_skip_logic(row, df_current_datadicc)
    assert output == expected


@mock.patch('bridge.arc.arc.logger')
@mock.patch('bridge.arc.arc.ArcApiClient.get_arc_version_list')
def test_get_arc_versions(mock_get_versions,
                          mock_logger):
    version_list = ['v1.0.0', 'v1.1.0', 'v1.1.1', 'v1.1.2', 'v1.1.3']
    mock_get_versions.return_value = version_list

    (version_list_output,
     latest_version_output) = arc.get_arc_versions()

    assert version_list_output == version_list
    assert latest_version_output == 'v1.1.3'


def test_get_variable_order():
    data = {
        'Sec': [
            'inclu',
            'inclu',
            'comor',
            'adsym',
        ],
        'vari': [
            'disease',
            'case',
            'chrcardiac',
            'resp',
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    list_expected = [
        'inclu_disease',
        'inclu_case',
        'comor_chrcardiac',
        'adsym_resp',
    ]
    list_output = arc.get_variable_order(df_current_datadicc)
    assert list_output == list_expected


@mock.patch('bridge.arc.arc.logger')
@mock.patch('bridge.arc.arc.get_dependencies')
@mock.patch('bridge.arc.arc.ArcApiClient.get_dataframe_arc_sha')
@mock.patch('bridge.arc.arc.ArcApiClient.get_arc_version_sha')
def test_get_arc(mock_sha,
                 mock_arc,
                 mock_dependencies,
                 mock_logger):
    sha_str = 'sha123'
    mock_sha.return_value = sha_str

    data = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_testreason_otth',
        ],
        'Question': [
            'Question for subjid',
            'Question for inclu_disease',
            'Question for inclu_testreason_otth',
        ],
        'preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff': [
            1,
            1,
            0,
        ],
        'preset_ARChetype Disease CRF_Dengue': [
            0,
            1,
            0,
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    mock_arc.return_value = df_datadicc

    data_dependencies = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_testreason_otth',
        ],
        'Dependencies': [
            '[[subjid]]',
            '[subjid]',
            '[inclu_testreason, subjid]',
        ],
    }
    df_dependencies = pd.DataFrame.from_dict(data_dependencies)
    mock_dependencies.return_value = df_dependencies

    data_expected = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_testreason_otth',
        ],
        'Question': [
            'Question for subjid',
            'Question for inclu_disease',
            'Question for inclu_testreason_otth',
        ],
        'preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff': [
            1,
            1,
            0,
        ],
        'preset_ARChetype Disease CRF_Dengue': [
            0,
            1,
            0,
        ],
        'Dependencies': [
            '[[subjid]]',
            '[subjid]',
            '[inclu_testreason, subjid]',
        ],
        'Question_english': [
            'Question for subjid',
            'Question for inclu_disease',
            'Question for inclu_testreason_otth',
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    preset_expected = [
        ['ARChetype Disease CRF', 'Covid Adding Some Extra Stuff'],
        ['ARChetype Disease CRF', 'Dengue'],
    ]

    version = 'v1.1.1'
    (df_output,
     preset_output,
     commit_output) = arc.get_arc(version)

    assert_frame_equal(df_output, df_expected)
    assert preset_output == preset_expected
    assert commit_output == sha_str


def test_get_dependencies():
    data = {
        'Variable': [
            'subjid',
            'inclu_consent_date',
            'readm_prev_site',
            'treat_an',
            'treat_another',
            'medi_something',
            'medi_somethingunits',
        ],
        'Skip Logic': [
            np.nan,
            "[inclu_consent]=\'1\'",
            "[readm_prev] = \'1\' or [readm_prev]=\'2\' or [readm_prev]=\'3\'",
            "[treat_dailydata]=\'1\'",
            "[treat_dailydata]=\'1\'",
            "[medi_treat()]=\'1\'",
            "[medi_treat()]=\'1\'",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        'Variable': [
            'subjid',
            'inclu_consent_date',
            'readm_prev_site',
            'treat_an',
            'treat_another',
            'medi_something',
            'medi_somethingunits',
        ],
        'Skip Logic': [
            np.nan,
            "[inclu_consent]=\'1\'",
            "[readm_prev] = \'1\' or [readm_prev]=\'2\' or [readm_prev]=\'3\'",
            "[treat_dailydata]=\'1\'",
            "[treat_dailydata]=\'1\'",
            "[medi_treat()]=\'1\'",
            "[medi_treat()]=\'1\'",
        ],
        'Dependencies': [
            ['subjid'],
            ['inclu_consent', 'subjid'],
            ['readm_prev', 'readm_prev', 'readm_prev', 'subjid'],
            ['treat_dailydata', 'subjid', 'treat_another'],
            ['treat_dailydata', 'subjid'],
            ['medi_treat', 'subjid', 'medi_somethingunits'],
            ['medi_treat', 'subjid'],
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    df_output = arc.get_dependencies(df_datadicc)
    assert_frame_equal(df_output, df_expected)


def test_set_select_units():
    data = {
        'Variable': [
            'demog_height',
            'demog_height_cm',
            'demog_height_in',
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
        'select units': [
            True,
            False,
            False,
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    data_expected = {
        'Variable': [
            'demog_height',
            'demog_height_cm',
            'demog_height_in',
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
        'select units': [
            True,
            True,
            True,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    df_output = arc.set_select_units(df_current_datadicc)
    assert_frame_equal(df_output, df_expected)


@mock.patch('bridge.arc.arc.set_select_units')
@mock.patch('bridge.arc.arc.add_required_datadicc_columns')
@mock.patch('bridge.arc.arc.get_dependencies')
def test_get_tree_items(mock_dependencies,
                        mock_required_columns,
                        mock_set_units):
    data = {
        'Form': [
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
        ],
        'Variable': [
            'inclu_disease',
            'demog_age_units',
            'demog_height',
            'pres_firstsym',
            'inclu_testreason',
            'inclu_testreason_otth',
        ],
        'Type': [
            'user_list',
            np.nan,
            np.nan,
            'multi_list',
            'radio',
            'text',
        ],
        'Question': [
            'Suspected or confirmed infection',
            'Age units',
            'Height (select units)',
            'Symptom(s) during first 24 hours of illness (select all that apply)',
            'Reason why the patient was tested',
            'Specify other reason',
        ],
        'vari': [
            'disease',
            'age',
            'height',
            'firstsym',
            'testreason',
            'testreason',
        ],
        'mod': [
            np.nan,
            'units',
            np.nan,
            None,
            None,
            'otth',
        ],
        'Sec_name': [
            'INCLUSION CRITERIA',
            'DEMOGRAPHICS',
            'DEMOGRAPHICS',
            'ONSET & PRESENTATION',
            'INCLUSION CRITERIA',
            'INCLUSION CRITERIA',
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    df_dependencies = pd.DataFrame.from_dict({
        'Variable': [
            'inclu_disease',
            'demog_age_units',
            'demog_height',
            'pres_firstsym',
            'inclu_testreason',
            'inclu_testreason_otth',
        ],
        'Dependencies': [
            ['subjid'],
            ['demog_birthknow', 'subjid'],
            ['subjid'],
            ['subjid'],
            ['subjid'],
            ['subjid'],
        ],
    })

    version = 'v1.1.1'

    # These extra columns aren't used
    mock_dependencies.return_value = df_dependencies
    mock_required_columns.return_value = df_datadicc
    mock_set_units.return_value = df_datadicc

    expected = {'children': [{
        'children': [{
            'children': [{
                'children': [],
                'key': 'inclu_disease',
                'title': '↳ Suspected or confirmed infection',
            },
                {
                    'children': [{
                        'key': 'inclu_testreason_otth',
                        'title': 'Specify other reason',
                    }],
                    'key': 'inclu_testreason',
                    'title': 'Reason why the patient was tested',
                }],
            'key': 'PRESENTATION-INCLUSION CRITERIA',
            'title': 'INCLUSION CRITERIA'},
            {
                'children': [{
                    'children': [],
                    'key': 'demog_height',
                    'title': 'Height (select units)',
                }],
                'key': 'PRESENTATION-DEMOGRAPHICS',
                'title': 'DEMOGRAPHICS'},
            {
                'children': [{
                    'children': [],
                    'key': 'pres_firstsym',
                    'title': '⇉ Symptom(s) during first '
                             '24 hours of illness (select all that apply)',
                }],
                'key': 'PRESENTATION-ONSET & PRESENTATION',
                'title': 'ONSET & PRESENTATION',
            }],
        'key': 'PRESENTATION',
        'title': 'PRESENTATION',
    }],
        'key': 'ARC',
        'title': 'v1.1.1',
    }

    output = arc.get_tree_items(df_datadicc,
                                version)

    assert output == expected


def test_extract_parenthesis_content():
    text = 'Neutrophils (select units)'
    output_str = arc.extract_parenthesis_content(text)
    expected_str = 'select units'
    assert output_str == expected_str


def test_get_include_not_show():
    data = [
        'demog_age',
        'demog_sex',
        'demog_outcountry',
        'demog_country',
    ]
    selected_variables = pd.Series(data, name='Variable')
    data = {
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_disease_otherl3',
            'demog_age',
            'demog_age_units',
            'demog_sex',
            'demog_outcountry',
            'demog_country_otherl3',
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        'Variable': [
            'demog_age',
            'demog_age_units',
            'demog_sex',
            'demog_outcountry',
            'demog_country_otherl3',
        ]
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc.get_include_not_show(selected_variables,
                                         df_current_datadicc)
    assert_frame_equal(df_output, df_expected)


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


def test_get_translations():
    english_dict = arc.get_translations('English')
    spanish_dict = arc.get_translations('Spanish')
    french_dict = arc.get_translations('French')
    portuguese_dict = arc.get_translations('Portuguese')
    assert len(english_dict) == len(spanish_dict) == len(french_dict) == len(portuguese_dict)
    assert english_dict['select'] == 'Select'


def test_get_translations_exception():
    with pytest.raises(ValueError):
        arc.get_translations('Klingon')


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
    data_list = {
        'Condition': [
            'Asplenia',
            'Dementia',
            'Hemiplegia',
            'Leukemia',
            'Obesity',
        ],
    }
    df_mock_list = pd.DataFrame(data_list)

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


@mock.patch('bridge.arc.arc.get_translations')
def test_get_list_content_no_list(mock_get_translations,
                                  translation_dict):
    mock_get_translations.return_value = translation_dict

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
            None,
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    (df_output,
     list_output) = arc.get_list_content(df_current_datadicc,
                                         version,
                                         language)

    assert df_output.empty
    assert not list_output


def test_set_cont_lo():
    data = {
        'Condition': [
            'Acute-on-chronic renal failure',
            'Asplenia',
            'Atrial Fibrillation',
            'Autoimmune Disease',
            'Blood coagulation disorder',
            'Cardiomyopathy',
            'Cerebrovascular Disease',
        ],
        'Value': [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
        ],
    }
    df_list_options = pd.DataFrame.from_dict(data)
    list_option = 'Cardiomyopathy'

    expected_int = 6
    output_int = arc.set_cont_lo(df_list_options,
                                 list_option)
    assert output_int == expected_int


def test_set_cont_lo_88():
    data = {
        'Condition': [
            'Acute-on-chronic renal failure',
            'Asplenia',
            'Atrial Fibrillation',
        ],
        'Value': [
            87,
            88,
            100,
        ],
    }
    df_list_options = pd.DataFrame.from_dict(data)
    list_option = 'Asplenia'

    expected_int = 89
    output_int = arc.set_cont_lo(df_list_options,
                                 list_option)
    assert output_int == expected_int


def test_set_cont_lo_99():
    data = {
        'Condition': [
            'Acute-on-chronic renal failure',
            'Asplenia',
            'Atrial Fibrillation',
        ],
        'Value': [
            87,
            99,
            105,
        ],
    }
    df_list_options = pd.DataFrame.from_dict(data)
    list_option = 'Asplenia'

    expected_int = 100
    output_int = arc.set_cont_lo(df_list_options,
                                 list_option)
    assert output_int == expected_int


def test_set_cont_lo_no_value():
    data = {
        'Condition': [
            'Acute-on-chronic renal failure',
            'Asplenia',
            'Atrial Fibrillation',
        ],
    }
    df_list_options = pd.DataFrame.from_dict(data)
    list_option = 'Asplenia'

    expected_int = 2
    output_int = arc.set_cont_lo(df_list_options,
                                 list_option)
    assert output_int == expected_int


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


@mock.patch('bridge.arc.arc.get_translations')
def test_get_list_data_no_list(mock_get_translations,
                               translation_dict):
    mock_get_translations.return_value = translation_dict

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
            None,
        ],  #
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    (list_choices_output,
     all_rows_output) = arc.get_list_data(df_current_datadicc,
                                          version,
                                          language,
                                          list_type)

    assert not list_choices_output
    assert not all_rows_output


@pytest.fixture()
def mock_list_choices():
    mock_list_choices = [
        ['inclu_disease', [
            [1, 'Adenovirus', 0],
            [2, 'Dengue', 0],
            [5, 'Mpox', 1],
        ]]]
    return mock_list_choices


@pytest.fixture()
def mock_all_rows():
    dict1 = {
        'Variable': 'inclu_disease',
        'Type': 'some_list',
        'List': 'inclusion_Diseases',
    }
    series1 = pd.Series(dict1, name=0)
    dict2 = {
        'Variable': 'inclu_disease_otherl3',
        'Type': 'text',
        'List': None,
    }
    series2 = pd.Series(dict2, name=0)
    mock_all_rows = [
        series1,
        series2,
    ]
    return mock_all_rows


@pytest.fixture()
def df_expected_get_list_content():
    data_expected = {
        'Variable': [
            'inclu_disease',
            'inclu_disease_otherl3',
        ],
        'Type': [
            'some_list',
            'text',
        ],
        'List': [
            'inclusion_Diseases',
            None,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    return df_expected


@pytest.fixture()
def list_expected_get_list_content():
    list_expected = [
        ['inclu_disease', [
            [1, 'Adenovirus', 0],
            [2, 'Dengue', 0],
            [5, 'Mpox', 1],
        ]]]
    return list_expected


@mock.patch('bridge.arc.arc.get_list_data')
def test_get_user_list_content(mock_list_data,
                               mock_list_choices,
                               mock_all_rows,
                               df_expected_get_list_content,
                               list_expected_get_list_content):
    mock_list_data.return_value = (mock_list_choices,
                                   mock_all_rows)

    df_current_datadicc = pd.DataFrame()
    version = 'v1.1.1'
    language = 'English'

    (df_output,
     list_output) = arc.get_user_list_content(df_current_datadicc,
                                              version,
                                              language)

    assert_frame_equal(df_output, df_expected_get_list_content)
    assert list_output == list_expected_get_list_content


@mock.patch('bridge.arc.arc.get_list_data')
def test_get_multi_list_content(mock_list_data,
                                mock_list_choices,
                                mock_all_rows,
                                df_expected_get_list_content,
                                list_expected_get_list_content):
    mock_list_data.return_value = (mock_list_choices,
                                   mock_all_rows)

    df_current_datadicc = pd.DataFrame()
    version = 'v1.1.1'
    language = 'English'

    (df_output,
     list_output) = arc.get_multi_list_content(df_current_datadicc,
                                               version,
                                               language)

    assert_frame_equal(df_output, df_expected_get_list_content)
    assert list_output == list_expected_get_list_content


def test_add_transformed_rows():
    data = {
        'Variable': [
            'demog_height',
            'comor_unlisted',
        ],
    }
    df_selected_variables = pd.DataFrame.from_dict(data)
    data = {
        'Variable': [
            'demog_height',
            'comor_unlisted',
            'comor_unlisted_0item',
            'test_var_0item',
        ],
        'Sec': [
            'demog',
            'comor',
            'comor',
            'test',
        ],
        'vari': [
            'height',
            'unlisted',
            'unlisted',
            'var',
        ],
    }
    df_arc_var_units_selected = pd.DataFrame.from_dict(data)

    variable_order = [
        'demog_height',
        'test_var_0item',
        'comor_unlisted',
    ]

    data_expected = {
        'Variable': [
            'demog_height',
            'test_var_0item',
            'comor_unlisted',
            'comor_unlisted_0item',
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc.add_transformed_rows(df_selected_variables,
                                         df_arc_var_units_selected,
                                         variable_order)

    assert_frame_equal(df_output, df_expected)


def test_custom_alignment():
    data = {
        'Variable / Field Name': [
            'text_field',
            'user_list_field',
            'radio_field',
            'radio_three_fields_over_40',
            'descriptive_field',
            'date_dmy_field',
            'checkbox_four_fields_under_40',
            'checkbox_field',

        ],
        'Field Type': [
            'text',
            'user_list',
            'radio',
            'radio',
            'descriptive',
            'date_dmy',
            'checkbox',
            'checkbox',
        ],
        'Choices, Calculations, OR Slider Labels': [
            None,
            '33, Mpox  | 88, Other',
            '1, Yes | 0, No | 99, Unknown',
            '1, Yeeeeeeees | 0, Nooooooo | 99, Unknown',
            None,
            None,
            '1, A | 2, B | 3, C | 4, D | 88, E',
            '1, Hunting | 2, Preparing | 88, Other',
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    df_custom_aligment = pd.DataFrame.from_dict({
        'Custom Alignment': [
            np.nan,
            np.nan,
            'RH',
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            'RH',
        ],
    })
    df_expected = df_datadicc.join(df_custom_aligment)

    df_output = arc._custom_alignment(df_datadicc)
    assert_frame_equal(df_output, df_expected)


def test_generate_crf():
    data = {
        'Form': [
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'outcome',
        ],
        'Section': [
            None,
            'INCLUSION CRITERIA',
            'INCLUSION CRITERIA',
            'ONSET & PRESENTATION',
            'CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing',
            'RE-ADMISSION AND PREVIOUS PIN',
            'INTERVENTIONS: Record interventions given or prescribed from day of presentation to day of discharge.',
        ],
        'Variable': [
            'subjid',
            'inclu_disease',
            'inclu_consent_date',
            'pres_firstsym',
            'comor_unlisted',
            'readm_prev_num',
            'inter_ivfluid_start',
        ],
        'Type': [
            'text',
            'user_list',
            'date_dmy',
            'multi_list',
            'list',
            'number',
            'datetime_dmy',
        ],
        'Question': [
            'Participant Identification Number (PIN)',
            'Suspected or confirmed infection',
            'Date of consent',
            'Symptom(s) during first 24 hours of illness (select all that apply)',
            'Other relevant comorbidity(s)',
            'Total number of previous admissions for this infection',
            'Date first IV fluid started',
        ],
        'Answer Options': [
            None,
            '33, Mpox  | 88, Other',
            None,
            '35, Fever | 54, Mucosal lesion | 69, Skin lesion | 88, Other',
            '1, Yes | 0, No | 99, Unknown',
            None,
            None,
        ],
        'Validation': [
            None,
            None,
            'date_dmy',
            None,
            None,
            'number',
            'datetime_dmy',
        ],
        'Minimum': [
            None,
            None,
            None,
            None,
            None,
            1,
            None,
        ],
        'Maximum': [
            None,
            None,
            'today',
            None,
            None,
            None,
            'today',
        ],
        'Skip Logic': [
            None,
            None,
            "[inclu_consent]=\'1\'",
            None,
            None,
            "[readm_prev] = \'1\' or [readm_prev]=\'2\' or [readm_prev]=\'3\'",
            "[inter_ivfluid] =\'1\'",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        'Variable / Field Name': [
            'subjid',
            'inclu_disease',
            'inclu_consent_date',
            'pres_firstsym',
            'comor_unlisted',
            'readm_prev_num',
            'inter_ivfluid_start',
        ],
        'Form Name': [
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'presentation',
            'outcome',
        ],
        'Section Header': [
            np.nan,
            'INCLUSION CRITERIA',
            np.nan,
            'ONSET & PRESENTATION',
            'CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing',
            'RE-ADMISSION AND PREVIOUS PIN',
            'INTERVENTIONS: Record interventions given or prescribed from day of presentation to day of discharge.',
        ],
        'Field Type': [
            'text',
            'radio',
            'text',
            'checkbox',
            'radio',
            'text',
            'text',
        ],
        'Field Label': [
            'Participant Identification Number (PIN)',
            'Suspected or confirmed infection',
            'Date of consent',
            'Symptom(s) during first 24 hours of illness (select all that apply)',
            'Other relevant comorbidity(s)',
            'Total number of previous admissions for this infection',
            'Date first IV fluid started',
        ],
        'Choices, Calculations, OR Slider Labels': [
            '',
            '33, Mpox  | 88, Other',
            '',
            '35, Fever | 54, Mucosal lesion | 69, Skin lesion | 88, Other',
            '1, Yes | 0, No | 99, Unknown',
            '',
            '',
        ],
        'Field Note': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Text Validation Type OR Show Slider Number': [
            '',
            '',
            'date_dmy',
            '',
            '',
            'number',
            'datetime_dmy',
        ],
        'Text Validation Min': [
            '',
            '',
            '',
            '',
            '',
            1,
            '',
        ],
        'Text Validation Max': [
            '',
            '',
            'today',
            '',
            '',
            '',
            'today',
        ],
        'Identifier?': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Branching Logic (Show field only if...)': [
            '',
            '',
            "[inclu_consent]=\'1\'",
            '',
            '',
            "[readm_prev] = \'1\' or [readm_prev]=\'2\' or [readm_prev]=\'3\'",
            "[inter_ivfluid] =\'1\'",
        ],
        'Required Field?': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Custom Alignment': [
            '',
            'RH',
            '',
            '',
            'RH',
            '',
            '',
        ],
        'Question Number (surveys only)': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Matrix Group Name': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Matrix Ranking?': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'Field Annotation': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc.generate_crf(df_datadicc)

    assert_frame_equal(df_output, df_expected)
