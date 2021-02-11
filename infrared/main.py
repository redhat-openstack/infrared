from __future__ import print_function

import argcomplete
import json
import os
from pbr import version
import pkg_resources as pkg
import sys


def inject_common_paths():
    """Discover the path to the common/ directory provided by infrared core."""
    def override_conf_path(common_path, envvar, specific_dir):
        conf_path = os.environ.get(envvar, '')
        additional_conf_path = os.path.join(common_path, specific_dir)
        if conf_path:
            full_conf_path = ':'.join([additional_conf_path, conf_path])
        else:
            full_conf_path = additional_conf_path
        os.environ[envvar] = full_conf_path

    version_info = version.VersionInfo('infrared')

    common_path = pkg.resource_filename(version_info.package,
                                        'common')
    override_conf_path(common_path, 'ANSIBLE_ROLES_PATH', 'roles')
    override_conf_path(common_path, 'ANSIBLE_FILTER_PLUGINS', 'filter_plugins')
    override_conf_path(common_path, 'ANSIBLE_MODULE_UTILS', 'module_utils')
    override_conf_path(common_path, 'ANSIBLE_CALLBACK_PLUGINS',
                       'callback_plugins')
    override_conf_path(common_path, 'ANSIBLE_LIBRARY', 'library')


# This needs to be called here because as soon as an ansible class is loaded
# the code in constants.py is triggered. That code reads the configuration
# settings from all sources (ansible.cfg, environment variables, etc).
# If the first include to ansible modules is moved deeper in the InfraRed
# code (or on demand), then this call can be moved as well in that place.
inject_common_paths()

from infrared import api  # noqa
import infrared.bash_completers as completers  # noqa
from infrared.core.services import CoreServices  # noqa
from infrared.core.services.plugins import PLUGINS_REGISTRY  # noqa
from infrared.core.utils import exceptions  # noqa
from infrared.core.utils import interactive_ssh  # noqa
from infrared.core.utils import logger  # noqa
from infrared.core.utils.print_formats import fancy_table  # noqa

LOG = logger.LOG


