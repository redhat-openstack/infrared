from os import path
from collections import namedtuple

# this import loads ansible.cfg
import ansible.constants

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.utils.display import Display

from cli import exceptions, logger

LOG = logger.LOG

SUPPORTED_ADDITIONAL_ARGS = ['limit', 'subset', 'ask_pass', 'listtags',
                             'become_user', 'sudo',
                             'private_key_file', 'syntax', 'skip_tags', 'diff',
                             'sftp_extra_args', 'check',
                             'force_handlers',
                             'remote_user', 'become_method',
                             'vault_password_file', 'listtasks',
                             'output_file', 'ask_su_pass',
                             'new_vault_password_file',
                             'listhosts', 'ssh_extra_args',
                             'tags', 'become_ask_pass',
                             'start_at_task',
                             'flush_cache', 'step', 'module_path',
                             'su_user', 'ask_sudo_pass',
                             'su', 'scp_extra_args', 'connection',
                             'ask_vault_pass', 'timeout', 'become',
                             'sudo_user', 'ssh_common_args']


def ansible_playbook(config, playbook, verbose=2, settings=None,
                     inventory="local_hosts", additional_args=None):
    """Wraps the 'ansible-playbook' CLI.

     :param config: the infrared configuration
     :param playbook: the playbook to invoke
     :param verbose: Ansible verbosity level
     :param settings: dict with Ansible variables.
     :param inventory: the inventory file to use, default: local_hosts
     :param additional_args: the additional ansible arguments
    """
    if additional_args is None:
        additional_args = {}
    settings = settings or {}
    if verbose is not None:
        verbose = int(verbose)
    LOG.debug("Additional ansible args: {}".format(additional_args))

    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    if not playbook:
        # TODO: remove all IRexceptions and change to regular Python exceptions
        raise exceptions.IRFileNotFoundException

    LOG.info("Executing Playbook: %s" % playbook)

    loader = DataLoader()

    # ------------------ Mocking ansible-playbook cli input ------------------
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
                      'listhosts': None, 'ssh_extra_args': '',
                      'tags': 'all', 'become_ask_pass': False,
                      'start_at_task': None,
                      'flush_cache': None, 'step': None, 'module_path': None,
                      'su_user': None, 'ask_sudo_pass': False,
                      'su': False,
                      'scp_extra_args': '', 'connection': 'smart',
                      'ask_vault_pass': False, 'timeout': 30, 'become': False,
                      'sudo_user': None, 'ssh_common_args': ''}
    module_path = config.get_modules_dir()
    path_to_playbook = path.join(config.get_playbooks_dir(), playbook)

    hacked_options.update(
        module_path=module_path,
        verbosity=verbose,
        forks=ansible.constants.DEFAULT_FORKS,
        remote_user=ansible.constants.DEFAULT_REMOTE_USER,
        private_key_file=ansible.constants.DEFAULT_PRIVATE_KEY_FILE,
    )

    hacked_options.update(additional_args)
    LOG.debug("All ansible options: {}".format(hacked_options))
    options = namedtuple('Options', hacked_options.keys())(**hacked_options)

    passwords = dict(vault_pass='secret')
    variable_manager = VariableManager()
    variable_manager.extra_vars = settings
    inventory = Inventory(loader=loader, variable_manager=variable_manager,
                          host_list=inventory)
    variable_manager.set_inventory(inventory)

    pbex = PlaybookExecutor(playbooks=[path_to_playbook], inventory=inventory,
                            variable_manager=variable_manager, loader=loader,
                            options=options, passwords=passwords)
    results = pbex.run()
    if isinstance(results, int):
        if results:
            raise exceptions.IRPlaybookFailedException(playbook)
    else:
        # print result output, for example in case when listtags is True.
        LOG.warning("Playbook result: {}".format(results))
