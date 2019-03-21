import tempfile

import yaml
from infrared.core.utils import logger

LOG = logger.LOG


def ansible_playbook(inventory, playbook_path, verbose=None,
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
    from ansible.utils.display import Display
    display = Display(verbosity=verbose)
    import __main__ as main
    setattr(main, "display", display)

    # TODO(yfried): Use proper ansible API instead of emulating CLI
    cli_args = ['execute',
                playbook_path,
                '--inventory', inventory]

    # infrared should not change ansible verbosity unless user specifies that
    if verbose:
        cli_args.append('-' + 'v' * int(verbose))

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
    # NOTE(oanufrii): !!!this import should be exactly here!!!
    #                 Ansible uses 'display' singleton from '__main__' and
    #                 gets it on module level. While we monkeypatching our
    #                 '__main__' in 'ansible_playbook' function import of
    #                 PlaybookCLI shoul be after that, to get patched
    #                 '__main__'. Otherwise ansible gets unpatched '__main__'
    #                 and creates new 'display' object with default (0)
    #                 verbosity.
    from ansible.cli.playbook import PlaybookCLI
    from ansible.errors import AnsibleOptionsError, AnsibleError
    with tempfile.NamedTemporaryFile(
            mode='w+', prefix="ir-settings-", delete=True) as tmp:
        tmp.write(yaml.safe_dump(vars_dict, default_flow_style=False))
        # make sure created file is readable.
        tmp.flush()
        cli_args.extend(['--extra-vars', "@" + tmp.name])
        cli = PlaybookCLI(cli_args)
        LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
        try:
            cli.parse()
            # Return the result:
            # 0: Success
            # 1: "Error"
            # 2: Host failed
            # 3: Unreachable
            # 4: Parser Error
            # 5: Options error
            return cli.run()
        except (AnsibleParserError, AnsibleOptionsError) as error:
            LOG.error('{}: {}'.format(type(error), error))
            raise error
