import io
import json
from functools import lru_cache
from time import perf_counter
from typing import Tuple

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import dcc, html, Input, Output, State, ALL

from bridge.arc import arc_translations, arc_tree
from bridge.arc.arc_api import ArcApiClient, ArcApiClientError
from bridge.utils.crf import (
    clean_crf_metadata,
    get_crf_template_metadata_modal_content,
    CRFTemplateMetadataModalContent,
    NOT_AVAILABLE_TYPE,
)
from bridge.utils.logger import setup_logger
from bridge.utils.trigger_id import get_trigger_id


CHECKLIST_STYLE = {"padding": "20px", "maxHeight": "250px", "overflowY": "auto"}
LIST_GROUP_STYLE = {"maxHeight": "250px", "overflowY": "auto"}
HIDDEN_STYLE = {"display": "none"}
logger = setup_logger(__name__)


def _build_list_options_mapping(ulist_multilist: list) -> dict:
    options_mapping = {}
    for variable_name, variable_options in ulist_multilist:
        options_mapping[str(variable_name)] = tuple(
            (str(option[0]), str(option[1]), int(option[2]))
            for option in variable_options
        )
    return options_mapping


def _freeze_list_options_mapping(options_mapping: dict) -> tuple:
    return tuple(sorted(options_mapping.items()))


@lru_cache(maxsize=512)
def _build_checklist_dom_from_mapping_cached(
    frozen_options_mapping: tuple, selected_variable: str
) -> tuple:
    options_mapping = dict(frozen_options_mapping)
    selected_options = options_mapping.get(selected_variable)
    if selected_options is None:
        return (), ()

    options = []
    checked_items = []
    for option_code, option_name, is_selected in selected_options:
        option_value = f"{option_code}_{option_name}"
        options.append((f"{option_code}, {option_name}", option_value))
        if is_selected == 1:
            checked_items.append(option_value)

    return tuple(options), tuple(checked_items)


def build_checklist_dom_from_mapping(
    options_mapping: dict, selected_variable: str
) -> Tuple[list, list]:
    options_data, checked_items_data = _build_checklist_dom_from_mapping_cached(
        _freeze_list_options_mapping(options_mapping),
        selected_variable,
    )
    options = [{"label": label, "value": value} for label, value in options_data]
    checked_items = list(checked_items_data)
    return options, checked_items


# --- Utility functions for the CRF metadata modal callbacks ---
def _get_crf_metadata_modal_section(
    title: str, content: dash.html.Div | dash.html.P
) -> dash.html.Section:
    return html.Section(
        [
            html.H3(title, className="section-title"),
            content,
        ],
        className="section",
    )


def _get_crf_metadata_modal_metadata_grid(items: tuple[str, str]) -> dash.html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Span(label, className="metadata-label"),
                    html.Div(value, className="metadata-value"),
                ],
                className="metadata-item",
            )
            for label, value in items
        ],
        className="metadata-grid",
    )


def _get_crf_metadata_modal_scope_item(label: str, value: str) -> dash.html.Div:
    return html.Div(
        [
            html.Div(label, className="scope-label"),
            html.Div(value, className="scope-value"),
        ],
        className="scope-item",
    )


def _get_crf_metadata_modal_pathogen_value(
    pathogens: tuple[str] | NOT_AVAILABLE_TYPE,
) -> dash.html.Div:
    if pathogens == "Not available":
        pathogens = ["Not available"]

    return html.Div(
        [html.Span(pathogen, className="pathogen-chip") for pathogen in pathogens],
        className="pathogen-list",
    )


def _get_crf_metadata_modal_population_item(
    label: str, value: str, first: bool = False
) -> dash.html.Div:
    class_name = "population-item first" if first else "population-item"

    return html.Div(
        [
            html.Div(label, className="population-label"),
            html.Div(value, className="population-value"),
        ],
        className=class_name,
    )


def _get_crf_metadata_modal_author_name_with_superscripts(
    author_record: tuple[str, tuple[int]],
) -> dash.html.Span:
    author, affiliation_numbers = author_record

    children = [author]

    if affiliation_numbers:
        children.append(
            html.Sup(
                ",".join(str(number) for number in affiliation_numbers),
                className="author-sup",
            )
        )

    return html.Span(children)


