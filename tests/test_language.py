import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bridge.callbacks.language import Language


@pytest.fixture
def version():
    return 'v1.0.0'


@pytest.fixture
def df_input():
    data = [{
        'row1': 'here is some data',
        'row2': 'here is some more data',
    }, ]
    df = pd.DataFrame.from_records(data)
    return df


@pytest.fixture
def df_output():
    data = [{
        'row1': 'here is some translated data',
        'row2': 'here is some more translated data',
    }, ]
    df = pd.DataFrame.from_records(data)
    return df


def test_get_dataframe_arc_language_english(version, df_input):
    language = 'English'
    result = Language(version, language).get_dataframe_arc_language(df_input)
    assert_frame_equal(result, df_input)


def test_get_dataframe_arc_language_not_english(version, df_input, df_output, mocker):
    language = 'Finnish'
    mocker.patch('bridge.arc.arc.get_arc_translation', return_value=df_output)
    result = Language(version, language).get_dataframe_arc_language(df_input)
    assert_frame_equal(result, df_output)
