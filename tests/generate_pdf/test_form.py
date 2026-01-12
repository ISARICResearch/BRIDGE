import pytest

from bridge.generate_pdf.form import Form


@pytest.mark.parametrize(
    "choices_str, field_type, threshold, is_units, expected_output",
    [
        (None, "radio", 65, False, None),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "radio",
            65,
            False,
            "○ Afghanistan   ○ Albania   ○ Algeria   ○ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "user_list",
            65,
            False,
            "○ Afghanistan   ○ Albania   ○ Algeria   ○ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "list",
            65,
            False,
            "○ Afghanistan   ○ Albania   ○ Algeria   ○ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "multi_list",
            65,
            False,
            "□ Afghanistan   □ Albania   □ Algeria   □ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "checkbox",
            65,
            False,
            "□ Afghanistan   □ Albania   □ Algeria   □ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "dropdown",
            65,
            False,
            "↧ Afghanistan   ↧ Albania   ↧ Algeria   ↧ Other",
        ),
        (
            "2, Afghanistan | 4, Albania | 56, Algeria | 88, Other",
            "not_on_the_list",
            65,
            False,
            "Afghanistan   Albania   Algeria   Other",
        ),
        (
            "2, Kilos | 4, Pounds | 56, Centimeters | 88, Other",
            "radio",
            65,
            True,
            "○Kilos   ○Pounds   ○Centimeters   ○Other",
        ),
        (
            "1, Symptomatic | 2, Asymptomatic, contact-traced | 3, Asymptomatic, mass testing campaign | 4, Not tested | 99, Unknown | 88, Other",
            "radio",
            65,
            False,
            "○ Symptomatic\n○ Asymptomatic, contact-traced\n○ Asymptomatic, mass testing campaign\n○ Not tested\n○ Unknown\n○ Other",
        ),
        (
            "1, A | 2, B | 3, C | 4, D | 5, E | 6, F | 7, G | 8, H | 9, I | 10, J | 11, K | 12, L | 13, M | 14, N | 15, O | 17, P",
            "radio",
            65,
            False,
            "_" * 40,
        ),
    ],
)
def test_format_choices(choices_str, field_type, threshold, is_units, expected_output):
    output = Form().format_choices(
        choices_str,  # type: ignore
        field_type,
        threshold,
        is_units,
    )

    assert output == expected_output


def test_parse_branching_logic_empty():
    logic_str = ""
    expected_output = []
    output = Form._parse_branching_logic(logic_str)
    assert output == expected_output


def test_parse_branching_logic():
    logic_str = "[inclu_testreason]='88'"
    output_list = Form._parse_branching_logic(logic_str)
    assert len(output_list) == 1
    assert output_list[0].field_name == "inclu_testreason"
    assert output_list[0].operator == "="
    assert output_list[0].value == "88"


def test_parse_branching_logic_or_operator():
    logic_str = "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'"
    output_list = Form._parse_branching_logic(logic_str)
    assert len(output_list) == 3
    assert output_list[0].field_name == "readm_prev"
    assert output_list[0].operator == "="
    assert output_list[0].value == "1"
    assert output_list[1].field_name == "readm_prev"
    assert output_list[1].operator == "="
    assert output_list[1].value == "2"
    assert output_list[2].field_name == "readm_prev"
    assert output_list[2].operator == "="
    assert output_list[2].value == "3"
