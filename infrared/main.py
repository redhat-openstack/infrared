import os
import sys

import git
import pip
from infrared.core.utils import logger
from infrared.core.plugins import PluginsInspector
from infrared import api
PLUGIN_SETTINGS = 'plugins/settings.yml'

LOG = logger.LOG


class PluginManagerSpec(api.SpecObject):

    def extend_cli(self, root_subparsers):
        parser_plugin = root_subparsers.add_parser(self.name, **self.kwargs)
        plugins_subparsers = parser_plugin.add_subparsers(dest="command0")

        # list command
        plugins_subparsers.add_parser(
            'list', help='List all the available plugins')

        # init plugin
        init_parser = plugins_subparsers.add_parser(
            'init', help='Initializes a core plugin')
        init_parser.add_argument("name", help="Plugin name")
        plugins_subparsers.add_parser(
            'init-all', help='Initializes all the core plugin')

    def spec_handler(self, parser, args):
        """
        Handles all the plugin manager commands
        :param parser: the infrared parser object.
        :param args: the list of arguments received from cli.
        """
        command0 = args.get('command0', '')

        if command0 == 'list':
            self._list_plugins()
        elif command0 == 'init':
            self._init_plugin(args['name'])
        elif command0 == 'init-all':
            self._init_all_plugins()

    def _list_plugins(self):
        print("Available plugins:")
        for plugin in PluginsInspector.iter_plugins():
            print('\t {name}: {path}'.format(
                name=plugin.name, path=plugin.root_dir))

    def _init_all_plugins(self):
        root_repo = git.Repo(os.getcwd())

        for submodule in root_repo.submodules:
            print("Initializing plugin submodule: '{}'...".format(submodule.name))
            submodule.update(init=True)

        # install all the requirements
        for plugin in PluginsInspector.iter_plugins():
            requirement_file = os.path.join(plugin.root_dir, "plugin_requirements.txt")
            if os.path.isfile(requirement_file):
                print("Installing requirements from: {}".format(requirement_file))
                pip_args = ['install', '-r', requirement_file]
                pip.main(args=pip_args)

    def __install_requirements(self, plugin):
        pass

    def _init_plugin(self, name):
        plugin = PluginsInspector.get_plugin(name)
        if plugin is None:
            LOG.warn("Unable to find plugin: %s", name)
            sys.exit(1)
        root_repo = git.Repo(os.getcwd())

        for submodule in root_repo.submodules:
            if os.path.abspath(submodule.path) == os.path.abspath(
                    plugin.root_dir):
                print("Updating plugin submodule: '{}'...".format(
                    submodule.name))
                submodule.update(init=True)
                break
        else:
            LOG.warn("No submodule found for plugin: %s", name)


def main():
    specs_manager = api.SpecManager()
    specs_manager.register_spec(PluginManagerSpec(
        'plugin', help="Plugin management command"))

    # add all the plugins
    for plugin in PluginsInspector.iter_plugins():
        specs_manager.register_spec(api.DefaultInfraredPluginSpec(plugin))

    specs_manager.run_specs()

if __name__ == '__main__':
    sys.exit(int(main() or 0))
