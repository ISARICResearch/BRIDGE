.. _citing:

Citing BRIDGE
=============

BRIDGE is **published** on `GitHub <https://github.com/ISARICResearch/BRIDGE/releases>`_ and `Zenodo <https://zenodo.org/records/18888928>`_. It has the DOI:

`10.5281/zenodo.14162844 <https://doi.org/10.5281/zenodo.14162844>`_

BRIDGE can be **cited** as follows:

	Garcia-Gallo E, Duque-Vallejo S, Wilson A, Thomson L, Edinburgh T, Murthy SR. ISARIC BRIDGE (v1.2). *ISARIC* |year|. doi:`10.5281/zenodo.14162844 <https://doi.org/10.5281/zenodo.14162844>`_

.. _note-for-maintainers-and-contributors:

A Note For Maintainers & Contributors
-------------------------------------

Maintainers and contributors should note that the `citation file <https://github.com/ISARICResearch/BRIDGE/blob/main/CITATION.cff>`_ should be kept up-to-date with changes in authorship. The file can be validated on the command line using the `cffconvert <https://github.com/citation-file-format/cffconvert>`_ library using the following command run from the root of the BRIDGE repository:

.. code:: shell

   cffconvert --validate

Any reported errors should be fixed, and the file staged and committed in the normal way. Citation file validation is included in the pre-commit status checks that happen automatically in GitHub on branch and PR updates.
