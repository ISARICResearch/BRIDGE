.. BRIDGE documentation master file, created by
   sphinx-quickstart on Thu Apr 30 15:24:02 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ISARIC BRIDGE
=============

.. image:: _static/BRIDGE-logo.png
   :height: 252.017
   :width:  304

`BRIDGE <https://github.com/ISARICResearch/BRIDGE>`_ (BioResearch Integrated Data tool GEnerator) is an open source web-based `application <https://bridge.isaric.org>`_ developed by `ISARIC <https://isaric.org>`_ designed to operationalize `ISARIC ARC <https://github.com/ISARICResearch/ARC>`_ to tailor `ARC case report forms (CRF) <https://isaricresearch.github.io/CCP/ARChetype-CRF-Guidelines>`_ to disease outbreaks.

By selecting and customizing clinical questions and ensuring necessary data points for each, BRIDGE automates the creation of CRFs for each disease and specific research context. It generates the data dictionary and XML needed to create a `REDCap <https://project-redcap.org/>`_ database for capturing data in the ARC structure. Additionally, it produces paper-like versions of the CRFs and completion guides via library functions - there are also made available as command-line/console project scripts that are described in more detail :ref:`here <cli>`.

See the :doc:`quickstart guide <sources/getting-started>` to start using BRIDGE, and the linked pages below for more information on features and code.

BRIDGE is licensed under the `MIT license <https://opensource.org/license/mit>`_.

.. image:: _static/osi-badge-light.svg
   :target: https://opensource.org/license/mit
   :height: 100px
   :width:  100px

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents:

   Getting Started <sources/getting-started>
   Running BRIDGE in Docker <sources/running-bridge-in-docker>
   CLI <sources/cli>
   Citing BRIDGE <sources/citing>
   Contributors <sources/contributors>
