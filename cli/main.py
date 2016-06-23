#!/usr/bin/env python
import logging
import inspect
import os

import yaml
from cli import logger  # logger should be imported first
from cli import execute, conf, clg, utils, exceptions, yamls

LOG = logger.LOG


def get_arguments_dict(spec_args):
    """
    Collect all ValueArgument args in dict according to arg names

    some-key=value will be nested in dict as:

    {"some": {
        "key": value}
    }

    For `YamlFileArgument` value is path to yaml so file content
    will be loaded as a nested dict.

    :param spec_args: Dictionary based on cmd-line args parsed from spec file
    :return: dict
    """
    settings_dict = {}
    for _name, argument in spec_args.items():
        utils.dict_insert(settings_dict, argument,
                          *_name.split("-"))

    return settings_dict


class IRFactory(object):
    """
    Creates and configures the IR specs.
    """

    @classmethod
    def create(cls, spec_name, config):
        """
        Create the spec object
        by module name and provided configuration.

        :param spec_name: str. the specification name
        :param config: dict. configuration details
        """
        settings_dirs = config.get_settings_dirs()
        supported_specs = cls.get_supported_specs(config)

        if spec_name not in supported_specs:
            raise exceptions.IRUnknownSpecException(spec_name)
        else:
            spec_app = clg.Spec.from_folder(settings_dirs, spec_name)
            spec_args = spec_app.parse_args()

            if spec_args is None:
                spec_instance = None
            else:
                nested_args = spec_args[0]
                control_args = spec_args[1]
                unknown_args = spec_args[2]
                cls.configure_environment(control_args)
                spec_instance = IRSpec(
                    config,
                    spec_name,
                    control_args,
                    nested_args,
                    unknown_args)

        return spec_instance

    @classmethod
    def get_supported_specs(cls, config):
        """
        Gets the list of supported specifications (installer, provisioner, etc)
        """
        supported_specs = [
            section for section in config.sections() if section != 'defaults']
        return supported_specs

    @classmethod
    def configure_environment(cls, control_args):
        """
        Performs the environment configuration.
        :param args:
        :return:
        """
        if control_args.get('debug', None):
            LOG.setLevel(logging.DEBUG)
            # todo(yfried): load exception hook now and not at init.


class IRSpec(object):
    """
    Hold the default spec workflow logic.
    """

    def __init__(self, config, name, control_args, nested_args, unknown_args):
        self.unknown_args = unknown_args
        self.config = config
        self.name = name
        self.nested_args = nested_args
        self.control_args = control_args
        self.spec_config = config.get_spec_config(name)
        self.settings_dirs = config.get_settings_dirs()

    def get_settings_files(self):
        """
        Collects all the settings files for given spec and sub-command
        """
        settings_files = []

        # first take all input files from args
        for input_file in self.control_args.get('input', []) or []:
            settings_files.append(utils.normalize_file(input_file))

        # get the sub-command yml file
        cmd_name = self.control_args['command0']
        for settings_dir in self.settings_dirs:
            path = os.path.join(
                settings_dir,
                self.name,
                cmd_name,
                cmd_name + '.yml')
            if os.path.exists(path):
                settings_files.append(path)

        LOG.debug("All settings files to be loaded:\n%s" % settings_files)
        return settings_files

    def run(self):
        """
        Runs the spec
        """
        try:
            settings = self.collect_settings()
            self.dump_settings(settings)
        # handle errors here and provide more output for user if required
        except exceptions.IRKeyNotFoundException as key_exception:
            if key_exception and key_exception.key.startswith("private."):
                raise exceptions.IRPrivateSettingsMissingException(
                    key_exception.key)
            else:
                raise

        if not self.control_args.get('dry-run'):
            playbook_settings = yaml.load(yaml.safe_dump(
                settings,
                default_flow_style=False))

            if self.control_args.get('cleanup', None):
                execute.ansible_playbook(
                    self.config,
                    self.spec_config['cleanup_playbook'],
                    verbose=self.control_args['verbose'],
                    settings=playbook_settings,
                    inventory=self.control_args['inventory'],
                    additional_args=self.control_args.get(
                        'ansible-args', None))
            else:
                execute.ansible_playbook(
                    self.config,
                    self.spec_config['main_playbook'],
                    verbose=self.control_args.get('verbose', None),
                    settings=playbook_settings,
                    inventory=self.control_args.get('inventory', None),
                    additional_args=self.control_args.get(
                        'ansible-args', None))

    def collect_settings(self):
        settings_files = self.get_settings_files()
        arguments_dict = {self.name: get_arguments_dict(self.nested_args)}

        # todo(yfried): fix after lookup refactor
        # utils.dict_merge(settings_files, arguments_dict)
        # return self.lookup(settings_files)

        # todo(yfried) remove this line after lookup refactor
        return self.lookup(settings_files, arguments_dict)

    def lookup(self, settings_files, settings_dict):
        """
        Replaces a setting values with !lookup
        in the setting files by values from
        other settings files.
        """
        all_settings = utils.load_settings_files(settings_files)
        utils.dict_merge(all_settings, settings_dict)
        utils.merge_extra_vars(
            all_settings,
            self.control_args.get('extra-vars', None))
        yamls.replace_lookup(all_settings)

        return all_settings

    def dump_settings(self, settings):
        LOG.debug("Dumping settings...")
        output = yaml.safe_dump(settings,
                                default_flow_style=False)
        dump_file = self.control_args.get('output', None)
        if dump_file:
            LOG.debug("Dump file: {}".format(dump_file))
            with open(dump_file, 'w') as output_file:
                output_file.write(output)
        else:
            print output


def main(spec_name):
    """
    The start function for a spec.
    """
    spec_runner = IRFactory.create(
        spec_name, conf.ConfigWrapper.load_config_file())
    if spec_runner:
        spec_runner.run()


def entry_point():
    """
    The main entry point for the ir-* scripts.
    """
    filename = inspect.stack()[1][1]
    spec_name = os.path.basename(filename).replace('ir-', '', 1)
    LOG.debug("Starting entry point for {}".format(spec_name))
    main(spec_name)


if __name__ == '__main__':
    # This is mainly for debug purposed
    main('provisioner')
    main('installer')
