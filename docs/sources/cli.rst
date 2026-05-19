.. _cli:

Command Line Interface (CLI)
============================

BRIDGE contains two command line ** project scripts** for paperlike CRF generation in PDF and Word formats, that become available once the project is installed locally in `editable mode <https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs>`_:

.. code:: shell

   pip install -e .

This will install the project locally in a package named ``isaric-bridge``, and set up two scripts for command line use:

- :program:`generate-paperlike-crf-pdf` - Generates a paperlike CRF in PDF format.
- :program:`generate-paperlike-crf-word` - Generates a paperlike CRF in Word format.

After using the scripts, it is advisable to uninstall the editable project installation using:

.. code:: shell

   pip uninstall -y isaric-bridge

.. _cli.generate-paperlike-crf-pdf:

Generate Paperlike CRF PDF
--------------------------

The :program:`generate-paperlike-crf-pdf` script can generate a paperlike CRF in PDF format given a local data dictionary CSV and either an `ARC <isaric-arc.readthedocs.io>`_ version string or custom local CSVs for the paperlike form details and supplemental phrases. An optional output file path, including the filename with extension, can also be provided: if it is not then the output file is written to timestamped PDF file in an ``output`` subfolder created in the working directory. The script help context can be accessed using the `--help` option and an excerpt is displayed below:

:: code:: shell

   Options:
	  --data-dictionary-csv TEXT      Path (absolute or relative) to the data
	                                  dictionary CSV  [required]
	  --paperlike-details-csv TEXT    Optional path (absolute or relative) to a
	                                  custom paperlike form details CSV
	  --supplemental-phrases-csv TEXT
	                                  Optional path (absolute or relative) to a
	                                  custom supplemental phrases CSV
	  --arc-version TEXT              Optional ARC version if not using custom
	                                  paperlike details and supplemental phrases,
	                                  defaults to the latest
	  --db-name TEXT                  Optional REDCap project DB name, defaults to
	                                  an empty string
	  --language TEXT                 Optional PDF language, defaults to English
	  --output-path TEXT              Optional path to write the PDF file,
	                                  defaults to ./output/CRF-<db_name>-<arc_vers
	                                  ion>-{language}-{timestamp}.pdf
	  --help                          Show this message and exit.

The data dictionary CSV is required, while all other arguments are optional: if custom local CSV filepaths for **both** the paperlike form details and supplemental phrases are provided then these are used, otherwise ARC is used with the given (or default) version.

An example run is given below to generate a Hantavirus CRF PDF in Spanish, where the default ARC version (``1.2.2``) is used to load the paperlike form details and supplemental phrases:

.. code:: shell

$ generate-paperlike-crf-pdf --data-dictionary-csv ~/Downloads/CCPUKHantavirus_DataDictionary_2026-05-15.csv --db-name "HANTA" --language Spanish
2026-05-19 06:55:50 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/CCPUKHantavirus_DataDictionary_2026-05-19.csv loaded with 586 rows.
2026-05-19 12:23:10 [INFO] bridge.cli: Paperlike CRF PDF (size 1818075 bytes) generated.
2026-05-19 12:23:10 [INFO] bridge.cli: Paperlike CRF PDF written to file /Users/smurthy/Documents/srm/BRIDGE/output/Hanta-paperlike-crf-arc1.2.2-es.pdf.

.. _cli.generate-paperlike-crf-word:

Generate Paperlike CRF Word
---------------------------

The :program:`generate-paperlike-crf-word` script can generate a paperlike CRF in Word format given a local data dictionary CSV and optional output file path. If no output file path is provided then the output file is written to timestamped Word (``docx``) file in an ``output`` subfolder created in the working directory.The script help context can be accessed using the `--help` option and an excerpt is displayed below:

:: code:: shell

Options:
  --data-dictionary-csv TEXT  Path (absolute or relative) to the data
                              dictionary CSV  [required]
  --include-descriptive-rows  Include source rows with descriptive field type
  --output-path TEXT          Optional path to write the Word file, defaults to
                              ./output/CRF-{timestamp}.docx
  --help                      Show this message and exit.

The data dictionary CSV is required, while the output file path is optional: 

An example run is given below to generate an Ebola CRF Word document in English:

.. code:: shell

$ generate-paperlike-crf-word --data-dictionary-csv ~/Downloads/Ebola_DataDictionary_2026-05-18.csv
2026-05-19 06:55:50 [INFO] bridge.cli: Data dictionary /Users/smurthy/Downloads/Ebola_DataDictionary_2026-05-18.csv loaded with 236 rows.
2026-05-19 06:55:50 [INFO] bridge.cli: Paperlike CRF Word document (size 43593 bytes) generated, with option to include descriptive rows set to True.
2026-05-19 06:55:50 [INFO] bridge.cli: Paperlike CRF Word document written to file /Users/smurthy/Documents/srm/dev/BRIDGE/output/Ebola-CRF-202605190900.docx
