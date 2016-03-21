#!/usr/bin/env python
import clg
import os
import logging

import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import utils
from cli import exceptions
from cli import spec
import cli.yamls
import cli.execute

APPLICATION = 'provisioner'

LOG = logger.LOG
CONF = conf.config

PROVISION_PLAYBOOK = "provision.yaml"
CLEANUP_PLAYBOOK = "cleanup.yaml"
NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output',
                        'input', 'dry-run', 'cleanup', 'inventory']


class TopologyArgument(spec.ValueArgument):

    def resolve_value(self, arg_name, defaults=None):
        super(TopologyArgument, self).resolve_value(arg_name, defaults)
        """
        Merges topology files in a single topology dict.

        :param clg_args: Dictionary based on cmd-line args parsed by clg
        :param app_settings_dir: path to the base directory holding the
            application's settings. App can be provisioner\installer\tester
            and the path would be: settings/<app_name>/
        """

        # post process topology
        topology_dir = os.path.join(self.get_app_attr("settings_dir"),
                                   'topology')
        topology_dict = {}
        for topology_item in self.value.split(','):
            if '_' in topology_item:
                number, node_type = topology_item.split('_')
            else:
                raise exceptions.IRConfigurationException(
                    "Topology node should be in format  <number>_<node role>. "
                    "Current value: '{}' ".format(topology_item))
            # todo(obaraov): consider moving topology to config on constant.
            topology_dict[node_type] = spec.find_file(node_type + ".yaml",
                                                      topology_dir)
            topology_dict[node_type]['amount'] = int(number)

        self.value = topology_dict

clg.TYPES.update({'Topology': TopologyArgument})


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

        if app_name in ["provisioner", ]:
            app_settings_dir = os.path.join(settings_dir, app_name)
            spec_args = spec.parse_args(app_settings_dir, args)
            cls.configure_environment(spec_args)
            # # todo(yfried): This should be in a more generic place
            # process_topology_args(spec_args, app_settings_dir)

            if spec_args.get('generate-conf-file', None):
                LOG.debug('Conf file "{}" has been generated. Exiting'.format(
                    spec_args['generate-conf-file']))
                app_instance = None
            else:
                app_instance = IRApplication(app_name, settings_dir, spec_args)

        else:
            raise exceptions.IRUnknownApplicationException(
                "Application is not supported: '{}'".format(app_name))
        return app_instance

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

    # todo(yfried): maybe move to spec?
    def get_arguments_dict(self):
        """
        Collect all spec.ValueArgument args in dict according to arg names

        some-key=value will be nested in dict as:

        {APPLICATION: {
            SUBCOMMAND: {
                "some": {
                    "key": value}
                }
            }
        }

        For spec.YamlFileArgument value is path to yaml so file content
        will be loaded as a nested dict

        :return: dict
        """
        settings_dict = {}

        for name, argument in self.args.iteritems():
            # if isinstance(argument, spec.YamlFileArgument):
            #     argument.find_file(self.settings_dir)
            if isinstance(argument, spec.ValueArgument):
                utils.dict_insert(settings_dict, argument.value,
                                  *argument.arg_name.split("-"))

        return {APPLICATION: {self.args["command0"]: settings_dict}}


class IRApplication(object):
    """
    Hold the default application workflow logic.
    """
    def __init__(self, name, settings_dir, args):
        self.name = name
        self.args = args
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
                cli.execute.ansible_playbook(CLEANUP_PLAYBOOK, self.args)
            else:
                cli.execute.ansible_playbook(PROVISION_PLAYBOOK, self.args)

    def collect_settings(self):
        settings_files = self.sub_command.get_settings_files()
        arguments_dict = self.sub_command.get_arguments_dict()

        # todo(yfried): fix after refactor
        # utils.dict_merge(settings_files, arguments_dict)
        # return self.lookup(settings_files)

        # todo(yfried) remove this line after refactor
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


def main():
    app = IRFactory.create(APPLICATION, CONF)
    if app:
        app.run()

if __name__ == '__main__':
    main()
