import datetime

import pytest


from bridge.generate_pdf.header_footer import get_page_numeral
MOCK_NOW = datetime.datetime(2025, 11, 13, 13, 8, 24)


@pytest.fixture
def patch_datetime_now(monkeypatch):
    class MockNow(datetime.datetime):
        @classmethod
        def now(cls, **kwargs):
            return MOCK_NOW

    monkeypatch.setattr(datetime, 'datetime', MockNow)


# TODO: Remove
def test_patch_datetime(patch_datetime_now):
    assert datetime.datetime.now() == MOCK_NOW

@pytest.mark.parametrize(
    "page_number, expected_output",
    [
        (1, "i"),
        (2, "ii"),
        (3, "iii"),
        (4, "iv"),
        (5, "v"),
        (6, "vi"),
        (7, "vii"),
        (8, "viii"),
        (9, "ix"),
        (10, "x"),
        (-5, "_"),
        (0, "_"),
        (27, "_"),
    ]
)
def test_get_page_numeral(page_number,
                          expected_output):
    assert get_page_numeral(page_number) == expected_output
