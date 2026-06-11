# -- IMPORTS --

# -- Standard libraries --
from pathlib import Path

# -- 3rd party libraries --
import pandas as pd
import pytest

# -- Internal libraries --


@pytest.fixture(scope="module")
def ccpuk_hantavirus_data_dictionary_2026_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath(
        "data", "ccpuk-hantavirus-data-dictionary-2026-05-15.csv"
    )


@pytest.fixture(scope="module")
def ccpuk_hantavirus_data_dictionary_2026(
    ccpuk_hantavirus_data_dictionary_2026_filepath,
) -> pd.DataFrame:
    return pd.read_csv(ccpuk_hantavirus_data_dictionary_2026_filepath)


@pytest.fixture(scope="module")
def arc_1_2_2__english__paperlike_crf_details_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath("data", "arc-1.2.2-en-paperlike-details.csv")


@pytest.fixture(scope="module")
def arc_1_2_2__english__paperlike_crf_details(
    arc_1_2_2__english__paperlike_crf_details_filepath,
) -> pd.DataFrame:
    return pd.read_csv(arc_1_2_2__english__paperlike_crf_details_filepath)


@pytest.fixture(scope="module")
def arc_1_2_2__english__supplemental_phrases_filepath() -> pd.DataFrame:
    return Path(__file__).parent.joinpath(
        "data", "arc-1.2.2-en-supplemental-phrases.csv"
    )


@pytest.fixture(scope="module")
def arc_1_2_2__english__supplemental_phrases(
    arc_1_2_2__english__supplemental_phrases_filepath,
) -> pd.DataFrame:
    return pd.read_csv(arc_1_2_2__english__supplemental_phrases_filepath)


@pytest.fixture(scope="module")
def arc_1_3_0__crf_metadata() -> pd.DataFrame:
    return pd.read_csv(
        Path(__file__).parent.joinpath("data", "arc-1.3.0-crf-metadata.csv")
    )
