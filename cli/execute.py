import os
import time
import yaml

from ansible.utils.display import Display
from ansible.cli.playbook import PlaybookCLI

from cli import exceptions, logger

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

    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v'*verbose,
                '--inventory', inventory or 'local_hosts',
                '--module-path', config.get_modules_dir()]

    cli_args.extend(additional_args)

    results = _run_playbook(cli_args, playbook_path, settings)

    if results:
        raise exceptions.IRPlaybookFailedException(playbook)
    return results


def _run_playbook(cli_args, playbook, settings):
    """
    Runs ansible cli.
    :param cli_args: the list of command line arguments
    :param playbook: path to the playbook to play
    :param settings: the settings dictionary
    :return: ansible results
    """
    dump_file = 'settings_{}_{}.yml'.format(
        os.path.basename(playbook).split('.')[0],
        time.strftime("%Y%m%d-%H%M%S"))
    output = yaml.safe_dump(settings,
                            default_flow_style=False)
    with open(dump_file, 'w') as output_file:
        output_file.write(output)

    try:
        cli_args.extend(['--extra-vars', "@" + dump_file])
        cli = PlaybookCLI(cli_args)
        LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
        cli.parse()
        return cli.run()
    finally:
        if os.path.exists(dump_file):
            os.remove(dump_file)
