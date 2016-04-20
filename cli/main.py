#!/usr/bin/env python
import logging
import inspect
import os

import yaml
from cli import logger  # logger should bne imported first
from cli import execute, conf, spec, utils, exceptions, yamls

LOG = logger.LOG
CONF = conf.config


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
    for _name, argument in spec_args.iteritems():
        if isinstance(argument, spec.ValueArgument):
            utils.dict_insert(settings_dict, argument.value,
                              *argument.arg_name.split("-"))

    return settings_dict


class IRFactory(object):
    """
    Creates and configures the IR specs.
    """

    @classmethod
    def create(cls, spec_name, config, args=None):
        """
        Create the spec object
        by module name and provided configuration.

        :param spec_name: str. the specification name
        :param config: dict. configuration details
        :param args: list. If given parse it instead of stdin input.
        """
        settings_dir = config.get('defaults', 'settings')
        supported_specs = cls.get_supported_specs(config)

        if spec_name not in supported_specs:
            raise exceptions.IRUnknownSpecException(spec_name)
        else:
            spec_settings_dir = os.path.join(settings_dir, spec_name)
            spec_args = spec.parse_args(settings_dir, spec_settings_dir, args)
            cls.configure_environment(spec_args)

            if spec_args.get('generate-conf-file', None):
                LOG.debug('Conf file "{}" has been generated. Exiting'.format(
                    spec_args['generate-conf-file']))
                spec_instance = None
            else:
                spec_config = dict(config.items(spec_name))
                spec_instance = IRSpec(
                    spec_name,
                    dict(cleanup=spec_config['cleanup_playbook'],
                         main=spec_config['main_playbook']),
                    settings_dir, spec_args)

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
    def configure_environment(cls, args):
        """
        Performs the environment configuration.
        :param args:
        :return:
        """
        if args['debug']:
            LOG.setLevel(logging.DEBUG)
            # todo(yfried): load exception hook now and not at init.


class IRSubCommand(object):
    """
    Represents a command (virsh, ospd, etc)
    for the spec.
    """

    def __init__(self, name, args, settings_dir):
        self.name = name
        self.args = args
        self.settings_dir = settings_dir

    @classmethod
    def create(cls, spec_name, settings_dir, args):
        """
        Constructs the sub-command.
        :param spec_name:  tha spec name
        :param settings_dir:  the default spec settings dir
        :param args: the spec args
        :return: the IRSubCommand instance.
        """
        if args:
            settings_dir = os.path.join(settings_dir,
                                        spec_name)
        if "command0" in args:
            settings_dir = os.path.join(settings_dir,
                                        args['command0'])
        return cls(args['command0'], args, settings_dir)

    def get_settings_files(self):
        """
        Collects all the settings files for given spec and sub-command
        """
        settings_files = []

        # first take all input files from args
        for input_file in self.args['input'] or []:
            settings_files.append(utils.normalize_file(input_file))

        # get the sub-command yml file
        settings_files.append(os.path.join(
            self.settings_dir,
            self.name + '.yml'))

        LOG.debug("All settings files to be loaded:\n%s" % settings_files)
        return settings_files


class IRSpec(object):
    """
    Hold the default spec workflow logic.
    """

    def __init__(self, name, playbooks, settings_dir, args):
        self.name = name
        self.args = args
        self.playbooks = playbooks
        self.settings_dir = settings_dir

        # todo(obaranov) replace with subcommand factory
        self.sub_command = IRSubCommand.create(name, settings_dir, args)

    def run(self):
        """
        Runs the spec
        """
        settings = self.collect_settings()
        self.dump_settings(settings)

        if not self.args['dry-run']:
            self.args['settings'] = yaml.load(yaml.safe_dump(
                settings,
                default_flow_style=False))

            if self.args['cleanup']:
                execute.ansible_playbook(
                    self.playbooks['cleanup'],
                    verbose=self.args['verbose'],
                    settings=self.args['settings'],
                    inventory=self.args['inventory'])
            else:
                execute.ansible_playbook(
                    self.playbooks['main'],
                    verbose=self.args['verbose'],
                    settings=self.args['settings'],
                    inventory=self.args['inventory'])

    def collect_settings(self):
        settings_files = self.sub_command.get_settings_files()
        arguments_dict = {self.name: get_arguments_dict(self.args)}

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
        utils.merge_extra_vars(all_settings, self.args['extra-vars'])
        yamls.replace_lookup(all_settings)

        return all_settings

    def dump_settings(self, settings):
        LOG.debug("Dumping settings...")
        output = yaml.safe_dump(settings,
                                default_flow_style=False)
        dump_file = self.args['output']
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
    spec_runner = IRFactory.create(spec_name, CONF)
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
