from contextvars import copy_context
from unittest import mock

import pytest

from bridge.utils.crf import get_selected_crf_presets, get_crf_name


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
        return get_crf_name(crf_name, checked_values, grouped_presets=grouped_presets)

    ctx = copy_context()
    output = ctx.run(run_callback, name, checked, grouped_presets=grouped_presets)
    assert output == expected_output
