import io
import json
from contextvars import copy_context
from unittest import mock

import dash
import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash import dcc, html
from pandas.testing import assert_frame_equal

from bridge.callbacks import modals

pytestmark = [pytest.mark.unit, pytest.mark.arc]


SUBMIT_N_CLICKS_NONE = None
CANCEL_N_CLICKS_NONE = None
CURRENT_DATADICC_SAVED_NONE = None
MODAL_TITLE_NONE = None
MODAL_OPTIONS_CHECKED_NONE = None
CHECKED_NONE = None
ULIST_VARIABLE_CHOICES_SAVED_NONE = None
MULTILIST_VARIABLE_CHOICES_SAVED_NONE = None
SELECTED_VERSION_DATA_NONE = None
SELECTED_LANGUAGE_DATA_NONE = None
DYNAMIC_UNITS_CONVERSION_NONE = None


def test_update_list_variables_checked():
    data = {
        "cod": [1, 15, 33],
        "Option": ["Adenovirus", "HSV", "Mpox"],
    }
    df_list_options_checked = pd.DataFrame.from_dict(data)
    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_disease_otherl2",
            "demog_country",
        ],
        "Answer Options": [
            "",
            "2, Andes virus",
            "",
            "",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    other_text = "Other"
    variable_submitted = "inclu_disease"
    variable_choices_list = [
        [
            "inclu_disease",
            [
                [1, "Adenovirus", 0],
                [2, "Andes virus", 0],
                [15, "HSV", 0],
                [33, "Mpox", 0],
            ],
        ],
        [
            "inclu_disease_otherl2",
            [
                [1, "Made this up", 0],
            ],
        ],
        ["demog_country", [[1, "Afghanistan", 0], [2, "Aland Islands", 0]]],
    ]
    df_output, str_output = modals.update_list_variables_checked(
        variable_choices_list,
        variable_submitted,
        df_list_options_checked,
        df_datadicc,
        other_text,
    )

    list_expected = [
        [
            "inclu_disease",
            [
                [1, "Adenovirus", 1],
                [2, "Andes virus", 0],
                [15, "HSV", 1],
                [33, "Mpox", 1],
            ],
        ],
        ["inclu_disease_otherl2", [[1, "Made this up", 0]]],
        ["demog_country", [[1, "Afghanistan", 0], [2, "Aland Islands", 0]]],
    ]
    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_disease_otherl2",
            "demog_country",
        ],
        "Answer Options": [
            "",
            "1, Adenovirus | 15, HSV | 33, Mpox | 88, Other",
            "2, Andes virus | 88, Other",
            "",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data)

    assert str_output == json.dumps(list_expected)
    assert_frame_equal(df_output, df_expected)


def test__section():
    test_title = "test_title"
    expected = html.Section(
        [
            html.H3(test_title, className="section-title"),
            html.Div("test_div"),
        ],
        className="section",
    )

    received = modals._section(test_title, html.Div("test_div"))

    assert isinstance(received, dash.html.Section)
    assert str(received) == str(expected)


def test__metadata_grid():
    test_items = [
        ("test_items_label1", "test_items_value1"),
        ("test_items_label2", "test_items_value2"),
    ]
    expected = html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="metadata-label"),
                    html.Div(value, className="metadata-value"),
                ],
                className="metadata-item",
            )
            for label, value in test_items
        ],
        className="metadata-grid",
    )

    received = modals._metadata_grid(test_items)

    assert isinstance(received, dash.html.Div)
    assert str(received) == str(expected)


def test__scope_item():
    test_label = "test_label"
    test_value = "test_value"
    expected = html.Div(
        [
            html.Div(test_label, className="scope-label"),
            html.Div(test_value, className="scope-value"),
        ],
        className="scope-item",
    )

    received = modals._scope_item(test_label, test_value)

    assert isinstance(received, dash.html.Div)
    assert str(received) == str(expected)


def test__pathogen_value():
    test_pathogens = ["test_pathogen1", "test_pathogen2"]
    expected = html.Div(
        [html.Span(pathogen, className="pathogen-chip") for pathogen in test_pathogens],
        className="pathogen-list",
    )

    received = modals._pathogen_value(test_pathogens)

    assert isinstance(received, dash.html.Div)
    assert str(received) == str(expected)


def test__approvers_inline():
    test_approvers = ["test_approver1", "test_approver2"]
    expected = html.Div(
        ", ".join(test_approvers),
        className="approver-line",
    )

    received = modals._approvers_inline(test_approvers)

    assert isinstance(received, dash.html.Div)
    assert str(received) == str(expected)


