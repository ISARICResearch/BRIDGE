import io
import json
from functools import lru_cache
from time import perf_counter
from typing import Tuple

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import html, Input, Output, State

from bridge.arc import arc_translations, arc_tree
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
