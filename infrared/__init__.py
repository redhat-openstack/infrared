# Holds the default variables

SHARED_GROUPS = [
    {
        'title': 'Debug Options',
        'options': {
            'debug': {
                'action': 'store_true',
                'help': 'Run InfraRed in DEBUG mode',
                'short': 'd'
            }
        }
    },
    {
        'title': 'Ansible options',
        'options': {
            'verbose': {
                'action': 'count',
                'default': 0,
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
            'input': {
                'action': 'append',
                'help': 'Input settings file to be loaded '
                        'before the merging of user args',
                'short': 'i',
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
