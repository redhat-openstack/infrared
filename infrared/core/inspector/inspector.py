import yaml

from infrared.core.utils import logger
from infrared.core.utils import utils
from infrared.core.utils import exceptions
from infrared.core.cli.cli import CliParser
import helper


LOG = logger.LOG


class SpecParser(object):
    """Parses the input arguments from different sources (cli, file, env). """

    @classmethod
    def from_files(cls, settings_folders, app_name, app_subfolder,
                   user_dict, subparser, *spec_files):
        """Reads specs files and constructs the parser instance. """
        if user_dict is None:
            user_dict = {}
        result = user_dict
        for spec_file in spec_files:
            with open(spec_file) as stream:
                spec = yaml.load(stream) or {}
                utils.dict_merge(
                    result,
                    spec,
                    utils.ConflictResolver.unique_append_list_resolver)

        return SpecParser(
            result, settings_folders, app_name, app_subfolder, subparser)

    def __init__(self, spec_dict, settings_folders,
                 app_name, app_subfolder, subparser):
        self.app_name = app_name
        self.app_subfolder = app_subfolder
        self.settings_folders = settings_folders
        self.subparser = subparser

        # inject name to the spec_dict to handle it as regular subparser
        spec_dict['name'] = app_name
        self.spec_helper = helper.SpecDictHelper(spec_dict)

        # create parser
        self.parser = CliParser.create_parser(self, subparsers=subparser)

    def add_shared_groups(self, list_of_groups):
        """ Adds the user defined shared groups

        :param list_of_groups:  the list of group dict's
        """
        shared_groups = self.spec_helper.spec_dict.get('shared_groups', [])
        shared_groups.expand(list_of_groups)
        self.spec_helper.spec_dict['shared_groups'] = shared_groups

    def parse_args(self, arg_parser):
        """
        Parses all the arguments (cli, file, env) and returns two dicts:
            * command arguments dict (arguments to control the IR logic)
            * nested arguments dict (arguments to pass to the playbooks)
        """
        raise Exception("Not implemented yet")
