# Holds the default variables
from pbr import version as pbr_version
import platform
import os

_v = pbr_version.VersionInfo("infrared").semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()


def version_details():
    from infrared import __version__  # noqa
    from ansible import __version__ as ansible_version  # noqa
    python_version = platform.python_version()
    python_revision = ', '.join(platform.python_build())
    return "{__version__} (" \
        "ansible-{ansible_version}, " \
        "python-{python_version})".format(**locals())

__all__ = (
    '__version__',   # string, standard across most modules
    'version_info',  # version tuple, same format as python sys.version_info
    'version_details'  # detailed version information, which may include major deps or plugins, used for bug reporting
)

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
        'src': 'https://github.com/pinikomarov/cloud-config.git',
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
    'reportportal': {
        'src': 'https://github.com/rhos-infra/reportportal.git',
        'src_path': 'infrared_plugin',
        'desc': 'Ansible role for sending XUnit test results to ReportPortal',
        'type': 'other'
    },
    'tempest': {
        'src': 'plugins/tempest',
        'desc': 'The tempest test runner',
        'type': 'test'
    },
    'tripleo-inventory': {
        'src': 'https://github.com/rhos-infra/tripleo-inventory.git',
        'src_path': 'infrared_plugin',
        'desc': 'Generates Tripleo inventory',
        'type': 'other'
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
    'tripleo-standalone': {
        'src': 'plugins/tripleo-standalone',
        'desc': 'Install TripleO overcloud in standalone mode',
        'type': 'install'
    },
    'tripleo-upgrade': {
        'src': 'https://github.com/pinikomarov/tripleo-upgrade.git',
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
