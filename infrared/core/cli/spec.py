import argparse

from infrared.core.cli import base, clg
from infrared.core.utils import logger

LOG = logger.LOG


class SpecManager(object):
    """
    Manages all the available specifications (specs).
    """

    def __init__(self):
        self.specs = {}
        self.subcommands_handlers = {}
        self.parser = argparse.ArgumentParser(
            description='Infrared entry point')
        self.root_subparsers = self.parser.add_subparsers(dest="subcommand")

    def add_subparser(self, parser_name, cmd_handler, **kwargs):
        result = self.root_subparsers.add_parser(parser_name, **kwargs)
        self.subcommands_handlers[parser_name] = cmd_handler
        return result

    def run(self):
        # first do standard parsing to get subcommand
        args = vars(self.parser.parse_args())
        subcommand = args.get('subcommand', '')

        if subcommand in self.specs:
            # validate plugin arguments
            pargs = self.specs[subcommand].parse_args(self.parser)
            self._call_handler(subcommand, pargs)
        elif subcommand in self.subcommands_handlers:
            self._call_handler(subcommand, args)

    def _call_handler(self, name, args):
        self.subcommands_handlers[name](args)

    def register_plugin_spec(self, plugin, cmd_handler, add_base_groups=True):
        """
        Registers plugin specification for future usage.
        :param plugin The plugin object
        :return:
        """
        if plugin.name in self.specs:
            LOG.warn("Spec with '%n' already registered")
        else:
            user_dict = {}
            if add_base_groups:
                user_dict = dict(
                    shared_groups=base.SHARED_GROUPS)

            spec = clg.SpecParser.from_folder(
                plugin.settings_folders(),
                plugin.name, user_dict=user_dict)

            self.specs[plugin.name] = spec

            # extend cli with spec paraser
            spec.create_parser(self.root_subparsers)
            # register handler
            self.subcommands_handlers[plugin.name] = cmd_handler
