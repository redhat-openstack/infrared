Tripleo OSP with Red Hat Subscriptions
======================================

.. _must be registered: https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/11/html/director_installation_and_usage/chap-installing_the_undercloud#sect-Registering_your_System
.. _uc: tripleo_undercloud.html
.. _module documentation: http://docs.ansible.com/ansible/redhat_subscription_module.html

Undercloud
----------

To deploy OSP, the Undercloud `must be registered`_ to Red Hat channels.
Define the subscription details:


.. code-block:: yaml
   :caption: undercloud_cdn.yml

   ---
   server_hostname: 'subscription.rhsm.redhat.com'
   username: 'infrared.user@example.com'
   password: '123456'
   autosubscribe: yes
   server_insecure: yes

.. warning:: During run time, contents of the file are hidden from the logged output, to protect private account credentials.

For the full list of supported input, see the Ansible `module documentation`_.
For example, ``autosubscribe: yes`` can be replaced with ``pool_id`` or ``pool: REGEX``,
where ``REGEX`` is a regular expression that searches for matching available pools.

.. note:: Pre-registered undercloud is also supported if ``--cdn`` flag is missing.

Deploy your undercloud. It's recommended to use ``--images-task rpm`` to fetch pre-packaged images that are only available via Red Hat channels::

    infrared tripleo-undercloud --version 11 --cdn undercloud_cdn.yml --images-task rpm

.. warning:: ``--images-update`` is not supported with cdn.

Overcloud
---------
Once the undercloud is registered, the overcloud can be deployed. However, the overcloud nodes will not be
registered and cannot receive updates. While the nodes can be later registered manually, Tripleo provides a
way to register them automatically on deployment.

According to the `guide`_ there are 2 heat-templates required. They can be included,
and their defaults overridden, using a `custom templates file`_.

.. _guide: https://access.redhat.com/documentation/en-us/red_hat_openstack_platform/10/html/advanced_overcloud_customization/sect-registering_the_overcloud
.. _custom templates file: tripleo_overcloud.html

.. code-block:: yaml
   :caption: overcloud_cdn.yml

   ---
   tripleo_heat_templates:
       - /usr/share/openstack-tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/rhel-registration-resource-registry.yaml
       - /usr/share/openstack-tripleo-heat-templates/extraconfig/pre_deploy/rhel-registration/environment-rhel-registration.yaml

   custom_templates:
       parameter_defaults:
           rhel_reg_activation_key: ""
           rhel_reg_org: ""
           rhel_reg_pool_id: ""
           rhel_reg_method: "portal"
           rhel_reg_sat_url: ""
           rhel_reg_sat_repo: "rhel-7-server-rpms rhel-7-server-extras-rpms rhel-7-server-rh-common-rpms rhel-ha-for-rhel-7-server-rpms rhel-7-server-openstack-10-rpms"
           rhel_reg_repos: ""
           rhel_reg_auto_attach: ""
           rhel_reg_base_url: "https://cdn.redhat.com"
           rhel_reg_environment: ""
           rhel_reg_force: "true"
           rhel_reg_machine_name: ""
           rhel_reg_password: "123456"
           rhel_reg_release: ""
           rhel_reg_server_url: "subscription.rhsm.redhat.com"
           rhel_reg_service_level: ""
           rhel_reg_user: "infrared.user@example.com"
           rhel_reg_type: ""
           rhel_reg_http_proxy_host: ""
           rhel_reg_http_proxy_port: ""
           rhel_reg_http_proxy_username: ""
           rhel_reg_http_proxy_password: ""

.. note:: Please notice that the repos in the file above are for OSP 10

Deploy the overcloud with the custom templates file::

    infrared tripleo-overcloud --version=11 --deployment-files=virt --introspect=yes --tagging=yes  --deploy=yes --overcloud-templates overcloud_cdn.yml --post=yes
