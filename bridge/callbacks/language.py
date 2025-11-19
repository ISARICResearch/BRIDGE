import json

import dash_bootstrap_components as dbc
import pandas as pd

from bridge.arc import arc_core, arc_translations
from bridge.arc.arc_lists import ArcList


class Language:

    def __init__(self,
                 version: str,
                 language: str,
                 initial_load: bool = False):
        self.version = version
        self.language = language
        self.initial_load = initial_load

    def get_dataframe_arc_language(self,
                                   df_version: pd.DataFrame) -> pd.DataFrame:
        df_version_language = arc_translations.get_arc_translation(
            self.language,
            self.version,
            df_version
        )
        return df_version_language

    def get_version_language_related_data(self):
        df_version, presets, commit = arc_core.get_arc(self.version)

        if not self.initial_load:
            df_version_language = self.get_dataframe_arc_language(df_version)
        else:
            df_version_language = df_version.copy()

        df_version_language = arc_core.add_required_datadicc_columns(df_version_language)

        df_arc_lists, list_variable_choices = ArcList(self.version, self.language).get_list_content(df_version_language)
        df_version_language = arc_core.add_transformed_rows(df_version_language,
                                                            df_arc_lists,
                                                            arc_core.get_variable_order(df_version_language))

        df_ulist, ulist_variable_choices = ArcList(self.version, self.language).get_user_list_content(
            df_version_language)

        df_version_language = arc_core.add_transformed_rows(df_version_language,
                                                            df_ulist,
                                                            arc_core.get_variable_order(df_version_language))

        df_multilist, multilist_variable_choices = ArcList(self.version, self.language).get_multi_list_content(
            df_version_language)

        df_version_language = arc_core.add_transformed_rows(df_version_language,
                                                            df_multilist,
                                                            arc_core.get_variable_order(df_version_language))

        grouped_presets = {}
        for section, preset_name in presets:
            grouped_presets.setdefault(section, []).append(preset_name)

        accordion_items = [
            dbc.AccordionItem(
                title=section,
                children=dbc.Checklist(
                    options=[{"label": preset_name, "value": preset_name} for preset_name in preset_names],
                    value=[],
                    id={'type': 'template_check', 'index': section},
                    switch=True,
                )
            )
            for section, preset_names in grouped_presets.items()
        ]
        return (
            df_version_language,
            commit,
            grouped_presets,
            accordion_items,
            json.dumps(ulist_variable_choices),
            json.dumps(multilist_variable_choices)
        )