class TestPopulationItem:
    def test__population_item__population_item_first_false(self):
        test_label = "test_label"
        test_value = "test_value"
        test_population_item_first_false = False
        expected = html.Div(
            [
                html.Div(test_label, className="population-label"),
                html.Div(test_value, className="population-value"),
            ],
            className="population-item",
        )

        received = modals._population_item(
            test_label, test_value, first=test_population_item_first_false
        )

        assert isinstance(received, dash.html.Div)
        assert str(received) == str(expected)

    def test__population_item__population_item_first_true(self):
        test_label = "test_label"
        test_value = "test_value"
        test_population_item_first_true = True
        expected = html.Div(
            [
                html.Div(test_label, className="population-label"),
                html.Div(test_value, className="population-value"),
            ],
            className="population-item first",
        )

        received = modals._population_item(
            test_label, test_value, first=test_population_item_first_true
        )

        assert isinstance(received, dash.html.Div)
        assert str(received) == str(expected)


class TestAuthorNameWithSuperscripts:
    def test__author_name_with_superscripts__no_affiliations(self):
        test_author_name = "test_author_name"
        test_affiliation_numbers = []
        test_author = {
            "name": test_author_name,
            "affiliations": test_affiliation_numbers,
        }
        expected = dash.html.Span(["test_author_name"])

        received = modals._author_name_with_superscripts(test_author)

        assert isinstance(received, dash.html.Span)
        assert str(received) == str(expected)

    def test__author_name_with_superscripts__affiliations_present(self):
        test_author_name = "test_author_name"
        test_affiliation_numbers = ["test_affiliation1", "test_affiliation2"]
        test_author = {
            "name": test_author_name,
            "affiliations": test_affiliation_numbers,
        }
        expected = dash.html.Span(
            [
                "test_author_name",
                html.Sup(
                    ",".join(str(number) for number in test_affiliation_numbers),
                    className="author-sup",
                ),
            ]
        )

        received = modals._author_name_with_superscripts(test_author)

        assert isinstance(received, dash.html.Span)
        assert str(received) == str(expected)


class TestAuthorsInline:
    def test__authors_line__no_authors_with_affiliations(self):
        test_author1_name = "test_author1_name"
        test_author1_affiliation_numbers = []
        test_author1 = {
            "name": test_author1_name,
            "affiliations": test_author1_affiliation_numbers,
        }
        test_author2_name = "test_author2_name"
        test_author2_affiliation_numbers = []
        test_author2 = {
            "name": test_author2_name,
            "affiliations": test_author2_affiliation_numbers,
        }
        test_authors = [test_author1, test_author2]
        expected = html.Div(
            [
                dash.html.Span(["test_author1_name"]),
                ", ",
                dash.html.Span(["test_author2_name"]),
            ],
            className="author-line",
        )

        received = modals._authors_inline(test_authors)

        assert isinstance(received, dash.html.Div)
        assert str(received) == str(expected)

    def test__authors_line__only_first_author_with_affiliations(self):
        test_author1_name = "test_author1_name"
        test_author1_affiliation_numbers = [
            "test_author1_affiliation1",
            "test_author1_affiliation2",
        ]
        test_author1 = {
            "name": test_author1_name,
            "affiliations": test_author1_affiliation_numbers,
        }
        test_author2_name = "test_author2_name"
        test_author2_affiliation_numbers = []
        test_author2 = {
            "name": test_author2_name,
            "affiliations": test_author2_affiliation_numbers,
        }
        test_authors = [test_author1, test_author2]
        expected = html.Div(
            [
                dash.html.Span(
                    [
                        "test_author1_name",
                        html.Sup(
                            ",".join(
                                str(number)
                                for number in test_author1_affiliation_numbers
                            ),
                            className="author-sup",
                        ),
                    ]
                ),
                ", ",
                dash.html.Span(["test_author2_name"]),
            ],
            className="author-line",
        )

        received = modals._authors_inline(test_authors)

        assert isinstance(received, dash.html.Div)
        assert str(received) == str(expected)

    def test__authors_line__both_authors_with_affiliations(self):
        test_author1_name = "test_author1_name"
        test_author1_affiliation_numbers = [
            "test_author1_affiliation1",
            "test_author1_affiliation2",
        ]
        test_author1 = {
            "name": test_author1_name,
            "affiliations": test_author1_affiliation_numbers,
        }
        test_author2_name = "test_author2_name"
        test_author2_affiliation_numbers = [
            "test_author2_affiliation1",
            "test_author2_affiliation2",
        ]
        test_author2 = {
            "name": test_author2_name,
            "affiliations": test_author2_affiliation_numbers,
        }
        test_authors = [test_author1, test_author2]
        expected = html.Div(
            [
                dash.html.Span(
                    [
                        "test_author1_name",
                        html.Sup(
                            ",".join(
                                str(number)
                                for number in test_author1_affiliation_numbers
                            ),
                            className="author-sup",
                        ),
                    ]
                ),
                ", ",
                dash.html.Span(
                    [
                        "test_author2_name",
                        html.Sup(
                            ",".join(
                                str(number)
                                for number in test_author2_affiliation_numbers
                            ),
                            className="author-sup",
                        ),
                    ]
                ),
            ],
            className="author-line",
        )

        received = modals._authors_inline(test_authors)

        assert isinstance(received, dash.html.Div)
        assert str(received) == str(expected)


