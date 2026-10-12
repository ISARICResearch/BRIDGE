.. _running-bridge-as-plotly-dash-app:

Running BRIDGE as a Plotly Dash app
===================================

You can run BRIDGE as a local Plotly Dash app, from the root of the repository, as follows:

1. In a Python 3.12+ virtual environment install `Astral uv <https://docs.astral.sh/uv/>`_ with :program:`pip`:

.. code:: shell

   python3 -m pip install uv

By default UV will make all dependency-related changes inside a new :file:`.venv` subfolder within the working directory - if this is OK then proceed to the next step. **If not** then either export the path of the preferred (e.g. pre-existing or working) virtual environment with the ``UV_PROJECT_ENVIRONMENT`` environment variable:

.. code:: shell

   export UV_PROJECT_ENVIRONMENT="/path/to/preferred/virtual/env"

or use the ``--active`` flag on the relevant UV command, which will usually be :command:`uv sync` - see the `documentation <https://docs.astral.sh/uv/concepts/projects/sync/>`_ for more details.

2. Install (or sync) all the project dependencies into the working environment with the command:

.. code:: shell

   uv sync --verbose --active --all-groups --no-install-project --no-cache --refresh --inexact

.. note::

   With the  ``--inexact`` flag :command:`uv sync` preserves dependencies installed in the target environment that are unrelated to the dependency structure implied by the project TOML, while with the ``--exact`` flag its execution will result in a set of dependencies (and sub-dependencies) in the working environment that exactly match the dependency structure implied by the project TOML, including the removal of unrelated dependencies. To be on the safe side, it is advisable to run :command:`uv sync` with ``--inexact``, unless explicitly required for some reason.

3. Run the BRIDGE app (:file:`BRIDGE/app.py`) with Python using a ``PYTHONPATH`` prefix to indicate the relative location to the top-level package:

.. code:: shell

   PYTHONPATH=src python3 app.py

The app should be available from ``http://localhost:8050`` - note that the port here is ``8050``, not ``80``, which applies to the :ref:`Docker version <running-bridge-in-docker>`.
