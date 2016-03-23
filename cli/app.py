import logging

import cli.execute
import cli.yamls
import os
import yaml
from cli import logger, conf, spec, utils, exceptions

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
    Creates and configures the IR applications.
    """

    @classmethod
    def create(cls, app_name, config, args=None):
        """
        Create the application object
        by module name and provided configuration.

        :param app_name: str
        :param config: dict. configuration details
        :param args: list. If given parse it instead of stdin input.
        """
        settings_dir = config.get('defaults', 'settings')

        if app_name not in ["provisioner", "installer"]:
            raise exceptions.IRUnknownApplicationException(
                "Application is not supported: '{}'".format(app_name))
        else:
            app_settings_dir = os.path.join(settings_dir, app_name)
            spec_args = spec.parse_args(settings_dir, app_settings_dir, args)
            cls.configure_environment(spec_args)

            if spec_args.get('generate-conf-file', None):
                LOG.debug('Conf file "{}" has been generated. Exiting'.format(
                    spec_args['generate-conf-file']))
                app_instance = None
            else:
                app_instance = getattr(cls, '_create_' + app_name)(app_name, settings_dir, spec_args)
        return app_instance

    @classmethod
    def _create_provisioner(cls, app_name, settings_dir, spec_args):
        return IRApplication(app_name,
                             dict(cleanup='cleanup.yaml', main='provision.yaml'),
                             settings_dir, spec_args)

    @classmethod
    def _create_installer(cls, app_name, settings_dir, spec_args):
        return IRApplication(app_name,
                             dict(cleanup='cleanup.yaml', main='install.yml'),
                             settings_dir, spec_args)

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
    for the application
    """

    def __init__(self, name, args, settings_dir):
        self.name = name
        self.args = args
        self.settings_dir = settings_dir

    @classmethod
    def create(cls, app, settings_dir, args):
        """
        Constructs the sub-command.
        :param app:  tha application name
        :param settings_dir:  the default application settings dir
        :param args: the application args
        :return: the IRSubCommand instance.
        """
        if args:
            settings_dir = os.path.join(settings_dir,
                                        app)
        if "command0" in args:
            settings_dir = os.path.join(settings_dir,
                                        args['command0'])
        return cls(args['command0'], args, settings_dir)

    def get_settings_files(self):
        """
        Collects all the settings files for given application and sub-command
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


class IRApplication(object):
    """
    Hold the default application workflow logic.
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
        Runs the application
        """
        settings = self.collect_settings()
        self.dump_settings(settings)

        if not self.args['dry-run']:
            self.args['settings'] = yaml.load(yaml.safe_dump(
                settings,
                default_flow_style=False))

            if self.args['cleanup']:
                cli.execute.ansible_playbook(
                    self.playbooks['cleanup'],
                    self.args,
                    inventory=self.args['inventory'])
            else:
                cli.execute.ansible_playbook(
                    self.playbooks['main'],
                    self.args,
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

        cli.yamls.Lookup.settings = utils.generate_settings(settings_files)
        # todo(yfried) remove this line after refactor
        cli.yamls.Lookup.settings.merge(settings_dict)
        cli.yamls.Lookup.settings = utils.merge_extra_vars(
            cli.yamls.Lookup.settings,
            self.args['extra-vars'])

        cli.yamls.Lookup.in_string_lookup()

        return cli.yamls.Lookup.settings

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