def _get_crf_metadata_modal_authors_inline(
    authors: tuple[tuple[str, tuple[int]]] | NOT_AVAILABLE_TYPE,
) -> dash.html.Div:
    if authors == "Not available":
        return html.Div([dash.html.Span(["Not available"])], className="author-line")

    children = []

    for index, author_record in enumerate(authors):
        if index > 0:
            children.append(", ")
        children.append(
            _get_crf_metadata_modal_author_name_with_superscripts(author_record)
        )

    return html.Div(children, className="author-line")


def _get_crf_metadata_modal_approvers_inline(
    approvers: tuple[str] | NOT_AVAILABLE_TYPE,
) -> dash.html.Div:
    if approvers == "Not available":
        approvers = ["Not available"]

    return html.Div(
        ", ".join(approvers),
        className="approver-line",
    )


def _get_crf_metadata_modal_keywords(
    keywords: tuple[str] | NOT_AVAILABLE_TYPE,
) -> dash.html.Section:
    if keywords == "Not available":
        keywords = ["Not available"]

    return _get_crf_metadata_modal_section(
        "Keywords",
        html.Div(
            [html.Span(keyword, className="keyword") for keyword in keywords],
            className="keyword-container",
        ),
    )


def _get_crf_metadata_modal_resources(
    resources: tuple[str] | NOT_AVAILABLE_TYPE,
) -> dash.html.Section:
    if resources == "Not available":
        resources = ["Not available"]

    return _get_crf_metadata_modal_section(
        "Resources",
        html.Div(
            [
                html.A(
                    [
                        html.Div("↗", className="resource-icon"),
                        html.Div([html.Div(url, className="resource-url")]),
                    ],
                    href=url,
                    target="_blank",
                    className="resource-link",
                )
                for url in resources
            ],
            className="resource-list",
        ),
    )


