.. _cli:

Command Line Interface (CLI)
============================

BRIDGE contains a very simple command line interface (CLI), currently providing two command line **project scripts/executables/entry points** (defined in the ``[project.scripts]`` section of the `project TOML <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml>`_) for paperlike CRF generation in PDF and Word formats, that become available once the project is installed locally in `editable mode <https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs>`_:

.. code:: shell

   pip install -e .

This will install the project locally in a package named ``isaric-bridge``, and set up two executables for command line use:

- :program:`generate-paperlike-crf-pdf` - Generates a paperlike CRF in PDF format.
- :program:`generate-paperlike-crf-word` - Generates a paperlike CRF in Word format.

These are described in more detail below. After using the executables, it is advisable to uninstall the editable project installation using:

.. code:: shell

   pip uninstall -y isaric-bridge

.. note::

   For more information on project CLI executables see `this <https://setuptools.pypa.io/en/latest/userguide/entry_point.html>`_ and `this <https://packaging.python.org/en/latest/specifications/entry-points/#entry-points>`_.

.. _cli.generate-paperlike-crf-pdf:

Generate Paperlike CRF PDF
--------------------------

The :program:`generate-paperlike-crf-pdf`  generates a paperlike CRF in PDF format given a local data dictionary CSV and either an `ARC <isaric-arc.readthedocs.io>`_ version string or custom local CSVs for the paperlike form details and supplemental phrases. An optional output file path, including the filename with extension, can also be provided: if not then the output file is written to a timestamped PDF file in an ``output`` subfolder in the working directory. The executable help context can be accessed using the ``--help`` option and an excerpt is displayed below:

.. code:: shell

   Options:
     --data-dictionary-csv TEXT      Path (absolute or relative) to the data
                                     dictionary CSV  [required]
     --arc-version TEXT              Optional ARC version if not using custom
                                     paperlike details and supplemental phrases,
                                     defaults to the latest (currently `1.2.2`)
     --redcap-db-name TEXT           Optional REDCap project DB name, defaults to
                                     `Generic`
     --language TEXT                 Optional PDF language, defaults to English
     --paperlike-details-csv TEXT    Optional path (absolute or relative) to a
                                     custom paperlike form details CSV
     --supplemental-phrases-csv TEXT
                                     Optional path (absolute or relative) to a
                                     custom supplemental phrases CSV
     --output-path TEXT              Optional path to write the PDF file,
                                     defaults to ./output/CRF-<redcap_db_name>-<l
                                     anguage>-<timestamp>.pdf
     --help                          Show this message and exit.


The data dictionary CSV is required, while all other arguments are optional: if custom local CSV filepaths for **both** the paperlike form details and supplemental phrases are provided then these are used, otherwise ARC is used with the given (or default) version.

An example run is given below to generate a Hantavirus CRF PDF in Spanish, where the default ARC version (``1.2.2``) is used to load the paperlike form details and supplemental phrases:

.. code:: shell

   $ generate-paperlike-crf-pdf --data-dictionary-csv ~/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15\(in\).csv \
                                --arc-version 1.2.2 \
                                --redcap-db-name HANTA \
                                --language Spanish
   2026-05-19 07:25:24 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15(in).csv loaded with 586 rows.
   2026-05-19 07:25:25 [INFO] bridge.cli: Paperlike CRF PDF (size 1818080 bytes) generated.
   2026-05-19 07:25:25 [INFO] bridge.cli: Paperlike CRF PDF written to file output/CRF-HANTA-1.2.2-Spanish-2026-05-19-072525.pdf.

.. _cli.generate-paperlike-crf-word:

Generate Paperlike CRF Word
---------------------------

The :program:`generate-paperlike-crf-word` executable can generate a paperlike CRF in Word format given a local data dictionary CSV and an optional output file path. If no output file path is provided then the output file is written to a timestamped Word (``docx``) file in an ``output`` subfolder in the working directory. The executable help context can be accessed using the ``--help`` option and an excerpt is displayed below:

.. code:: shell

   Options:
     --data-dictionary-csv TEXT  Path (absolute or relative) to the data
                                 dictionary CSV  [required]
     --include-descriptive-rows  Include source rows with descriptive field type, defaults to `False`
     --output-path TEXT          Optional path to write the Word file, defaults
                                 to ./output/CRF-<timestamp>.docx
     --help                      Show this message and exit.


The data dictionary CSV is required, while the output file path is optional:

An example run is given below to generate an Ebola CRF Word document in English:

.. code:: shell

   $ generate-paperlike-crf-word --data-dictionary-csv ~/Downloads/Ebola_DataDictionary_2026-05-18.csv \
                                 --include-descriptive-rows
   2026-05-19 07:25:32 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/Ebola_DataDictionary_2026-05-18.csv loaded with 236 rows.
   2026-05-19 07:25:32 [INFO] bridge.cli: Paperlike CRF Word document (size 43593 bytes) generated, with option to include descriptive rows set to True.
   2026-05-19 07:25:32 [INFO] bridge.cli: Paperlike CRF Word document written to file output/CRF-2026-05-19-072532.docx.
