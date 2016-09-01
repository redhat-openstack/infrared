import sys

from infrared.core.plugins.manager import PluginsManager
from infrared.core.cli.spec import SpecManager
PLUGIN_SETTINGS = 'plugins/settings.yml'


def main():
    specs_manager = SpecManager()

    # create plugins manager command (just as placeholder for now)
    parser_plugin = specs_manager.add_subparser(
        'plugin', cmd_handler= handle_plugin_manager_commands,
        help='Plugins manager',)
    plugins_subparsers = parser_plugin.add_subparsers(dest="plugin")

    # add
    add_plugin_parser = plugins_subparsers.add_parser(
        'add', help='Adds new plugin')
    add_plugin_parser.add_argument('uri', help="Plugin git repo uri.")
    add_plugin_parser.add_argument('name', help="Plugin name.")
    add_plugin_parser.add_argument('--branch', help="Plugin branch to use.")

    # ***********************************************
    # collect all the plugins
    for plugin in PluginsManager.iter_plugins():
        # collect plugin specs
        specs_manager.register_plugin_spec(
            plugin,
            cmd_handler=handle_plugin_commands)

    specs_manager.run()


def handle_plugin_manager_commands(args):
    print "Hanlde plugin manager"


def handle_plugin_commands(args):
    """
    Handler function for the plugins.
    """
    print "Hanlde plugin"
    # print args[0] # nested
    print args[1] # control args

if __name__ == '__main__':
    sys.exit(int(main() or 0))