def test__build_crf_metadata_modal_tabbed_body():
    test_selected_version = "test_selected_version"
    test_template_name = "test crf"
    expected = html.Div(
        [
            "",
            dcc.Tabs(
                id="crf-metadata-modal-tabbed-body",
                value="test_selected_version|test crf|project-overview-tab",
                children=[
                    dcc.Tab(
                        label="Project Overview",
                        value="test_selected_version|test crf|project-overview-tab",
                    ),
                    dcc.Tab(
                        label="Scientific Scope",
                        value="test_selected_version|test crf|scientific-scope-tab",
                    ),
                    dcc.Tab(
                        label="Governance & Contributors",
                        value="test_selected_version|test crf|governance-and-contributors-tab",
                    ),
                    dcc.Tab(
                        label="Documentation & Discoverability",
                        value="test_selected_version|test crf|documentation-and-discoverability-tab",
                    ),
                ],
            ),
            html.Div(
                id="crf-metadata-modal-body-tab-content",
                style={
                    "width": "800px",
                    "height": "250px",
                    "overflow-x": "hidden",
                    "white-space": "normal",
                },
            ),
        ]
    )

    received = modals._build_crf_metadata_modal_tabbed_body(
        test_selected_version, test_template_name
    )
    assert str(received) == str(expected)


def test__build_crf_metadata_modal_project_overview_tab(arc_1_4_0__crf_metadata):
    dengue_metadata = (
        arc_1_4_0__crf_metadata.iloc[1].fillna("Unknown").replace("", "Unknown")
    )
    expected = dcc.Markdown(
        f"""
        - **Description** - {dengue_metadata['Description']}
        - **Study Type** - {dengue_metadata['Study type']}
        - **Version** - {dengue_metadata['Version']}
        - **Publication Date** - {dengue_metadata['Date of publication/release']}
        """
    )
    received = modals._build_crf_metadata_modal_project_overview_tab(dengue_metadata)
    assert str(received) == str(expected)


def test__build_crf_metadata_modal_scientific_scope_tab(arc_1_4_0__crf_metadata):
    dengue_metadata = (
        arc_1_4_0__crf_metadata.iloc[1].fillna("Unknown").replace("", "Unknown")
    )
    expected = dcc.Markdown(
        f"""
        - **Research Questions** - {dengue_metadata['Research questions']}
        - **Target Population** - {dengue_metadata['Target population']}
        - **Inclusion Criteria** - {dengue_metadata['Inclusion Criteria']}
        - **Exclusion Criteria** - {dengue_metadata['Exclusion Criteria']}
        - **Pathogen/Agent** - {dengue_metadata['Pathogen or agent']}
        - **Syndrome** - {dengue_metadata['Syndrome / clinical presentation']}
        - **Setting** - {dengue_metadata['Setting']}
        - **Geographic Scope** - {dengue_metadata['Geographic scope']}
        """
    )
    received = modals._build_crf_metadata_modal_scientific_scope_tab(dengue_metadata)
    assert str(received) == str(expected)


def test__build_crf_metadata_modal_governance_and_contributors_tab(
    arc_1_4_0__crf_metadata,
):
    dengue_metadata = (
        arc_1_4_0__crf_metadata.iloc[1].fillna("Unknown").replace("", "Unknown")
    )
    expected = dcc.Markdown(
        f"""
        - **Authors** - {dengue_metadata['Authors']}
        - **Approvers** - {dengue_metadata['Approvers']}
        - **Institutions** - {dengue_metadata['Institutions']}
        - **Contact** - Unknown
        """
    )
    received = modals._build_crf_metadata_modal_governance_and_contributors_tab(
        dengue_metadata
    )
    assert str(received) == str(expected)


