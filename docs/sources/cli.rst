.. _cli:

Command Line Interface (CLI)
============================

BRIDGE contains a very simple command line interface (CLI) named :program:`bridge-cli` that become available once the project is installed locally in `editable mode <https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs>`_:

.. code:: shell

   pip install -e .

This will install the project locally in a package named ``isaric-bridge``, and set up :program:`bridge-cli`. The (current) command hierarchy is displayed below as a tree:

.. code:: shell

   bridge-cli
   ├── arc
   └── crf
       ├── paperlike-pdf
       │   └── generate
       ├── paperlike-word
       │   └── generate
       └── completion-guide
           └── generate

There are two main command groups, :program:`arc`, which is not implemented, and :program:`crf`, which contains three (sub)commands described in more detail below.

To avoid conflicts while running other command-line workflows, such as when running unit tests, you can uninstall the editable project installation when you're done running the CLI:

.. code:: shell

   pip uninstall -y isaric-bridge

.. note::

   For more information on project CLI executables see `this <https://setuptools.pypa.io/en/latest/userguide/entry_point.html>`_ and `this <https://packaging.python.org/en/latest/specifications/entry-points/#entry-points>`_.

.. _cli.crf:

:program:`crf`
--------------

This is the main command group for all commands related to case report forms (CRF), which currently includes commands for the generation of paperlike PDFs and Word documents, and also completion guides. These are described in more detail below.

.. _cli.crf-paperlike-pdf:

:program:`paperlike-pdf`
~~~~~~~~~~~~~~~~~~~~~~~~

This is the main (sub)command group for all (sub)commands relating to paperlike PDFs of CRFs. Currently there is just one command, which is :program:`generate` for generating a paperlike CRF in PDF format given a local data dictionary CSV and either an `ARC <isaric-arc.readthedocs.io>`_ version string or custom local CSVs for the paperlike form details and supplemental phrases. An optional output file path, including the filename with extension, can also be provided: if not then the output file is written to a timestamped PDF file in an ``output`` subfolder in the working directory. The executable help context can be accessed using the ``--help`` option and an excerpt is displayed below:

.. code:: shell

   $ bridge-cli crf paperlike-pdf generate --help

   ...

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

   $ bridge-cli crf paperlike-pdf generate --data-dictionary-csv ~/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15\(in\).csv --arc-version 1.2.2 --redcap-db-name HANTA --language Spanish
   2026-06-02 15:53:58 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15(in).csv loaded with 586 rows.
   2026-06-02 15:53:58 [INFO] bridge.cli: Generating paperlike CRF PDF using data dictionary CSV "/Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15(in).csv" with the following parameters: REDCap project database name "HANTA", ARC version "1.2.2", language "Spanish".
   2026-06-02 15:53:59 [INFO] bridge.cli: Paperlike CRF PDF (size 1818069 bytes) generated.
   2026-06-02 15:53:59 [INFO] bridge.cli: Paperlike CRF PDF written to file /Users/smurthy/Documents/srm/dev/BRIDGE/output/CCPUKHantavirus_DataDictionary_2026-05-15(in)-HANTA-1.2.2-Spanish-2026-06-02-155359.pdf.

.. _cli.crf-paperlike-word:

:program:`paperlike-word`
~~~~~~~~~~~~~~~~~~~~~~~~~

This is the main (sub)command group for all (sub)commands relating to paperlike Word documents of CRFs. Currently there is just one command, which is :program:`generate` for generating a paperlike CRF in Word (:file:`.docx`) format given a local data dictionary CSV and an optional output file path. If no output file path is provided then the output file is written to a timestamped Word (``docx``) file in an ``output`` subfolder in the working directory. The executable help context can be accessed using the ``--help`` option and an excerpt is displayed below:

.. code:: shell

   $ bridge-cli crf paperlike-word generate --help

   ...

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

   $ bridge-cli crf paperlike-word generate --data-dictionary-csv ~/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15\(in\).csv
   2026-06-02 15:31:02 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15(in).csv loaded with 586 rows.
   2026-06-02 15:31:02 [INFO] bridge.cli: Generating paperlike CRF Word document using data dictionary CSV "/Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15(in).csv" with the following parameters: include descriptive rows: "False".
   2026-06-02 15:31:02 [INFO] bridge.cli: Paperlike CRF Word document (size 49371 bytes) generated, with option to include descriptive rows set to False.
   2026-06-02 15:31:02 [INFO] bridge.cli: Paperlike CRF Word document written to file /Users/smurthy/Documents/srm/dev/BRIDGE/output/CCPUKHantavirus_DataDictionary_2026-05-15(in)-2026-06-02-153102.docx.
