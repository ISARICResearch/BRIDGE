__all__ = [
    "generate_crf_completion_guide",
    "generate_paperlike_crf_pdf",
    "generate_paperlike_crf_word",
]


# -- IMPORTS --

# -- Standard libraries --
import sys
from datetime import datetime
from pathlib import Path

# -- 3rd party libraries --
import click
import pandas as pd

# -- Internal libraries --
import bridge.generate_pdf.paper_crf as paper_crf
import bridge.generate_pdf.paper_word as paper_word

from bridge.arc.arc_api import ArcApiClientError
from bridge.utils.logger import setup_logger


logger = setup_logger(__name__)  # pragma: no cover


@click.group("bridge-cli", help="BRIDGE command line interface (CLI).")
def bridge_cli(): ...


@bridge_cli.group("arc", help="ARC-related commands. Not implemented.")
def arc(): ...


@bridge_cli.group("crf", help="Case report form (CRF)-related commands.")
def crf(): ...


@crf.group("paperlike-pdf", help="Commands relating to paperlike PDFs of CRFs.")
def paperlike_pdf(): ...


@paperlike_pdf.command(
    "generate", help="Generates a paperlike PDF of the given CRF."
)  # pragma: no cover
@click.option(
    "--data-dictionary-csv",
    required=True,
    help="Path (absolute or relative) to the data dictionary CSV",
)
@click.option(
    "--arc-version",
    default="1.2.2",
    required=False,
    help="Optional ARC version if not using custom paperlike details and supplemental phrases, defaults to the latest (currently `1.2.2`)",
)
@click.option(
    "--redcap-db-name",
    default="Generic",
    required=False,
    help="Optional REDCap project DB name, defaults to `Generic`",
)
@click.option(
    "--language",
    default="English",
    required=False,
    help="Optional PDF language, defaults to English",
)
@click.option(
    "--paperlike-details-csv",
    required=False,
    help="Optional path (absolute or relative) to a custom paperlike form details CSV",
)
@click.option(
    "--supplemental-phrases-csv",
    required=False,
    help="Optional path (absolute or relative) to a custom supplemental phrases CSV",
)
@click.option(
    "--output-path",
    required=False,
    help="Optional target path, including filename with `.pdf` extension, to write the PDF file",
)
def generate_paperlike_crf_pdf(
    data_dictionary_csv: str,
    arc_version: str | None = "1.2.2",
    redcap_db_name: str | None = "Generic",
    language: str | None = "English",
    paperlike_details_csv: str | None = None,
    supplemental_phrases_csv: str | None = None,
    output_path: str | None = None,
) -> bytes:
    """:py:class:`bytes` : Generates and returns a PDF of the paperlike CRF.

    Parameters
    ----------
    data_dictionary_csv : str
        The local path to the data dictionary CSV file.

    arc_version : str, default="1.2.2"
            Optional ARC version string, defaults to the current latest version
            ``"1.2.2"`` (as of 15.05.2026).

    redcap_db_name : str, default=""
            Optional REDCap database name, defaults to ``"Generic"``.

    language : str, default="English"
            Optional PDF language setting, defaults to ``"English"``.

    paperlike_details_csv : str, default=None
        Optional paperlike form details CSV, defaults to ``None``.

    supplemental_phrases_csv : str, default=None
        Optional supplemental phrases CSV, defaults to ``None``.

    output_path : str, default=None
            Optional output path string, defaults to ``None``. If ``None`` then
            output file is created in a subfolder named ``output`` created in
            the working directory.

    Returns
    -------
    bytes
            The CRF PDF object as bytes.
    """
    # Load the data dictionary
    data_dictionary_csv = Path(data_dictionary_csv).resolve()
    data_dictionary = pd.read_csv(data_dictionary_csv)

    logger.info(
        f"Data dictionary {data_dictionary_csv} loaded with {len(data_dictionary)} rows."
    )

    # Main conditional logic to support ARC vs non-ARC loading of paperlike
    # form details and supplemental phrases.
    if not (paperlike_details_csv and supplemental_phrases_csv):
        # Call the Bridge function to get the CRF PDF with ARC-based logic, as
        # at least one of the user-defined paperlike form details and
        # supplemental phrases CSVs must be null at this point. The function
        # defines a default ARC version of ``"1.2.2"`` so the ARC version will
        # never be null here.
        try:
            logger.info(
                "Generating paperlike CRF PDF using data dictionary CSV "
                f'"{data_dictionary_csv}" with the following parameters: '
                f'REDCap project database name "{redcap_db_name}", '
                f'ARC version "{arc_version}", '
                f'language "{language}".'
            )
            pdf = paper_crf.generate_paperlike_pdf(
                data_dictionary=data_dictionary,
                version=arc_version,
                db_name=redcap_db_name,
                language=language,
            )
        except ArcApiClientError as e:
            logger.error(e)
            sys.exit(1)
    else:
        # Load the user-defined paperlike details and supplmental phrases CSVs
        paperlike_details = pd.read_csv(paperlike_details_csv)
        supplemental_phrases = pd.read_csv(supplemental_phrases_csv)
        # Call the Bridge function to get the CRF PDF with non-ARC logic
        logger.info(
            "Generating paperlike CRF PDF using data dictionary CSV "
            f'"{data_dictionary_csv}" with the following parameters: '
            f'REDCap project database name "{redcap_db_name}", '
            f'language "{language}", '
            f'custom paperlike details CSV "{paperlike_details_csv}", '
            f'custom supplemental phrases CSV "{supplemental_phrases_csv}".'
        )
        pdf = paper_crf.generate_paperlike_pdf(
            data_dictionary=data_dictionary,
            db_name=redcap_db_name,
            language=language,
            paperlike_details=paperlike_details,
            supplemental_phrases=supplemental_phrases,
        )

    logger.info(f"Paperlike CRF PDF (size {sys.getsizeof(pdf)} bytes) generated.")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    # Create the output folder if it doesn't exist, and form the output file
    # path.
    if not output_path:
        if not Path("output").exists():
            Path("output").mkdir()
        output_filename = data_dictionary_csv.stem
        output_path = (
            Path("output")
            .resolve()
            .joinpath(
                f"{output_filename}-{redcap_db_name}-{arc_version}-{language}-{timestamp}.pdf"
            )
            if not (paperlike_details_csv and supplemental_phrases_csv)
            else Path("output")
            .resolve()
            .joinpath(f"{output_filename}-{redcap_db_name}-{language}-{timestamp}.pdf")
        )
    else:
        output_path = Path(output_path).resolve()

    # Write the PDF document to the output file, before returning it.
    output_path.write_bytes(pdf)

    logger.info(f"Paperlike CRF PDF written to file {output_path}.")

    return pdf


