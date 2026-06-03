.. _getting-started:

Getting Started
===============

The latest release, which is |release|, containing the source code, can be downloaded from `GitHub <https://github.com/ISARICResearch/BRIDGE/releases/tag/v1.2>`_, or the repository can be cloned with Git or an Git-integrated IDE of your choice, e.g. VS Code. There is no public Python package associated with the BRIDGE repository.

There is a `public BRIDGE app <https://bridge.isaric.org>`_ that is freely available to use. Or you can build and run your own local version in a standalone Docker container, as described :ref:`here <building-and-running>`.

.. _requirements:

Requirements
------------

The main BRIDGE requirements are a minimum of Python ``3.12+`` (although ``3.11`` should also be OK), and the
specific dependencies listed in the ``[project]`` section of the `project TOML <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml>`_.

If you're running BRIDGE locally, as described :ref:`here <building-and-running>`, then these dependencies (and their sub-dependencies) will be pre-installed inside the container, so no direct user installation is required.

If you're running BRIDGE directly on your system as a Python (Plotly Dash) app then you need to ensure all of these dependencies are installed in your environment with the current version pins, **before** running the app. If you haven't already done this, then you can do this either by installing the project in editable mode, via :command:`pip install -e .`, which will also install the main ``bridge`` package in your environment, or a direct installation using a package manager such as `Astral UV <https://docs.astral.sh/uv/>`_. For example, if using UV you may consider using the :command:`uv sync` command as described `here <https://docs.astral.sh/uv/concepts/projects/sync/#syncing-the-environment>`_.

.. _building-and-running:

Building and Running the App Locally
------------------------------------

You can build and run your own local version of BRIDGE as a Docker service as follows:

1. Checkout the local BRIDGE Git branch on which you want to build and run the app - usually this will be the ``main`` branch, but it could also be any feature or fix branch. If you have access to a command line shell you can do this using:

.. code:: shell

   git checkout <target branch name>

.. note::

   If you have any unstaged or uncommited changes on your current branch then please use Git, or your editor or IDE, to stage or discard these, as appropriate, before switching to the target branch.

2. Build the Docker image (named ``isaric-bridge``, but which could be something of your choice) on the branch using:

.. code:: shell

   docker build -t isaric-bridge .

3. Run the app in the container (named ``isaric-bridge``, again which could be something of your choice) using the image:

.. code:: shell

   docker run -d -p 80:8050 --name isaric-bridge isaric-bridge

The app will accessible at ``http://localhost:80``.

.. note::

   If you're also running a local version of VERTEX make sure the ports don't conflict - use port ``80`` for BRIDGE and port ``8050`` for VERTEX.

The app will be available as long as the container (and also the main Docker daemon) is running.

You can also run the app directly (outside of Docker) just using Python, but this requires more precise control over the environment and BRIDGE dependencies, as described :ref:`here <requirements>`.
