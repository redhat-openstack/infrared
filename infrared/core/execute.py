import tempfile

import yaml
from ansible.utils.display import Display
from ansible.cli.playbook import PlaybookCLI

from infrared.core.utils import logger

LOG = logger.LOG


def ansible_playbook(inventory, playbook_path, verbose=2,
                     extra_vars=None, ansible_args=None):
    """Wraps the 'ansible-playbook' CLI.

     :param inventory: inventory file to use.
     :param playbook_path: the playbook to invoke
     :param verbose: Ansible verbosity level
     :param extra_vars: dict. Passed to Ansible as extra-vars
     :param ansible_args: dict of ansible-playbook arguments to plumb down
         directly to Ansible.
    """
    ansible_args = ansible_args or []
    LOG.debug("Additional ansible args: {}".format(ansible_args))

    # hack for verbosity
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    # TODO(yfried): Use proper ansible API instead of emulating CLI
    cli_args = ['execute',
                playbook_path,
                "-v" if not verbose else '-' + 'v' * verbose,
                '--inventory', inventory]
    cli_args.extend(ansible_args)

    results = _run_playbook(cli_args,
                            vars_dict=extra_vars or {})

    if results:
        LOG.error('Playbook "%s" failed!' % playbook_path)
    return results


def _run_playbook(cli_args, vars_dict):
    """Runs ansible cli with vars dict

    :param vars_dict: dict, Will be passed as Ansible extra-vars
    :param cli_args: the list  of command line arguments
    :return: ansible results
    """

    # TODO(yfried): use ansible vars object instead of tmpfile
    with tempfile.NamedTemporaryFile(
            prefix="ir-settings-", delete=True) as tmp:
        tmp.write(yaml.safe_dump(vars_dict, default_flow_style=False))
        # make sure created file is readable.
        tmp.flush()
        cli_args.extend(['--extra-vars', "@" + tmp.name])
        cli = PlaybookCLI(cli_args)
        LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
        cli.parse()
        return cli.run()
