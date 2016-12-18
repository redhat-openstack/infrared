import yaml

from infrared.core.utils import logger
from infrared.core.utils import utils
from infrared.core.cli.cli import CliParser
import helper


LOG = logger.LOG


class SpecParser(object):
    """Parses the input arguments from different sources (cli, file, env). """

    @classmethod
    def from_files(cls, subparser, spec_file, settings_folders, base_groups):
        """Reads specs file and constructs the parser instance

        :param subparser: argparse.subparser to extend
        :param spec_file: plugin spec file
        :param settings_folders:
        :param base_groups: dict, included groups
        :return:
        """

        spec_dict = base_groups or {}
        with open(spec_file) as stream:
            spec = yaml.load(stream) or {}
            utils.dict_merge(
                base_groups,
                spec,
                utils.ConflictResolver.unique_append_list_resolver)

        return SpecParser(subparser, spec_dict, settings_folders)

    def __init__(self, subparser, spec_dict, settings_folders):
        """

        :param subparser: argparse.subparser to extend
        :param spec_dict: dict with CLI description
        :param settings_folders:
        """
        self.settings_folders = settings_folders
        self.spec_helper = helper.SpecDictHelper(spec_dict)

        # create parser
        self.parser = CliParser.create_parser(self, subparser)

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