def _build_crf_metadata_modal_tabbed_body(
    selected_version: str, template_id: str
) -> dash.html.Div:
    return html.Div(
        [
            "",
            dcc.Tabs(
                id="crf-metadata-modal-tabbed-body",
                value=f"{selected_version}|{template_id}|project-overview-tab",
                children=[
                    dcc.Tab(
                        label="Project Overview",
                        value=f"{selected_version}|{template_id}|project-overview-tab",
                    ),
                    dcc.Tab(
                        label="Scientific Scope",
                        value=f"{selected_version}|{template_id}|scientific-scope-tab",
                    ),
                    dcc.Tab(
                        label="Governance & Contributors",
                        value=f"{selected_version}|{template_id}|governance-and-contributors-tab",
                    ),
                    dcc.Tab(
                        label="Documentation & Discoverability",
                        value=f"{selected_version}|{template_id}|documentation-and-discoverability-tab",
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
        ],
    )


def _build_crf_metadata_modal_project_overview_tab(
    modal_content: CRFTemplateMetadataModalContent,
) -> dash.html.Div:
    overview = modal_content.overview_section
    scientific_scope = modal_content.scientific_scope_section

    return html.Div(
        [
            _get_crf_metadata_modal_section(
                "Description",
                html.P(
                    overview.description,
                    className="section-text",
                ),
            ),
            _get_crf_metadata_modal_section(
                "CRF metadata",
                _get_crf_metadata_modal_metadata_grid(overview.metadata),
            ),
            _get_crf_metadata_modal_section(
                "Study population",
                html.Div(
                    [
                        _get_crf_metadata_modal_population_item(
                            "Target population",
                            scientific_scope.target_population,
                            first=True,
                        ),
                        _get_crf_metadata_modal_population_item(
                            "Inclusion criteria",
                            scientific_scope.inclusion_criteria,
                        ),
                        _get_crf_metadata_modal_population_item(
                            "Exclusion criteria",
                            scientific_scope.exclusion_criteria,
                        ),
                    ]
                ),
            ),
        ]
    )


def _build_crf_metadata_modal_scientific_scope_tab(
    modal_content: CRFTemplateMetadataModalContent,
) -> dash.html.Div:
    scientific_scope = modal_content.scientific_scope_section

    questions = html.Ol(
        [html.Li(q) for q in scientific_scope.research_questions],
        className="research-list",
    )

    clinical_context = html.Div(
        [
            _get_crf_metadata_modal_scope_item("Syndrome", scientific_scope.syndrome),
            _get_crf_metadata_modal_scope_item(
                "Pathogen / agent",
                _get_crf_metadata_modal_pathogen_value(scientific_scope.pathogens),
            ),
            _get_crf_metadata_modal_scope_item("Setting", scientific_scope.setting),
            _get_crf_metadata_modal_scope_item(
                "Geographic scope", scientific_scope.geographic_scope
            ),
        ],
        className="scope-grid",
    )

    syndrome_definition = None
    if hasattr(scientific_scope, "syndrome_definition"):
        syndrome_definition = html.Div(
            [
                html.Span(
                    "Syndrome definition",
                    className="definition-label",
                ),
                scientific_scope.syndrome_definition,
            ],
            className="definition-block",
        )

    return html.Div(
        [
            _get_crf_metadata_modal_section(
                "Clinical context",
                html.Div(
                    [
                        clinical_context,
                        syndrome_definition,
                    ]
                ),
            ),
            _get_crf_metadata_modal_section("Research questions", questions),
        ]
    )


def _build_crf_metadata_modal_governance_and_contributors_tab(
    modal_content: CRFTemplateMetadataModalContent,
) -> dash.html.Div:
    governance = modal_content.governance_section

    authors = governance.authors
    approvers = governance.approvers
    affiliations = governance.affiliations
    contact_name, contact_email = governance.contact

    affiliation_nodes = []
    for number, institution in enumerate(affiliations, start=1):
        affiliation_nodes.append(
            html.Div(
                [
                    html.Sup(str(number), className="affiliation-number"),
                    html.Span(institution),
                ],
                className="affiliation-item",
            )
        )

    return html.Div(
        [
            _get_crf_metadata_modal_section(
                "Contributors",
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("Authors", className="paper-subtitle"),
                                html.Div(
                                    f"{len(authors)} people",
                                    className="paper-count",
                                ),
                                _get_crf_metadata_modal_authors_inline(authors),
                            ],
                            className="paper-subsection",
                        ),
                        html.Div(
                            [
                                html.H4("Approvers", className="paper-subtitle"),
                                html.Div(
                                    f"{len(approvers)} people",
                                    className="paper-count",
                                ),
                                _get_crf_metadata_modal_approvers_inline(approvers),
                            ],
                            className="paper-subsection",
                        ),
                    ],
                    className="paper-columns",
                ),
            ),
            _get_crf_metadata_modal_section(
                "Affiliations",
                html.Div(
                    [
                        html.Div(
                            f"{len(affiliations)} affiliations",
                            className="paper-count",
                        ),
                        html.Div(
                            affiliation_nodes,
                            className="affiliation-list",
                        ),
                    ]
                ),
            ),
            html.Div(className="governance-divider"),
            _get_crf_metadata_modal_section(
                "Correspondence",
                html.Div(
                    [
                        html.Span(
                            contact_name,
                            style={"fontWeight": "600"},
                        ),
                        " - ",
                        html.A(
                            contact_email,
                            href=f"mailto:{contact_email}",
                            className="correspondence-email",
                        ),
                    ],
                    className="correspondence",
                ),
            ),
        ]
    )


def _build_crf_metadata_modal_documentation_and_discoverability_tab(
    modal_content: CRFTemplateMetadataModalContent,
) -> dash.html.Div:
    documentation = modal_content.documentation_section

    return html.Div(
        [
            _get_crf_metadata_modal_keywords(documentation.keywords),
            _get_crf_metadata_modal_resources(documentation.resources),
        ]
    )


def _create_placeholder_template_metadata(template_id: str) -> pd.Series:
    placeholder_columns = [
        "Title of CRF",
        "Description",
        "Study type",
        "Version",
        "Date of publication/release",
        "Research questions",
        "Target population",
        "Inclusion Criteria",
        "Exclusion Criteria",
        "Pathogen or agent",
        "Syndrome / clinical presentation",
        "Setting",
        "Geographic scope",
        "Authors",
        "Approvers",
        "Institutions",
        "Contact First Name",
        "Contact Last Name",
        "Contact email",
        "Keywords",
        "Relevant resources",
        "Related documents, protocols, repositories, websites, publication",
    ]
    rowfill = dict(
        zip(
            placeholder_columns,
            ["Not available"] * len(placeholder_columns),
        )
    )
    rowfill["Title of CRF"] = template_id

    return pd.DataFrame(rowfill, index=range(1)).iloc[0]