def test__build_crf_metadata_modal_documentation_and_discoverability_tab(
    arc_1_4_0__crf_metadata,
):
    dengue_metadata = (
        arc_1_4_0__crf_metadata.iloc[1].fillna("Unknown").replace("", "Unknown")
    )

    expected = html.Div(
        [
            html.Ul(
                children=[
                    html.Li([html.B("Keywords"), f" - {dengue_metadata['Keywords']}"]),
                    html.Li(
                        [html.B("Relevant Links"), " - "]
                        + [
                            html.A(url, href=url, target="_blank")
                            if url.lower() != "unknown"
                            else "Unknown"
                            for url in dengue_metadata["Relevant resources"].split(",")
                        ]
                    ),
                ]
            )
        ]
    )
    received = modals._build_crf_metadata_modal_documentation_and_discoverability_tab(
        dengue_metadata
    )
    assert str(received) == str(expected)


def test_on_modal_button_click_not_triggered():
    trigger = None
    output = get_output_on_modal_button_click(
        trigger,
        SUBMIT_N_CLICKS_NONE,
        CANCEL_N_CLICKS_NONE,
        CURRENT_DATADICC_SAVED_NONE,
        MODAL_TITLE_NONE,
        MODAL_OPTIONS_CHECKED_NONE,
        CHECKED_NONE,
        ULIST_VARIABLE_CHOICES_SAVED_NONE,
        MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
        SELECTED_VERSION_DATA_NONE,
        SELECTED_LANGUAGE_DATA_NONE,
        DYNAMIC_UNITS_CONVERSION_NONE,
    )
    expected = (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    assert output == expected


@mock.patch("bridge.callbacks.modals.get_trigger_id", return_value="nothing_modal")
def test_on_modal_button_click_wrong_trigger(mock_trigger_id):
    output = get_output_on_modal_button_click(
        mock_trigger_id,
        SUBMIT_N_CLICKS_NONE,
        CANCEL_N_CLICKS_NONE,
        CURRENT_DATADICC_SAVED_NONE,
        MODAL_TITLE_NONE,
        MODAL_OPTIONS_CHECKED_NONE,
        CHECKED_NONE,
        ULIST_VARIABLE_CHOICES_SAVED_NONE,
        MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
        SELECTED_VERSION_DATA_NONE,
        SELECTED_LANGUAGE_DATA_NONE,
        DYNAMIC_UNITS_CONVERSION_NONE,
    )
    expected = (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
    assert output == expected


@mock.patch("bridge.callbacks.modals.get_trigger_id", return_value="modal_cancel")
def test_on_modal_button_click_modal_cancel(mock_trigger_id):
    output = get_output_on_modal_button_click(
        mock_trigger_id,
        SUBMIT_N_CLICKS_NONE,
        CANCEL_N_CLICKS_NONE,
        CURRENT_DATADICC_SAVED_NONE,
        MODAL_TITLE_NONE,
        MODAL_OPTIONS_CHECKED_NONE,
        CHECKED_NONE,
        ULIST_VARIABLE_CHOICES_SAVED_NONE,
        MULTILIST_VARIABLE_CHOICES_SAVED_NONE,
        SELECTED_VERSION_DATA_NONE,
        SELECTED_LANGUAGE_DATA_NONE,
        DYNAMIC_UNITS_CONVERSION_NONE,
    )
    expected = (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    assert output == expected


@pytest.mark.parametrize(
    "ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        (
            '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
            '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
            (
                False,
                '{"columns":["Form","Variable"],"index":[0,1],"data":[["presentation","inclu_disease"],["presentation","inclu_disease"]]}',
                [
                    [
                        "inclu_disease",
                        [
                            [1, "Adenovirus", 0],
                            [2, "Andes virus", 0],
                            [10, "Dengue", 1],
                            [33, "Mpox ", 1],
                        ],
                    ]
                ],
                [
                    [
                        "pres_firstsym",
                        [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]],
                    ]
                ],
                ["Just for checking"],
            ),
        ),
        (
            '[["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 1], [3, "Finland", 1]]]]',
            '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
            (False, dash.no_update, dash.no_update, dash.no_update, dash.no_update),
        ),
    ],
)
@mock.patch("bridge.callbacks.modals.html.Div", return_value=["Just for checking"])
@mock.patch("bridge.callbacks.modals.arc_tree.get_tree_items")
@mock.patch("bridge.callbacks.modals.update_list_variables_checked")
@mock.patch(
    "bridge.callbacks.modals.arc_translations.get_translations",
    return_value={"other": "Other"},
)
@mock.patch("bridge.callbacks.modals.get_trigger_id", return_value="modal_submit")
def test_on_modal_button_click_modal_submit(
    mock_trigger_id,
    _mock_get_translations,
    mock_list_choices,
    _mock_get_tree_items,
    _mock_html_div,
    ulist_variable_choices_saved,
    multilist_variable_choices_saved,
    expected_output,
):
    submit_n_clicks = None
    cancel_n_clicks = None
    current_datadicc_saved = '{"columns":["Form", "Variable"], "index":[0, 1], "data":[["presentation", "inclu_disease"]]}'
    df_current_datadicc = pd.read_json(
        io.StringIO(current_datadicc_saved), orient="split"
    )
    modal_title = "Suspected or confirmed infection [inclu_disease]"
    modal_options_checked = ["33_Mpox ", "1_Adenovirus", "10_Dengue "]
    checked = []
    selected_version_data = {"selected_version": "v1.1.1"}
    selected_language_data = {"selected_language": "English"}
    dynamic_units_conversion = False  # Not used

    mock_list_choices.side_effect = [
        (df_current_datadicc, json.loads(ulist_variable_choices_saved)),
        (df_current_datadicc, json.loads(multilist_variable_choices_saved)),
    ]

    output = get_output_on_modal_button_click(
        mock_trigger_id,
        submit_n_clicks,
        cancel_n_clicks,
        current_datadicc_saved,
        modal_title,
        modal_options_checked,
        checked,
        ulist_variable_choices_saved,
        multilist_variable_choices_saved,
        selected_version_data,
        selected_language_data,
        dynamic_units_conversion,
    )

    assert output == expected_output


