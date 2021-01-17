from datetime import datetime
from distutils.util import strtobool
import errno
import json
import os
import re
import sys
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


class IRStdFd(object):
    pass


class IRStdoutFd(IRStdFd):

    def __init__(self, print_stdout=True):
        self.print_stdout = print_stdout
        self.org_stdout = sys.stdout
        sys.stdout = self

    def write(self, data):
        if self.print_stdout:
            sys.__stdout__.write(data)
            sys.__stdout__.flush()
        for fd in IRSTDFDManager.fds:
            if not isinstance(fd, IRStdFd):
                fd.write(data)
                fd.flush()

    @staticmethod
    def flush():
        sys.__stdout__.flush()

    @staticmethod
    def close():
        sys.stdout = sys.__stdout__


class IRStderrFd(IRStdFd):

    def __init__(self, print_stderr=True):
        self.print_stderr = print_stderr
        self.org_stderr = sys.stderr
        sys.stderr = self

    def write(self, data):
        if self.print_stderr:
            sys.__stderr__.write(data)
            sys.__stderr__.flush()
        for fd in IRSTDFDManager.fds:
            if not isinstance(fd, IRStdFd):
                fd.write(data)
                fd.flush()

    @staticmethod
    def flush():
        sys.__stderr__.flush()

    @staticmethod
    def close():
        sys.stderr = sys.__stderr__


class IRSTDFDManager(object):

    fds = set()

    def __init__(self, stdout=True, stderr=True, *fds):

        self.stdout = stdout
        self.stderr = stderr

        for fd in fds:
            self.add(fd)

        self.add(IRStdoutFd(print_stdout=self.stdout))
        self.add(IRStderrFd(print_stderr=self.stderr))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def write(self, data):
        for fd in self.fds:
            fd.write(data)
            fd.flush()

    def flush(self):
        for fd in self.fds:
            fd.flush()

    def close(self):
        for fd in self.fds:
            fd.close()

    def add(self, fd):
        self.fds.add(fd)


def ansible_playbook(ir_workspace, ir_plugin, playbook_path, verbose=None,
                     extra_vars=None, ansible_args=None):
    """Wraps the 'ansible-playbook' CLI.

     :param ir_workspace: An Infrared Workspace object represents the active
     workspace
     :param ir_plugin: An InfraredPlugin object of the current plugin
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
    :param ir_workspace: An Infrared Workspace object represents the active
     workspace
    :param ir_plugin: An InfraredPlugin object of the current plugin
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
    # NOTE(afazekas): GlobalCLIArgs gets value only once per invocation, but
    # since it has singleton decorator, so it would remember to old arguments in different tests
    # removing the singleton decorator
    try:
        from ansible.utils import context_objects
        context_objects.GlobalCLIArgs = context_objects.CLIArgs
    except ImportError:
        # older version
        pass

    from ansible.cli.playbook import PlaybookCLI
    from ansible.errors import AnsibleOptionsError
    from ansible.errors import AnsibleParserError

    with tempfile.NamedTemporaryFile(
            mode='w+', prefix="ir-settings-", delete=True) as tmp:
        tmp.write(yaml.safe_dump(vars_dict, default_flow_style=False))
        # make sure created file is readable.
        tmp.flush()
        cli_args.extend(['--extra-vars', "@" + tmp.name])

        if not bool(strtobool(os.environ.get('IR_NO_EXTRAS', 'no'))):
            ir_extras = {
                'infrared': {
                    'python': {
                        'executable': sys.executable,
                        'version': {
                            'full': sys.version.split()[0],
                            'major': sys.version_info.major,
                            'minor': sys.version_info.minor,
                            'micro': sys.version_info.micro,
                        }
                    }
                }
            }
            cli_args.extend(['--extra-vars', str(ir_extras)])

        cli = PlaybookCLI(cli_args)
        LOG.debug('Starting ansible cli with args: {}'.format(cli_args[1:]))
        try:
            cli.parse()

            stdout = not bool(
                strtobool(os.environ.get('IR_ANSIBLE_NO_STDOUT', 'no')))
            stderr = not bool(
                strtobool(os.environ.get('IR_ANSIBLE_NO_STDERR', 'no')))

            ansible_outputs_dir = \
                os.path.join(ir_workspace.path, 'ansible_outputs')
            ansible_vars_dir = \
                os.path.join(ir_workspace.path, 'ansible_vars')

            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S.%f")
            filename_template = \
                "ir_{timestamp}_{plugin_name}{postfix}.{file_ext}"

            for _dir in (ansible_outputs_dir, ansible_vars_dir):
                try:
                    os.makedirs(_dir)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise

            if bool(strtobool(os.environ.get('IR_GEN_VARS_JSON', 'no'))):
                filename = filename_template.format(
                    timestamp=timestamp,
                    plugin_name=ir_plugin.name,
                    postfix='',
                    file_ext='json'
                )
                vars_file = os.path.join(ansible_vars_dir, filename)
                with open(vars_file, 'w') as fp:
                    json.dump(vars_dict, fp, indent=4, sort_keys=True)

            with IRSTDFDManager(stdout=stdout, stderr=stderr) as fd_manager:

                if bool(strtobool(os.environ.get(
                        'IR_ANSIBLE_LOG_OUTPUT', 'no'))):
                    filename = filename_template.format(
                        timestamp=timestamp,
                        plugin_name=ir_plugin.name,
                        postfix='',
                        file_ext='log'
                    )
                    log_file = os.path.join(ansible_outputs_dir, filename)
                    fd_manager.add(open(log_file, 'w'))

                if bool(strtobool(os.environ.get(
                        'IR_ANSIBLE_LOG_OUTPUT_NO_ANSI', 'no'))):
                    filename = filename_template.format(
                        timestamp=timestamp,
                        plugin_name=ir_plugin.name,
                        postfix='_no_ansi',
                        file_ext='log'
                    )
                    log_file = os.path.join(ansible_outputs_dir, filename)
                    fd_manager.add(NoAnsiFile(open(log_file, 'w')))

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
