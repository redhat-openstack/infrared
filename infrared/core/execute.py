from datetime import datetime
from distutils.util import strtobool
import errno
import os
import sys
import re
import tempfile

from infrared.core.utils import logger
import yaml

LOG = logger.LOG


class NoAnsiFile(object):

    re_ansi = re.compile(r'\x1b[^m]*m')

    def __init__(self, fd):
        self.fd = fd

    def write(self, data):
        no_ansi_data = self.re_ansi.sub('', data)
        self.fd.write(no_ansi_data)

    def close(self):
        self.fd.close()

    def flush(self):
        self.fd.flush()


def ansible_playbook(ir_workspace, ir_plugin, playbook_path, verbose=None,
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
                '--inventory', ir_workspace.inventory]

    # infrared should not change ansible verbosity unless user specifies that
    if verbose:
        cli_args.append('-' + 'v' * int(verbose))

    cli_args.extend(ansible_args)

    results = _run_playbook(cli_args, vars_dict=extra_vars or {},
                            ir_workspace=ir_workspace, ir_plugin=ir_plugin)

    if results:
        LOG.error('Playbook "%s" failed!' % playbook_path)
    return results


def _run_playbook(cli_args, vars_dict, ir_workspace, ir_plugin):
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
    from ansible.errors import AnsibleOptionsError
    from ansible.errors import AnsibleParserError

    rp, wp = os.pipe()
    process_id = os.fork()

    ansible_outputs_dir = os.path.join(ir_workspace.path, 'ansible_outputs')
    try:
        os.makedirs(ansible_outputs_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Child process
    if not process_id:
        os.close(wp)
        fd_list = []

        try:
            rp = os.fdopen(rp)

            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            filename_template = "ir_{timestamp}_{plugin_name}{postfix}.log"

            if not bool(strtobool(
                    os.environ.get('IR_ANSIBLE_NO_STDOUT', 'no'))):
                fd_list.append(sys.stdout)
            if bool(strtobool(
                    os.environ.get('IR_ANSIBLE_LOG_OUTPUT', 'no'))):
                filename = filename_template.format(
                    timestamp=timestamp, plugin_name=ir_plugin.name, postfix=''
                )
                log_file = os.path.join(ansible_outputs_dir, filename)
                fd_list.append(open(log_file, 'w'))
            if bool(strtobool(
                    os.environ.get('IR_ANSIBLE_LOG_OUTPUT_NO_ANSI', 'no'))):
                filename = filename_template.format(
                    timestamp=timestamp, plugin_name=ir_plugin.name,
                    postfix='_no_ansi'
                )
                log_file = os.path.join(ansible_outputs_dir, filename)
                fd_list.append(NoAnsiFile(open(log_file, 'w')))

            while True:
                stdin_line = rp.readline()
                if not stdin_line:
                    break
                for fd in fd_list:
                    fd.write(stdin_line)
                    fd.flush()

        finally:
            for fd in fd_list:
                fd.close()
            rp.close()

        sys.exit(0)

    # Parent process
    else:
        os.close(rp)
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

                # Saves originals instead of using sys.__stdout__ &
                # sys.__stderr__ in case these got changes at an earlier stage
                org_stdout = sys.stdout
                org_stderr = sys.stderr

                wp = os.fdopen(wp, 'w')
                sys.stdout = wp
                if bool(strtobool(
                        os.environ.get('IR_ANSIBLE_STDERR_TO_STDOUT', 'no'))):
                    sys.stderr = wp

                # Return the result:
                # 0: Success
                # 1: "Error"
                # 2: Host failed
                # 3: Unreachable
                # 4: Parser Error
                # 5: Options error
                # sys.stderr.write('my error')
                return cli.run()

            except (AnsibleParserError, AnsibleOptionsError) as error:
                LOG.error('{}: {}'.format(type(error), error))
                raise error

            finally:
                sys.stdout.flush()
                wp.close()

                sys.stdout = org_stdout
                sys.stderr = org_stderr
