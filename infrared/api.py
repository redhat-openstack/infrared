# provides API to run plugins
import argparse
import abc

from infrared import SHARED_GROUPS
from infrared.core import execute
from infrared.core.inspector.inspector import SpecParser
from infrared.core.services import CoreServices
from infrared.core.utils import exceptions
from infrared.core.utils import logger

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
        :param parser:
        :param args:
        :return: exit code to be propagated out.
        """


class InfraRedPluginsSpec(SpecObject):
    """Integrates Plugin object with Specs"""

    add_base_groups = True

    def __init__(self, plugin, *args, **kwargs):
        """Initialize Plugin spec

        :param plugin: plugin object
        """
        self.plugin = plugin
        self.specification = None
        super(InfraRedPluginsSpec, self).__init__(plugin.name, *args, **kwargs)

    def extend_cli(self, root_subparsers):
        """Extend CLI with plugin subparser. """
        spec_file = self.plugin.spec

        user_dict = {}
        if self.add_base_groups:
            user_dict = dict(shared_groups=SHARED_GROUPS)

        self.specification = SpecParser.from_files(
            subparser=root_subparsers,
            spec_file=spec_file,
            settings_folders='',
            base_groups=user_dict)

    def spec_handler(self, parser, args):
        """Execute plugin's main playbook.

        :param parser:
        :param args:
        :return: Ansible exit code
        """

        active_profile = CoreServices.profile_manager().get_active_profile()
        if not active_profile:
            raise exceptions.IRNoActiveProfileFound()

        # TODO(yfried): when accepting inventory from CLI, need to update:
        # profile.inventory = CLI[inventory]

        result = execute.ansible_playbook(inventory=active_profile.inventory,
                                          playbook_path=self.plugin.playbook)
        return result


class SpecManager(object):
    """
    Manages all the available specifications (specs).
    """

    def __init__(self):
        # create entry point
        self.parser = argparse.ArgumentParser(
            description='Infrared entry point')
        self.root_subparsers = self.parser.add_subparsers(dest="subcommand")
        self.spec_objects = {}

    def register_spec(self, spec_object):
        spec_object.extend_cli(self.root_subparsers)
        self.spec_objects[spec_object.get_name()] = spec_object

    def run_specs(self):
        args = vars(self.parser.parse_args())
        subcommand = args.get('subcommand', '')

        if subcommand in self.spec_objects:
            return self.spec_objects[subcommand].spec_handler(self.parser,
                                                              args)
