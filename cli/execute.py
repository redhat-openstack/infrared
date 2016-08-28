import os
import tempfile
import yaml

from ansible.utils.display import Display
from ansible.cli.playbook import PlaybookCLI

from cli import exceptions
from cli import logger
from cli import workspace

LOG = logger.LOG


def ansible_playbook(config, playbook, verbose=2, settings=None,
                     inventory="local_hosts", additional_args=None):
    """Wraps the 'ansible-playbook' CLI.

     :param config: the infrared configuration
     :param playbook: the playbook to invoke
     :param verbose: Ansible verbosity level
     :param settings: dict with Ansible variables.
     :param inventory: the inventory file to use, default: local_hosts
     :param additional_args: the list of additional arguments to pass to
        the Ansible runner.
    """
    if additional_args is None:
        additional_args = {}
    settings = settings or {}
    additional_args = additional_args or []
    playbook_path = os.path.join(config.get_playbooks_dir(), playbook)
    LOG.debug("Additional ansible args: {}".format(additional_args))

    myworkspace = workspace.WorkspaceManager.get(inventory=inventory)

    # with myworkspace.activate():
    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v' * verbose,
                '--inventory', myworkspace.inventory,
                '--module-path', config.get_modules_dir()]

    cli_args.extend(additional_args)

        results = _run_playbook(cli_args, settings)

    if results:
        raise exceptions.IRPlaybookFailedException(playbook)
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
