.. BRIDGE documentation master file, created by
   sphinx-quickstart on Thu Apr 30 15:24:02 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BRIDGE Documentation
====================

`BRIDGE <https://github.com/ISARICResearch/BRIDGE>`_ (BioResearch Integrated Data tool GEnerator) is a web-based `application <https://bridge.isaric.org>`_ designed to operationalize `ISARIC ARC <https://github.com/ISARICResearch/ARC>`_ to tailor ARC CRFs to an outbreak's particular context. By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of Case Report Forms (CRFs) for each disease and specific research context. It generates the data dictionary and XML needed to create a `REDCap <https://project-redcap.org/>`_ database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides via library functions - there are also made available as command-line project scripts/executables that are described in more detail :ref:`here <cli>`.

The documentation is currently limited to an :doc:`app user guide <sources/app>`, a :doc:`CLI user guide <sources/cli>` and an :doc:`API reference <sources/api-reference>` - more features and guides will be added here over time.

BRIDGE is licensed under the `Open Source Initiative (OSI) <https://opensource.org>`_-compliant `MIT license <https://opensource.org/license/mit>`_.

.. image:: _static/osi-badge-light.svg
   :target: https://opensource.org/license/mit
   :height: 200px
   :width:  200px

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents:

   sources/app
   sources/cli
   sources/api-reference
   sources/contributors
