import yaml

from infrared.core.utils import exceptions, utils, logger, yamls

LOG = logger.LOG


class SettingsManager(object):

    @classmethod
    def generate_settings(cls,
                          plugin_name,
                          nested_args,
                          settings_files,
                          input_files=None,
                          extra_vars=None,
                          dump_file=None):
        try:
            settings = cls._collect_settings(
                plugin_name, nested_args, settings_files,
                input_files=input_files, extra_vars=extra_vars)

            cls._dump_settings(settings, dump_file=dump_file)
        # handle errors here and provide more output for user if required
        except exceptions.IRKeyNotFoundException as key_exception:
            if key_exception and key_exception.key.startswith("private."):
                raise exceptions.IRPrivateSettingsMissingException(
                    key_exception.key)
            else:
                raise

    @classmethod
    def _get_settings_files(cls, settings_files, input_files=None):
        """
        Collects all the settings files for given spec and sub-command
        """
        result = settings_files[:]

        # first take all input files from args
        for input_file in input_files or []:
            result.append(utils.normalize_file(input_file))

        LOG.debug("All settings files to be loaded:\n%s" % result)
        return result

    @classmethod
    def _collect_settings(cls,
                          plugin_name,
                          nested_args,
                          settings_files,
                          input_files=None,
                          extra_vars=None):
        settings_files = cls._get_settings_files(settings_files, input_files)

        settings_dict = {}
        for _name, argument in nested_args.items():
            utils.dict_insert(settings_dict, argument,
                              *_name.split("-"))
        arguments_dict = {plugin_name: settings_dict}

        # todo(yfried): fix after lookup refactor
        # utils.dict_merge(settings_files, arguments_dict)
        # return self.lookup(settings_files)

        # todo(yfried) remove this line after lookup refactor
        return cls._lookup(settings_files, arguments_dict, extra_vars)

    @classmethod
    def _lookup(self, settings_files, settings_dict, extra_vars=None):
        """
        Replaces a setting values with !lookup
        in the setting files by values from
        other settings files.
        """
        all_settings = utils.load_settings_files(settings_files)
        utils.dict_merge(all_settings, settings_dict)
        utils.merge_extra_vars(
            all_settings,
            extra_vars)
        yamls.replace_lookup(all_settings)

        return all_settings

    @classmethod
    def _dump_settings(self, settings, dump_file=None):
        LOG.debug("Dumping settings...")
        output = yaml.safe_dump(settings,
                                default_flow_style=False)
        if dump_file:
            LOG.debug("Dump file: {}".format(dump_file))
            with open(dump_file, 'w') as output_file:
                output_file.write(output)
        else:
            print output