def get_output_on_modal_button_click(
    trigger,
    submit_n_clicks,
    cancel_n_clicks,
    current_datadicc_saved,
    modal_title,
    modal_options_checked,
    checked,
    ulist_variable_choices_saved,
    multilist_variable_choices_saved,
    selected_version_data,
    selected_language_data,
    dynamic_units_conversion,
):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return modals.on_modal_button_click(
            submit_n_clicks,
            cancel_n_clicks,
            current_datadicc_saved,
            modal_title,
            modal_options_checked,
            checked,
            ulist_variable_choices_saved,
            multilist_variable_choices_saved,
            selected_version_data,
            selected_language_data,
            dynamic_units_conversion,
        )

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


@pytest.mark.parametrize(
    "selected, ulist_variable_choices_saved, multilist_variable_choices_saved, current_datadicc_saved, expected_output",
    [
        (
            [],
            None,
            None,
            None,
            (
                False,
                "",
                "",
                "",
                "",
                {"display": "none"},
                {"display": "none"},
                [],
                [],
                [],
            ),
        ),
    ],
)
def test_display_selected_in_modal_nothing_selected(
    selected,
    ulist_variable_choices_saved,
    multilist_variable_choices_saved,
    current_datadicc_saved,
    expected_output,
):
    output = get_output_display_selected_in_modal(
        selected,
        ulist_variable_choices_saved,
        multilist_variable_choices_saved,
        current_datadicc_saved,
    )
    assert output == expected_output


@mock.patch(
    "bridge.callbacks.modals.dbc.ListGroupItem", return_value=["List group item"]
)
@pytest.mark.parametrize(
    "selected, ulist_variable_choices_saved, multilist_variable_choices_saved, expected_output",
    [
        (
            ["inclu_disease"],
            '[["inclu_disease", [[1, "Adenovirus", 0], [2, "Andes virus", 0], [10, "Dengue", 1], [33, "Mpox ", 1]]]]',
            '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
            (
                True,
                "This is the question [inclu_disease]",
                "This is the definition",
                "This is the completion guideline",
                "This is the branch",
                {"maxHeight": "250px", "overflowY": "auto", "padding": "20px"},
                {"display": "none"},
                [
                    {"label": "1, Adenovirus", "value": "1_Adenovirus"},
                    {"label": "2, Andes virus", "value": "2_Andes virus"},
                    {"label": "10, Dengue", "value": "10_Dengue"},
                    {"label": "33, Mpox ", "value": "33_Mpox "},
                ],
                ["10_Dengue", "33_Mpox "],
                [],
            ),
        ),
        (
            ["inclu_disease"],
            '[["demog_country", [[1, "Afghanistan", 0], [2, "Estonia", 0]]]]',
            '[["pres_firstsym", [[1, "Abdominal pain", 0], [2, "Abnormal weight loss", 0]]]]',
            (
                True,
                "This is the question [inclu_disease]",
                "This is the definition",
                "This is the completion guideline",
                "This is the branch",
                {"display": "none"},
                {"maxHeight": "250px", "overflowY": "auto"},
                [],
                [],
                [["List group item"]],
            ),
        ),
    ],
)
def test_display_selected_in_modal(
    _mock_list_group_item,
    selected,
    ulist_variable_choices_saved,
    multilist_variable_choices_saved,
    expected_output,
):
    current_datadicc_saved = (
        '{"columns":["Form", "Variable", "Question", "Definition", "Completion Guideline", "Branch", "Answer Options"],'
        '"index":[0, 1, 2, 3, 4, 5, 6],'
        '"data":['
        '["presentation",'
        '"inclu_disease",'
        '"This is the question",'
        '"This is the definition",'
        '"This is the completion guideline",'
        '"This is the branch",'
        '"These are the answer options"]]}'
    )

    output = get_output_display_selected_in_modal(
        selected,
        ulist_variable_choices_saved,
        multilist_variable_choices_saved,
        current_datadicc_saved,
    )
    assert output == expected_output