def _build_crf_metadata_modal_tab_content(
    selected_version: str, template_id: str, tab_id: str
) -> dash.html.Div:
    try:
        arc_crf_metadata = ArcApiClient().get_dataframe_crf_metadata(selected_version)
    except ArcApiClientError:
        template_metadata = _create_placeholder_template_metadata(template_id)
    else:
        arc_crf_metadata = clean_crf_metadata(arc_crf_metadata)
        try:
            template_metadata = arc_crf_metadata[
                arc_crf_metadata["Title of CRF"] == template_id
            ].iloc[0]
        except IndexError:
            template_metadata = _create_placeholder_template_metadata(template_id)

    modal_content = get_crf_template_metadata_modal_content(template_metadata)

    match tab_id:
        case "project-overview-tab":
            return _build_crf_metadata_modal_project_overview_tab(modal_content)
        case "scientific-scope-tab":
            return _build_crf_metadata_modal_scientific_scope_tab(modal_content)
        case "governance-and-contributors-tab":
            return _build_crf_metadata_modal_governance_and_contributors_tab(
                modal_content
            )
        case "documentation-and-discoverability-tab":
            return _build_crf_metadata_modal_documentation_and_discoverability_tab(
                modal_content
            )
        case _:
            return html.Div()


@lru_cache(maxsize=512)
def _split_answer_options(answer_options: str) -> tuple:
    return tuple(answer_options.split("|"))


@dash.callback(
    [
        Output("modal", "is_open"),
        Output("modal_title", "children"),
        Output("definition-text", "children"),
        Output("completion-guide-text", "children"),
        Output("skip-logic-text", "children"),
        Output("options-checklist", "style"),
        Output("options-list-group", "style"),
        Output("options-checklist", "options"),
        Output("options-checklist", "value"),
        Output("options-list-group", "children"),
    ],
    [
        Input("input", "selected"),
    ],
    [
        State("ulist_variable_choices-store", "data"),
        State("multilist_variable_choices-store", "data"),
        State("current_datadicc-store", "data"),
    ],
)
def display_selected_in_modal(
    selected: list,
    ulist_variable_choices_saved: str,
    multilist_variable_choices_saved: str,
    current_datadicc_saved: str,
) -> Tuple[bool, str, str, str, str, dict, dict, list, list, list]:
    if selected:
        ulist = json.loads(ulist_variable_choices_saved)
        multilist = json.loads(multilist_variable_choices_saved)
        ulist_multilist = ulist + multilist
        list_options_mapping = _build_list_options_mapping(ulist_multilist)
        df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient="split")
        selected_variable = selected[0]
        if selected_variable in list(df_datadicc["Variable"]):
            process_start = perf_counter()
            question = (
                df_datadicc["Question"]
                .loc[df_datadicc["Variable"] == selected[0]]
                .iloc[0]
            )
            definition = (
                df_datadicc["Definition"]
                .loc[df_datadicc["Variable"] == selected[0]]
                .iloc[0]
            )
            completion = (
                df_datadicc["Completion Guideline"]
                .loc[df_datadicc["Variable"] == selected[0]]
                .iloc[0]
            )
            skip_logic = (
                df_datadicc["Branch"]
                .loc[df_datadicc["Variable"] == selected[0]]
                .iloc[0]
            )

            if selected_variable in list_options_mapping:
                options, checked_items = build_checklist_dom_from_mapping(
                    list_options_mapping, selected_variable
                )
                logger.debug(
                    "modals.display_selected_in_modal checklist variable=%s options=%s elapsed_ms=%.3f",
                    selected_variable,
                    len(options),
                    (perf_counter() - process_start) * 1000,
                )
                return (
                    True,
                    question + " [" + selected_variable + "]",
                    definition,
                    completion,
                    skip_logic,
                    CHECKLIST_STYLE,
                    HIDDEN_STYLE,
                    options,
                    checked_items,
                    [],
                )
            else:
                options = []
                answer_options = (
                    df_datadicc["Answer Options"]
                    .loc[df_datadicc["Variable"] == selected_variable]
                    .iloc[0]
                )
                if isinstance(answer_options, str):
                    for ulist_multilist_variable in _split_answer_options(
                        answer_options
                    ):
                        options.append(dbc.ListGroupItem(ulist_multilist_variable))
                else:
                    options = []
                logger.debug(
                    "modals.display_selected_in_modal static_options variable=%s items=%s elapsed_ms=%.3f",
                    selected_variable,
                    len(options),
                    (perf_counter() - process_start) * 1000,
                )
                return (
                    True,
                    question + " [" + selected_variable + "]",
                    definition,
                    completion,
                    skip_logic,
                    HIDDEN_STYLE,
                    LIST_GROUP_STYLE,
                    [],
                    [],
                    options,
                )

    return False, "", "", "", "", HIDDEN_STYLE, HIDDEN_STYLE, [], [], []


