Interactive SSH
^^^^^^^^^^^^^^^

There are situation, when user needs to establish interactive ssh session to host, managed  by `infrared`.
One provides simpliest way to do this. Just call:

.. code-block:: console

   infrared ssh <nodename>

where 'nodename' is a hostname from inventory file.

For example

.. code-block:: console

   infrared ssh controller-0
