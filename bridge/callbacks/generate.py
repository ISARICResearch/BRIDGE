import io
import json
import zipfile
from datetime import datetime
from os.path import join, dirname, abspath

import dash
import numpy as np
import pandas as pd
from dash import dcc, Input, Output, State
from unidecode import unidecode

from bridge.generate_pdf import paper_crf, paper_word
from bridge.utils.crf_name import get_crf_name
from bridge.utils.trigger_id import get_trigger_id

pd.options.mode.copy_on_write = True

CONFIG_DIR = join(
    dirname(dirname(dirname(abspath(__file__)))), "assets", "config_files"
)
XML_FILE_NAME = "ISARIC Clinical Characterisation Setup"


@dash.callback(
    [
        Output("loading-output-generate", "children"),
        Output("download-dataframe-csv", "data"),
        Output("download-compGuide-pdf", "data"),
        Output("download-projectxml-pdf", "data"),
        Output("download-paperlike-pdf", "data"),
        Output("download-paperlike-docx", "data"),
    ],
    [
        Input("crf_generate", "n_clicks"),
    ],
    [
        State("selected_data-store", "data"),
        State("selected-version-store", "data"),
        State("selected-language-store", "data"),
        State({"type": "template_check", "index": dash.ALL}, "value"),
        State("crf_name", "value"),
        State("output-files-store", "data"),
        State("browser-info-store", "data"),
    ],
    prevent_initial_call=True,
)
def on_generate_click(
    n_clicks: int,
    json_data: str,
    selected_version_data: dict,
    selected_language_data: dict,
    checked_presets: list,
    crf_name: str,
    output_files: list,
    browser_info: str,
):
    ctx = dash.callback_context

    if not n_clicks:
        # Return empty or initial state if button hasn't been clicked
        return (
            "",
            None,
            None,
            None,
            None,
            None,
        )

    if not any(json.loads(json_data).values()):
        # Nothing ticked
        return (
            "",
            None,
            None,
            None,
            None,
            None,
        )

    trigger_id = get_trigger_id(ctx)

    if trigger_id == "crf_generate":
        date = datetime.today().strftime("%Y-%m-%d")
        crf_name = get_crf_name(crf_name, checked_presets)

        selected_variables_from_data = pd.read_json(
            io.StringIO(json_data), orient="split"
        )
        version = selected_version_data.get("selected_version")
        language = selected_language_data.get("selected_language")

        df_crf = _generate_crf(selected_variables_from_data)
        # PDFs
        pdf_paperlike_crf = paper_crf.generate_paperlike_pdf(
            df_crf, version, crf_name, language
        )
        pdf_completion_guide = paper_crf.generate_completion_guide(
            selected_variables_from_data, version, crf_name
        )

        # WORD
        word_bytes = paper_word.df_to_word(df_crf)

        # CSV
        csv_data_dict_buffer = io.BytesIO()
        df_crf.loc[df_crf["Field Type"] == "descriptive", "Field Label"] = df_crf.loc[
            df_crf["Field Type"] == "descriptive", "Field Label"
        ].apply(
            lambda x: f'<div class="rich-text-field-label"><h5 style="text-align: center;"><span style="color: #236fa1;">{x}</span></h5></div>'
        )
        if language != "English":
            df_crf["Form Name"] = df_crf["Form Name"].apply(lambda x: unidecode(str(x)))
        df_crf.to_csv(csv_data_dict_buffer, index=False, encoding="utf8")
        csv_data_dict_buffer.seek(0)

        # XML
        xml_file_name = f"{XML_FILE_NAME}_{language}.xml"
        xml_file_path = f"{CONFIG_DIR}/{xml_file_name}"
        with open(xml_file_path, "rb") as file:
            xml_content = file.read()

        is_safari = (
            browser_info and "Safari" in browser_info and "Chrome" not in browser_info
        )

        include_csv = "redcap_csv" in output_files
        include_pdf_paper = "paper_like" in output_files
        include_xml = "redcap_xml" in output_files
        include_word = "paper_word" in output_files

        if is_safari:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                if include_csv:
                    zip_file.writestr(
                        f"{crf_name}_DataDictionary_{date}.csv",
                        csv_data_dict_buffer.getvalue(),
                    )
                if include_pdf_paper:
                    zip_file.writestr(
                        f"{crf_name}_Completion_Guide_{date}.pdf", pdf_completion_guide
                    )
                    zip_file.writestr(
                        f"{crf_name}_paperlike_{date}.pdf", pdf_paperlike_crf
                    )
                if include_word:
                    zip_file.writestr(f"{crf_name}_CRFreview_{date}.docx", word_bytes)
                if include_xml:
                    zip_file.writestr(xml_file_name, xml_content)

            zip_buffer.seek(0)
            return (
                "",
                dcc.send_bytes(zip_buffer.getvalue(), f"{crf_name}_bundle_{date}.zip"),
                None,
                None,
                None,
                None,
            )

        return (
            "",
            dcc.send_bytes(
                csv_data_dict_buffer.getvalue(), f"{crf_name}_DataDictionary_{date}.csv"
            )
            if include_csv
            else None,
            dcc.send_bytes(
                pdf_completion_guide, f"{crf_name}_Completion_Guide_{date}.pdf"
            )
            if include_pdf_paper
            else None,
            dcc.send_bytes(xml_content, xml_file_name) if include_xml else None,
            dcc.send_bytes(pdf_paperlike_crf, f"{crf_name}_paperlike_{date}.pdf")
            if include_pdf_paper
            else None,
            dcc.send_bytes(word_bytes, f"{crf_name}_CRFreview_{date}.docx")
            if include_word
            else None,
        )

    else:
        return (
            "",
            None,
            None,
            None,
            None,
            None,
        )


