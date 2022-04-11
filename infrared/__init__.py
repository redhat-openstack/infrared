# Holds the default variables
import os
from pbr import version as pbr_version
import platform

_v = pbr_version.VersionInfo("infrared").semantic_version()
__version__ = _v.release_string()
version_info = _v.version_tuple()


def version_details():
    from ansible import __version__ as ansible_version  # noqa
    from infrared import __version__  # noqa
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
            },
        }
    },
    {
        'title': 'Common variables',
        'options': {
            'default-pip-versions': {
                'type': 'NestedDict',
                'help': 'Infrared common pip packages versions'
                        ' to be used by all plugins',
                'ansible_variable': 'ir_default_pip_versions',
                'default': r'pyghmi=1.2.16,'
                           r'pytest=4.3.0,'
                           r'pip=19.0.3,'
                           r'setuptools=40.8.0,'
                           r'pbr=5.1.3,'
                           r'requests=2.21.0,'
                           r'six=1.12.0,'
                           r'prettytable=0.7.2,'
                           r'cryptography=2.6.1,'
                           r'rally-openstack=1.3.0,'
                           r'openstacksdk=0.25.0,'
                           r'oslo.utils=3.40.3,'
                           r'oslo.i18n=3.23.1,'
                           r'kubernetes=8.0.1,'
                           r'os-testr=1.0.0,'
                           r'python-subunit=1.3.0,'
                           r'junitxml=0.7,'
                           r'unittest2=1.1.0,'
                           r'nose=1.3.7,'
                           r'Tempest=19.0.0'
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
        'desc': '(deprecated) Collect log from all nodes in the active workspace',
        'type': 'other'
    },
    'ansible-role-collect-logs': {
        'src': 'https://github.com/openstack/ansible-role-collect-logs.git',
        'src_path': 'infrared_plugin',
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
    'patch-components': {
        'src': 'https://github.com/rhos-infra/patch-components.git',
        'desc': 'Package and install OpenStack component from source directory',
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
        'type': 'other',
        'link_roles': 'true'
    },
    'tempest': {
        'src': 'plugins/tempest',
        'desc': 'The tempest test runner',
        'type': 'test'
    },
    'tobiko': {
        'src': 'https://opendev.org/x/tobiko.git',
        'src_path': 'infrared_plugin',
        'desc': 'Deploy and run Tobiko test cases',
        'type': 'test'
    },
    'tripleo-clouds-inventory': {
        'src': 'https://github.com/rhos-infra/tripleo-clouds-inventory.git',
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
        'src': 'https://github.com/openstack/tripleo-upgrade.git',
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
