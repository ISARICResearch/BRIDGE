# BRIDGE
ISARIC BRIDGE is a web-based application designed to operationalize [ISARIC ARC](https://github.com/ISARICResearch/ARC) and edit any ISARIC CRF and tailor it to outbreaks particular context. By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of Case Report Forms (CRFs) for each disease and specific research context. It generates the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides.

## About BRIDGE

BRIDGE (BioResearch Integrated Data tool GEnerator) is designed to serve as a resource for researchers and healthcare professionals involved in the study of outbreaks and emerging public health threats. BRIDGE allows users to:

- **Choose**: BRIDGE uses the machine-readable library ARC and allows the user to choose the questions they want to include in the CRF. BRIDGE presents ARC as a tree structure with different levels: ARC version, forms, sections, and questions. Users navigate through this tree and select the questions they want to include in the CRF. Additionally, users can start with one of our Templates, which are pre-selected groups of questions. They can click on the Templates tab and select those they want to include in the CRF. All selected questions can be customized.

- **Customize**: BRIDGE allows customization of CRFs from chosen questions. For some questions, users can also select measurement units or answer options from predefined checkable lists. Users can click the relevant question, and a checkable list will appear with options for the site or disease being researched. This feature ensures that the CRF is tailored to specific needs, enhancing the precision and relevance of the data collected.

- **Capture**: BRIDGE generates files for creating databases within REDCap, including the data dictionary and XML needed to create a REDCap database for capturing data in the ARC structure. It also produces paper-like versions of the CRFs and completion guides. Once users are satisfied with their selections, they can name the CRF and click on generate to finalize the process, ensuring a seamless transition to data collection.

BRIDGE is openly available to the research community under the Creative Commons Attribution-ShareAlike 4.0 International license. While contributions are limited to authorized individuals, the app is freely accessible for use by others, provided they adhere to the terms of this license, including attribution and the sharing of derivative works under the same terms.

## BRIDGE Version 1.0

BRIDGE Version 1.0 enables users to select variables from the ARC versions that are saved in the ARC folder within the repository. It also allows the selection of templates included in these versions and supports the generation of the following files:

### Files

   - **Clinical Characterization XML:** This XML file provides a recommended configuration and structure for clinical characterization studies. It includes information about users, events, project settings, and functionality, serving as a reference for setting up clinical characterization studies.

   - **REDCap Data Dictionary:** This file is a csv that can be directly uploaded to REDCap to generate the database.

  - **Paper-like CRF:** This is a PDF document designed to be used in manual data collection as needed.

## How to Use BRIDGE

You can find intructions about how to use BRIDGE in our [Getting started with BRIDGE Guide](https://isaricresearch.github.io/Training/bridge_starting.html). BRIDGE is a web-based application and ISARIC hosts a live version of this using the current version of the codebase. The link to this can be found in the Getting started guide. We expect users to access BRIDGE through this web-based application rather than through the source code. However, we encourage all users to submit an [issue](https://github.com/ISARICResearch/BRIDGE/issues) on this repository or send us a [mail](mailto:data@isaric.org) if they would like to report any issues or to contribute improvements.

## Contributors

- Esteban Garcia-Gallo - [esteban.garcia@ndm.ox.ac.uk](mailto:esteban.garcia@ndm.ox.ac.uk)
- Laura Merson - [laura.merson@ndm.ox.ac.uk](mailto:laura.merson@ndm.ox.ac.uk)
- Sara Duque-Vallejo - [sara.duquevallejo@ndm.ox.ac.uk](mailto:sara.duquevallejo@ndm.ox.ac.uk)
- Tom Edinburgh - [tom.edinburgh@ndm.ox.ac.uk](mailto:tom.edinburgh@ndm.ox.ac.uk)
- Elise Pesonel - [elise.pesonel@ndm.ox.ac.uk](mailto:elise.pesonel@ndm.ox.ac.uk)


---

**Note**: BRIDGE is maintained by ISARIC. For inquiries, support, or collaboration, please [contact us](mailto:data@isaric.org).