def _generate_crf(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    # Create a new list to build the reordered rows
    new_rows = []
    used_indices = set()

    # Loop through each row in the original dataframe
    for index, row in df_datadicc.iterrows():
        variable = row["Variable"]
        variable_type = row["Type"]

        # Skip rows that have already been added to the new list
        if index in used_indices:
            continue

        # Add the current row to the reordered list
        new_rows.append(row)
        used_indices.add(index)

        # If it's a multi_list or dropdown, check for corresponding _otherl2 and _otherl3
        if variable_type in ["multi_list", "user_list"]:
            # Extract the prefix (e.g., "drug14_antiviral" from "drug14_antiviral_type")
            prefix = "_".join(variable.split("_")[:2])

            # Find and add the _otherl2 and _otherl3 rows right after the current one
            for suffix in ["_otherl2", "_otherl3"]:
                mask = df_datadicc["Variable"].str.startswith(prefix + suffix)
                for i in df_datadicc[mask].index:
                    new_rows.append(df_datadicc.loc[i])
                    used_indices.add(i)

    # Create the final reordered dataframe
    df_datadicc = pd.DataFrame(new_rows)

    df_datadicc.loc[df_datadicc["Type"] == "user_list", "Type"] = "radio"
    df_datadicc.loc[df_datadicc["Type"] == "multi_list", "Type"] = "checkbox"
    df_datadicc.loc[df_datadicc["Type"] == "list", "Type"] = "radio"
    df_datadicc = df_datadicc[
        [
            "Form",
            "Section",
            "Variable",
            "Type",
            "Question",
            "Answer Options",
            "Validation",
            "Minimum",
            "Maximum",
            "Skip Logic",
        ]
    ]

    df_datadicc.columns = [
        "Form Name",
        "Section Header",
        "Variable / Field Name",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Branching Logic (Show field only if...)",
    ]
    redcap_cols = [
        "Variable / Field Name",
        "Form Name",
        "Section Header",
        "Field Type",
        "Field Label",
        "Choices, Calculations, OR Slider Labels",
        "Field Note",
        "Text Validation Type OR Show Slider Number",
        "Text Validation Min",
        "Text Validation Max",
        "Identifier?",
        "Branching Logic (Show field only if...)",
        "Required Field?",
        "Custom Alignment",
        "Question Number (surveys only)",
        "Matrix Group Name",
        "Matrix Ranking?",
        "Field Annotation",
    ]
    df_datadicc = df_datadicc.reindex(columns=redcap_cols)

    df_datadicc.loc[
        df_datadicc["Field Type"].isin(
            [
                "date_dmy",
                "number",
                "integer",
                "datetime_dmy",
            ]
        ),
        "Field Type",
    ] = "text"
    df_datadicc = df_datadicc.loc[
        df_datadicc["Field Type"].isin(
            [
                "text",
                "notes",
                "radio",
                "dropdown",
                "calc",
                "file",
                "checkbox",
                "yesno",
                "truefalse",
                "descriptive",
                "slider",
            ]
        )
    ]
    df_datadicc["Section Header"] = df_datadicc["Section Header"].where(
        df_datadicc["Section Header"] != df_datadicc["Section Header"].shift(), np.nan
    )
    # For the new empty columns, fill NaN values with a default value (in this case an empty string)
    df_datadicc = df_datadicc.fillna("")

    df_datadicc["Section Header"] = df_datadicc["Section Header"].replace({"": np.nan})
    df_datadicc = _custom_alignment(df_datadicc)

    return df_datadicc


def _custom_alignment(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mask = (df_datadicc["Field Type"].isin(["checkbox", "radio"])) & (
        (
            df_datadicc["Choices, Calculations, OR Slider Labels"]
            .str.split("|")
            .str.len()
            < 4
        )
        & (df_datadicc["Choices, Calculations, OR Slider Labels"].str.len() <= 40)
    )
    df_datadicc.loc[mask, "Custom Alignment"] = "RH"
    return df_datadicc