@crf.group(
    "paperlike-word", help="Commands relating to paperlike Word documents of CRFs."
)  # pragma: no cover
def paperlike_word(): ...


@paperlike_word.command(
    "generate", help="Generates a paperlike Word document of the given CRF."
)
@click.option(
    "--data-dictionary-csv",
    required=True,
    help="Path (absolute or relative) to the data dictionary CSV",
)
@click.option(
    "--include-descriptive-rows",
    required=False,
    is_flag=True,
    default=False,
    help="Include source rows with descriptive field type, defaults to `False`",
)
@click.option(
    "--output-path",
    required=False,
    help="Optional target path, including filename with `.docx` extension, to write the Word file",
)
def generate_paperlike_crf_word(
    data_dictionary_csv: str,
    include_descriptive_rows: bool = False,
    output_path: str | Path | None = None,
) -> bytes:
    """:py:class:`bytes` : Generates and returns a Word document (``.docx``) of the paperlike CRF.

    Parameters
    ----------
    data_dictionary_csv : str
            The local path to the data dictionary CSV file.

    include_descriptive_rows : bool, default=False
            Include source rows with descriptive field type.

    output_path : str, default=None
            Optional output path string, defaults to ``None``. If ``None`` then
            output file is created in a subfolder named ``output`` created in
            the working directory.

    Returns
    -------
    bytes
            The CRF Word document object as bytes.
    """
    # Load the data dictionary
    data_dictionary_csv = Path(data_dictionary_csv).resolve()
    data_dictionary = pd.read_csv(data_dictionary_csv)

    logger.info(
        f"Data dictionary {data_dictionary_csv} loaded with {len(data_dictionary)} rows."
    )

    # Call the Bridge function to get the CRF Word document.
    logger.info(
        "Generating paperlike CRF Word document using data dictionary CSV "
        f'"{data_dictionary_csv}" with the following parameters: '
        f'include descriptive rows: "{include_descriptive_rows}".'
    )
    word = paper_word.df_to_word(
        data_dictionary, include_descriptive_rows=include_descriptive_rows
    )

    logger.info(
        f"Paperlike CRF Word document (size {sys.getsizeof(word)} bytes) generated, with option to include descriptive rows set to {include_descriptive_rows}."
    )

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    # Create the output folder if it doesn't exist, and form the output file
    # path.
    if not output_path:
        if not Path("output").exists():
            Path("output").mkdir()
        output_filename = data_dictionary_csv.stem
        output_path = (
            Path("output").resolve().joinpath(f"{output_filename}-{timestamp}.docx")
        )
    else:
        output_path = Path(output_path).resolve()

    # Write the Word document to the output file, before returning it.
    output_path.write_bytes(word)

    logger.info(f"Paperlike CRF Word document written to file {output_path}.")

    return word


