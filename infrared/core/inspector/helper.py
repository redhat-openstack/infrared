from copy import deepcopy
from infrared.core.utils.exceptions import SpecParserException

OptionState = dict(
    UNRECOGNIZED='unrecognized',
    IS_SET='is set',
    NOT_SET='is no set'
)


class SpecDictHelper(object):
    """
    Controls the spec dicts and provides useful methods to get spec info.
    """

    def __init__(self, spec_dict):
        self.spec_dict = spec_dict
        # make structure of the dict flat
        # 1. handle include_groups directive in main parser
        parser_dict = self.spec_dict
        self._include_groups(parser_dict)
        # 2. Include groups for all subparsers
        for subparser_name, subparser_dict in parser_dict.get(
                'subparsers', {}).items():
            self._include_groups(subparser_dict)

    def iterate_parsers(self):
        """Iterates over the main parsers and subparsers. """

        for subparser_name, subparser_dict in self.spec_dict.get(
                'subparsers', {}).items():
            yield dict(name=subparser_name, **subparser_dict)

    def iterate_option_specs(self):
        """Iterates over all the option specs.

        Returns pair of parser and option on every iteration.
        """
        for parser in self.iterate_parsers():
            for spec_option in self._get_all_options_spec(parser):
                yield parser, spec_option

    @staticmethod
    def _get_all_options_spec(parser_dict):
        """Gets all the options specification as the list of dicts. """
        result = []
        for group in parser_dict.get('groups', []):
            for option_name, option_dict in group.get('options', {}).items():
                result.append(dict(name=option_name, **option_dict))

        for option_name, option_dict in parser_dict.get('options', {}).items():
            result.append(dict(name=option_name, **option_dict))

        return result

    def get_parser_option_specs(self, command_name):
        """Gets all the options for the specified command

        :param command_name: the command name (main, virsh, ospd, etc...)
        :return: the list of all command options
        """
        options = []
        for parser in self.iterate_parsers():
            if parser['name'] == command_name:
                options = self._get_all_options_spec(parser)
                break
        return options

    def get_option_spec(self, command_name, argument_name):
        """Gets the specification for the specified option name. """

        options = self.get_parser_option_specs(command_name)
        return next((opt for opt in options
                     if opt['name'] == argument_name), {})

    def get_option_state(self, command_name, option_name, args):
        """Gets the option state.

        :param command_name: The command name
        :param option_name: The option name to analyze
        :param args: The received arguments.
        """
        option_spec = self.get_option_spec(command_name, option_name)

        if not option_spec:
            res = OptionState['UNRECOGNIZED']

        elif option_name not in args.get(command_name, {}):
            res = OptionState['NOT_SET']
        else:
            option_value = args[command_name][option_name]
            if option_spec.get('action', '') in ['store_true'] \
                    and option_value is False:
                res = OptionState['NOT_SET']
            else:
                res = OptionState['IS_SET']

        return res

    def _include_groups(self, parser_dict):
        """Resolves the include dict directive in the spec files. """
        for group in parser_dict.get('include_groups', []):
            # ensure we have that group
            grp_dict = next(
                (grp for grp in self.spec_dict.get('shared_groups', [])
                 if grp['title'] == group),
                None)
            if grp_dict is None:
                raise SpecParserException(
                    "Unable to include group '{}' in '{}' parser. "
                    "Group was not found!".format(
                        group,
                        parser_dict['name']))

            for option in grp_dict.get('options', {}).values():
                option['is_shared_group_option'] = True

            parser_groups_list = parser_dict.get('groups', [])
            parser_groups_list.append(deepcopy(grp_dict))
            parser_dict['groups'] = parser_groups_list