class WorkspaceManagerSpec(api.SpecObject):
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
            help='Switches workspace to the specified workspace')
        checkout_parser.add_argument(
            "name",
            help="Workspace name").completer = completers.workspace_list
        checkout_parser.add_argument(
            "-c", "--create", action='store_true', dest="checkout_create",
            help="Creates a workspace if not exists and "
                 "switches to it")

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
        importer_parser.add_argument("filename", help="Archive file name or URL.")
        importer_parser.add_argument(
            "-n", "--name", dest="workspacename",
            help="Workspace name to import with. "
            "If not specified - file name will be used.")

        # export settings
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
        nodelist_parser.add_argument(
            "-f", "--format", choices=['fancy', 'json'], default='fancy',
            help="Output format")

        # group list
        grouplist_parser = workspace_subparsers.add_parser(
            'group-list',
            help='List groups, managed by workspace')
        grouplist_parser.add_argument(
            "-n", "--name",
            help="Workspace name").completer = completers.workspace_list

    def spec_handler(self, parser, args):
        """Handles all the plugin manager commands

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'create':
            self._create_workspace(pargs.name)
        elif subcommand == 'checkout':
            self._checkout_workspace(pargs.name, pargs.checkout_create)
        elif subcommand == 'inventory':
            self._fetch_inventory(pargs.name)
        elif subcommand == 'list':
            if pargs.print_active:
                print(self.workspace_manager.get_active_workspace().name)
            else:
                workspaces = self.workspace_manager.list()
                headers = ("Name", "Active")
                workspaces = sorted([workspace.name for workspace in
                                     self.workspace_manager.list()])
                print(fancy_table(
                    headers,
                    *[(workspace, ' ' * (len(headers[-1]) // 2) + "*" if
                        self.workspace_manager.is_active(workspace) else "")
                      for workspace in workspaces]))
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
            if pargs.format == 'json':
                nodes_dict = [
                    {'name': name, 'address': address, 'groups': groups}
                    for name, address, groups in nodes]
                print(json.dumps({'nodes': nodes_dict}))
            else:
                print(fancy_table(
                    ("Name", "Address", "Groups"),
                    *[node_name for node_name in nodes]))
        elif subcommand == "group-list":
            groups = self.workspace_manager.group_list(pargs.name)
            print(fancy_table(
                ("Name", "Nodes"), *[group_name for group_name in groups]))

    def _create_workspace(self, name):
        """Creates a workspace

        :param name: Name of the workspace to create
        """
        self.workspace_manager.create(name)
        print("Workspace '{}' has been added".format(name))

    def _checkout_workspace(self, name, create=False):
        """Checkouts (activate) a workspace

        :param name: The name of the workspace to checkout
        :param create: if set to true will create a new workspace
        before checking out to it
        """
        if create:
            self._create_workspace(name)
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
        print(wkspc.inventory)


class PluginManagerSpec(api.SpecObject):

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
        add_parser.add_argument("src", nargs='+',
                                help="Plugin Source (name/path/git URL)\n'all'"
                                     " will install all available plugins")
        add_parser.add_argument("--revision", help="git branch/tag/revision"
                                " sourced plugins. Ignored for"
                                "'plugin add all' command.")

        add_parser.add_argument("--src-path",
                                help="Relative path within the repository "
                                     "where infrared plugin can be found.\n"
                                     "(Required with --link-roles")

        add_parser.add_argument("--link-roles", action='store_true',
                                help="Auto creates symbolic 'roles' directory "
                                     "in the path provided with '--src-path' "
                                     "which points to the 'roles' directory "
                                     "inside the project's root dir if exists,"
                                     " otherwise to the project's root dir "
                                     "itself.")

        add_parser.add_argument("--skip-roles", action='store_true',
                                help="Skip the from file roles installation. "
                                     "(Don't install Ansible roles from "
                                     "'requirements.yml' or "
                                     "'requirements.yaml' file)")

        # Remove plugin
        remove_parser = plugin_subparsers.add_parser(
            "remove",
            help="Remove a plugin, 'all' will remove all installed plugins")
        remove_parser.add_argument(
            "name", nargs='+',
            help="Plugin name").completer = completers.plugin_list

        # List command
        list_parser = plugin_subparsers.add_parser(
            'list', help='List all the available plugins')
        list_parser.add_argument(
            "--available", action='store_true',
            help="Prints all available plugins in addition "
                 "to installed plugins")
        list_parser.add_argument(
            "--versions", action='store_true',
            help="Prints version of each installed plugins")

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

        # import plugins from registry yml file
        plugin_subparsers.add_parser(
            'import', help='Install plugins from a YAML file')

        # Add plugin
        import_parser = plugin_subparsers.add_parser(
            'import', help='Install plugins from a registry YML file')
        import_parser.add_argument("src",
                                   help="The registry YML file Source")

    def spec_handler(self, parser, args):
        """Handles all the plugin manager commands

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'list':
            self._list_plugins(pargs.available, pargs.versions)
        elif subcommand == 'add':
            if 'all' in pargs.src:
                self.plugin_manager.add_all_available()
                self._list_plugins(print_available=False, print_version=False)
            else:
                if len(pargs.src) > 1 and (pargs.revision or pargs.src_path):
                    raise exceptions.IRFailedToAddPlugin(
                        "'--revision' works with one plugin source only.")
                for _plugin in pargs.src:
                    self.plugin_manager.add_plugin(
                        _plugin, rev=pargs.revision,
                        plugin_src_path=pargs.src_path,
                        skip_roles=pargs.skip_roles,
                        link_roles=pargs.link_roles)
        elif subcommand == 'remove':
            if 'all' in pargs.name:
                self.plugin_manager.remove_all()
                self._list_plugins(print_available=False, print_version=False)
            else:
                for _plugin in pargs.name:
                    self.plugin_manager.remove_plugin(_plugin)
        elif subcommand == 'freeze':
            self.plugin_manager.freeze()
        elif subcommand == 'update':
            self.plugin_manager.update_plugin(
                pargs.name, pargs.revision, pargs.skip_reqs, pargs.hard_reset)
        elif subcommand == 'search':
            self._search_plugins()
        elif subcommand == 'import':
            self.plugin_manager.import_plugins(pargs.src)

    def _list_plugins(self, print_available=False, print_version=False):
        """Print a list of installed & available plugins"""
        table_rows = []
        table_headers = ["Type", "Name"]
        installed_mark = ' ' * (len('Installed') // 2) + '*'

        plugins_dict = \
            self.plugin_manager.get_all_plugins() \
            if print_available \
            else self.plugin_manager.get_installed_plugins()

        for plugins_type, plugins in plugins_dict.items():
            installed_plugins_list = \
                self.plugin_manager.get_installed_plugins(plugins_type).keys()
            plugins_names = list(plugins.keys())
            plugins_names.sort()

            if print_available:
                all_plugins_list = []
                for plugin_name in plugins_names:
                    all_plugins_list.append(plugin_name)
                installed_plugins_mark_list = \
                    [installed_mark if plugin_name in installed_plugins_list
                     else '' for plugin_name in all_plugins_list]

                plugins_descs = \
                    [PLUGINS_REGISTRY.get(plugin, {}).get('desc', '')
                     for plugin in all_plugins_list]

                row = [plugins_type, '\n'.join(all_plugins_list),
                       '\n'.join(installed_plugins_mark_list),
                       '\n'.join(plugins_descs)]

                if print_version:
                    plugins_version = [
                        self.plugin_manager.get_plugin_version(plugin_name)
                        if plugin_name in installed_plugins_list else ''
                        for plugin_name in all_plugins_list]

                    row.append('\n'.join(plugins_version))

            else:
                row = [
                    plugins_type,
                    '\n'.join(installed_plugins_list)]

                if print_version:
                    plugins_version = [self.plugin_manager.get_plugin_version(
                        plugin_name) for plugin_name in installed_plugins_list]
                    row.append('\n'.join(plugins_version))

            table_rows.append(row)

        if print_available:
            table_headers.append("Installed")
            table_headers.append("Description")

        if print_version:
            table_headers.append("Version")

        print(fancy_table(table_headers, *table_rows))

    def _search_plugins(self):
        """Search git organizations and print a list of available plugins """

        table_rows = []
        table_headers = ["Type", "Name", "Description", "Source"]

        plugins_dict = \
            self.plugin_manager.get_all_git_plugins()

        for plugins_type, plugins in plugins_dict.items():
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


class SSHSpec(api.SpecObject):

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


def main(args=None):
    CoreServices.setup()

    # inject ansible config file
    CoreServices.ansible_config_manager().inject_config()

    specs_manager = api.SpecManager()

    # Init Managers
    specs_manager.register_spec(
        WorkspaceManagerSpec('workspace',
                             description="Workspace manager. "
                                         "Allows to create and use an "
                                         "isolated environment for plugins "
                                         "execution."))
    specs_manager.register_spec(
        PluginManagerSpec('plugin',
                          description="Plugin management"))

    specs_manager.register_spec(
        SSHSpec(
            'ssh',
            description="Interactive ssh session to node from inventory."))

    # register all plugins
    for plugin in CoreServices.plugins_manager().PLUGINS_DICT.values():
        specs_manager.register_spec(api.InfraredPluginsSpec(plugin))

    argcomplete.autocomplete(specs_manager.parser)
    return specs_manager.run_specs(args) or 0


if __name__ == '__main__':
    sys.exit(int(main() or 0))
