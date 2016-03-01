#!/usr/bin/env python

import os

import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import utils
import cli.yamls
import cli.execute

LOG = logger.LOG
CONF = conf.config

NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                        'input-files', 'dry-run', 'cleanup', 'inventory']


class IRFactory(object):
    """
    Creates and configures the IR applications.
    """

    @classmethod
    def create(cls, app_name, config):
        """
        Create the application object
        by module name and provided configuration.
        """
        if app_name in ["provisioner", ]:
            args = conf.SpecManager.parse_args(app_name, config)
            cls.configure_environment(args)
            setting_dir = utils.validate_settings_dir(
                CONF.get('defaults', 'settings'))
            app_instance = IRApplication(app_name, setting_dir, args)

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
        LOG.setLevel((WARNING, INFO)[args.verbose]
                     if args.verbose < 2 else DEBUG)


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
        if hasattr(args, "command0"):
            settings_dir = os.path.join(settings_dir,
                                        args['command0'])
        return cls(args['command0'], args, settings_dir)

    def get_settings_files(self):
        """
        Collects all the settings files for given application and sub-command
        """
        settings_files = []

        # first take all the files from the input-files args
        for input_file in self.args['input-files'] or []:
            settings_files.append(utils.normalize_file(input_file))

        # get the sub-command yml file
        settings_files.append(os.path.join(
            self.settings_dir,
            self.name + '.yml'))

        # load directly from args
        for key, val in vars(self.args).iteritems():
            if val is not None and key not in NON_SETTINGS_OPTIONS:
                settings_file = os.path.join(
                    self.settings_dir, key, val + '.yml')
                LOG.debug('Searching settings file for the "%s" key...' % key)
                if not os.path.isfile(settings_file):
                    settings_file = utils.normalize_file(val)
                settings_files.append(settings_file)
                LOG.debug('"%s" was added to settings '
                          'files list as an argument '
                          'for "%s" key' % (settings_file, key))

        LOG.debug("All settings files to be loaded:\n%s" % settings_files)
        return settings_files


class IRApplication(object):
    """
    Hold the default application workflow logic.
    """
    def __init__(self, name, settings_dir, args):
        self.name = name
        self.args = args
        self.settings_dir = settings_dir
        self.sub_command = IRSubCommand.create(name, settings_dir, args)

    def run(self):
        """
        :return: Runs the application
        """
        settings = self.lookup(self.sub_command.get_settings_files())
        self.dump_settings(settings)
        self.execute(settings)

    def lookup(self, settings_files):
        """
        Replaces a setting values with !lookup
        in the setting files by values from
        other settings files.
        """
        cli.yamls.Lookup.settings = utils.generate_settings(
            settings_files,
            self.args['extra-vars'])
        cli.yamls.Lookup.in_string_lookup()

        return cli.yamls.Lookup.settings

    def dump_settings(self, settings):
        LOG.debug("Dumping settings...")
        output = yaml.safe_dump(settings,
                                default_flow_style=False)
        if self.args['output-file']:
            with open(self.args['output-file'], 'w') as output_file:
                output_file.write(output)
        else:
            print output

    def execute(self, settings):
        """
        Executes a playbook.
        """
        if not self.args['dry-run']:
            vars(self.args)['settings'] = yaml.load(yaml.safe_dump(
                settings,
                default_flow_style=False))
            if not self.args['cleanup']:
                vars(self.args)['provision'] = True

            cli.execute.ansible_wrapper(self.args)

        cli.execute.ansible_wrapper(args)

def main():
    app = IRFactory.create('provisioner', CONF)
    app.run()

if __name__ == '__main__':
    main()
