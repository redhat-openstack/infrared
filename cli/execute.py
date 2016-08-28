import tempfile

import os
import yaml
from ansible.cli.playbook import PlaybookCLI
from ansible.utils.display import Display
from cli import exceptions
from cli import logger
from cli import profile_manager

LOG = logger.LOG


def ansible_playbook(config, playbook, verbose=2, settings=None,
                     inventory=None, additional_args=None):
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

    # setup profile
    if config.get_profiles_dir():
        myprofile = profile_manager.ProfileManager.get_active()
        myprofile = myprofile or profile_manager.ProfileManager.create(
            inventory=inventory)
        # Set ansible cfg if exists in cwd or provided via ENV vars. else skip
        local_ansible_cfg = "ansible.cfg"
        myprofile.ansible_cfg = os.environ.get(
            "ANSIBLE_CONFIG",
            local_ansible_cfg if os.path.exists(local_ansible_cfg) else None
        )
        # TODO(yfried): Remove this when Profile becomes mandatory
        inventory = myprofile.inventory
    else:
        LOG.warning("DEPRECATED - Profiles will be mandatory in future "
                    "versions. "
                    "See 'ir-profile' --help for more details")

    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v' * verbose,
                '--inventory', inventory,
                '--module-path', config.get_modules_dir()]

    cli_args.extend(additional_args)

    results = _run_playbook(cli_args, settings)

    # todo(yfried): depracte this
    try:
        os.unlink("hosts")
    except OSError as e:
        if e.errno != 2:
            raise

    # TODO(yfried): Remove this when Profile becomes mandatory
    if config.get_profiles_dir():
        os.symlink(myprofile.inventory, "hosts")

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
