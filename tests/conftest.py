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