@dash.callback(
    [
        Output("modal", "is_open", allow_duplicate=True),
        Output("current_datadicc-store", "data"),
        Output("ulist_variable_choices-store", "data"),
        Output("multilist_variable_choices-store", "data"),
        Output("tree_items_container", "children", allow_duplicate=True),
    ],
    [
        Input("modal_submit", "n_clicks"),
        Input("modal_cancel", "n_clicks"),
    ],
    [
        State("current_datadicc-store", "data"),
        State("modal_title", "children"),
        State("options-checklist", "value"),
        State("input", "checked"),
        State("ulist_variable_choices-store", "data"),
        State("multilist_variable_choices-store", "data"),
        State("selected-version-store", "data"),
        State("selected-language-store", "data"),
        State("dynamic-units-conversion", "data"),
    ],
    prevent_initial_call=True,
)
def on_modal_button_click(
    _submit_n_clicks: int,
    _cancel_n_clicks: int,
    current_datadicc_saved: str,
    modal_title: str,
    modal_options_checked: list,
    checked: list,
    ulist_variable_choices_saved: str,
    multilist_variable_choices_saved: str,
    selected_version_data: dict,
    selected_language_data: dict,
    dynamic_units_conversion: bool,
):
    ctx = dash.callback_context

    if not ctx.triggered:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    trigger_id = get_trigger_id(ctx)

    if trigger_id == "modal_submit":
        df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient="split")
        selected_version = selected_version_data.get("selected_version")
        selected_language = selected_language_data.get("selected_language")
        translations_for_language = arc_translations.get_translations(selected_language)
        other_text = translations_for_language["other"]

        variable_selected = modal_title.split("[")[1][:-1]

        ulist_variable_choices_saved_list = json.loads(ulist_variable_choices_saved)
        multilist_variable_choices_saved_list = json.loads(
            multilist_variable_choices_saved
        )

        ulist_variables = [i[0] for i in ulist_variable_choices_saved_list]
        multilist_variables = [i[0] for i in multilist_variable_choices_saved_list]

        if (variable_selected in ulist_variables) | (
            variable_selected in multilist_variables
        ):
            list_options_checked = []
            for checked_option in modal_options_checked:
                list_options_checked.append(checked_option.split("_"))

            list_options_checked = pd.DataFrame(
                data=list_options_checked, columns=["cod", "Option"]
            )

            df_datadicc, ulist_variable_choices = update_list_variables_checked(
                ulist_variable_choices_saved_list,
                variable_selected,
                list_options_checked,
                df_datadicc,
                other_text,
            )

            df_datadicc, multilist_variable_choices = update_list_variables_checked(
                multilist_variable_choices_saved_list,
                variable_selected,
                list_options_checked,
                df_datadicc,
                other_text,
            )

            checked.append(variable_selected)

            tree_items_data = arc_tree.get_tree_items(
                df_datadicc, selected_version, dynamic_units_conversion
            )

            tree_items = html.Div(
                dash_treeview_antd.TreeView(
                    id="input",
                    multiple=False,
                    checkable=True,
                    checked=df_datadicc["Variable"].loc[
                        df_datadicc["Variable"].isin(checked)
                    ],
                    expanded=df_datadicc["Variable"].loc[
                        df_datadicc["Variable"].isin(checked)
                    ],
                    data=tree_items_data,
                ),
                id="tree_items_container",
                className="tree-item",
            )
            return (
                False,
                df_datadicc.to_json(date_format="iso", orient="split"),
                ulist_variable_choices,
                multilist_variable_choices,
                tree_items,
            )
        else:
            return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    elif trigger_id == "modal_cancel":
        # Just close the modal without doing anything else
        return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


