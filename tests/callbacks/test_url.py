from contextvars import copy_context

import dash
import pytest

from bridge.callbacks import url


@pytest.mark.parametrize(
    "template_check, presets, address, expected_output",
    [
        (False, None, None, dash.no_update),
        (True, None, "http://127.0.0.1:8050/main", dash.no_update),
    ],
)
def test_update_output_based_on_url_no_action(
    template_check, presets, address, expected_output
):
    output = get_output_update_output_based_on_url(template_check, presets, address)
    assert output == expected_output


@pytest.mark.parametrize(
    "template_check, presets, address, expected_output",
    [
        (
            True,
            {
                "ARChetype Disease CRF": ["Covid", "Dengue", "Mpox"],
                "ARChetype Syndromic CRF": ["ARI"],
            },
            "http://127.0.0.1:8050/main?param=ARChetype%20Disease%20CRF_Dengue",
            (["Dengue"], [["Dengue"], []]),
        ),
        (
            True,
            {
                "ARChetype Disease CRF": ["Covid", "Dengue", "Mpox"],
                "Recommended Outcomes": ["Dengue"],
            },
            "http://127.0.0.1:8050/main?param=Recommended%20Outcomes_Dengue",
            (["Dengue"], [[], ["Dengue"]]),
        ),
    ],
)
def test_update_output_based_on_url(template_check, presets, address, expected_output):
    output = get_output_update_output_based_on_url(template_check, presets, address)
    assert output == expected_output


def get_output_update_output_based_on_url(template_check, presets, address):
    def run_callback(template_check_flag, grouped_presets, href):
        return url.update_output_based_on_url(
            template_check_flag, grouped_presets, href
        )

    ctx = copy_context()
    output = ctx.run(
        run_callback,
        template_check,
        presets,
        address,
    )
    return output
