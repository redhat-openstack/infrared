OSPD UI tester
==============

Runs UI tests against the OSPD UI deployed on overcloud. Supports only RHOS10+.


Environment
-----------

To use the OSPD UI tester the following requirements should be met:

1) Undercloud should be installed
2) ``Instackenv.json`` should be generated and put into the undercloud machine.
3) A dedicated machine (uitester) should be provisioned. This machine will be used to run all the tests.

InfraRed allows to setup such environment. For example, the `virsh <virsh.html>`_ plugin can be used to provision required machines::

    ir virsh -vvvv -o provision.yml \
        --topology-nodes=undercloud:1,controller:3,compute:1,uitester:1 \
        --host-address=example.host.redhat.com \
        --host-key ~/.ssh/example-key.pem

To install undercloud use the `tripleo undercloud <tripleo-undercloud.html>`_ plugin::

    ir tripleo-undercloud -vvvv \
        --version=10 \
        --images-task=rpm

To deploy undercloud with the ssl support the ``generate_service_certificate = true`` should be added to the undercloud.conf file::

    echo "generate_service_certificate = true" >> plugins/tripleo-undercloud/templates/undercloud.conf


The next step is to generate ``instackenv.json`` file. This step can be done using the `tripleo overcloud <tripleo-overcloud.html>`_ plugin::

    ir tripleo-overcloud -vvvv \
        --version=10 \
        --deployment-files=virt \
        --ansible-args="tags=init,instack" \
        --introspect=yes

For the overcloud plugin it is important to specify the ``instack`` ansible tag to limit overcloud execution only by the generation of the instackenv.json file.

OSPD UI tester options
----------------------

To run OSPD UI tester the following command can be used::

    ir ospdui -vvvv \
        --openstack-version=10 \
        --tests=login \
        --ssl yes \
        --webdriver=chrome

Required arguments::
    * ``--openstack-version``: specifies the version of the product under test.
    * ``--test``: the test suite to run. Run ``ir ospdui --help`` to see the list of all available suites to run.

Optional arguments::
    * ``--ssl``: specifies whether the undercloud was installed with ssl enabled or not.
    * ``--webdriver``: the webdriver to use. Default browser is firefox
    * ``--setup``: specifies the config parameters for the tester. See `Advanced configuration`_ for details


Advanced configuration
----------------------

By default all the tester parameters are read from the ``vars\setup\default.yml`` file under the plugin dir.
Setup variable file describes selenium, test repo and network parameters to use::

    setup:
        selenium:
            chrome_driver:
                url: http://chromedriver.storage.googleapis.com/2.27/chromedriver_linux64.zip
            firefox_driver:
                url: https://github.com/mozilla/geckodriver/releases/download/v0.14.0/geckodriver-v0.14.0-linux64.tar.gz
                binary_name: geckodriver
        ospdui:
            repo: git://git.app.eng.bos.redhat.com/ospdui.git
            revision: HEAD
            dir: ~/ospdui_tests
        network:
            dev: eth0
            ipaddr: 192.168.24.240
            netmask: 255.255.255.0

To override any of these value you can copy ``vars\setup\default.yml`` to the same folder with the different name and change any value in that yml (for example git revision).
New setup config (without .yml extension) then can be specified with the ``--setup`` flag::

    ir ospdui -vvvv \
        --openstack-version=10 \
        --tests=login \
        --setup=custom_setup


Debugging
---------

The OSPD UI tester starts VNC server on the tester machine (by default on display ``:1``). This allows to remotely debug and observe what is happening on the tester.

If you have direct netwrok access to the tester, you can use any vnc client and connect.
If you are using virtual deployment the tunneling through the virthost to the tester instance should be created::

   client $> ssh -f root@myvirthost.redhat.com -L 5901:<tester ip address>:5901 -N

Then you can use vnc viewer and connect to the ``localhost:5901``.
