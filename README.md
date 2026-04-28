# BRIDGE

[![CodeQL](https://github.com/ISARICResearch/BRIDGE/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/ISARICResearch/BRIDGE/actions/workflows/github-code-scanning/codeql)
[![pre-commit](https://github.com/ISARICResearch/BRIDGE/actions/workflows/lint.yml/badge.svg)](https://github.com/ISARICResearch/BRIDGE/actions/workflows/lint.yml)
[![Tests and Coverage](https://github.com/ISARICResearch/BRIDGE/actions/workflows/tests.yml/badge.svg)](https://github.com/ISARICResearch/BRIDGE/actions/workflows/tests.yml)
[![Codecov](https://codecov.io/gh/ISARICResearch/BRIDGE/graph/badge.svg?token=NOW9MD1TQZ)](https://codecov.io/gh/ISARICResearch/BRIDGE)
[![Docker Build and Test](https://github.com/ISARICResearch/BRIDGE/actions/workflows/build.yaml/badge.svg)](https://github.com/ISARICResearch/BRIDGE/actions/workflows/build.yaml)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

ISARIC BRIDGE is a web-based application designed to operationalize [ISARIC ARC](https://github.com/ISARICResearch/ARC) and edit any ISARIC CRF and tailor it to outbreaks particular context. By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of Case Report Forms (CRFs) for each disease and specific research context. It generates the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides.

## About BRIDGE

BRIDGE (BioResearch Integrated Data tool GEnerator) is designed to serve as a resource for researchers and healthcare professionals involved in the study of outbreaks and emerging public health threats.

Key features include:

- **Multilingual support (AI-translated):** BRIDGE allows users to generate CRFs in multiple languages, currently including **English, Spanish, Portuguese, and French**.
  > *Note: translations are AI-generated and may require local review or adaptation before deployment.*

- **Choose**: BRIDGE uses the machine-readable library ARC and allows the user to choose the questions they want to include in the CRF. BRIDGE presents ARC as a tree structure with different levels: ARC version, forms, sections, and questions. Users navigate through this tree and select the questions they want to include in the CRF. Additionally, users can start with one of our Templates, which are pre-selected groups of questions. They can click on the Templates tab and select those they want to include in the CRF. All selected questions can be customized.

- **Customize**: BRIDGE allows customization of CRFs from chosen questions. For some questions, users can also select measurement units or answer options from predefined checkable lists. Users can click the relevant question, and a   checkable list will appear with options for the site or disease being researched. This feature ensures that the CRF is tailored to specific needs, enhancing the precision and relevance of the data collected.

- **Save and share progress**: BRIDGE includes a save-template functionality that enables users to save their work at any stage. The saved template can be reloaded later to continue customization or shared with collaborators. This means that a researcher can design a partially customized CRF, export it, and then another colleague can import it into BRIDGE to continue the process seamlessly. This feature promotes collaboration, reduces duplication of effort, and ensures consistency across teams.

- **Capture**: BRIDGE generates files for creating databases within REDCap, including the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. It also produces paper-like versions of the CRFs and completion guides. Once users are satisfied with their selections, they can name the CRF and click on generate to
  finalize the process, ensuring a seamless transition to data collection.

- **Paper-like design**: The generated CRFs are provided in professional, publication-style layouts that are suitablefor both digital use and printed deployment in field settings.

- **Flexibility for outbreaks**: CRFs can be rapidly adapted to the context of new or re-emerging diseases, ensuring timely deployment during health emergencies.

BRIDGE is openly available to the research community under the Creative Commons Attribution-ShareAlike 4.0 International license. While contributions are limited to authorized individuals, the app is freely accessible for use by others, provided they adhere to the terms of this license, including attribution and the sharing of derivative works under the
same terms.

BRIDGE enables users to select variables from the ARC versions that are saved in the ARC folder within the repository. It also allows the selection of templates included in these versions and supports the generation of the following files:

## Files

- **Clinical Characterization XML:** This XML file provides a recommended configuration and structure for clinical characterization studies. It includes information about users, events, project settings, and functionality, serving as a reference for setting up clinical characterization studies.

- **REDCap Data Dictionary:** This file is a CSV that can be directly uploaded to REDCap to generate the database.

- **Paper-like CRF:** This is a PDF document designed to be used in manual data collection as needed, available in multiple languages for global usability (AI translations).

- **Completion Guide:** A detailed PDF guide that includes **variable definitions and instructions for field completion**, supporting accurate and standardized data collection across sites.

## How to Use BRIDGE

You can find instructions about how to use BRIDGE in our [Getting started with BRIDGE Guide](https://isaricresearch.github.io/Training/bridge_starting.html). BRIDGE is a web-based application and ISARIC hosts a live version of this using the current version of the codebase. The link to this can be found in the Getting started guide. We expect users to access BRIDGE through this web-based application rather than through the source code. However, if you encounter any issues or would like to contribute improvements, please feel free to submit an [issue](https://github.com/ISARICResearch/BRIDGE/issues) on this repository or email us at: [data@isaric.org](mailto:data@isaric.org).

## Project TOML & Managing Dependencies

Project metadata, including information about authors, maintainers, dependencies, are contained in the [`pyproject.toml`](https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml). This is a key file that should be maintained: any changes affecting project metadata, including dependencies, should be staged and committed in the normal way.

There are groups of optional dependencies (listed in the `[optional-dependencies]` section), which are purely for development and/or testing. A `requirements.txt` containing the app dependencies does not exist, but can easily be generated locally, from the project TOML, using, for example, the `pip-compile` tool from [`pip-tools`](https://pip-tools.readthedocs.io/en/latest/):
```shell
pip-compile -o requirements.txt pyproject.toml
```
or a more advanced package manager such as [Astral `uv`](https://docs.astral.sh/uv):
```shell
uv export -v --format requirements.txt -o requirements.txt
```
A more comprehensive dependency file format such as [`pylock.toml`](https://packaging.python.org/en/latest/specifications/pylock-toml/), with full dependency file hashes, can also be generated, for example, with `uv`, using:
```shell
uv export -v --format pylock.toml -o pylock.toml
```
This version of the `pylock.toml` will only contain the app dependencies - if some combination of development and/or optional dependencies is required in the `pylock.toml` then this can be achieved with `uv lock` using a combination of the `--group` and/or `--all-groups` flags - see the [`uv export` command reference](https://docs.astral.sh/uv/reference/cli/#uv-export). Changes to the `pylock.toml` should be staged and committed in the normal way.

To install from a `pylock.toml`, for example, with `uv`, you can use:
```shell
uv pip install -r pylock.toml
```

For further information consult the [`uv` documentation](https://docs.astral.sh/uv/).

## Versioning and Releases

Versioning will be managed via the `bridge/__init__.py` file, and the goal is to follow some kind of semantic versioning. Currently, releases are manually prepared and published to [GitHub](https://github.com/ISARICResearch/BRIDGE/releases) and Zenodo - this process may be automated in the future. The last (GitHub) release was [`v1.2`](https://github.com/ISARICResearch/BRIDGE/releases/tag/v1.2).

## Contributors

- Esteban Garcia-Gallo - [esteban.garcia@ndm.ox.ac.uk](mailto:esteban.garcia@ndm.ox.ac.uk)
- Laura Merson - [laura.merson@ndm.ox.ac.uk](mailto:laura.merson@ndm.ox.ac.uk)
- Sara Duque-Vallejo - [sara.duquevallejo@ndm.ox.ac.uk](mailto:sara.duquevallejo@ndm.ox.ac.uk)
- Laura Thomson - [laura.thomson@dtc.ox.ac.uk](mailto:laura.thomson@dtc.ox.ac.uk)
- Alasdair Wilson - [alasdair.wilson@dtc.ox.ac.uk](mailto:alasdair.wilson@dtc.ox.ac.uk)
- Sandeep Murthy - [sandeep.murthy@ndm.ox.ac.uk](mailto:sandeep.murthy@ndm.ox.ac.uk)

---

**Note**: BRIDGE is maintained by ISARIC. For inquiries, support, or collaboration, please [contact us](mailto:data@isaric.org).
