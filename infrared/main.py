import sys

from tabulate import tabulate

from infrared import api
from infrared.core.services import CoreServices
from infrared.core.utils import logger
from infrared.core.utils import interactive_ssh

LOG = logger.LOG


class ProfileManagerSpec(api.SpecObject):
    """The profile manager CLI. """

    def __init__(self, name, *args, **kwargs):
        super(ProfileManagerSpec, self).__init__(name, **kwargs)
        self.profile_manager = CoreServices.profile_manager()

    def extend_cli(self, root_subparsers):
        profile_plugin = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)
        profile_subparsers = profile_plugin.add_subparsers(dest="command0")

        # create
        create_parser = profile_subparsers.add_parser(
            'create', help='Creates a new profile')
        create_parser.add_argument("name", help="Profie name")

        # checkout
        checkout_parser = profile_subparsers.add_parser(
            'checkout',
            help='Creates a profile if it is not presents and switches to it')
        checkout_parser.add_argument("name", help="Profie name")

        # list
        profile_subparsers.add_parser(
            'list', help='Lists all the profiles')

        # delete
        delete_parser = profile_subparsers.add_parser(
            'delete', help='Deletes a profile')
        delete_parser.add_argument("name", help="Profie name")

        # cleanup
        cleanup_parser = profile_subparsers.add_parser(
            'cleanup', help='Removes all the files from profile')
        cleanup_parser.add_argument("name", help="Profie name")

        # import settings
        importer_parser = profile_subparsers.add_parser(
            'import', help='Import deployment configs.')
        importer_parser.add_argument("filename", help="Archive file name.")
        importer_parser.add_argument(
            "-n", "--name", dest="profilename",
            help="Profile name to import with."
            "If not specified - file name will be used.")

        # exort settings
        exporter_parser = profile_subparsers.add_parser(
            'export', help='Export deployment configurations.')
        exporter_parser.add_argument("-n", "--name", dest="profilename",
                                     help="Profile name. If not sepecified - "
                                     "active profile will be used.")
        exporter_parser.add_argument("-f", "--filename", dest="filename",
                                     help="Archive file name.")

        # node list
        nodelist_parser = profile_subparsers.add_parser(
            'node-list',
            help='List nodes, managed by profile')
        nodelist_parser.add_argument("-n", "--name", help="Profie name")

    def spec_handler(self, parser, args):
        """
        Handles all the plugin manager commands
        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'create':
            self._create_profile(pargs.name)
        elif subcommand == 'checkout':
            self._checkout_profile(pargs.name)
        elif subcommand == 'list':
            profiles = self.profile_manager.list()
            print(
                tabulate(
                    [[p.name, self.profile_manager.is_active(p.name) or ""]
                     for p in profiles],
                    headers=("Name", "Is Active"),
                    tablefmt='orgtbl'))
        elif subcommand == 'delete':
            self.profile_manager.delete(pargs.name)
            print("Profile '{}' deleted".format(pargs.name))
        elif subcommand == 'cleanup':
            self.profile_manager.cleanup(pargs.name)
        elif subcommand == 'export':
            self.profile_manager.export_profile(
                pargs.profilename, pargs.filename)
        elif subcommand == 'import':
            self.profile_manager.import_profile(
                pargs.filename, pargs.profilename)
        elif subcommand == 'node-list':
            nodes = self.profile_manager.node_list(pargs.name)
            print(
                tabulate([node_name for node_name in nodes],
                         headers=("Name", "Address"),
                         tablefmt='orgtbl'))

    def _create_profile(self, name):
        """Creates a profile """

        self.profile_manager.create(name)
        print("Profile '{}' added".format(name))

    def _checkout_profile(self, name):
        """Checkouts (create+activate) a profile """

        if not self.profile_manager.has_profile(name):
            self._create_profile(name)
        self.profile_manager.activate(name)
        print("Now using profile: '{}'".format(name))


class PluginManagerSpec(api.SpecObject):

    def __init__(self, name, plugin_manager, *args, **kwargs):
        self.plugin_manager = plugin_manager
        super(PluginManagerSpec, self).__init__(name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        plugin_parser = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)
        plugin_subparsers = plugin_parser.add_subparsers(dest="command0")

        # Add plugin
        add_parser = plugin_subparsers.add_parser(
            'add', help='Add a plugin')
        add_parser.add_argument("path", help="Plugin path")
        add_parser.add_argument("--dest", help="Destination directory to "
                                "clone plugin under, in case of Git URL is "
                                "provided as path")

        # Remove plugin
        remove_parser = plugin_subparsers.add_parser(
            'remove', help='Remove a plugin')
        remove_parser.add_argument("type", help="Plugin type")
        remove_parser.add_argument("name", help="Plugin name")

        # List command
        plugin_subparsers.add_parser(
            'list', help='List all the available plugins')

    def spec_handler(self, parser, args):
        """Handles all the plugin manager commands

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        subcommand = pargs.command0

        if subcommand == 'list':
            self._list_plugins()
        elif subcommand == 'add':
            self.plugin_manager.add_plugin(pargs.path, pargs.dest)
        elif subcommand == 'remove':
            self.plugin_manager.remove_plugin(pargs.type, pargs.name)

    def _list_plugins(self):
        """
        Print a list of available plugins sorted by type
        :return:
        """
        longest_type = max(self.plugin_manager.supported_plugin_types,
                           key=len)

        print("Available plugins:")
        for plugin_type in self.plugin_manager.supported_plugin_types:

            plugins_names = [name for name, plugin in self.plugin_manager
                             if plugin.config["plugin_type"] == plugin_type]
            plugins_names.sort()
            print('  {:{align}{width}} {{{}}}'.format(
                plugin_type, ','.join(plugins_names), align='<',
                width=len(longest_type) + 6))


class SSHSpec(api.SpecObject):

    def __init__(self, name, *args, **kwargs):
        super(SSHSpec, self).__init__(name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        issh_parser = root_subparsers.add_parser(
            self.name,
            help=self.kwargs["description"],
            **self.kwargs)

        issh_parser.add_argument("node_name", help="Node name. "
                                 "Ex.: controller-0")

    def spec_handler(self, parser, args):
        """Handles the ssh command

        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        pargs = parser.parse_args(args)
        self._issh(pargs.node_name)

    def _issh(self, node_name):
        interactive_ssh.ssh_to_host(node_name)


def main(args=None):
    # configure core services
    CoreServices.setup('infrared.cfg')

    # Init Managers
    plugin_manager = CoreServices.plugins_manager()

    specs_manager = api.SpecManager()

    specs_manager.register_spec(
        ProfileManagerSpec('profile',
                           description="Profile manager. "
                                       "Allows to create and use an isolated "
                                       "environement  for plugins execution."))
    specs_manager.register_spec(
        PluginManagerSpec('plugin',
                          plugin_manager=plugin_manager,
                          description="Plugin management"))

    specs_manager.register_spec(
        SSHSpec(
            'ssh',
            description="Interactive ssh session to node from inventory."))

    # register all plugins
    for plugin in plugin_manager.PLUGINS_DICT.values():
        specs_manager.register_spec(api.InfraRedPluginsSpec(plugin))

    return specs_manager.run_specs(args) or 0


if __name__ == '__main__':
    sys.exit(int(main() or 0))
