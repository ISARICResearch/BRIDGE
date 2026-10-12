.. _getting-started:

Getting Started
===============

The latest release, which is |release|, containing the source code, can be downloaded from `GitHub <https://github.com/ISARICResearch/BRIDGE/releases/tag/v1.2>`_, or the repository can be cloned with Git or an Git-integrated IDE of your choice, e.g. VS Code. There is no public Python package associated with the BRIDGE repository.

There is a `public BRIDGE app <https://bridge.isaric.org>`_ that is freely available to use, for which there is a usage guide `here <https://isaricresearch.github.io/Training/bridge_starting.html>`_.

Alternatively, you can build and run your own local version in a standalone Docker container, as described :ref:`here <running-bridge-in-docker>`.

.. _requirements:

Project Requirements
--------------------

The requirements for using BRIDGE as a local app depend on how you want to run it:

* If you want to run BRIDGE in a **Docker container**, as described :ref:`here <running-bridge-in-docker>`, then the only requirement is `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_. The Docker build process will ensure, via the `Dockerfile <https://github.com/ISARICResearch/BRIDGE/blob/main/Dockerfile>`_, that all the app dependencies (and their sub-dependencies) are pre-installed inside the image used to run the container. **Docker is the recommended way of running BRIDGE locally** as it results in more stable, reproducible builds.

* If you want to run BRIDGE directly on your system / host as a Python **Plotly Dash** app, as described then you need to ensure all of the `project dependencies <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml#L62>`_ are installed in your BRIDGE environment, as described :ref:`here <running-bridge-as-plotly-dash-app>`, **before** running the app. Please ensure that your environment is using a minimum of Python ``3.12+`` (although ``3.11`` should also be OK). For further information on the requirement dependencies see the `project TOML <https://github.com/ISARICResearch/BRIDGE/blob/main/pyproject.toml>`_.
