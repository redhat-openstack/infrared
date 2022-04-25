---
config:
    plugin_type: install
subparsers:
    tripleo-standalone:
        description: The standalone tripleo installation of the openstack
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Deploy parameters
              options:
                  stackname:
                      type: Value
                      help: Overcloud stack Name
                      default: standalone
                  local-interface:
                      type: Value
                      help: The data network interface name
                      default: eth0
                  default-gateway:
                      type: Value
                      help: Gateway for local network interface, used in ControlPlaneStaticRoutes
                      default: 192.168.24.1
                  deployment-user:
                      type: Value
                      help: User name for the purpose of standalone deployment
                      default: cloud-user
            - title: Setup Packages
              options:
                  mirror:
                      type: Value
                      help: |
                          Enable usage of specified mirror (for rpm, pip etc) [brq,qeos,tlv - or hostname].
                          (Specified mirror needs to proxy multiple rpm source hosts and pypi packages.)

                  version:
                      type: Value
                      required: yes
                      help: |
                          The product version (product == director)
                          Numbers are for OSP releases
                          Names are for RDO releases
                      choices:
                        - "7"
                        - "8"
                        - "9"
                        - "10"
                        - "11"
                        - "12"
                        - "13"
                        - "14"
                        - "15"
                        - "15-trunk"
                        - "16.1"
                        - "16.2"
                        - kilo
                        - liberty
                        - mitaka
                        - newton
                        - ocata
                        - pike
                        - queens
                        - rocky
                  build:
                      help: |
                          String represents a timestamp of the OSP puddle.
                          Note: for versions 6 < OSPd < 10 to specify director
                          version use '--director-build' flag.
                          (for the given product core version).
                          Supports any rhos-release labels.
                          RDO supported labels: master-tripleo-ci
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                      type: Value

                  director-build:
                      help: |
                          String represents a timestamp of the OSP director puddle
                          (for the given product core version). Only applies for
                          6 < OSPd < 10, and could be used with '--build' flag.
                          Note: for versions >= 10 only the --build flag should be used to
                          specify a puddle.
                          Supports any rhos-release labels.
                          Examples: "passed_phase1", "2016-08-11.1", "Y1", "Z3", "GA"
                          If missing, will equal to "latest".
                      type: Value

                  buildmods:
                      type: Value
                      help: |
                          List of flags for rhos-release module.
                          Currently works with
                          pin - pin puddle (dereference 'latest' links to prevent content from changing)
                          flea - enable flea repos
                          unstable - this will enable brew repos or poodles (in old releases)
                          cdn - use internal mirrors of the CDN repos. (internal use)
                          none - use none of those flags
                      default: pin

                  reboot-timeout:
                      type: Value
                      default: 600
                      help: |
                          The timeout for the undercloud host to come back from a reboot after package updates or
                          an upgrade.

            - title: Custom Repositories
              options:
                  cdn:
                      type: FileValue
                      help: |
                          YAML file
                          Register the undercloud with a Red Hat Subscription Management platform.
                          see documentation for more details
                  repos-config:
                      type: VarFile
                      help: |
                          YAML file
                          define new repositories or update existing according to file.
                          see documentation for more details
                  repos-urls:
                      type: Value
                      help: |
                          comma separated list of URLs to download repo files to ``/etc/yum.repos.d``
                  repos-skip-release:
                      type: Bool
                      help: |
                          specifies whether the rhos/rdo-release tools should
                          be used to install tripleo packages. This flag also disables installation of the extra cdn
                          repositories.
                  custom-sources-script-url:
                      help: |
                          Script which is downloaded and executed at repo and registry setup time,
                          IR provides context for the scripts via environment variables.
                          Implies repos-skip-release , the script can call foo-release if wishes
                          In case of a remote url you can pass get parameters.
                      default: ""
                  custom-sources-script-args:
                      help: |
                           Extra arguments for the custom-sources script.
                  skip-remove-repo:
                      type: Value
                      action: append
                      help: |
                          In the rhos-release role all repositories are clean up before tripleo-undercloud
                          deployment, if some repos are required during deployment then use option
                          '--skip-remove-repo' and specify path to the repository file. In that case this
                          repository will be ignored during delete procedure.
                          Example: --skip-remove-repo /etc/yum.repos.d/rhel-updates.repo
