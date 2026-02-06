import pandas as pd

INCLUDE_NOT_SHOW = [
    "otherl3",
    "otherl2",
    "route",
    "route2",
    "agent",
    "agent2",
    "warn",
    "warn2",
    "warn3",
    "units",
    "add",
    "vol",
    "txt",
    "calc",
]


def _format_question_text(row):
    if row["Type"] == "user_list":
        return "↳ " + row["Question"]
    elif row["Type"] == "multi_list":
        return "⇉ " + row["Question"]
    return row["Question"]


def get_tree_items(df_datadicc: pd.DataFrame, version: str) -> dict:
    rows_for_tree = [
        "Form",
        "Sec_name",
        "vari",
        "mod",
        "Question",
        "Variable",
        "Type",
    ]

    # rows used for the tree (hide some mods)
    df_for_item = df_datadicc[rows_for_tree].loc[
        ~df_datadicc["mod"].isin(INCLUDE_NOT_SHOW)
    ]

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
            mask_units: pd.Series = df_variable["Question"].str.contains(
                "(select units)", case=False, na=False, regex=False
            )
            if mask_units.any():
                parent_row = df_variable.loc[mask_units].iloc[0]
                parent_title = _format_question_text(parent_row)
                parent_key = f"{parent_row['Variable']}"  # use the units variable as the parent key

                parent_node = {
                    "title": parent_title,
                    "key": parent_key,
                    "children": [],
                }
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
