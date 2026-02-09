import io
import re
from typing import Tuple

import dash
import pandas as pd
from dash import Input, Output, State

from bridge.arc import arc_core
from bridge.generate_pdf.form import Form
from bridge.logging.logger import setup_logger

logger = setup_logger(__name__)


@dash.callback(
    [
        Output("CRF_representation_grid", "rowData", allow_duplicate=True),
        Output("selected_data-store", "data"),
        Output("focused-cell-run-callback", "data", allow_duplicate=True),
        Output("focused-cell-index", "data"),
    ],
    [
        Input("input", "checked"),
    ],
    [
        State("current_datadicc-store", "data"),
        State("focused-cell-index", "data"),
        State("selected-version-store", "data"),
    ],
    prevent_initial_call=True,
)
def display_checked_in_grid(
    checked: list,
    current_datadicc_saved: str,
    focused_cell_index: int,
    selected_version_data: dict,
) -> Tuple[list, str, bool, int]:
    df_datadicc = pd.read_json(io.StringIO(current_datadicc_saved), orient="split")

    if checked:
        version = selected_version_data.get("selected_version", None)
        df_selected_variables = _create_selected_dataframe(
            df_datadicc, checked, version
        )
        new_row_list = _create_new_row_list(df_selected_variables)

        # Update selected variables with new rows including separators
        df_table_visualization = pd.DataFrame(new_row_list)
        df_table_visualization = df_table_visualization.loc[
            df_table_visualization["Type"] != "group"
        ]

        # Convert to dictionary for row_data_list
        row_data_list = df_table_visualization.to_dict(orient="records")
    else:
        df_selected_variables = pd.DataFrame()
        row_data_list = []

    focused_cell_index = _get_focused_cell_index(
        row_data_list, focused_cell_index, checked
    )

    focused_cell_run_callback = False
    if type(focused_cell_index) is int:
        focused_cell_run_callback = True

    return (
        row_data_list,
        df_selected_variables.to_json(date_format="iso", orient="split"),
        focused_cell_run_callback,
        focused_cell_index,
    )


def _create_selected_dataframe(
    df_datadicc: pd.DataFrame, checked: list, version: str
) -> pd.DataFrame:
    selected_dependency_lists = (
        df_datadicc["Dependencies"].loc[df_datadicc["Variable"].isin(checked)].tolist()
    )
    flat_selected_dependency = set()
    for sublist in selected_dependency_lists:
        flat_selected_dependency.update(sublist)
    all_selected = set(checked).union(flat_selected_dependency)
    df_selected_variables = df_datadicc.loc[df_datadicc["Variable"].isin(all_selected)]

    ## REDCAP Pipeline
    df_selected_variables = _get_include_not_show(
        df_selected_variables["Variable"], df_datadicc
    )

    # Select Units Transformation
    df_grid_units_display, unit_variables_to_delete = _units_transformation(
        df_selected_variables["Variable"], df_datadicc, version
    )

    if not df_grid_units_display.empty:
        df_selected_variables = arc_core.add_transformed_rows(
            df_selected_variables,
            df_grid_units_display,
            arc_core.get_variable_order(df_datadicc),
        )

        if len(unit_variables_to_delete) > 0:
            # This remove all the unit variables that were included in a select unit type question
            df_selected_variables = df_selected_variables.loc[
                ~df_selected_variables["Variable"].isin(unit_variables_to_delete)
            ]

    df_selected_variables = df_selected_variables.fillna("")
    df_selected_variables = df_selected_variables.reset_index(drop=True)
    return df_selected_variables


