import sys

from tabulate import tabulate

from infrared import api
from infrared.core.services import CoreServices
from infrared.core.utils import logger

PLUGIN_SETTINGS = 'plugins/settings.yml'

LOG = logger.LOG


class ProfileManagerSpec(api.SpecObject):
    """THe profile manager CLI. """

    def __init__(self, name, *args, **kwargs):
        super(ProfileManagerSpec, self).__init__(name, *args, **kwargs)
        self.profile_manager = None

    def extend_cli(self, root_subparsers):
        parser_plugin = root_subparsers.add_parser(self.name, **self.kwargs)
        plugins_subparsers = parser_plugin.add_subparsers(dest="command0")

        # create
        create_parser = plugins_subparsers.add_parser(
            'create', help='Creates a new profile')
        create_parser.add_argument("name", help="Profie name")

        # activate
        activate_parser = plugins_subparsers.add_parser(
            'activate', help='Activates a profile')
        activate_parser.add_argument("name", help="Profie name")

        # list
        plugins_subparsers.add_parser(
            'list', help='Lists all the profiles')

        # delete
        delete_parser = plugins_subparsers.add_parser(
            'delete', help='Deletes a profile')
        delete_parser.add_argument("name", help="Profie name")

        # cleanup
        cleanup_parser = plugins_subparsers.add_parser(
            'cleanup', help='Removes all the files from profile')
        cleanup_parser.add_argument("name", help="Profie name")

    def spec_handler(self, parser, args):
        """
        Handles all the plugin manager commands
        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        command0 = args.get('command0', '')

        profile_manager = CoreServices.profile_manager()
        if command0 == 'create':
            profile_manager.create(args.get('name'))
            print("Profile '{}' added".format(args.get('name')))
        elif command0 == 'activate':
            profile_manager.activate(args.get('name'))
            print("Profile '{}' activated".format(args.get('name')))
        elif command0 == 'list':
            profiles = profile_manager.list()
            print(
                tabulate([[p.name, profile_manager.is_active(p.name)]
                         for p in profiles],
                         headers=("Name", "Is Active"),
                         tablefmt='orgtbl'))
        elif command0 == 'delete':
            profile_manager.delete(args.get('name'))
            print("Profile '{}' deleted".format(args.get('name')))
        elif command0 == 'cleanup':
            profile_manager.cleanup(args.get('name'))


class PluginManagerSpec(api.SpecObject):

    def __init__(self, name, plugin_manager, *args, **kwargs):
        self.plugin_mamanger = plugin_manager
        super(PluginManagerSpec, self).__init__(name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        plugin_parser = root_subparsers.add_parser(self.name, **self.kwargs)
        plugin_subparsers = plugin_parser.add_subparsers(dest="command0")

        # Add plugin
        add_parser = plugin_subparsers.add_parser(
            'add', help='Add a plugin')
        add_parser.add_argument("path", help="Plugin path")

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
        command0 = args.get('command0', '')

        if command0 == 'list':
            self._list_plugins()
        elif command0 == 'add':
            self.plugin_mamanger.add_plugin(args['path'])
        elif command0 == 'remove':
            self.plugin_mamanger.remove_plugin(args['type'], args['name'])

    def _list_plugins(self):
        """
        Print a list of available plugins sorted by type
        :return:
        """
        longest_type = max(self.plugin_mamanger.supported_plugin_types,
                           key=len)

        print("Available plugins:")
        for plugin_type, plugins in \
                self.plugin_mamanger.PLUGINS_DICT.iteritems():
            plugins_names = [plugin.name for plugin in plugins.values()]
            plugins_names.sort()
            print('  {:{align}{width}} {{{}}}'.format(
                plugin_type, ','.join(plugins_names), align='<',
                width=len(longest_type) + 6))


def main():
    # configure core services
    CoreServices.from_ini_file('infrared.cfg')

    # Init Managers
    plugin_manager = CoreServices.plugins_manager()

    specs_manager = api.SpecManager()

    specs_manager.register_spec(
        ProfileManagerSpec('profile',
                           description="Profile manager. "
                                       "Allows to create and use an isolated "
                                       "environement  for plugins execution.")
    )
    specs_manager.register_spec(PluginManagerSpec(
        'plugin',
        plugin_manager=plugin_manager,
        description="Plugin management"))
    for action_type in plugin_manager.supported_plugin_types:
        specs_manager.register_spec(api.InfraRedGroupedPluginsSpec(
            action_type,
            plugin_manager.get_desc_of_type(action_type),
            plugin_manager.PLUGINS_DICT[action_type]))

    specs_manager.run_specs()


if __name__ == '__main__':
    sys.exit(int(main() or 0))
