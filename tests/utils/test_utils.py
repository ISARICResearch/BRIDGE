# -- IMPORTS --

# -- Standard libraries --

# -- 3rd party libraries --
import pytest

# -- Internal libraries --
from bridge.utils.utils import (
    strip_html,
    strip_nonstandard_unicode_chars,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1, -1),
        (True, True),
        ("<b>Value</b>", "Value"),
        ("<b><i>Value</i></b>", "Value"),
    ],
)
def test_strip_html(value, expected):
    assert strip_html(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1, -1),
        (True, True),
        ("<b>Value</b>", "<b>Value</b>"),
        ("<b><i>Value</i></b>", "<b><i>Value</i></b>"),
        ("↳ Value", " Value"),
    ],
)
def test_strip_nonstandard_unicode_chars(value, expected):
    assert strip_nonstandard_unicode_chars(value) == expected
