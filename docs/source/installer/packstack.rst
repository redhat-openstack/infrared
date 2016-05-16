Packstack
---------

Infrared allows to use the Packstack to install Openstack::

    $ ir-installer -d -vvvv --inventory hosts packstack --product-version=8 -o install.yml -e @provision.yml -e @private.yml

Here required arguments are:
    --product-version: the product version to install.

Optional arguments:
    * provision.yml - the settings file generated ny provisiner. I might contains required for Packstack settings.
    * private.yml - the settings file with the private properties.


Settings structure
^^^^^^^^^^^^^^^^^^

The main settings file for packstack installer is located in the::

    settings/installer/packstack/packstack.yml


This file provides defaults settings and default configuration options for the packstack answer files.

Additional answer  options can be added using the the following approaches:

    * Using a non default config argument value::

        $ ir-installer --inventory hosts packstack --config=basic_neutron.yml

    * Using the extra-vars flags::

        $ ir-installer --inventory hosts packstack --product-version=8 --extra-vars=installer.config.CONFIG_DEBUG_MODE=no

    * Network based answer file options can be selected whether by choosing network backend or by modyfing config with --extra-vars::

        $ ir-installer --inventory hosts packstack --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml

        $ ir-installer --inventory hosts packstack --product-version=8 --network=neutron.yml --netwrok-variant=neutron_gre.yml --extra-vars=installer.network.config.CONFIG_NEUTRON_USE_NAMESPACES=n



Both installer.network.config.* and installer.config.* options will be merged into one config and used as the answer file for Packstack installer.
