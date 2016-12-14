from infrared.core.utils import exceptions, utils


class SettingsManager(object):

    @classmethod
    def generate_settings(cls,
                          entry_point,
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

        >>> SettingsManager.generate_settings(
        ... 'entry_point', {'foo-bar': 'value1',
        ...                 'foo2': 'value2',
        ...                 'foo-another-bar': 'value3'})
        {'entry_point': {'foo': {'bar': 'value1', 'another':\
 {'bar': 'value3'}}, 'foo2': 'value2'}}
        """
        settings_dict = {entry_point: {}}
        try:
            for _name, argument in nested_args.items():
                utils.dict_insert(settings_dict[entry_point],
                                  argument,
                                  *_name.split(delimiter))

        # handle errors here and provide more output for user if required
        except exceptions.IRKeyNotFoundException as key_exception:
            if key_exception and key_exception.key.startswith("private."):
                raise exceptions.IRPrivateSettingsMissingException(
                    key_exception.key)
            else:
                raise
        return settings_dict
