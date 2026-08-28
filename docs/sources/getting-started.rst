.. _getting-started:

Getting Started
===============

The latest release, which is |release|, containing the source code, can be downloaded from `GitHub <https://github.com/ISARICResearch/BRIDGE/releases/tag/v1.2>`_, or the repository can be cloned with Git or an Git-integrated IDE of your choice, e.g. VS Code. There is no public Python package associated with the BRIDGE repository.

There is a `public BRIDGE app <https://bridge.isaric.org>`_ that is freely available to use. Or you can build and run your own local version in a standalone Docker container, as described :ref:`here <running-bridge-in-docker>`.

.. _requirements:

Requirements
------------

The requirements for using BRIDGE as a local app depend on how you want to run it:

* If you want to run BRIDGE in a **Docker container**, as described :ref:`here <running-bridge-in-docker>`, then the only requirement is `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_. The Docker build process will ensure, via the `Dockerfile <https://github.com/ISARICResearch/BRIDGE/blob/main/Dockerfile>`_, that all the app dependencies (and their sub-dependencies) are pre-installed inside the image used to run the container. **Docker is the recommended way of running BRIDGE locally.**

* If you want to run BRIDGE directly on your system / host as a Python **Plotly Dash** app then you need to ensure all of the `project dependencies <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml#L62>`_ are installed in your BRIDGE environment, as described :ref:`below <plotly-dash-set-up>`, **before** running the app. Please ensure that your environment is using a minimum of Python ``3.12+`` (although ``3.11`` should also be OK). For further information on the requirement dependencies see the `project TOML <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml>`_.

.. _plotly-dash-set-up:

Setting up the BRIDGE environment to run as a Plotly Dash app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. In a Python 3.12+ virtual environment install UV with :program:`pip`:

.. code:: shell

   python3 -m pip install uv

By default UV will make all dependency-related changes inside a new :file:`.venv` subfolder within the working directory - if this is OK then proceed to the next step. **If not** then export the path of the preferred (e.g. pre-existing) virtual environment with the ``UV_PROJECT_ENVIRONMENT`` environment variable:

.. code:: shell

   export UV_PROJECT_ENVIRONMENT="/path/to/preferred/virtual/env"

2. Install (or sync) all the project dependencies into the environment with the command:

.. code:: shell

   uv sync --verbose --all-groups --all-extras --no-install-project --no-cache --refresh --inexact

For more details on :command:`uv sync` see `this <https://docs.astral.sh/uv/concepts/projects/sync/#syncing-the-environment>`_.
