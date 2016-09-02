import os
import tempfile
import yaml

from ansible.utils.display import Display
from ansible.cli.playbook import PlaybookCLI

from infrared.core.utils import exceptions, logger

LOG = logger.LOG


def ansible_playbook(playbook_path, verbose=2, settings=None,
                     module_path="modules",
                     inventory="local_hosts", additional_args=None):
    """Wraps the 'ansible-playbook' CLI.

     :param playbook_path: the playbook to invoke
     :param verbose: Ansible verbosity level
     :param settings: dict with Ansible variables
     :param module_path: path to the modules folder
     :param inventory: the inventory file to use, default: local_hosts
     :param additional_args: the list of additional arguments to pass to
        the Ansible runner.
    """
    if additional_args is None:
        additional_args = {}
    settings = settings or {}
    additional_args = additional_args or []
    LOG.debug("Additional ansible args: {}".format(additional_args))

    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v' * verbose,
                '--inventory', inventory or 'local_hosts',
                '--module-path', module_path]

    cli_args.extend(additional_args)

    results = _run_playbook(cli_args, settings)

    if results:
        raise exceptions.IRPlaybookFailedException(playbook_path)
    return results


def _run_playbook(cli_args, settings):
    """
    Runs ansible cli.
    :param cli_args: the list  of command line arguments
    :param settings: the settings dictionary
    :return: ansible results
    """
    with tempfile.NamedTemporaryFile(
            prefix="ir-settings-", delete=True) as tmp:
        tmp.write(yaml.safe_dump(settings, default_flow_style=False))
        # make sure ansible can read that file.
        tmp.flush()
        cli_args.extend(['--extra-vars', "@" + tmp.name])
        cli = PlaybookCLI(cli_args)
        LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
        cli.parse()
        return cli.run()