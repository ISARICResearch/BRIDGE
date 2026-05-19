.. _app:

The BRIDGE App
==============

The BRIDGE app can be used online at https://bridge.isaric.org, or you can build your local version and run it via Docker using the following instructions:

1. Checkout the BRIDGE Git branch on which you want to run the app - usually this will be the ``main`` branch, and if you've got access to a command line shell the way you can do this using:

.. code:: shell

   git branch -v

If you're not on the target stash any working changes using :command:`git stash` and checkout the target using :code:`git checkout <target branch name>`.

2. Build the Docker image (named ``isaric-bridge``) on the branch using:

.. code:: shell

   docker build -t isaric-bridge .

3. Run the app in the container (named ``isaric-bridge``) using the image:

.. code:: shell

   docker run -d -p 80:8050 --name isaric-bridge isaric-bridge

The app will accessible at ``http://localhost:80``.