def update_list_variables_checked(
    variable_choices_list: list,
    variable_name: str,
    df_checked: pd.DataFrame,
    df_current_datadicc: pd.DataFrame,
    other_text: str,
) -> Tuple[pd.DataFrame, str]:
    variable_name_not_selected = f"{variable_name}_otherl2"
    list_options = []
    variable_list_options = []

    position = 0
    for var_select in variable_choices_list:
        if var_select[0] == variable_name:
            select_answer_options = ""
            not_select_answer_options = ""

            for option_var_select in var_select[1]:
                list_item_number = option_var_select[0]
                list_item_name = option_var_select[1]
                if list_item_name in (list(df_checked["Option"])):
                    list_options.append([list_item_number, list_item_name, 1])
                    select_answer_options += (
                        str(list_item_number) + ", " + str(list_item_name) + " | "
                    )
                else:
                    list_options.append([list_item_number, list_item_name, 0])
                    not_select_answer_options += (
                        str(list_item_number) + ", " + str(list_item_name) + " | "
                    )

            variable_list_options.append([var_select, list_options])
            variable_choices_list[position][1] = variable_list_options[0][1]

            df_current_datadicc.loc[
                df_current_datadicc["Variable"] == variable_name, "Answer Options"
            ] = select_answer_options + "88, " + other_text

            if variable_name_not_selected in list(df_current_datadicc["Variable"]):
                df_current_datadicc.loc[
                    df_current_datadicc["Variable"] == variable_name_not_selected,
                    "Answer Options",
                ] = not_select_answer_options + "88, " + other_text

        position += 1
    return (
        df_current_datadicc,
        json.dumps(variable_choices_list),
    )


@dash.callback(
    Output({"type": "template-info-btn", "index": ALL}, "style"),
    Input({"type": "template_check", "index": ALL}, "value"),
    [
        State({"type": "template_check", "index": ALL}, "id"),
        State("grouped_presets-store", "data"),
        State("arc-crf-metadata", "data"),
    ],
    prevent_initial_call=True,
)
def toggle_template_info_icon_visibility(
    switch_values: list,
    switch_ids: list,
    grouped_presets: dict,
    arc_crf_metadata_json: str,
) -> list:
    """:py:class:`list` : Returns a list of styling dicts for the CRF preset/template information icons.

    These styling dicts are of the form:
    ::

        {
            "background": "none",
            "border": "none",
            "cursor": "pointer",
            "fontSize": "16px",
            "padding": "0 8px",
            "marginLeft": "auto",
            "display": "block" if status else "none",
        }

    A ``"display"`` value of ``"block"`` for a template corresponds to the
    information icon being visible for that template, while a display value of
    ``"none"`` hides the icon.

    Parameters
    ----------
    switch_values : list
        A list of boolean indicators of the toggle status of the CRF
        presets/templates, one for each template.

    switch_ids : list
        A list of IDs for the CRF presets/templates, eacn ID a dict in
        the form:
        ::

            {
                "type": "template_check",
                "index": "<section name>_<template name>"}
            }

    grouped_presets : dict
        A dict of CRF presets/templates keyed by section name.

    arc_crf_metadata_json : str
        The raw JSON of the CRF metadata CSV obtained (via the ARC API client)
        from an ARC release matching the currently selected version.

    Returns
    -------
    list
        The list of styling dicts for the CRF presets/templates.

    """
    # Load the CRF metadata CSV from the raw JSON, and extract the list of
    # sections implicitly defined in the rows of the CSV
    arc_crf_metadata = pd.read_json(io.StringIO(arc_crf_metadata_json), orient="split")
    info_icon_template_ids = arc_crf_metadata["Title of CRF"].tolist()

    # For each combination of switch ID and value, determine the visibility
    # of the corresponding template, and build a map/dict keyed by section and
    # whose values are template names.
    template_status = {}

    for switch_id, is_on in zip(switch_ids, switch_values):
        template_id = (
            switch_id.get("index", "")
            if isinstance(switch_id, dict)
            else str(switch_id)
        )
        section, template_name = template_id.split("_")
        if template_id in info_icon_template_ids:
            template_status[(section, template_name)] = is_on
        else:
            template_status[(section, template_name)] = False

    # Using the map above, return a list of styles, one for each template.
    return [
        {
            "background": "none",
            "border": "none",
            "cursor": "pointer",
            "fontSize": "16px",
            "padding": "0 8px",
            "marginLeft": "auto",
            "display": "block" if status else "none",
        }
        for (section, template_name), status in template_status.items()
    ]


