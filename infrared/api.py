# provides API to run plugins
import argparse
import abc
import logging
import yaml


from infrared import SHARED_GROUPS
from infrared import version_details
from infrared.core import execute
from infrared.core.inspector.inspector import SpecParser
from infrared.core.services import CoreServices
from infrared.core.settings import VarsDictManager
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
            self.plugin.type,
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


class SpecManager(object):
    """Manages all the available specifications (specs). """

    def __init__(self):

        # create entry point
        self.parser = argparse.ArgumentParser(
            description='infrared entry point',
            formatter_class=argparse.RawTextHelpFormatter)
        self.parser.add_argument("--version", action='version',
                                 version=version_details())
        self.parser.add_argument("--no-log-commands", action='store_true',
                                 help='disables logging of all commands')
        self.root_subparsers = self.parser.add_subparsers(dest="subcommand")
        self.spec_objects = {}
        self.execution_logger = None

    def register_spec(self, spec_object):
        spec_object.extend_cli(self.root_subparsers)
        self.spec_objects[spec_object.get_name()] = spec_object

    def run_specs(self, args=None):
        spec_args = vars(self.parser.parse_args(args))
        subcommand = spec_args.get('subcommand', '')
        if not spec_args.get('no_log_commands'):
            if self.execution_logger is None:
                self.execution_logger = CoreServices.execution_logger_manager()
            self.execution_logger.command()

        if subcommand in self.spec_objects:
            return self.spec_objects[subcommand].spec_handler(
                self.parser, args=args)
