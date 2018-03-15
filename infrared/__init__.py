# Holds the default variables
import os

SHARED_GROUPS = [
    {
        'title': 'Debug Options',
        'options': {
            'debug': {
                'action': 'store_true',
                'help': 'Run infrared in DEBUG mode',
                'short': 'd'
            }
        }
    },
    {
        'title': 'Ansible options',
        'options': {
            'verbose': {
                'action': 'count',
                'default': int(os.getenv('ANSIBLE_VERBOSITY', 0)),
                'help': 'Control Ansible verbosity level',
                'short': 'v'
            },
            'ansible-args': {
                'help': 'Extra variables for ansible - playbook tool \n'
                        'Should be specified as a list of '
                        'ansible-playbook options, separated with ";". \n'
                        'For example, '
                        '--ansible-args="tags=tagging,overcloud;forks=500"',
                'type': 'AdditionalArgs'
            }
        }
    },
    {
        'title': 'Inventory',
        'options': {
            'inventory': {
                 'help': 'Inventory file',
                 'type': 'Inventory'
            }
        },
    },
    {
        'title': 'Common options',
        'options': {
            'dry-run': {
                'action': 'store_true',
                'help': 'Only generate settings, '
                        'skip the playbook execution stage'
            },
            'extra-vars': {
                'action': 'append',
                'help': 'Extra variables to be merged last',
                'short': 'e',
                'type': 'str'
            },
            'output': {
                'help': 'File to dump the generated '
                        'settings into (default: stdout)',
                'short': 'o',
                'type': 'str'
            }
        },
    },
    {
        'title': 'Answers file',
        'options': {
            'from-file': {
                'action': 'read-answers',
                'help': 'reads arguments from file.'
            },
            'generate-answers-file': {
                'action': 'generate-answers',
                'help': 'generate configuration file with default values'
            }
        },
    }
]

PLUGINS_REGISTRY = {
    'beaker': {
        'src': 'plugins/beaker',
        'desc': 'Provision systems using Beaker',
        'type': 'provision'
    },
    'cloud-config': {
        'src': 'https://github.com/rhos-infra/cloud-config.git',
        'desc': 'Collection of overcloud configuration tasks',
        'type': 'install'
    },
    'collect-logs': {
        'src': 'plugins/collect-logs',
        'desc': 'Collect log from all nodes in the active workspace',
        'type': 'other'
    },
    'pytest-runner': {
        'src': 'plugins/pytest-runner',
        'desc': 'The Pytest runner',
        'type': 'test'
    },
    'foreman': {
        'src': 'plugins/foreman',
        'desc': 'Provision systems using Foreman',
        'type': 'provision'
    },
    'gabbi': {
        'src': 'https://github.com/rhos-infra/gabbi.git',
        'desc': 'The gabbi test runner',
        'type': 'test'
    },
    'list-builds': {
        'src': 'plugins/list-builds',
        'desc': 'Lists all the available puddles',
        'type': 'other'
    },
    'octario': {
        'src': 'https://github.com/redhat-openstack/octario.git',
        'desc': 'Octario test runner',
        'type': 'test'
    },
    'openstack': {
        'src': 'plugins/openstack',
        'desc': 'Provision systems using Ansible OpenStack modules',
        'type': 'provision'
    },
    'ospdui': {
        'src': 'plugins/ospdui',
        'desc': 'The ospdui test runner',
        'type': 'test'
    },
    'packstack': {
        'src': 'plugins/packstack',
        'desc': 'OpenStack installation using Packstack',
        'type': 'install'
    },
    'rally': {
        'src': 'plugins/rally',
        'desc': 'Rally tests runner',
        'type': 'test'
    },
    'tempest': {
        'src': 'plugins/tempest',
        'desc': 'The tempest test runner',
        'type': 'test'
    },
    'tripleo-overcloud': {
        'src': 'plugins/tripleo-overcloud',
        'desc': 'Install TripleO overcloud using a designated undercloud node',
        'type': 'install'
    },
    'tripleo-undercloud': {
        'src': 'plugins/tripleo-undercloud',
        'desc': 'Install TripleO on a designated undercloud node',
        'type': 'install'
    },
    'tripleo-upgrade': {
        'src': 'https://git.openstack.org/openstack/tripleo-upgrade.git',
        'src_path': 'infrared_plugin',
        'desc': 'Upgrade or update TripleO deployment',
        'type': 'install'
    },
    'virsh': {
        'src': 'plugins/virsh',
        'desc': 'Provision virtual machines on a single Hypervisor using libvirt',
        'type': 'provision'
    }
}
