from functools import partial
from io import BytesIO
from os.path import join, dirname, abspath

import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate

from bridge.arc.arc_api import ArcApiClientError
from bridge.arc.arc_core import ArcApiClient
from bridge.generate_pdf.form import Form
from bridge.generate_pdf.guide import generate_guide_doc
from bridge.generate_pdf.header_footer import generate_paperlike_header_footer
from bridge.generate_pdf.opener import generate_opener
from bridge.utils.logger import setup_logger
from bridge.utils.utils import clean_dataframe

logger = setup_logger(__name__)

REGISTERED_FONT = "DejaVuSans"
REGISTERED_FONT_BOLD = "DejaVuSans-Bold"

ASSETS_DIR_FULL = join(dirname(dirname(dirname(abspath(__file__)))), "assets")
FONTS_DIR_FULL = join(ASSETS_DIR_FULL, "fonts")

pdfmetrics.registerFont(
    TTFont(REGISTERED_FONT, join(FONTS_DIR_FULL, f"{REGISTERED_FONT}.ttf"))
)
pdfmetrics.registerFont(
    TTFont(REGISTERED_FONT_BOLD, join(FONTS_DIR_FULL, f"{REGISTERED_FONT_BOLD}.ttf"))
)

registerFontFamily(REGISTERED_FONT, normal=REGISTERED_FONT, bold=REGISTERED_FONT_BOLD)


def generate_paperlike_pdf(
    data_dictionary: pd.DataFrame,
    version: str | None = "1.2.2",
    db_name: str | None = "Generic",
    language: str | None = "English",
    paperlike_details: pd.DataFrame | None = None,
    supplemental_phrases: pd.DataFrame | None = None,
) -> bytes:
    """:py:class:`bytes` : Returns a paperlike CRF PDF.

    The paperlike form details and supplemental phrases can be user-defined,
    i.e., loaded as local CSVs, or, if either of these is empty, they are
    loaded from ARC using the ARC ``version``.

    Parameters
    ----------
    data_dictionary : pd.DataFrame
        The incoming data dictionary.

    version : str, default=``"1.2.2"``
        Optional ARC version string, defaults to the latest.

    db_name : str, default="Generic"
        Optional associated REDCap project database name, defaults to
        ``"Generic"``.

    language : str, default="English"
        Optional PDF publication language, defaults to ``"English"``.

    paperlike_details : pd.DataFrame, default=None
        Optional user-defined dataframe defining the paperlike CRF output
        details, defaults to ``None``. If this is null then the paperlike
        details are loaded from ARC.

    supplemental_phrases : pd.DataFrame, default=None
        Optional user-defined dataframe containing supplemental phrases,
        defaults to ``None``. If this is null then the supplemental phrases
        are loaded from ARC.

    Raises
    ------
    bridge.arc.arc_api.ArcApiClientError
        If either the paperlike form details or supplemental phrases CSVs
        cannot be found for the given combination of ARC version and language,
        when ARC is being used as the source for these.

    Returns
    -------
    bytes
        The PDF file bytes object.

    """
    # Set up an ARC API client
    arc_api_client = ArcApiClient()

    # Clean the dataframe by removing any HTML characters and also removing
    # non-standard / non-textual Unicode characters.
    data_dictionary = clean_dataframe(data_dictionary)

    buffer = BytesIO()
    data_dictionary = data_dictionary[
        ~data_dictionary["Field Label"].str.startswith((">", "->"))
    ]
    preg_flag = 0

    if (
        data_dictionary["Form Name"]
        .str.contains("neonate|pregnancy", case=False, na=False)
        .any()
    ):
        preg_flag = 1

    if (
        isinstance(paperlike_details, pd.DataFrame) and paperlike_details.empty
    ) or paperlike_details is None:
        try:
            paperlike_details = arc_api_client.get_dataframe_paper_like_details(
                version, language
            )
        except ArcApiClientError as e:
            raise ArcApiClientError(
                "Could not find paperlike details CSV for ARC version "
                f'"{version}" and language "{language}"'
            ) from e

    if preg_flag == 0:
        paperlike_details = paperlike_details.loc[
            (paperlike_details["Paper-like section"] != "PREGNANCY FORM")
            & (paperlike_details["Paper-like section"] != "NEONATE FORM")
        ]

        mask = paperlike_details["Paper-like section"] == "Timing /Events"

        paperlike_details.loc[mask, "Text_translation"] = (
            "Hospital admission / initial assessment | Admission to ICU (if applicable) | Research sample taken (optional) | As per site protocol (optional) | Discharge / death / end of study"
        )

    if (
        isinstance(supplemental_phrases, pd.DataFrame) and supplemental_phrases.empty
    ) or supplemental_phrases is None:
        try:
            supplemental_phrases = arc_api_client.get_dataframe_supplemental_phrases(
                version, language
            )
        except ArcApiClientError as e:
            raise ArcApiClientError(
                "Could not find supplemental phrases CSV for ARC version "
                f'"{version}" and language "{language}"'
            ) from e

    # Locate the phrase in the supplemental phrases DataFrame
    def locate_phrase(variable: str) -> dict:
        try:
            phrase = supplemental_phrases.loc[
                supplemental_phrases["variable"] == variable, "text"
            ].values[0]
            return {"error": False, "text": phrase}
        except IndexError:
            logger.warning(f"Variable '{variable}' not found in supplemental phrases.")
            return {"error": True, "text": ""}

    left_margin = 0.3 * inch
    right_margin = 0.3 * inch
    top_margin = 0.7 * inch
    bottom_margin = 0.7 * inch

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    element_list = []
    element_list = generate_opener(element_list, paperlike_details, db_name)
    data_dictionary["Section Header"] = data_dictionary["Section Header"].replace(
        {"": np.nan}
    )
    element_list = Form().generate_form(data_dictionary, element_list, locate_phrase)
    header_footer_partial = partial(generate_paperlike_header_footer, title=db_name)

    try:
        doc.build(
            element_list,
            onFirstPage=header_footer_partial,
            onLaterPages=header_footer_partial,
        )
    except ValueError as e:
        logger.error(e)
        raise RuntimeError("Failed to build Paperlike PDF")

    buffer.seek(0)
    return buffer.getvalue()


def generate_completion_guide(
    data_dictionary: pd.DataFrame, version: str, db_name: str
) -> bytes:
    data_dictionary = data_dictionary.copy()
    buffer = BytesIO()
    generate_guide_doc(data_dictionary, version, db_name, buffer)
    buffer.seek(0)
    return buffer.getvalue()