def _create_new_row_list(df_selected_variables: pd.DataFrame) -> list:
    last_form = None
    last_section = None
    new_row_list = []

    for _, row in df_selected_variables.iterrows():
        # Add form separator
        if row["Form"] != last_form:
            new_row_list.append(
                {
                    "Question": f"{row['Form'].upper()}",
                    "Answer Options": "",
                    "IsSeparator": True,
                    "SeparatorType": "form",
                }
            )
            last_form = str(row["Form"])

        # Add section separator
        if row["Section"] != last_section and row["Section"] != "":
            new_row_list.append(
                {
                    "Question": f"{row['Section'].upper()}",
                    "Answer Options": "",
                    "IsSeparator": True,
                    "SeparatorType": "section",
                }
            )
            last_section = str(row["Section"])

        if row["Type"] == "descriptive":
            new_row = row.to_dict()
            new_row["IsDescriptive"] = True

            new_row["Answer Options"] = ""
            new_row["IsSeparator"] = False
            new_row_list.append(new_row)
            continue

            # Process the actual row
        if row["Type"] in [
            "radio",
            "dropdown",
            "checkbox",
            "list",
            "user_list",
            "multi_list",
        ]:
            formatted_choices = Form().format_choices(
                row["Answer Options"], row["Type"]
            )
            row["Answer Options"] = formatted_choices

        elif row["Validation"] == "date_dmy":
            date_str = "[_D_][_D_]/[_M_][_M_]/[_2_][_0_][_Y_][_Y_]"
            row["Answer Options"] = date_str

        else:
            row["Answer Options"] = Form().line_placeholder

        # Add the processed row to new_row_list
        new_row = row.to_dict()
        new_row["IsSeparator"] = False
        new_row_list.append(new_row)
    return new_row_list


def _extract_parenthesis_content(text: str) -> str:
    match = re.search(r"\(([^)]+)\)$", text)
    return match.group(1) if match else text


def _get_include_not_show(
    selected_variables: pd.Series, df_current_datadicc: pd.DataFrame
) -> pd.DataFrame:
    include_not_show = [
        "otherl2",
        "otherl3",
        "agent",
        "agent2",
        "warn",
        "warn2",
        "warn3",
        "units",
        "add",
        "vol",
        "0item",
        "0otherl2",
        "0addi",
        "1item",
        "1otherl2",
        "1addi",
        "2item",
        "2otherl2",
        "2addi",
        "3item",
        "3otherl2",
        "3addi",
        "4item",
        "4otherl2",
        "4addi",
        "txt",
    ]

    # Get the include not show for the selected variables
    possible_vars_to_include = [
        f"{var}_{suffix}" for var in selected_variables for suffix in include_not_show
    ]
    actual_vars_to_include = [
        var
        for var in possible_vars_to_include
        if var in df_current_datadicc["Variable"].values
    ]
    selected_variables = list(selected_variables) + list(actual_vars_to_include)
    # Deduplicate the final list in case of any overlaps
    selected_variables = list(set(selected_variables))
    df_include_not_show = df_current_datadicc.loc[
        df_current_datadicc["Variable"].isin(selected_variables)
    ].reset_index(drop=True)
    return df_include_not_show


def _add_select_units_field(
    df_datadicc: pd.DataFrame, dynamic_units_conversion: bool
) -> pd.DataFrame:
    if not dynamic_units_conversion:
        # E.g. demog_height_units
        df_datadicc["select units"] = df_datadicc["Validation"] == "units"

        # E.g. Add demog_height_cm / demog_height_in
        for _, row in df_datadicc[df_datadicc["select units"]].iterrows():
            variable_key = f"{row['Variable']}"
            mask_sec_vari = (df_datadicc["Sec"] == row["Sec"]) & (
                df_datadicc["vari"] == row["vari"]
            )
            df_datadicc.loc[mask_sec_vari, "select units"] = True
            # Only show the original one (NOT suffixed "_units") in the grid
            # This maps to what is in the tree
            df_datadicc.loc[df_datadicc["Variable"] == variable_key, "select units"] = (
                False
            )

    else:
        # E.g. demog_height (demog_height_units doesn't exist)
        df_datadicc["select units"] = df_datadicc["Question_english"].str.contains(
            "(select units)", case=False, na=False, regex=False
        )
        # E.g. Add demog_height_cm / demog_height_in
        for _, row in df_datadicc[df_datadicc["select units"]].iterrows():
            mask_sec_vari = (df_datadicc["Sec"] == row["Sec"]) & (
                df_datadicc["vari"] == row["vari"]
            )
            df_datadicc.loc[mask_sec_vari, "select units"] = True

    return df_datadicc


