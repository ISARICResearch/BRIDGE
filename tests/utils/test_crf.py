# -- IMPORTS --

# -- Standard libraries --
from contextvars import copy_context
from unittest import mock

# -- 3rd party libraries --
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

# -- Internal libraries --
from bridge.utils.crf import (
    clean_crf_metadata,
    get_selected_crf_presets,
    get_crf_name,
)


@pytest.mark.parametrize(
    "grouped_presets, checked_values, expected_output",
    [
        (
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            [True, False, False, False, False, False],
            (("test_section1", "test_option1__first_selected"),),
        ),
        (
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3__second_selected",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            [True, False, True, False, False, False],
            (
                ("test_section1", "test_option1__first_selected"),
                ("test_section1", "test_option3__second_selected"),
            ),
        ),
        (
            {
                "test_section1": [
                    "test_option1",
                    "test_option2__first_selected",
                    "test_option3",
                ],
                "test_section2": [
                    "test_option4",
                    "test_option5__second_selected",
                    "test_option6",
                ],
            },
            [False, True, False, False, True, False],
            (
                ("test_section1", "test_option2__first_selected"),
                ("test_section2", "test_option5__second_selected"),
            ),
        ),
    ],
)
@mock.patch("bridge.utils.crf.logger")
def test_get_selected_crf_presets(
    _mock_logger, grouped_presets, checked_values, expected_output
):
    received_output = get_selected_crf_presets(grouped_presets, checked_values)

    assert expected_output == received_output


@pytest.mark.parametrize(
    "name, checked, grouped_presets, expected_output",
    [
        (["name1", "name2", "name3"], [], None, "name1"),
        (
            None,
            [True, False, False, False, False, False],
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": ["test_option4", "test_option5", "test_option6"],
            },
            "test_option1__first_selected",
        ),
        (
            None,
            [True, False, False, True, False, False],
            {
                "test_section1": [
                    "test_option1__first_selected",
                    "test_option2",
                    "test_option3",
                ],
                "test_section2": [
                    "test_option4__first_selected",
                    "test_option5",
                    "test_option6",
                ],
            },
            "test_option1__first_selected",
        ),
    ],
)
@mock.patch("bridge.utils.crf.logger")
def test_get_crf_name(_mock_logger, name, checked, grouped_presets, expected_output):
    def run_callback(crf_name, checked_values, grouped_presets):
        return get_crf_name(
            crf_name, checked_values, grouped_presets=(grouped_presets or None)
        )

    ctx = copy_context()
    output = ctx.run(run_callback, name, checked, grouped_presets)
    assert output == expected_output


@pytest.mark.parametrize(
    "crf_metadata, expected_output",
    [
        # An example case where no cleaning is required
        (
            pd.DataFrame().assign(
                A=["A1", "A2", "A3"], B=["B1", "B2", "B3"], C=["C1", "C2", "C3"]
            ),
            pd.DataFrame().assign(
                A=["A1", "A2", "A3"], B=["B1", "B2", "B3"], C=["C1", "C2", "C3"]
            ),
        ),
        # An example case where cleaning is required
        (
            pd.DataFrame().assign(
                A=["A1", "Fake A2", "A3"],
                B=["Example B1", "B2", "B3"],
                C=["C1", "C2", "C3@example.org"],
            ),
            pd.DataFrame().assign(
                A=["A1", "Unknown", "A3"],
                B=["Unknown", "B2", "B3"],
                C=["C1", "C2", "Unknown"],
            ),
        ),
    ],
)
def test_clean_crf_metadata(crf_metadata, expected_output):
    received_output = clean_crf_metadata(crf_metadata)
    assert_frame_equal(received_output, expected_output)
