import pandas as pd
from packaging.version import parse

from bridge.arc.arc_core import ARC_UNIT_CHANGE_VERSION


def _format_question_text(row):
    if row["Type"] == "user_list":
        return "↳ " + row["Question"]
    elif row["Type"] == "multi_list":
        return "⇉ " + row["Question"]
    return row["Question"]


def get_tree_items(df_datadicc: pd.DataFrame, version: str) -> dict:
    if parse(version.replace("v", "")) < parse(ARC_UNIT_CHANGE_VERSION.replace("v", "")):
        # Uses "Question" contains "(select units)"
        select_units_conversion = True
    else:
        # Uses "Validation" == "units"
        select_units_conversion = False

    include_not_show = [
        "otherl3",
        "otherl2",
        "route",
        "route2",
        "agent",
        "agent2",
        "warn",
        "warn2",
        "warn3",
        "add",
        "vol",
        "txt",
        "calc",
    ]

    # rows used for the tree (hide some mods)
    df_for_item = df_datadicc[
        ["Form", "Sec_name", "vari", "mod", "Question", "Variable", "Type", "Validation", "Answer Options"]
    ].loc[~df_datadicc["mod"].isin(include_not_show)]

    # -------- counts per (Form, Sec_name, vari) --------
    base_for_counts = df_for_item[["Form", "Sec_name", "vari"]].copy()
    group_counts_total = (
        base_for_counts.groupby(["Form", "Sec_name", "vari"], dropna=False)
        .size()
        .rename("n_in_vari_total")
        .reset_index()
    )
    # ---------------------------------------------------

    # prep indexing and "first question"
    df_for_item = df_for_item[df_for_item["Sec_name"].notna()].copy()
    df_for_item["_row_order"] = range(len(df_for_item))
    df_idx_first = (
        df_for_item.sort_values("_row_order")
        .groupby(["Form", "Sec_name", "vari"], dropna=False, as_index=False)
        .nth(0)[["Form", "Sec_name", "vari", "Question", "Variable"]]
        .rename(columns={"Question": "first_question", "Variable": "first_variable"})
        .reset_index(drop=True)
    )

    # merge counts + first-question
    df_for_item = df_for_item.merge(
        group_counts_total, on=["Form", "Sec_name", "vari"], how="left"
    ).merge(df_idx_first, on=["Form", "Sec_name", "vari"], how="left")

    tree = {"title": version.replace("ICC", "ARC"), "key": "ARC", "children": []}
    seen_forms, seen_sections = set(), {}

    # Build tree
    for (form, sec_name), df_sec in df_for_item.groupby(
            ["Form", "Sec_name"], dropna=False, sort=False
    ):
        form_upper = str(form).upper()
        sec_name_upper = str(sec_name).upper()

        # form
        if form_upper not in seen_forms:
            tree["children"].append(
                {
                    "title": form_upper,
                    "key": form_upper,
                    "children": [],
                }
            )
            seen_forms.add(form_upper)
            seen_sections[form_upper] = set()
        # section
        if sec_name_upper not in seen_sections[form_upper]:
            for child in tree["children"]:
                if child["title"] == form_upper:
                    child["children"].append(
                        {
                            "title": sec_name_upper,
                            "key": f"{form_upper}-{sec_name_upper}",
                            "children": [],
                        }
                    )
                    break
            seen_sections[form_upper].add(sec_name_upper)

        # find section node
        section_node = None
        for child in tree["children"]:
            if child["title"] == form_upper:
                for sec_child in child["children"]:
                    if sec_child["title"] == sec_name_upper:
                        section_node = sec_child
                        break

        df_sec = df_sec.sort_values("_row_order")
        for vari, df_variable in df_sec.groupby("vari", dropna=False, sort=False):
            # SPECIAL CASE: when a "(select units)" question exists in this vari,
            # make THAT row the parent, and attach all other rows (same vari) as children.
            if not select_units_conversion:
                unit_mask = df_variable["Validation"] == "units"
                df_units: pd.DataFrame = df_variable[unit_mask]
                if not df_units.empty:
                    parent_row = df_units.iloc[0]
                    parent_title = _format_question_text(parent_row)
                    parent_key = f"{parent_row['Variable']}"  # use the units variable as the parent key
                    old_parent_key = parent_key.replace("_units", "")

                    parent_node = {"title": parent_title, "key": parent_key, "children": []}
                    section_node["children"].append(parent_node)

                    # add children excluding the units row
                    df_children = df_variable[(~unit_mask) & (df_variable["Variable"] != old_parent_key)]
                    for _, row in df_children.iterrows():
                        parent_node["children"].append(
                            {
                                "title": _format_question_text(row),
                                "key": f"{row['Variable']}",
                            }
                        )
                    continue  # this vari handled

            else:
                mask_units: pd.Series = df_variable["Question"].str.contains(
                    "(select units)", case=False, na=False, regex=False
                )
                if mask_units.any():
                    parent_row = df_variable.loc[mask_units].iloc[0]
                    parent_title = _format_question_text(parent_row)
                    parent_key = f"{parent_row['Variable']}"  # use the units variable as the parent key

                    parent_node = {"title": parent_title, "key": parent_key, "children": []}
                    section_node["children"].append(parent_node)

                    # add children excluding the units row
                    for _, variable_series in df_variable.loc[~mask_units].iterrows():
                        parent_node["children"].append(
                            {
                                "title": _format_question_text(variable_series),
                                "key": f"{variable_series['Variable']}",
                            }
                        )
                    continue  # this vari handled

            # Fallback: your normal grouping (>=3 => group; else flat)
            n_total = int(
                df_variable["n_in_vari_total"].iloc[0]
                if pd.notna(df_variable["n_in_vari_total"].iloc[0])
                else 0
            )

            if n_total >= 3:
                parent_title = df_variable["first_question"].iloc[0]
                parent_key = f"{form_upper}-{sec_name_upper}-VARI-{vari}-GROUP"
                parent_node = {
                    "title": parent_title + " (Group)",
                    "key": parent_key,
                    "children": [],
                }
                section_node["children"].append(parent_node)

                for _, variable_series in df_variable.iterrows():
                    parent_node["children"].append(
                        {
                            "title": _format_question_text(variable_series),
                            "key": f"{variable_series['Variable']}",
                        }
                    )
            else:
                for _, variable_series in df_variable.iterrows():
                    section_node["children"].append(
                        {
                            "title": _format_question_text(variable_series),
                            "key": f"{variable_series['Variable']}",
                        }
                    )

    return tree
