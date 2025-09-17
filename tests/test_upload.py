from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
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
