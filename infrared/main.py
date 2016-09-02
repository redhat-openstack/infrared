import sys
import logging
import yaml

from infrared.core import execute
from infrared.core.plugins import PluginsManager
from infrared.core.settings import SettingsManager
from infrared.core.cli.spec import SpecManager
from infrared.core.utils import logger
PLUGIN_SETTINGS = 'plugins/settings.yml'

LOG = logger.LOG


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


def handle_plugin_manager_commands(subcommand, args):
    print "Hanlde plugin manager"


def handle_plugin_commands(subcommand, args):
    """
    Handler function for the plugins.
    """
    plugin = PluginsManager.get_plugin(subcommand)

    nested_args = args[0]
    control_args = args[1]
    unknown_args = args[2]
    subcommand_name = control_args['command0']

    if control_args.get('debug', None):
        LOG.setLevel(logging.DEBUG)

    settings = SettingsManager.generate_settings(
        plugin.name,
        nested_args,
        plugin.subcommand_settings_files(subcommand_name),
        input_files=control_args.get('input', []),
        extra_vars=control_args.get('extra-vars', None),
        dump_file=control_args.get('output', None))

    if not control_args.get('dry-run'):
        playbook_settings = yaml.load(yaml.safe_dump(
            settings,
            default_flow_style=False))

        if control_args.get('cleanup', None):
            playbook = plugin.cleanup_playbook
        else:
            playbook = plugin.main_playbook

        execute.ansible_playbook(
            playbook,
            module_path=plugin.modules_dir,
            verbose=control_args.get('verbose', None),
            settings=playbook_settings,
            inventory=control_args.get('inventory', None))

if __name__ == '__main__':
    sys.exit(int(main() or 0))
