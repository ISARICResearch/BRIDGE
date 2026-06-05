import json
from copy import deepcopy
from time import perf_counter

import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

from bridge.arc import arc_core, arc_translations
from bridge.arc.arc_lists import ArcList
from bridge.utils.logger import setup_logger

logger = setup_logger(__name__)

_VERSION_LANGUAGE_CACHE: dict[tuple[str, str, bool], tuple] = {}


class Language:
    """A class defining language-related callbacks for CRF translations."""

    def __init__(self, version: str, language: str, initial_load: bool = False):
        """Initialiser.

        Parameters
        ----------
        version : str
            ARC version.

        language : str
            CRF language

        initial_load : bool, default=False
            Optional setting to perform initial loading, defaults to ``False``.
        """
        self.version = version
        self.language = language
        self.initial_load = initial_load

    def get_dataframe_arc_language(self, df_version: pd.DataFrame) -> pd.DataFrame:
        """Get ARC language dataframe.

        Parameters
        ----------
        df_version : pandas.DataFrame
            ARC version dataframe.

        Returns
        -------
        pandas.DataFrame
            ARC language version dataframe.
        """
        df_version_language = arc_translations.get_arc_translation(
            self.language, self.version, df_version
        )
        return df_version_language

    def build_accordion_item_children(
        self, section: str, preset_names: list[str]
    ) -> dbc.Checklist | html.Div:
        """Build accordion item children based on section type.

        Parameters
        ----------
        section : str
            The section name (e.g., "ARChetype Disease CRF")
        preset_names : list
            List of template names in this section

        Returns
        -------
        dbc.Checklist
            For regular sections, html.Div with sliders and info icons for ARChetype
        """
        if section == "ARChetype Disease CRF":
            # For ARChetype Disease CRF: use sliders with conditional info icons
            return html.Div(
                [
                    html.Div(
                        [
                            dbc.Switch(
                                id={
                                    "type": "template_check",
                                    "index": f"{section}_{preset_name}",
                                },
                                label=preset_name,
                                value=False,
                            ),
                            html.Button(
                                "ℹ️",
                                id={"type": "template-info-btn", "index": preset_name},
                                n_clicks=0,
                                style={
                                    "background": "none",
                                    "border": "none",
                                    "cursor": "pointer",
                                    "fontSize": "16px",
                                    "padding": "0 8px",
                                    "marginLeft": "auto",
                                    "display": "none",  # Hidden by default
                                },
                                className="template-info-button",
                            ),
                        ],
                        id={"type": "template-item-container", "index": preset_name},
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "padding": "8px 0",
                        },
                    )
                    for preset_name in preset_names
                ]
            )
        else:
            # For other sections: use standard checklist
            return dbc.Checklist(
                options=[
                    {"label": preset_name, "value": preset_name}
                    for preset_name in preset_names
                ],
                value=[],
                id={"type": "template_check", "index": section},
                switch=True,
            )

    def build_accordion_items(self) -> list[dbc.AccordionItem]:
        """Build accordion items.

        Returns
        -------
        list
            List of accordion items.
        """
        return [
            dbc.AccordionItem(
                title=section,
                children=html.Div(
                    [
                        self.build_accordion_item_children(section, [preset_name])
                        for preset_name in preset_names
                    ]
                ),
            )
            for section, preset_names in self.grouped_presets.items()
        ]

    def get_version_language_related_data(self) -> tuple:
        """:py:class:`tuple` : Returns version language related data as a tuple.

        Returns
        -------
        tuple
            A tuple of the version language (as a dataframe), ARC commit SHA,
            the grouped presets dict, accordion items, and the ``ulist`` choices
            and ``multilist`` choices.
        """
        cache_initial_load = self.initial_load if self.language != "English" else False
        cache_key = (self.version, self.language, cache_initial_load)
        if cache_key in _VERSION_LANGUAGE_CACHE:
            (
                df_cached,
                cached_commit,
                cached_grouped_presets,
                cached_accordion_items,
                cached_ulist_json,
                cached_multilist_json,
            ) = _VERSION_LANGUAGE_CACHE[cache_key]
            return (
                df_cached.copy(deep=True),
                cached_commit,
                deepcopy(cached_grouped_presets),
                deepcopy(cached_accordion_items),
                cached_ulist_json,
                cached_multilist_json,
            )

        build_start = perf_counter()
        df_version, presets, commit = arc_core.get_arc(self.version)

        if self.initial_load or self.language == "English":
            df_version_language = df_version.copy()
        else:
            df_version_language = self.get_dataframe_arc_language(df_version)

        df_version_language = arc_core.add_required_datadicc_columns(
            df_version_language
        )

        df_arc_lists, list_variable_choices = ArcList(
            self.version, self.language
        ).get_list_content(df_version_language)
        df_version_language = arc_core.add_transformed_rows(
            df_version_language,
            df_arc_lists,
            arc_core.get_variable_order(df_version_language),
        )

        df_ulist, ulist_variable_choices = ArcList(
            self.version, self.language
        ).get_user_list_content(df_version_language)

        df_version_language = arc_core.add_transformed_rows(
            df_version_language,
            df_ulist,
            arc_core.get_variable_order(df_version_language),
        )

        df_multilist, multilist_variable_choices = ArcList(
            self.version, self.language
        ).get_multi_list_content(df_version_language)

        df_version_language = arc_core.add_transformed_rows(
            df_version_language,
            df_multilist,
            arc_core.get_variable_order(df_version_language),
        )

        self.grouped_presets = {}
        for section, preset_name in presets:
            self.grouped_presets.setdefault(section, []).append(preset_name)

        accordion_items = self.build_accordion_items()
        output = (
            df_version_language,
            commit,
            self.grouped_presets,
            accordion_items,
            json.dumps(ulist_variable_choices),
            json.dumps(multilist_variable_choices),
        )
        _VERSION_LANGUAGE_CACHE[cache_key] = (
            output[0].copy(deep=True),
            output[1],
            deepcopy(output[2]),
            deepcopy(output[3]),
            output[4],
            output[5],
        )
        logger.debug(
            "language.get_version_language_related_data cache=MISS version=%s language=%s initial_load=%s elapsed_ms=%.3f",
            self.version,
            self.language,
            cache_initial_load,
            (perf_counter() - build_start) * 1000,
        )
        return output
