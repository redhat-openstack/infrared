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
        self.config = conf.load_config_file(self.ir_conf_file.strpath)
        self._monkeypatch = monkeypatch

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
groups:
    - name: common
      options:
          - name: verbose
            help: 'Control Ansible verbosity level'
            short: v
            action: count
            default: 0
          - name: inventory
            help: 'Inventory file'
            type: str
            default: local_hosts
          - name: debug
            help: 'Run InfraRed in DEBUG mode'
            short: d
            action: store_true
""")

    spec_file.write("""---
command:
    subcommands:
        - name: cmdmock
          include_groups: ['common']
          groups:
              - name: test args
                options:
                     - name: image
                       complex_type: YamlFile
                       help: test_file
                       default: default.yml
                     - name: opt
                       help: optional value
                     - name: req
                       help: required value
                       required: yes
                     - name: choice
                       help: list of predefined value
                       choices: ["1", "2", "3"]
                       default: 2
                     - name: from-file
                       action: read-config
                       help: reads arguments from file.
                     - name: generate-conf-file
                       action: generate-config
                       help: generate configuration file with default values
                     - name: output
                       type: str
                       short: o
                       help: 'File to dump the generated settings into'
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
