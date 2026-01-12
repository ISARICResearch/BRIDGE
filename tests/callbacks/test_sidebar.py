from contextvars import copy_context
from unittest import mock

import pytest

from bridge.callbacks import sidebar

SETTINGS_ON = "settings_on.png"
SETTINGS_OFF = "settings_off.png"
PRESET_ON = "preset_on.png"
PRESET_OFF = "preset_off.png"


class ConditionalMock:
    # https://stackoverflow.com/questions/74795034/single-line-conditional-mocking-return-values-in-pytest
    def __init__(self, mocker, path):
        self.mock = mocker.patch(path, new=self._replacement)
        self._side_effects = {}
        self._default = None
        self._raise_if_not_matched = True

    def expect(self, condition, return_value):
        condition = tuple(condition)
        self._side_effects[condition] = return_value
        return self

    def _replacement(self, *args):
        if args in self._side_effects:
            return self._side_effects[args]
        if self._raise_if_not_matched:
            raise AssertionError(f"Arguments {args} not expected")
        return self._default


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (True, False, False, SETTINGS_OFF, PRESET_ON)),
        (None, None, False, True, (True, False, False, SETTINGS_OFF, PRESET_ON)),
        (None, None, True, False, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, False, (True, False, False, SETTINGS_OFF, PRESET_ON)),
    ],
)
@mock.patch("bridge.callbacks.sidebar.get_trigger_id", return_value="toggle-settings-2")
def test_toggle_columns_settings_two(
    mock_trigger_id,
    mocker,
    n_presets,
    n_settings,
    in_presets,
    in_settings,
    expected_output,
):
    ConditionalMock(mocker, "dash.get_asset_url").expect(
        (SETTINGS_ON,), return_value=SETTINGS_ON
    ).expect((SETTINGS_OFF,), return_value=SETTINGS_OFF).expect(
        (PRESET_ON,), return_value=PRESET_ON
    ).expect((PRESET_OFF,), return_value=PRESET_OFF)

    output = get_output_toggle_columns(n_presets, n_settings, in_presets, in_settings)
    assert output == expected_output


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (False, True, False, SETTINGS_ON, PRESET_OFF)),
        (None, None, False, True, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
        (None, None, True, False, (False, True, False, SETTINGS_ON, PRESET_OFF)),
        (None, None, False, False, (False, True, False, SETTINGS_ON, PRESET_OFF)),
    ],
)
@mock.patch("bridge.callbacks.sidebar.get_trigger_id", return_value="toggle-settings-1")
def test_toggle_columns_settings_one(
    mock_trigger_id,
    mocker,
    n_presets,
    n_settings,
    in_presets,
    in_settings,
    expected_output,
):
    ConditionalMock(mocker, "dash.get_asset_url").expect(
        (SETTINGS_ON,), return_value=SETTINGS_ON
    ).expect((SETTINGS_OFF,), return_value=SETTINGS_OFF).expect(
        (PRESET_ON,), return_value=PRESET_ON
    ).expect((PRESET_OFF,), return_value=PRESET_OFF)

    output = get_output_toggle_columns(n_presets, n_settings, in_presets, in_settings)
    assert output == expected_output


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (True, True, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, True, (False, True, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, True, False, (True, False, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, False, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
    ],
)
@mock.patch("bridge.callbacks.sidebar.get_trigger_id", return_value="no-settings")
def test_toggle_columns_settings_none(
    mock_trigger_id,
    mocker,
    n_presets,
    n_settings,
    in_presets,
    in_settings,
    expected_output,
):
    ConditionalMock(mocker, "dash.get_asset_url").expect(
        (SETTINGS_ON,), return_value=SETTINGS_ON
    ).expect((SETTINGS_OFF,), return_value=SETTINGS_OFF).expect(
        (PRESET_ON,), return_value=PRESET_ON
    ).expect((PRESET_OFF,), return_value=PRESET_OFF)

    output = get_output_toggle_columns(n_presets, n_settings, in_presets, in_settings)
    assert output == expected_output


def get_output_toggle_columns(n_presets, n_settings, in_presets, in_settings):
    def run_callback(_n_presets, _n_settings, is_in_presets, is_in_settings):
        return sidebar.toggle_columns(
            _n_presets, _n_settings, is_in_presets, is_in_settings
        )

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        n_presets,
        n_settings,
        in_presets,
        in_settings,
    )
    return output