@crf.group(
    "completion-guide", help="Commands relating to the CRF completion guide (PDF)."
)  # pragma: no cover
def completion_guide(): ...


@completion_guide.command(
    "generate", help="Generates a PDF completion guide for the CRF."
)
@click.option(
    "--data-dictionary-csv",
    required=True,
    help="Path (absolute or relative) to the data dictionary CSV",
)
@click.option(
    "--arc-version",
    default="1.2.2",
    required=False,
    help="Optional ARC version if not using custom paperlike details and supplemental phrases, defaults to the latest (currently `1.2.2`)",
)
@click.option(
    "--redcap-db-name",
    default="Generic",
    required=False,
    help="Optional REDCap project DB name, defaults to `Generic`",
)
@click.option(
    "--output-path",
    required=False,
    help="Optional path to write the completion guide",
)
def generate_crf_completion_guide(
    data_dictionary_csv: str,
    arc_version: str | None = "1.2.2",
    redcap_db_name: str | None = "Generic",
    output_path: str | Path | None = None,
) -> bytes:
    """:py:class:`bytes` : Generates and returns a PDF completion guide for the CRF.

    Parameters
    ----------
    data_dictionary_csv : str
            The local path to the data dictionary CSV file.

    arc_version : str, default="1.2.2"
            Optional ARC version string, defaults to the current latest version
            ``"1.2.2"`` (as of 15.05.2026).

    redcap_db_name : str, default=""
            Optional REDCap database name, defaults to ``"Generic"``.

    output_path : str, default=None
            Optional output path string, defaults to ``None``. If ``None`` then
            output file is created in a subfolder named ``output`` created in
            the working directory.

    Returns
    -------
    bytes
            The CRF completion guide PDF document object as bytes.
    """
    # Load the data dictionary
    data_dictionary_csv = Path(data_dictionary_csv).resolve()
    data_dictionary = pd.read_csv(data_dictionary_csv)

    logger.info(
        f"Data dictionary {data_dictionary_csv} loaded with {len(data_dictionary)} rows."
    )

    # Call the Bridge function to get the CRF Word document.
    logger.info(
        "Generating CRF completion guide PDF using data dictionary CSV "
        f'"{data_dictionary_csv}" with the following parameters: '
        f'REDCap project database name "{redcap_db_name}", '
        f'ARC version "{arc_version}".'
    )
    pdf = paper_crf.generate_completion_guide(
        data_dictionary, version=arc_version, db_name=redcap_db_name
    )

    logger.info(
        f"CRF completion guide PDF (size {sys.getsizeof(pdf)} bytes) generated."
    )

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    # Create the output folder if it doesn't exist, and form the output file
    # path.
    if not output_path:
        if not Path("output").exists():
            Path("output").mkdir()
        output_filename = data_dictionary_csv.stem
        output_path = (
            Path("output")
            .resolve()
            .joinpath(
                f"{output_filename}-{redcap_db_name}-{arc_version}-{timestamp}.pdf"
            )
        )
    else:
        output_path = Path(output_path).resolve()

    # Write the Word document to the output file, before returning it.
    output_path.write_bytes(pdf)

    logger.info(f"CRF completion guide PDF written to file {output_path}.")

    return pdf
