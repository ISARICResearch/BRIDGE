from unittest import mock

import numpy as np
import pandas as pd

from bridge.arc import arc_tree


@mock.patch("bridge.arc.arc_core.set_select_units")
@mock.patch("bridge.arc.arc_core.add_required_datadicc_columns")
@mock.patch("bridge.arc.arc_core.get_dependencies")
def test_get_tree_items(mock_dependencies, mock_required_columns, mock_set_units):
    data = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
            "presentation",
        ],
        "Variable": [
            "inclu_disease",
            "demog_age_units",
            "demog_height",
            "pres_firstsym",
            "inclu_testreason",
            "inclu_testreason_otth",
        ],
        "Type": [
            "user_list",
            np.nan,
            np.nan,
            "multi_list",
            "radio",
            "text",
        ],
        "Question": [
            "Suspected or confirmed infection",
            "Age units",
            "Height (select units)",
            "Symptom(s) during first 24 hours of illness (select all that apply)",
            "Reason why the patient was tested",
            "Specify other reason",
        ],
        "vari": [
            "disease",
            "age",
            "height",
            "firstsym",
            "testreason",
            "testreason",
        ],
        "mod": [
            np.nan,
            "units",
            np.nan,
            None,
            None,
            "otth",
        ],
        "Sec_name": [
            "INCLUSION CRITERIA",
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
            "ONSET & PRESENTATION",
            "INCLUSION CRITERIA",
            "INCLUSION CRITERIA",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    df_dependencies = pd.DataFrame.from_dict(
        {
            "Variable": [
                "inclu_disease",
                "demog_age_units",
                "demog_height",
                "pres_firstsym",
                "inclu_testreason",
                "inclu_testreason_otth",
            ],
            "Dependencies": [
                ["subjid"],
                ["demog_birthknow", "subjid"],
                ["subjid"],
                ["subjid"],
                ["subjid"],
                ["subjid"],
            ],
        }
    )

    version = "v1.1.1"

    # These extra columns aren't used
    mock_dependencies.return_value = df_dependencies
    mock_required_columns.return_value = df_datadicc
    mock_set_units.return_value = df_datadicc

    expected = {
        "children": [
            {
                "children": [
                    {
                        "children": [
                            {
                                "key": "inclu_disease",
                                "title": "↳ Suspected or confirmed " "infection",
                            },
                            {
                                "key": "inclu_testreason",
                                "title": "Reason why the patient " "was tested",
                            },
                            {
                                "key": "inclu_testreason_otth",
                                "title": "Specify other reason",
                            },
                        ],
                        "key": "PRESENTATION-INCLUSION CRITERIA",
                        "title": "INCLUSION CRITERIA",
                    },
                    {
                        "children": [
                            {
                                "children": [],
                                "key": "demog_height",
                                "title": "Height (select units)",
                            }
                        ],
                        "key": "PRESENTATION-DEMOGRAPHICS",
                        "title": "DEMOGRAPHICS",
                    },
                    {
                        "children": [
                            {
                                "key": "pres_firstsym",
                                "title": "⇉ Symptom(s) during first 24 hours of illness (select all that apply)",
                            }
                        ],
                        "key": "PRESENTATION-ONSET & PRESENTATION",
                        "title": "ONSET & PRESENTATION",
                    },
                ],
                "key": "PRESENTATION",
                "title": "PRESENTATION",
            }
        ],
        "key": "ARC",
        "title": "v1.1.1",
    }

    output = arc_tree.get_tree_items(df_datadicc, version)

    assert output == expected