@dash.callback(
    [
        Output("crf_metadata_modal", "is_open"),
        Output("crf_metadata_modal_title", "children"),
        Output("crf_metadata_modal_body", "children"),
    ],
    [
        Input({"type": "template-info-btn", "index": ALL}, "n_clicks"),
        Input("crf_metadata_modal_close", "n_clicks"),
    ],
    [
        State({"type": "template-info-btn", "index": ALL}, "id"),
        State("selected-version-store", "data"),
    ],
    prevent_initial_call=True,
)
def display_crf_metadata_modal(
    info_btn_clicks: list[bool],
    close_btn_clicks: bool,
    info_btn_ids: list,
    selected_version_data: dict,
) -> tuple:
    """:py:class:`tuple` : Callback for the display of the CRF metadata modal.

    Parameters
    ----------
    info_btn_clicks : list
        A list of boolean (given as ``0``/``1``) indicators of click status
        for the CRF presets/templates, with ``0`` representing no-click and
        ``1`` representing a click.

    close_btn_clicks : bool
        A bool (given as ``0``/``1``) indicating whether the modal Close button
        was clicked, with ``0`` representing no-click and ``1`` representing
        a click.

    info_btn_ids : list
        A list of IDs for the CRF preset/template icons as dicts in the form:
        ::

            {
                "type": "template-info-btn",
                "index": <template name>
            }

    selected_version_data : dict
        A dict indicating the currently selected version in the form:
        ::

            {
                "selected_version": "<version string>"
            }

    Returns
    -------
    tuple
        A tuple consisting of display indicator (bool), template ID or a
        Dash update indicator, and the CRF metadata body div or Dash
        update indicator.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, "", ""

    trigger_id = ctx.triggered[0]["prop_id"]
    trigger_value = ctx.triggered[0]["value"]

    # Handle close button
    if "crf_metadata_modal_close" in trigger_id:
        return False, dash.no_update, dash.no_update

    # Handle info icon click - only proceed if n_clicks > 0
    if "template-info-btn" in trigger_id and trigger_value and trigger_value > 0:
        # Extract template name from the button ID
        button_info = json.loads(trigger_id.split(".")[0])
        template_id = button_info.get("index", "Unknown")
        selected_version = selected_version_data.get("selected_version")
        # The tabbed CRF template metadata div
        crf_metadata_body = _build_crf_metadata_modal_tabbed_body(
            selected_version, template_id
        )

        return (
            True,  # Open modal
            " | ".join(template_id.split("_")),  # "<section name> | <template name>
            crf_metadata_body,  # Body
        )

    return False, dash.no_update, dash.no_update


@dash.callback(
    Output("crf-metadata-modal-body-tab-content", "children"),
    Input("crf-metadata-modal-tabbed-body", "value"),
)
def display_crf_metadata_modal_body_selected_tab(value_str: str) -> dash.html.Div:
    """:py:class:`str` : Callback for the display of the currently selected tab in the CRF metadata modal.

    Parameters
    ----------
    value_str
        A value string in the form:
        ::

            <selected_version>|<template_id>|<tab ID>

        For example:
        ::

            v1.4.0|ARChetype Disease CRF_Dengue|project-overview-tab

    Returns
    -------
    dash.html.Div
        The CRF metadata modal selected tab div, with content dynamically
        determined by the selection version, template ID and tab ID.
    """
    values = value_str.split("|")
    if len(values) == 1:
        selected_version = values[0]
        template_id = tab_id = ""
    else:
        selected_version, template_id, tab_id = values
    logger.info(f'Tab display for "{template_id}" (version "{selected_version}")')

    return _build_crf_metadata_modal_tab_content(selected_version, template_id, tab_id)
