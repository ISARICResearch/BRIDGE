.. _app:

Using the BRIDGE App
====================

The BRIDGE app can be used online at https://bridge.isaric.org, or you can build your own local version and run it (via Docker) using the following instructions:

1. Checkout the local BRIDGE Git branch on which you want to build and run the app - usually this will be the ``main`` branch, but it could also be any feature or fix branch. If you have access to a command line shell you can do this using:

.. code:: shell

   git checkout <target branch name>

.. note::

   If you have any unsaved/unstaged/uncommited changes on your current branch then you can stage and commit these, or discard (:command:`git reset`) or stash them somewhere (:command:`git stash`), before switching to the target branch.

2. Build the Docker image (named ``isaric-bridge``) on the branch using:

.. code:: shell

   docker build -t isaric-bridge .

3. Run the app in the container (named ``isaric-bridge``) using the image:

.. code:: shell

   docker run -d -p 80:8050 --name isaric-bridge isaric-bridge

The app will accessible at ``http://localhost:80``.