def test_build_checklist_dom_from_mapping_is_cached():
    modals._build_checklist_dom_from_mapping_cached.cache_clear()
    options_mapping = {
        "inclu_disease": (
            ("1", "Adenovirus", 0),
            ("10", "Dengue", 1),
            ("33", "Mpox", 1),
        )
    }

    output_1 = modals.build_checklist_dom_from_mapping(options_mapping, "inclu_disease")
    output_2 = modals.build_checklist_dom_from_mapping(options_mapping, "inclu_disease")
    cache_info = modals._build_checklist_dom_from_mapping_cached.cache_info()

    assert output_1 == output_2
    assert output_1 == (
        [
            {"label": "1, Adenovirus", "value": "1_Adenovirus"},
            {"label": "10, Dengue", "value": "10_Dengue"},
            {"label": "33, Mpox", "value": "33_Mpox"},
        ],
        ["10_Dengue", "33_Mpox"],
    )
    assert cache_info.hits == 1


def get_output_display_selected_in_modal(
    selected,
    ulist_variable_choices_saved,
    multilist_variable_choices_saved,
    current_datadicc_saved,
):
    def run_callback():
        return modals.display_selected_in_modal(
            selected,
            ulist_variable_choices_saved,
            multilist_variable_choices_saved,
            current_datadicc_saved,
        )

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


def get_output_display_crf_metadata_modal(
    trigger, info_btn_clicks, close_btn_clicks, info_btn_ids, selected_version_data
):
    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": trigger}))
        return modals.display_crf_metadata_modal(
            info_btn_clicks, close_btn_clicks, info_btn_ids, selected_version_data
        )

    ctx = copy_context()
    output = ctx.run(run_callback)
    return output


