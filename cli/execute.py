from os import path

from collections import namedtuple
import ansible.constants
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
# from ansible.playbook.play_context import PlayContext
from ansible.utils.vars import load_extra_vars
from ansible.utils.display import Display

from cli import conf, exceptions, logger

LOG = logger.LOG
CONF = conf.config

VERBOSITY = 0
HOSTS_FILE = "hosts"
PLAYBOOKS = ["provision", "install", "test", "collect-logs", "cleanup"]

assert "playbooks" == path.basename(
    CONF.get('defaults', 'playbooks')), "Bad path to playbooks"


def ansible_playbook(playbook, args, inventory="local_hosts"):
    """
    Wraps the 'ansible-playbook' CLI.
     :playbook: the playbook to invoke
     :args: all arguments passed for the playbook
     :inventory: the inventory file to use, default: local_hosts
    """
    verbosity = args["verbose"]
    display = Display(verbosity=verbosity)
    import __main__ as main
    setattr(main, "display", display)

    if not playbook:
        LOG.error("No playbook to execute (%s)" % PLAYBOOKS)

        # TODO: remove all IRexceptions and change to regular Python exceptions
        raise exceptions.IRFileNotFoundException

    LOG.info("Executing Playbook: %s" % playbook)

    variable_manager = VariableManager()
    loader = DataLoader()

    #### Mocking ansible-playbook cli input ####
    # These values were extracted from ansible-playbook runtime.
    # todo(yfried): decide which options are hardcoded and which should be
    # exposed to user
    hacked_options = {'subset': None, 'ask_pass': False, 'listtags': None,
                      'become_user': 'root', 'sudo': False,
                      'private_key_file': None,
                      'syntax': None, 'skip_tags': None, 'diff': False,
                      'sftp_extra_args': '', 'check': False,
                      'force_handlers': False,
                      'remote_user': None, 'become_method': 'sudo',
                      'vault_password_file': None, 'listtasks': None,
                      'output_file': None, 'ask_su_pass': False,
                      'new_vault_password_file': None,
                      'inventory': 'local_hosts',
                      'forks': 5, 'listhosts': None, 'ssh_extra_args': '',
                      'tags': 'all', 'become_ask_pass': False,
                      'start_at_task': None,
                      'flush_cache': None, 'step': None, 'module_path': None,
                      'su_user': None, 'ask_sudo_pass': False,
                      'su': False,
                      'scp_extra_args': '', 'connection': 'smart',
                      'ask_vault_pass': False, 'timeout': 30, 'become': False,
                      'sudo_user': None, 'ssh_common_args': ''}


    module_path = CONF.get('defaults', 'modules')
    path_to_playbook = path.join(CONF.get('defaults', 'playbooks'), playbook)

    hacked_options.update(
        module_path=module_path,
        verbosity=verbosity,
        forks=ansible.constants.DEFAULT_FORKS,
        remote_user=ansible.constants.DEFAULT_REMOTE_USER,
        private_key_file=ansible.constants.DEFAULT_PRIVATE_KEY_FILE,

    )
    options = namedtuple('Options', hacked_options.keys())(**hacked_options)

    passwords = dict(vault_pass='secret')
    inventory = Inventory(loader=loader, variable_manager=variable_manager,
                          host_list=inventory)
    variable_manager.set_inventory(inventory)

    loader = DataLoader()

    variable_manager = VariableManager()
    variable_manager.extra_vars = args["settings"]
    pbex = PlaybookExecutor(playbooks=[path_to_playbook], inventory=inventory,
                            variable_manager=variable_manager, loader=loader,
                            options=options, passwords=passwords)
    results = pbex.run()
    pass

