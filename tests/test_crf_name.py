from contextvars import copy_context
from unittest import mock

import dash
import pytest

from bridge.utils.crf_name import get_crf_name


@pytest.mark.parametrize(
    "name, checked, expected_output",
    [
        (['name1', 'name2', 'name3'], [], 'name1'),
        (None, [], 'no_name'),
        (None, [['Covid'], [], [], [], []], 'Covid'),
        (None, [['Covid', 'Dengue'], [], [], [], []], 'Covid'),
        (None, [['Dengue'], [], ['Oropouche'], [], []], 'Dengue'),
        (None, [[], [], ['Oropouche'], [], []], 'Oropouche'),
    ]
)
@mock.patch('bridge.callbacks.settings.logger')
def test_get_crf_name(mock_logger, name, checked, expected_output):
    def run_callback(crf_name, checked_values):
        return get_crf_name(crf_name, checked_values)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        name,
        checked,
    )
    assert output == expected_output
