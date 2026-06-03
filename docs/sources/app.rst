.. _app:

Using the BRIDGE App
====================

The BRIDGE app can be used online at https://bridge.isaric.org, or you can build your own local version and run it (via Docker) using the following instructions:

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