@pytest.mark.parametrize(
    "trigger, info_btn_clicks, close_btn_clicks, info_btn_ids, selected_version_data, expected_output",
    [
        # ARChetype Disease CRF preset modal - test input when no option is selected
        (
            None,
            [0, 0, 0, 0, 0, 0],
            0,
            [
                {"type": "template-info-btn", "index": "Covid"},
                {"type": "template-info-btn", "index": "H5Nx"},
                {"type": "template-info-btn", "index": "Dengue"},
                {"type": "template-info-btn", "index": "Chikungunya"},
                {"type": "template-info-btn", "index": "Mpox"},
                {"type": "template-info-btn", "index": "Mpox Pregnancy and Paediatric"},
            ],
            {"selected_version": "test_selected_version"},
            (False, "", ""),
        ),
        # ARChetype Disease CRF preset modal - test input when the Covid option is selected and the modal is opened
        (
            [
                {
                    "prop_id": '{"index":"Covid","type":"template-info-btn"}.n_clicks',
                    "value": 1,
                }
            ],
            [1, 0, 0, 0, 0, 0],
            0,
            [
                {"type": "template-info-btn", "index": "Covid"},
                {"type": "template-info-btn", "index": "H5Nx"},
                {"type": "template-info-btn", "index": "Dengue"},
                {"type": "template-info-btn", "index": "Chikungunya"},
                {"type": "template-info-btn", "index": "Mpox"},
                {"type": "template-info-btn", "index": "Mpox Pregnancy and Paediatric"},
            ],
            {"selected_version": "test_selected_version"},
            (
                True,
                "Covid",
                html.Div(
                    [
                        "",
                        dcc.Tabs(
                            children=[
                                dcc.Tab(
                                    label="Project Overview",
                                    value="test_selected_version|Covid|project-overview-tab",
                                ),
                                dcc.Tab(
                                    label="Scientific Scope",
                                    value="test_selected_version|Covid|scientific-scope-tab",
                                ),
                                dcc.Tab(
                                    label="Governance & Contributors",
                                    value="test_selected_version|Covid|governance-and-contributors-tab",
                                ),
                                dcc.Tab(
                                    label="Documentation & Discoverability",
                                    value="test_selected_version|Covid|documentation-and-discoverability-tab",
                                ),
                            ],
                            id="crf-metadata-modal-tabbed-body",
                            value="test_selected_version|Covid|project-overview-tab",
                        ),
                        html.Div(
                            id="crf-metadata-modal-body-tab-content",
                            style={
                                "width": "800px",
                                "height": "250px",
                                "overflow-x": "hidden",
                                "white-space": "normal",
                            },
                        ),
                    ]
                ),
            ),
        ),
        # ARChetype Disease CRF preset modal - test input when both the Covid and Dengue options
        # are selected but the Dengue modal is opened
        (
            [
                {
                    "prop_id": '{"index":"Dengue","type":"template-info-btn"}.n_clicks',
                    "value": 1,
                }
            ],
            [1, 0, 1, 0, 0, 0],
            0,
            [
                {"type": "template-info-btn", "index": "Covid"},
                {"type": "template-info-btn", "index": "H5Nx"},
                {"type": "template-info-btn", "index": "Dengue"},
                {"type": "template-info-btn", "index": "Chikungunya"},
                {"type": "template-info-btn", "index": "Mpox"},
                {"type": "template-info-btn", "index": "Mpox Pregnancy and Paediatric"},
            ],
            {"selected_version": "test_selected_version"},
            (
                True,
                "Dengue",
                html.Div(
                    [
                        "",
                        dcc.Tabs(
                            children=[
                                dcc.Tab(
                                    label="Project Overview",
                                    value="test_selected_version|Dengue|project-overview-tab",
                                ),
                                dcc.Tab(
                                    label="Scientific Scope",
                                    value="test_selected_version|Dengue|scientific-scope-tab",
                                ),
                                dcc.Tab(
                                    label="Governance & Contributors",
                                    value="test_selected_version|Dengue|governance-and-contributors-tab",
                                ),
                                dcc.Tab(
                                    label="Documentation & Discoverability",
                                    value="test_selected_version|Dengue|documentation-and-discoverability-tab",
                                ),
                            ],
                            id="crf-metadata-modal-tabbed-body",
                            value="test_selected_version|Dengue|project-overview-tab",
                        ),
                        html.Div(
                            id="crf-metadata-modal-body-tab-content",
                            style={
                                "width": "800px",
                                "height": "250px",
                                "overflow-x": "hidden",
                                "white-space": "normal",
                            },
                        ),
                    ]
                ),
            ),
        ),
        # ARChetype Disease CRF preset modal - test input when both the Covid and Dengue options
        # are selected, and the Dengue modal is opened and then closed.
        (
            [{"prop_id": "crf_metadata_modal_close.n_clicks", "value": 1}],
            [1, 0, 1, 0, 0, 0],
            1,
            [
                {"type": "template-info-btn", "index": "Covid"},
                {"type": "template-info-btn", "index": "H5Nx"},
                {"type": "template-info-btn", "index": "Dengue"},
                {"type": "template-info-btn", "index": "Chikungunya"},
                {"type": "template-info-btn", "index": "Mpox"},
                {"type": "template-info-btn", "index": "Mpox Pregnancy and Paediatric"},
            ],
            {"selected_version": "test_selected_version"},
            (False, dash.no_update, dash.no_update),
        ),
    ],
)
def test_display_crf_metadata_modal(
    trigger,
    info_btn_clicks: list,
    close_btn_clicks: int | list,
    info_btn_ids: list,
    selected_version_data: dict,
    expected_output: tuple,
):
    received_open_modal, received_template_name, received_div_output = (
        get_output_display_crf_metadata_modal(
            trigger,
            info_btn_clicks,
            close_btn_clicks,
            info_btn_ids,
            selected_version_data,
        )
    )
    expected_open_modal, expected_template_name, expected_div_output = expected_output

    assert received_open_modal == expected_open_modal
    assert received_template_name == expected_template_name
    assert str(received_div_output) == str(expected_div_output)


