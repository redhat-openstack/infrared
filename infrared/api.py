# provides API to run plugins
import logging

import abc
import yaml

import bash_completers as completers
from infrared import SHARED_GROUPS, plugins_registry
from infrared.core import execute
from infrared.core.inspector.inspector import SpecParser
from infrared.core.services import CoreServices  # noqa
from infrared.core.settings import VarsDictManager
from infrared.core.utils import exceptions  # noqa
from infrared.core.utils import interactive_ssh  # noqa
from infrared.core.utils import logger  # noqa
from infrared.core.utils.print_formats import fancy_table  # noqa

LOG = logger.LOG


class SpecObject(object):
    """
    Base object to describe basic specification.
    """

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def get_name(self):
        return self.name

    @abc.abstractmethod
    def extend_cli(self, subparser):
        """Adds the spec cli options to to the main entry point.

        :param subparser: the subparser object to extend.
        """

    @abc.abstractmethod
    def spec_handler(self, parser, args):
        """
        The main method for the spec.

        This method will be called by the spec managers once the subcommand
        with the spec name is called from cli.
        :param parser: argparse object
        :param args: dict, input arguments as parsed by the parser.
        :return: exit code to be propagated out.
        """


class InfraredPluginsSpec(SpecObject):
    """Adds Plugin object as subparser to ``infrared`` commnad. """

    add_base_groups = True

    def __init__(self, plugin, *args, **kwargs):
        """Initialize Plugin spec

        :param plugin: plugin object
        """
        self.plugin = plugin
        self.specification = None
        super(InfraredPluginsSpec, self).__init__(plugin.name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        """Extend CLI with plugin subparser. """

        user_dict = {}
        if self.add_base_groups:
            user_dict = dict(shared_groups=SHARED_GROUPS)

        self.specification = SpecParser.from_plugin(
            subparser=root_subparsers,
            plugin=self.plugin,
            base_groups=user_dict)

    def spec_handler(self, parser, args):
        """Execute plugin's main playbook.

        if "--generate-answers-file":
            only generate answers file
        if "--dry-run":
            only generate vars dict
        else:
            run Ansible with vars dict as input
        if "-o":
            write vars dict to file

        :param parser: argparse object
        :param args: dict, input arguments as parsed by the parser.
        :return:
            * Ansible exit code if ansible is executed.
            * None if "--generate-answers-file" or "--dry-run" answers file is
              generated
        """
        workspace_manager = CoreServices.workspace_manager()

        active_workspace = workspace_manager.get_active_workspace()
        if not active_workspace:
            active_workspace = workspace_manager.create()
            workspace_manager.activate(active_workspace.name)
            LOG.warn("There are no workspaces. New workspace added: %s",
                     active_workspace.name)

        # TODO(yfried): when accepting inventory from CLI, need to update:
        # workspace.inventory = CLI[inventory]

        if self.specification is None:
            # FIXME(yfried): Create a proper exception type
            raise Exception("Unable to create specification "
                            "for '{}' plugin. Check plugin "
                            "config and settings folders".format(self.name))
        parsed_args = self.specification.parse_args(parser, args)
        if parsed_args is None:
            return None

        # unpack parsed arguments
        nested_args, control_args = parsed_args

        if control_args.get('debug', None):
            logger.LOG.setLevel(logging.DEBUG)

        vars_dict = VarsDictManager.generate_settings(
            # TODO(yfried): consider whether to use type (for legacy) or name
            self.plugin.config["plugin_type"],
            nested_args,
        )

        VarsDictManager.merge_extra_vars(vars_dict,
                                         control_args.get('extra-vars'))

        LOG.debug("Dumping vars dict...")
        vars_yaml = yaml.safe_dump(vars_dict,
                                   default_flow_style=False)
        output_filename = control_args.get("output")
        if output_filename:
            LOG.debug("Output file: {}".format(output_filename))
            with open(output_filename, 'w') as output_file:
                output_file.write(vars_yaml)
        else:
            print(vars_yaml)
        if control_args.get("dry-run"):
            return None

        result = execute.ansible_playbook(
            inventory=active_workspace.inventory,
            playbook_path=self.plugin.playbook,
            verbose=control_args.get('verbose', None),
            extra_vars=vars_dict,
            ansible_args=control_args.get('ansible-args', None))
        return result


class WorkspaceManagerSpec(SpecObject):
    """The workspace manager CLI. """

    def __init__(self, name, *args, **kwargs):
        super(WorkspaceManagerSpec, self).__init__(name, **kwargs)
        self.workspace_manager = CoreServices.workspace_manager()

    def extend_cli(self, root_subparsers):
        workspace_plugin = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)
        workspace_subparsers = workspace_plugin.add_subparsers(dest="command0")

        # create
        create_parser = workspace_subparsers.add_parser(
            'create', help='Creates a new workspace')
        create_parser.add_argument("name", help="Workspace name")

        # checkout
        checkout_parser = workspace_subparsers.add_parser(
            'checkout',
            help='Creates a workspace if it is not presents and '
                 'switches to it')
        checkout_parser.add_argument(
            "name",
            help="Workspace name").completer = completers.workspace_list

        # inventory
        inventory_parser = workspace_subparsers.add_parser(
            'inventory',
            help="prints workspace's inventory file")
        inventory_parser.add_argument(
            "name", help="Workspace name",
            nargs="?").completer = completers.workspace_list

        # list
        wrkspc_list_parser = workspace_subparsers.add_parser(
            'list', help='Lists all the workspaces')
        wrkspc_list_parser.add_argument(
            "--active", action='store_true', dest='print_active',
            help="Prints the active workspace only")

        # delete
        delete_parser = workspace_subparsers.add_parser(
            'delete', help='Deletes workspaces')
        delete_parser.add_argument(
            'name', nargs='+',
            help="Workspace names").completer = completers.workspace_list

        # cleanup
        cleanup_parser = workspace_subparsers.add_parser(
            'cleanup', help='Removes all the files from workspace')
        cleanup_parser.add_argument(
            "name",
            help="Workspace name").completer = completers.workspace_list

        # import settings
        importer_parser = workspace_subparsers.add_parser(
            'import', help='Import deployment configs.')
        importer_parser.add_argument("filename", help="Archive file name.")
        importer_parser.add_argument(
            "-n", "--name", dest="workspacename",
            help="Workspace name to import with. "
            "If not specified - file name will be used.")

        # exort settings
        exporter_parser = workspace_subparsers.add_parser(
            'export', help='Export deployment configurations.')
        exporter_parser.add_argument(
            "-n", "--name", dest="workspacename",
            help="Workspace name. If not sepecified - active "
            "workspace will be used.").completer = completers.workspace_list
        exporter_parser.add_argument("-f", "--filename", dest="filename",
                                     help="Archive file name.")

        exporter_parser.add_argument("-K", "--copy-keys", dest="copykeys",
                                     action="store_true",
                                     help="Silently copy ssh keys "
                                     "to workspace.")
        # node list
        nodelist_parser = workspace_subparsers.add_parser(
            'node-list',
            help='List nodes, managed by workspace')
        nodelist_parser.add_argument(
            "-n", "--name",
            help="Workspace name").completer = completers.workspace_list
        nodelist_parser.add_argument(
            "-g", "--group",
            help="List nodes in specific group"
            ).completer = completers.group_list

        # group list
        grouplist_parser = workspace_subparsers.add_parser(
            'group-list',
            help='List groups, managed by workspace')
        grouplist_parser.add_argument(
            "-n", "--name",
            help="Workspace name").completer = completers.workspace_list

    def spec_handler(self, parser, args):
        """
        Handles all the plugin manager commands
        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'create':
            self._create_workspace(pargs.name)
        elif subcommand == 'checkout':
            self._checkout_workspace(pargs.name)
        elif subcommand == 'inventory':
            self._fetch_inventory(pargs.name)
        elif subcommand == 'list':
            if pargs.print_active:
                print self.workspace_manager.get_active_workspace().name
            else:
                workspaces = self.workspace_manager.list()
                headers = ("Name", "Active")
                workspaces = sorted([workspace.name for workspace in
                                     self.workspace_manager.list()])
                print fancy_table(
                    headers,
                    *[(workspace, ' ' * (len(headers[-1]) / 2) + "*" if
                        self.workspace_manager.is_active(workspace) else "")
                      for workspace in workspaces])
        elif subcommand == 'delete':
            for workspace_name in pargs.name:
                self.workspace_manager.delete(workspace_name)
                print("Workspace '{}' deleted".format(workspace_name))
        elif subcommand == 'cleanup':
            self.workspace_manager.cleanup(pargs.name)
        elif subcommand == 'export':
            self.workspace_manager.export_workspace(
                pargs.workspacename, pargs.filename, pargs.copykeys)
        elif subcommand == 'import':
            self.workspace_manager.import_workspace(
                pargs.filename, pargs.workspacename)
        elif subcommand == 'node-list':
            nodes = self.workspace_manager.node_list(pargs.name, pargs.group)
            print fancy_table(
                ("Name", "Address", "Groups"),
                *[node_name for node_name in nodes])
        elif subcommand == "group-list":
            groups = self.workspace_manager.group_list(pargs.name)
            print fancy_table(
                ("Name", "Nodes"), *[group_name for group_name in groups])

    # deprecated method
    def _create_workspace(self, name):
        """Creates a workspace """

        self._checkout_workspace(name)

    def _checkout_workspace(self, name):
        """Checkouts (create+activate) a workspace """

        if not self.workspace_manager.has_workspace(name):
            self.workspace_manager.create(name)
            print("Workspace '{}' added".format(name))
        self.workspace_manager.activate(name)
        print("Now using workspace: '{}'".format(name))

    def _fetch_inventory(self, name):
        """fetch inventory file for workspace.

        if no active workspace found - create a new workspace
        """
        if name:
            wkspc = self.workspace_manager.get(name)
        else:
            wkspc = self.workspace_manager.get_active_workspace()
        if not wkspc:
            raise exceptions.IRNoActiveWorkspaceFound()
        print wkspc.inventory


class PluginManagerSpec(SpecObject):

    def __init__(self, name, *args, **kwargs):
        super(PluginManagerSpec, self).__init__(name, *args, **kwargs)
        self.plugin_manager = CoreServices.plugins_manager()

    def extend_cli(self, root_subparsers):
        plugin_parser = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)
        plugin_subparsers = plugin_parser.add_subparsers(dest="command0")

        # Add plugin
        add_parser = plugin_subparsers.add_parser(
            'add', help='Add a plugin')
        add_parser.add_argument("src",
                                help="Plugin Source (name/path/git URL)\n'all'"
                                     " will install all available plugins")
        add_parser.add_argument("--revision", help="git branch/tag/revision"
                                " sourced plugins. Ingnored for"
                                "'plugin add all' command.")
        add_parser.add_argument("--dest", help="Destination directory to "
                                "clone plugin under, in case of Git URL is "
                                "provided as path")

        # Remove plugin
        remove_parser = plugin_subparsers.add_parser(
            "remove",
            help="Remove a plugin, 'all' will remove all installed plugins")
        remove_parser.add_argument(
            "name",
            help="Plugin name").completer = completers.plugin_list

        # List command
        list_parser = plugin_subparsers.add_parser(
            'list', help='List all the available plugins')
        list_parser.add_argument(
            "--available", action='store_true',
            help="Prints all available plugins in addition "
                 "to installed plugins")

        # Update plugin
        update_parser = plugin_subparsers.add_parser(
            "update",
            help="Update a Git-based plugin")
        update_parser.add_argument(
            "name",
            help="Name of the plugin to update")
        update_parser.add_argument(
            "revision", nargs='?', default='latest',
            help="Revision number to checkout (if not given, will only pull "
                 "changes from the remote)")
        update_parser.add_argument(
            '--skip_reqs', '-s', action='store_true',
            help="Skips plugin's requirements installation")
        update_parser.add_argument(
            '--hard-reset', action='store_true',
            help="Drop all local changes using hard "
                 "reset (changes will be stashed")

        plugin_subparsers.add_parser(
            "freeze", help="Run through installed plugins. For git sourced "
            "one writes its current revision to plugins registry.")

        # search all plugins from github organization
        plugin_subparsers.add_parser(
            'search', help='Search and list all the available plugins from '
            "rhos-infra organization on GitHub")

    def spec_handler(self, parser, args):
        """Handles all the plugin manager commands

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'list':
            self._list_plugins(pargs.available)
        elif subcommand == 'add':
            if pargs.src == 'all':
                self.plugin_manager.add_all_available()
                self._list_plugins(print_available=False)
            else:
                self.plugin_manager.add_plugin(pargs.src, rev=pargs.revision,
                                               dest=pargs.dest)
        elif subcommand == 'remove':
            if pargs.name == 'all':
                self.plugin_manager.remove_all()
                self._list_plugins(print_available=False)
            else:
                self.plugin_manager.remove_plugin(pargs.name)
        elif subcommand == 'freeze':
            self.plugin_manager.freeze()
        elif subcommand == 'update':
            self.plugin_manager.update_plugin(
                pargs.name, pargs.revision, pargs.skip_reqs, pargs.hard_reset)
        elif subcommand == 'search':
            self._search_plugins()

    def _list_plugins(self, print_available=False):
        """Print a list of installed & available plugins"""
        table_rows = []
        table_headers = ["Type", "Name"]
        installed_mark = ' ' * (len('Installed') / 2) + '*'

        plugins_dict = \
            self.plugin_manager.get_all_plugins() \
            if print_available \
            else self.plugin_manager.get_installed_plugins()

        for plugins_type, plugins in plugins_dict.iteritems():
            installed_plugins_list = \
                self.plugin_manager.get_installed_plugins(plugins_type).keys()
            plugins_names = plugins.keys()
            plugins_names.sort()

            if print_available:
                all_plugins_list = []
                for plugin_name in plugins_names:
                    all_plugins_list.append(plugin_name)
                installed_plugins_mark_list = \
                    [installed_mark if plugin_name in installed_plugins_list
                     else '' for plugin_name in all_plugins_list]
                registry = plugins_registry.load(self.plugin_manager.plugins_dir)
                plugins_descs = \
                    [registry .get(plugin, {}).get('desc', '')
                     for plugin in all_plugins_list]

                table_rows.append([
                    plugins_type,
                    '\n'.join(all_plugins_list),
                    '\n'.join(installed_plugins_mark_list),
                    '\n'.join(plugins_descs)])
            else:
                table_rows.append([
                    plugins_type,
                    '\n'.join(installed_plugins_list)])

        if print_available:
            table_headers.append("Installed")
            table_headers.append("Description")

        print fancy_table(table_headers, *table_rows)

    def _search_plugins(self):
        """
        Search git organizations and print a list of available plugins
        """
        table_rows = []
        table_headers = ["Type", "Name", "Description", "Source"]

        plugins_dict = \
            self.plugin_manager.get_all_git_plugins()

        for plugins_type, plugins in plugins_dict.iteritems():
            # prepare empty lists
            all_plugins_list = []
            plugins_descs = []
            plugins_sources = []

            for plugin_name in sorted(plugins.iterkeys()):
                # get all plugin names
                all_plugins_list.append(plugin_name)
                # get all plugin descriptions
                plugins_descs.append(plugins[plugin_name]["desc"])
                # get all plugins sources
                plugins_sources.append(plugins[plugin_name]["src"])

            table_rows.append([
                plugins_type,
                '\n'.join(all_plugins_list),
                '\n'.join(plugins_descs),
                '\n'.join(plugins_sources)])

        print(fancy_table(table_headers, *table_rows))


class SSHSpec(SpecObject):

    def __init__(self, name, *args, **kwargs):
        super(SSHSpec, self).__init__(name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        issh_parser = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)

        issh_parser.add_argument("node_name", help="Node name. "
                                 "Ex.: controller-0"
                                 ).completer = completers.node_list
        issh_parser.add_argument("remote_command", nargs="?", help="Run "
                                 "provided command line on remote host and "
                                 "return its output.")

    def spec_handler(self, parser, args):
        """Handles the ssh command

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        return interactive_ssh.ssh_to_host(
            pargs.node_name, remote_command=pargs.remote_command)