def _get_units_language(
    df_datadicc: pd.DataFrame, dynamic_units_conversion: bool
) -> str:
    if not dynamic_units_conversion:
        df_units = df_datadicc.loc[df_datadicc["Validation"] == "units"]
    else:
        df_units = df_datadicc.loc[
            df_datadicc["Question_english"].str.contains("(select units)", regex=False)
        ]
    units_lang = df_units.sample(n=1)["Question"].iloc[0]
    units_lang = _extract_parenthesis_content(units_lang)
    return units_lang


def _create_units_dataframe(
    df_datadicc: pd.DataFrame,
    selected_variables: pd.Series,
) -> pd.DataFrame:
    df_units = df_datadicc.loc[
        df_datadicc["select units"]  # True
        & df_datadicc["Variable"].isin(selected_variables.values)
        & pd.notnull(df_datadicc["mod"])
    ]
    df_units["count"] = df_units.groupby(["Sec", "vari"]).transform("size")
    df_units = df_units.reset_index(drop=True)
    return df_units


def _units_transformation(
    selected_variables: pd.Series,
    df_datadicc: pd.DataFrame,
    version: str,
) -> tuple[pd.DataFrame, list]:
    dynamic_units_conversion = arc_core.get_dynamic_units_conversion_bool(version)
    df_datadicc = _add_select_units_field(df_datadicc, dynamic_units_conversion)
    units_lang = _get_units_language(df_datadicc, dynamic_units_conversion)

    df_units = _create_units_dataframe(df_datadicc, selected_variables)

    select_unit_rows_list = []
    unit_variables_to_delete = []
    seen_variables = set()

    for _, row in df_units.iterrows():
        if row["count"] > 1:
            matching_rows = df_units[
                (df_units["Sec"] == row["Sec"]) & (df_units["vari"] == row["vari"])
            ]

            for delete_variable in matching_rows["Variable"]:
                unit_variables_to_delete.append(delete_variable)

            max_value = pd.to_numeric(matching_rows["Maximum"], errors="coerce").max()
            min_value = pd.to_numeric(matching_rows["Minimum"], errors="coerce").min()

            options = " | ".join(
                [
                    f"{idx + 1},{_extract_parenthesis_content(str(r['Question']))}"
                    for idx, (_, r) in enumerate(matching_rows.iterrows())
                ]
            )

            row_value = row.copy()
            row_value["Variable"] = row["Sec"] + "_" + row["vari"]
            row_value["Answer Options"] = None
            row_value["Type"] = "text"
            row_value["Maximum"] = max_value
            row_value["Minimum"] = min_value
            row_value["Question"] = row["Question"].split("(")[0]
            row_value["Validation"] = "number"

            row_units = row.copy()
            row_units["Variable"] = row["Sec"] + "_" + row["vari"] + "_units"
            row_units["Answer Options"] = options
            row_units["Type"] = "radio"
            row_units["Maximum"] = None
            row_units["Minimum"] = None
            row_units["Question"] = (
                row["Question"].split("(")[0] + "(" + units_lang + ")"
            )
            row_units["Validation"] = None

            # Row values
            if row_value["Variable"] not in seen_variables:
                select_unit_rows_list.append(row_value)
                seen_variables.add(row_value["Variable"])

            # Row units
            if row_units["Variable"] not in seen_variables:
                select_unit_rows_list.append(row_units)
                seen_variables.add(row_units["Variable"])

    if len(select_unit_rows_list) > 0:
        df_units_selected_rows = pd.DataFrame(select_unit_rows_list).reset_index(
            drop=True
        )
        return (
            df_units_selected_rows,
            sorted(
                list(
                    set(unit_variables_to_delete)
                    - set(df_units_selected_rows["Variable"])
                )
            ),
        )
    return pd.DataFrame(), list()