@pytest.mark.parametrize(
    "switch_values, switch_ids, grouped_presets, expected_styles",
    [
        # ARChetype Disease CRF presets - test input for Covid-only selection
        (
            [True, False, False, False, False, False, [], [], [], [], [], [], [], []],
            [
                {"type": "template_check", "index": "ARChetype Disease CRF_Covid"},
                {"type": "template_check", "index": "ARChetype Disease CRF_H5Nx"},
                {"type": "template_check", "index": "ARChetype Disease CRF_Dengue"},
                {
                    "type": "template_check",
                    "index": "ARChetype Disease CRF_Chikungunya",
                },
                {"type": "template_check", "index": "ARChetype Disease CRF_Mpox"},
                {
                    "type": "template_check",
                    "index": "ARChetype Disease CRF_Mpox Pregnancy and Paediatric",
                },
                {"type": "template_check", "index": "ARChetype Syndromic CRF_ARI"},
                {"type": "template_check", "index": "ARChetype Syndromic CRF_VHF"},
                {"type": "template_check", "index": "Score_CharlsonCI"},
                {"type": "template_check", "index": "Score_mSOFA"},
                {"type": "template_check", "index": "Score_mSOFA Dengue"},
                {"type": "template_check", "index": "Recommended Outcomes_Dengue"},
                {"type": "template_check", "index": "Populations_Paediatric"},
                {"type": "template_check", "index": "Populations_Pregnancy"},
            ],
            {
                "ARChetype Disease CRF": [
                    "Covid",
                    "H5Nx",
                    "Dengue",
                    "Chikungunya",
                    "Mpox",
                    "Mpox Pregnancy and Paediatric",
                ],
                "ARChetype Syndromic CRF": ["ARI", "VHF"],
                "Score": ["CharlsonCI", "mSOFA", "mSOFA Dengue"],
                "Recommended Outcomes": ["Dengue"],
                "Populations": ["Paediatric", "Pregnancy"],
            },
            [
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "block",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
            ],
        ),
        # ARChetype Disease CRF presets - test input for Covid and Dengue selections
        (
            [True, False, True, False, False, False, [], [], [], [], [], [], [], []],
            [
                {"type": "template_check", "index": "ARChetype Disease CRF_Covid"},
                {"type": "template_check", "index": "ARChetype Disease CRF_H5Nx"},
                {"type": "template_check", "index": "ARChetype Disease CRF_Dengue"},
                {
                    "type": "template_check",
                    "index": "ARChetype Disease CRF_Chikungunya",
                },
                {"type": "template_check", "index": "ARChetype Disease CRF_Mpox"},
                {
                    "type": "template_check",
                    "index": "ARChetype Disease CRF_Mpox Pregnancy and Paediatric",
                },
                {"type": "template_check", "index": "ARChetype Syndromic CRF_ARI"},
                {"type": "template_check", "index": "ARChetype Syndromic CRF_VHF"},
                {"type": "template_check", "index": "Score_CharlsonCI"},
                {"type": "template_check", "index": "Score_mSOFA"},
                {"type": "template_check", "index": "Score_mSOFA Dengue"},
                {"type": "template_check", "index": "Recommended Outcomes_Dengue"},
                {"type": "template_check", "index": "Populations_Paediatric"},
                {"type": "template_check", "index": "Populations_Pregnancy"},
            ],
            {
                "ARChetype Disease CRF": [
                    "Covid",
                    "H5Nx",
                    "Dengue",
                    "Chikungunya",
                    "Mpox",
                    "Mpox Pregnancy and Paediatric",
                ],
                "ARChetype Syndromic CRF": ["ARI", "VHF"],
                "Score": ["CharlsonCI", "mSOFA", "mSOFA Dengue"],
                "Recommended Outcomes": ["Dengue"],
                "Populations": ["Paediatric", "Pregnancy"],
            },
            [
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "block",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "block",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
                {
                    "background": "none",
                    "border": "none",
                    "cursor": "pointer",
                    "fontSize": "16px",
                    "padding": "0 8px",
                    "marginLeft": "auto",
                    "display": "none",
                },
            ],
        ),
    ],
)
def test_toggle_template_info_icon_visibility(
    switch_values: list,
    switch_ids: list,
    grouped_presets: dict,
    expected_styles: list[dict],
    arc_1_4_0__crf_metadata,
):
    received_styles = modals.toggle_template_info_icon_visibility(
        switch_values,
        switch_ids,
        grouped_presets,
        arc_1_4_0__crf_metadata.to_json(date_format="iso", orient="split"),
    )

    assert received_styles == expected_styles
