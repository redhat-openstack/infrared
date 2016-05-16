import sys
import pytest
from cli import main, conf


class IRMock(object):
    """
    The mock wrapper for the IRSec classes.
    """
    IR_ROOT = 'ir'
    IR_CONFIG = 'infrared.cfg'
    IR_SETTINGS = 'settings'
    IR_PLAYBOOKS = 'playbooks'
    IR_APP_NAME = 'appmock'
    IR_SUB_COMMAND = 'cmdmock'

    def __init__(self, mock_roots, monkeypatch):

        self.ir_conf_file = mock_roots['irconfig']
        self.config = conf.ConfigWrapper.load_config_file(
            self.ir_conf_file.strpath)
        self._monkeypatch = monkeypatch
        self.spec_app = None

    def run(self, spec_args=None):
        """
        The function to run spec.
        """

        if spec_args is None:
            spec_args = []
        argv = ['appmock', 'cmdmock'] + spec_args

        # replace argument by what we want
        self._monkeypatch.setattr(sys, 'argv', argv)
        spec_app = main.IRFactory.create('appmock', self.config)
        if spec_app:
            spec_app.run()

        self.spec_app = spec_app


@pytest.fixture
def mock_roots(tmpdir):
    root = tmpdir.mkdir(IRMock.IR_ROOT)
    settings = root.mkdir(IRMock.IR_SETTINGS)
    playbooks = root.mkdir(IRMock.IR_PLAYBOOKS)
    cfg_file = root.join(IRMock.IR_CONFIG)
    cfg_file.write("""
[defaults]
settings  = {0}
modules   = library
roles     = roles
playbooks = {1}

[appmock]
cleanup_playbook=cleanup.yml
main_playbook=appmock.yml

""".format(settings.strpath,
           playbooks.strpath))
    return dict(settings=settings,
                playbooks=playbooks,
                irconfig=cfg_file)


@pytest.fixture
def mock_settings(mock_roots):
    """
    Creates the test settings structure.
    """
    app_dir = mock_roots['settings'].mkdir(IRMock.IR_APP_NAME)
    base_spec_file = app_dir.join('base.spec')
    app_spec_dir = app_dir.mkdir(IRMock.IR_SUB_COMMAND)
    spec_file = app_spec_dir.join(IRMock.IR_SUB_COMMAND + ".spec")
    spec_yml_file = app_spec_dir.join(IRMock.IR_SUB_COMMAND + ".yml")
    image_file = app_spec_dir.mkdir('image').join('default.yml')

    base_spec_file.write("""---
shared_groups:
    - title: common
      options:
          verbose:
              help: 'Control Ansible verbosity level'
              short: v
              action: count
              default: 0
          inventory:
              help: 'Inventory file'
              type: str
              default: local_hosts
          debug:
              help: 'Run InfraRed in DEBUG mode'
              short: d
              action: store_true

""")

    spec_file.write("""---
subparsers:
    cmdmock:
        include_groups: ['common']
        groups:
          - title: test args
            options:
                image:
                    type: YamlFile
                    help: test_file
                    default: default.yml
                opt:
                    type: Value
                    help: optional value
                req:
                    type: Value
                    help: required value
                    required: yes
                choice:
                    type: Value
                    help: list of predefined value
                    choices: ["1", "2", "3"]
                    default: 2
                from-file:
                    action: read-config
                    help: reads arguments from file.
                generate-conf-file:
                    action: generate-config
                    help: generate configuration file with default values
                output:
                    short: o
                    help: 'File to dump the generated settings into'

          - title: require when test args
            options:
                images-task:
                    type: Value
                    choices: [import, build, rpm]
                    default: rpm
                images-url:
                    type: Value
                    required_when: "images-task == import"

          - title: silent test args
            options:
                do-silent:
                    action: store_true
                    silent:
                       - req

          - title: priority test args
            options:
                priority_p1:
                    type: Value
                priority_p2:
                    type: Value
                priority_p3:
                    type: Value

          - title: nested test args
            options:
                nested_arg1:
                    type: Value
                    default: defvalue1
                nested_arg2:
                    type: Value
                control_arg1:
                    type: str

""")
    image_file.write("""---
image_file: file.qcow
image_size: 555
""")

    spec_yml_file.write("""---
appmock: {}
""")


@pytest.fixture
def mock_playbooks(mock_roots):
    # create simple playbooks
    main_playbook = mock_roots['playbooks'].join(
        IRMock.IR_APP_NAME + '.yml')
    main_playbook.write("""---
- name: Ping localhost
  hosts: localhost
  gather_facts: no
  tasks:
    - ping:

""")
    return dict(main_playbook=main_playbook)


@pytest.fixture
def mock_spec(mock_roots, mock_settings, mock_playbooks, monkeypatch):
    """
    Main function to get a mock spec.

    Returns a function which will run mock.
    """
    return IRMock(mock_roots, monkeypatch)
