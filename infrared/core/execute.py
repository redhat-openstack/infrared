from ansible.utils.display import Display
from ansible.cli.playbook import PlaybookCLI

from infrared.core.utils import logger

LOG = logger.LOG


def ansible_playbook(inventory, playbook_path, verbose=2):
    """Wraps the 'ansible-playbook' CLI.

     :param inventory: inventory file to use.
     :param playbook_path: the playbook to invoke
     :param verbose: Ansible verbosity level
    """
    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v' * verbose,
                '--inventory', inventory]

    results = _run_playbook(cli_args)

    if results:
        LOG.error('Playbook "%s" failed!' % playbook_path)
    return results


def _run_playbook(cli_args):
    """
    Runs ansible cli.
    :param cli_args: the list  of command line arguments
    :return: ansible results
    """
    cli = PlaybookCLI(cli_args)
    LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
    cli.parse()
    return cli.run()
