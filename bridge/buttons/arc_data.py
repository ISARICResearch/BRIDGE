import json

import dash_bootstrap_components as dbc

from bridge.arc import arc


class ARCData:

    def __init__(self, selected_version, selected_language):
        self.selected_version = selected_version
        self.selected_language = selected_language

    def get_dataframe_arc_language(self, df_version):
        if self.selected_language == 'English':
            return df_version
        else:
            df_version_language = arc.get_arc_translation(
                self.selected_language,
                self.selected_version,
                df_version
            )
            return df_version_language

    def get_version_language_related_data(self):
        df_version, version_presets, version_commit = arc.get_arc(self.selected_version)
        df_version = arc.add_required_datadicc_columns(df_version)
        df_version_language = self.get_dataframe_arc_language(df_version)

        version_arc_lists, version_list_variable_choices = arc.get_list_content(df_version_language,
                                                                                self.selected_version,
                                                                                self.selected_language)
        df_version_language = arc.add_transformed_rows(df_version_language, version_arc_lists,
                                                       arc.get_variable_order(df_version_language))

        version_arc_ulist, version_ulist_variable_choices = arc.get_user_list_content(df_version_language,
                                                                                      self.selected_version,
                                                                                      self.selected_language)

        df_version_language = arc.add_transformed_rows(df_version_language, version_arc_ulist,
                                                       arc.get_variable_order(df_version_language))

        version_arc_multilist, version_multilist_variable_choices = arc.get_multi_list_content(df_version_language,
                                                                                               self.selected_version,
                                                                                               self.selected_language)

        df_version_language = arc.add_transformed_rows(df_version_language, version_arc_multilist,
                                                       arc.get_variable_order(df_version_language))

        version_grouped_presets = {}
        for section, preset_name in version_presets:
            version_grouped_presets.setdefault(section, []).append(preset_name)

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
            for section, preset_names in version_grouped_presets.items()
        ]
        return (
            df_version_language,
            version_commit,
            version_grouped_presets,
            accordion_items,
            json.dumps(version_ulist_variable_choices),
            json.dumps(version_multilist_variable_choices)
        )
