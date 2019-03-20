import yaml

from infrared.core.utils import exceptions, dict_utils


class VarsDictManager(object):

    @staticmethod
    def generate_settings(entry_point,
                          nested_args,
                          delimiter='-'):
        """Unifies all input into a single dict of Ansible extra-vars

        :param entry_point: All input will be nested under this key
        :param nested_args: dict. these values will be nested
            example:
                {
                    foo-bar: value1,
                    foo2: value2
                    foo-another-bar: value3
                }
        :param delimiter: character to split keys by.
        :return: dict. nest input with keys splitted by delimiter

        >>> VarsDictManager.generate_settings(
        ... 'entry_point', {'foo-bar': 'value1',
        ...                 'foo2': 'value2',
        ...                 'foo-another-bar': 'value3'})
        {'entry_point': {'foo': {'bar': 'value1', 'another':\
 {'bar': 'value3'}}, 'foo2': 'value2'}}
        """
        vars_dict = {entry_point: {}}
        try:
            for _name, argument in nested_args.items():
                dict_utils.dict_insert(vars_dict[entry_point],
                                       argument,
                                       *_name.split(delimiter))

        # handle errors here and provide more output for user if required
        except exceptions.IRKeyNotFoundException as key_exception:
            if key_exception and key_exception.key.startswith("private."):
                raise exceptions.IRPrivateSettingsMissingException(
                    key_exception.key)
            else:
                raise
        return vars_dict

    @staticmethod
    def merge_extra_vars(vars_dict, extra_vars=None):
        """Extend ``vars_dict`` with ``extra-vars``

        :param vars_dict: Dictionary to merge extra-vars into
        :param extra_vars: List of extra-vars
        """
        for extra_var in extra_vars or []:
            if extra_var.startswith('@'):
                with open(extra_var[1:]) as f_obj:
                    loaded_yml = yaml.safe_load(f_obj)

                dict_utils.dict_merge(
                    vars_dict,
                    loaded_yml,
                    conflict_resolver=dict_utils.ConflictResolver.
                    unique_append_list_resolver)

            else:
                if '=' not in extra_var:
                    raise exceptions.IRExtraVarsException(extra_var)
                key, value = extra_var.split("=", 1)
                if value.startswith('@'):
                    with open(value[1:]) as f_obj:
                        loaded_yml = yaml.safe_load(f_obj)

                    tmp_dict = {}
                    dict_utils.dict_insert(tmp_dict, loaded_yml, *key.split("."))

                    dict_utils.dict_merge(
                        vars_dict,
                        tmp_dict,
                        conflict_resolver=dict_utils.ConflictResolver.
                        unique_append_list_resolver)

                else:
                    dict_utils.dict_insert(vars_dict, value, *key.split("."))
