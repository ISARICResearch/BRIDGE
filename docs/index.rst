.. BRIDGE documentation master file, created by
   sphinx-quickstart on Thu Apr 30 15:24:02 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ISARIC BRIDGE
=============

`BRIDGE <https://github.com/ISARICResearch/BRIDGE>`_ (BioResearch Integrated Data tool GEnerator) is a web-based `application <https://bridge.isaric.org>`_ designed to operationalize `ISARIC ARC <https://github.com/ISARICResearch/ARC>`_ to tailor `ARC case report forms (CRF) <https://isaricresearch.github.io/CCP/ARChetype-CRF-Guidelines>`_ to disease outbreaks.

By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of CRFs for each disease and specific research context. It generates the data dictionary and XML needed to create a `REDCap <https://project-redcap.org/>`_ database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides via library functions - there are also made available as command-line/console project scripts that are described in more detail :ref:`here <cli>`.

See the :doc:`quickstart guide <sources/getting-started>` to start using BRIDGE, and the linked pages below for more information on features and code.

BRIDGE is licensed under the `Open Source Initiative (OSI) <https://opensource.org>`_-compliant `MIT license <https://opensource.org/license/mit>`_.

.. image:: _static/osi-badge-light.svg
   :target: https://opensource.org/license/mit
   :height: 200px
   :width:  200px

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents:

   sources/getting-started
   sources/app
   sources/cli
   sources/contributors
