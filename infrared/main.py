import os
import shutil
import sys

import pip
from tabulate import tabulate

from infrared import api
from infrared.core.services import CoreServices
from infrared.core.utils import logger

PLUGIN_SETTINGS = 'plugins/settings.yml'

LOG = logger.LOG


class ProfileManagerSpec(api.SpecObject):
    """
    THe profile manager CLI.
    """

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
            profile = profile_manager.create(args.get('name'))
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


def main():
    # configure core services
    CoreServices.from_ini_file('infrared.cfg')

    specs_manager = api.SpecManager()

    specs_manager.register_spec(ProfileManagerSpec(
        'profile', description="Profile manager. " \
        "Allows to create and use an isolated environement " \
        "for plugins execution."))

    specs_manager.run_specs()

if __name__ == '__main__':
    sys.exit(int(main() or 0))
