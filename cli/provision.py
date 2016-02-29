#!/usr/bin/env python

import os

from cli import logger  # logger creation is first thing to be done
import cli.execute
import cli.yamls
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
    Creates and configures tha IR applications.
    """
    from logging import WARNING, INFO, DEBUG
    LOG.setLevel((WARNING, INFO)[level] if level < 2 else DEBUG)

    NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                            'input-files', 'dry-run', 'cleanup', 'inventory']

    @classmethod
    def create(cls, app_name, config):
        """
        Create the application object
        by module name and provided configuration.
        """
        if app_name in ["provisioner", ]:
            args = conf.SpecManager.parse_args(app_name, config)
            settings_files = cls.configure(app_name, config, args)
            app_instance = IRApplication(app_name, args, settings_files)

        else:
            raise Exception("Application is not supported: '{}'".format(app_name))
        return app_instance

    @classmethod
    def configure(cls, app_name, config, args):
        cls._configure_log(args)
        settings_files = cls._collect_settings_files(app_name, config, args)
        LOG.debug("All settings files to be loaded:\n%s" % settings_files)
        return settings_files

    @classmethod
    def _configure_log(cls, args):
        """
        Perfroms the logging module configuration.
        :return:
        """
        from logging import WARNING, INFO, DEBUG
        LOG.setLevel((WARNING, INFO)[args.verbose]
                     if args.verbose < 2 else DEBUG)

    @classmethod
    def _collect_settings_files(cls, app_name, config, args):
        """
        Collects all the settings files for given module and sub-command
        """
        settings_files = []
        settings_dir = utils.validate_settings_dir(
            config.get('defaults', 'settings'))
        module_dir = os.path.join(
            settings_dir,
            app_name,
            args.command0)

        # first take all the files from the input-files args
        for input_file in args['input-files'] or []:
            settings_files.append(utils.normalize_file(input_file))

        # get the sub-command yml file
        settings_files.append(os.path.join(
            module_dir,
            args.command0 + '.yml'))

        # load directly from args
        for key, val in vars(args).iteritems():
            if val is not None and key not in cls.NON_SETTINGS_OPTIONS:
                settings_file = os.path.join(module_dir, key, val + '.yml')
                LOG.debug('Searching settings file for the "%s" key...' % key)
                if not os.path.isfile(settings_file):
                    settings_file = utils.normalize_file(val)
                settings_files.append(settings_file)
                LOG.debug('"%s" was added to settings '
                          'files list as an argument '
                          'for "%s" key' % (settings_file, key))

        return settings_files

    cli.yamls.Lookup.in_string_lookup()

class IRApplication(object):
    """
    Hold the default application workflow logic.
    """
    def __init__(self, name, args, settings_files):
        self.name = name
        self.args = args
        self.settings_files = settings_files

    def run(self):
        """
        :return: Runs the application
        """
        settings = self.lookup(self.settings_files)
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
            vars(self.args)['settings'] = settings
            if not self.args['cleanup']:
                vars(self.args)['provision'] = True

        cli.execute.ansible_wrapper(self.args)


def main():
    app = IRFactory.create('provisioner', CONF)
    app.run()

if __name__ == '__main__':
    main()
