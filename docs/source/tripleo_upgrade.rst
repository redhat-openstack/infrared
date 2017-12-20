TripleO Upgrade
===============

Starting with OSP12 the upgrade/update of a TripleO deployment can be done via the tripleo-upgrade plugin.
tripleo-upgrade comes preinstalled as an InfraRed plugin. After a successful InfraRed overcloud deployment 
you need to run the following steps to upgrade the deployment:

Symlink roles path::

    ln -s $(pwd)/plugins $(pwd)/plugins/tripleo-upgrade/infrared_plugin/roles

Set up undercloud upgrade repositories::

    infrared tripleo-undercloud \
        --upgrade yes \
        --mirror ${mirror_location} \
        --ansible-args="tags=upgrade_repos"

Upgrade undercloud::

    infrared tripleo-upgrade \
        --undercloud-upgrade yes

Set up overcloud upgrade repositories::

    infrared tripleo-overcloud \
        --deployment-files virt \
        --upgrade yes \
        --mirror ${mirror_location} \
        --ansible-args="tags=upgrade_collect_info,upgrade_repos"

Upgrade overcloud::

    infrared tripleo-upgrade \
        --overcloud-upgrade yes