def _get_focused_cell_index(
    row_data: list, focused_cell_index: int, checked: list
) -> int:
    if checked:
        df_row_data = pd.DataFrame(row_data)
        df_row_data["Question"] = df_row_data["Question"].str.split(":").str[0]

        # TODO: This is messy and unclear what it's doing
        try:
            if len(checked) > 1:
                latest_checked_variable = checked[-1]
                while (
                    latest_checked_variable.isupper()
                    or latest_checked_variable not in df_row_data["Variable"].values
                ) and len(checked) > 1:
                    checked.pop()
                    latest_checked_variable = checked[-1]
            else:
                latest_checked_variable = checked[0]
        except IndexError:
            latest_checked_variable = checked[0]

        df_row_data_variable = df_row_data[
            df_row_data["Variable"] == latest_checked_variable
        ]
        section_name = df_row_data_variable["Section"].values[0]
        df_row_data_section = df_row_data[df_row_data["Section"] == section_name]

        df_row_data_section = df_row_data_section[
            ~df_row_data_section["Variable"].str.contains("_otherl")
        ]

        uppercase_variable_list = []
        for item in checked:
            if item.isupper():
                uppercase_variable_list.append(item)

        type_list = df_row_data_section["Type"].values
        latest_type = type_list[-1]
        list_types = [
            variable_type
            for variable_type in type_list
            if variable_type in ["multi_list", "user_list"]
        ]
        if latest_type not in ["multi_list", "user_list"]:
            # Not a list => pick latest variable
            focused_cell_index = df_row_data_section.index.tolist()[-1]

        elif len(list_types) > 1 or latest_type in ["multi_list", "user_list"]:
            # Multiple lists checked => pick latest list
            df_lists = df_row_data_section[df_row_data_section["Type"].isin(list_types)]
            focused_cell_index = df_lists.index.tolist()[-1]

        elif len(df_row_data_section) == 1:
            # Section checked, then a variable in a different section => highlight the variable
            focused_cell_index = df_row_data_variable.index.tolist()[0]

        elif uppercase_variable_list:
            # One or more section headers have been checked
            if "ARC" in uppercase_variable_list:
                # Everything checked => pick first
                uppercase_variable_list.remove("ARC")
                section_header = uppercase_variable_list[0]
                section_question_list = [
                    question
                    for question in df_row_data["Question"].values
                    if question.isupper()
                ]
                if section_header not in section_question_list:
                    # Subsection, then all
                    section_header = uppercase_variable_list[1]

            else:
                first_header = uppercase_variable_list[0]
                section_list = [
                    item for item in uppercase_variable_list if "-" not in item
                ]

                if (
                    all(
                        [
                            item.startswith(first_header)
                            for item in uppercase_variable_list
                        ]
                    )
                    and section_list
                ):
                    # All sections checked => pick first
                    section_header = first_header

                elif section_list:
                    # No subsections checked => pick last selected section
                    section_header = section_list[-1]

                else:
                    # Multiple subsections checked => pick last one
                    section_subsection_list = [
                        item for item in uppercase_variable_list if "-" in item
                    ]
                    subsection_list = []

                    for item in section_subsection_list:
                        subsection_list = subsection_list + item.split("-")
                    section_header = subsection_list[-1]

                    section_question_list = [
                        question
                        for question in df_row_data["Question"].values
                        if question.isupper()
                    ]
                    if section_header not in section_question_list:
                        # Subsection contains a "-"
                        section_header = "-".join(
                            [subsection_list[-2], subsection_list[-1]]
                        )

            df_row_data_section_start = df_row_data[
                df_row_data["Question"] == section_header
            ]
            focused_cell_index = df_row_data_section_start.index.tolist()[0]

        else:
            # Single variable ticked
            # Group checked => pick last item in group
            focused_cell_index = df_row_data_variable.index.tolist()[0]

    return focused_cell_index
