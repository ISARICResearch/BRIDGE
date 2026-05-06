===========================
Getting Started with BRIDGE
===========================

.. container::

   .. rubric:: Contents
      :name: contents

   - :ref:`Introduction <getting-started.introduction>`
   - :ref:`Structure <getting-started.structure>`
   - :ref:`Settings <getting-started.settings>`

.. _getting-started.introduction:

Introduction
------------

BRIDGE is a `web application <https://bridge.isaric.org>`_ developed by `ISARIC <https://isaric.org/>`_ that assists in the creation of Clinical Report Forms (CRFs). It is based on `ARC <https://github.com/ISARICResearch/ARC>`_, also developed by ISARIC.

ARC is a comprehensive machine-readable document in CSV format, designed for use in Clinical Report Forms (CRFs) during disease outbreaks. It includes a library of questions covering demographics, comorbidities, symptoms, medications, and outcomes. Each question is
based on a standardized schema, has specific definitions mapped to controlled terminologies, and has built-in quality control. ARC is openly accessible, with version control via GitHub ensuring document integrity and collaboration.

BRIDGE is a web-based application designed to operationalize ARC and edit any ISARIC CRF and tailor it to an outbreak's particular context. By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of Case Report Forms (CRFs) for each disease and specific research context. It generates the data dictionary and XML needed to create a `REDCap <https://project-redcap.org/>`_ database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides.

.. _getting-started.structure:

Structure
---------

BRIDGE is divided into three components:

#. The tool bar is located on the left and allows the user to enter
   the settings and the templates. To open each of those you should
   click on the respective icon and click back when you want to
   return to the general view.
#. The ARC checkable tree is in the central panel of the application.
   It presents ARC as a tree structure with different levels: ARC
   version, forms, sections, and questions.
#. The CRF representation panel shows how the CRF is going to be when
   generating, including selected questions and support questions
   needed to be functional (that are automatically added by BRIDGE).

|BRIDGE structure|

.. _getting-started.settings:

Settings
--------

In the settings panel, users can select the version of ARC they want to use and the BRIDGE outcomes they want to generate:

- **ISARIC Clinical Characterization XML:** This file can be used to generate a REDCap project. It contains the clinical characterization structure that can be uploaded to REDCap to generate a project that allows data capture in the ARC structure.
- **REDCap Data Dictionary:** This file can be used to add the specific forms and questions selected in BRIDGE to the REDCap project.
- **Paper-like CRF:** This is a PDF file that can be printed and used to collect data manually, allowing sites that cannot capture data electronically to collect information that can later be uploaded to the REDCap database.

|BRIDGE settings|

.. container:: footer

   Licensed under the `MIT license <https://opensource.org/licenses/MIT/>`_ International License by `ISARIC <https://isaric.org/>`_ on
   behalf of Oxford University.

.. |BRIDGE structure| image:: https://github.com/ISARICResearch/Training/raw/main/docs/assets/1_structure.png
.. |BRIDGE settings| image:: https://github.com/ISARICResearch/Training/raw/main/docs/assets/2_settings.png
