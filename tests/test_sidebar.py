from contextvars import copy_context
from unittest import mock

import pytest

from bridge.callbacks import sidebar as sidebar

ASSETS_DIR = '../../assets'
ICONS_DIR = f'{ASSETS_DIR}/icons'
SETTINGS_ON = f"{ICONS_DIR}/settings_on.png"
SETTINGS_OFF = f"{ICONS_DIR}/settings_off.png"
PRESET_ON = f"{ICONS_DIR}/preset_on.png"
PRESET_OFF = f"{ICONS_DIR}/preset_off.png"


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (True, False, False, SETTINGS_OFF, PRESET_ON)),
        (None, None, False, True, (True, False, False, SETTINGS_OFF, PRESET_ON)),
        (None, None, True, False, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, False, (True, False, False, SETTINGS_OFF, PRESET_ON)),
    ]
)
@mock.patch('bridge.callbacks.sidebar.get_trigger_id', return_value='toggle-settings-2')
def test_toggle_columns_settings_two(
        mock_trigger_id,
        n_presets,
        n_settings,
        in_presets,
        in_settings,
        expected_output,
):
    output = get_output_toggle_columns(n_presets,
                                       n_settings,
                                       in_presets,
                                       in_settings)
    assert output == expected_output


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (False, True, False, SETTINGS_ON, PRESET_OFF)),
        (None, None, False, True, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
        (None, None, True, False, (False, True, False, SETTINGS_ON, PRESET_OFF)),
        (None, None, False, False, (False, True, False, SETTINGS_ON, PRESET_OFF)),
    ]
)
@mock.patch('bridge.callbacks.sidebar.get_trigger_id', return_value='toggle-settings-1')
def test_toggle_columns_settings_one(
        mock_trigger_id,
        n_presets,
        n_settings,
        in_presets,
        in_settings,
        expected_output,
):
    output = get_output_toggle_columns(n_presets,
                                       n_settings,
                                       in_presets,
                                       in_settings)
    assert output == expected_output


@pytest.mark.parametrize(
    "n_presets, n_settings, in_presets, in_settings, expected_output",
    [
        (None, None, True, True, (True, True, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, True, (False, True, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, True, False, (True, False, False, SETTINGS_OFF, PRESET_OFF)),
        (None, None, False, False, (False, False, True, SETTINGS_OFF, PRESET_OFF)),
    ]
)
@mock.patch('bridge.callbacks.sidebar.get_trigger_id', return_value='no-settings')
def test_toggle_columns_settings_none(
        mock_trigger_id,
        n_presets,
        n_settings,
        in_presets,
        in_settings,
        expected_output,
):
    output = get_output_toggle_columns(n_presets,
                                       n_settings,
                                       in_presets,
                                       in_settings)
    assert output == expected_output


def get_output_toggle_columns(n_presets,
                              n_settings,
                              in_presets,
                              in_settings):
    def run_callback(_n_presets,
                     _n_settings,
                     is_in_presets,
                     is_in_settings):
        return sidebar.toggle_columns(_n_presets,
                                      _n_settings,
                                      is_in_presets,
                                      is_in_settings)

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        n_presets,
        n_settings,
        in_presets,
        in_settings,
    )
    return output
