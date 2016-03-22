#!/usr/bin/env python

import os
import logging
from cli.install import set_network_template as set_network

import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import utils
from cli import exceptions
from cli import spec
import cli.yamls
import cli.execute

LOG = logger.LOG
CONF = conf.config

PROVISION_PLAYBOOK = "provision.yaml"
CLEANUP_PLAYBOOK = "cleanup.yaml"
NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output',
                        'input', 'dry-run', 'cleanup', 'inventory']


def process_topology_args(clg_args, app_settings_dir):
    """
    Merges topology files in a single topology dict.

    :param clg_args: Dictionary based on cmd-line args parsed by clg
    :param app_settings_dir: path to the base directory holding the
        application's settings. App can be provisioner\installer\tester
        and the path would be: settings/<app_name>/
    """

    # post process topology
    if clg_args.get("topology") is not None:
        topology_dict = {}
        for topology_item in clg_args['topology'].split(','):
            if '_' in topology_item:
                number, node_type = topology_item.split('_')
            else:
                raise exceptions.IRConfigurationException(
                    "Topology node should be in format  <number>_<node role>. "
                    "Current value: '{}' ".format(topology_item))
            # todo(obaraov): consider moving topology to config on constant.
            node_file = os.path.join(
                app_settings_dir, 'topology', node_type + '.yaml')
            with open(node_file) as stream:
                topology_dict[node_type] = yaml.load(stream)
                topology_dict[node_type]['amount'] = int(number)

        clg_args['topology'] = topology_dict


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
        settings_dir = CONF.get('defaults', 'settings')

        if app_name in ["provisioner", ]:
            app_settings_dir = os.path.join(settings_dir, app_name)
            args = spec.parse_args(app_settings_dir)
            cls.configure_environment(args)
            # todo(yfried): This should be in a more generic place
            process_topology_args(args, app_settings_dir)

            if args.get('generate-conf-file', None):
                LOG.debug('Conf file "{}" has been generated. Exiting'.format(
                    args['generate-conf-file']))
                app_instance = None
            else:
                app_instance = IRApplication(app_name, settings_dir, args)

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

        settings_files.extend(self._load_yaml_files())

        LOG.debug("All settings files to be loaded:\n%s" % settings_files)
        return settings_files

    def _load_yaml_files(self):
        # load directly from args
        settings_files = []
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
        return settings_files

    def get_settings_dict(self):
        return {}


class VirshCommand(IRSubCommand):

    def get_settings_dict(self):

        # todo(obaranov) this is virsh specific
        # rework that and make this part of lookup or something.
        image = dict(
            name=self.args['image-file'],
            base_url=self.args['image-server']
        )
        host = dict(
            ssh_host=self.args['host'],
            ssh_user=self.args['ssh-user'],
            ssh_key_file=self.args['ssh-key']
        )

        settings_dict = {'provisioner': {'image': image}}
        utils.dict_merge(settings_dict,
                         {'provisioner': {'hosts': {'host1': host}}})

        # load network and image settings
        for arg_dir in ('network',):
            if self.args[arg_dir] is None:
                raise exceptions.IRConfigurationException(
                    "A value for for the  '{}' "
                    "argument should be provided!".format(arg_dir))
            with open(set_network(self.args[arg_dir], os.path.join(
                    self.settings_dir, arg_dir))) as settings_file:
                settings = yaml.load(settings_file)
            utils.dict_merge(settings_dict, settings)

        # inject topology from args to the required fro virsh place.
        utils.dict_merge(
            settings_dict,
            {'provisioner': {'nodes': self.args['topology']}})
        return settings_dict

    def _load_yaml_files(self):
        # do not load additional yaml files.
        return []


class BeakerCommand(IRSubCommand):

    def get_settings_dict(self):
        host0 = dict(
            server_url=self.args['base-url'],
            remote_user=self.args['username'],
            remote_pass=self.args['password'],
            fqdn=self.args['fqdn'],
            action=self.args['action'],
            distro_tree_id=self.args['distro-tree']
        )

        return {'provisioner': {'hosts': {'host0': host0}}}

    def _load_yaml_files(self):
        # do not load additional yaml files.
        return []


class IRApplication(object):
    """
    Hold the default application workflow logic.
    """
    def __init__(self, name, settings_dir, args):
        self.name = name
        self.args = args
        self.settings_dir = settings_dir

        # todo(obaranov) replace with subcommand factory
        sc = {'virsh': VirshCommand, 'beaker': BeakerCommand}[args['command0']]
        self.sub_command = sc.create(name, settings_dir, args)

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
        settings_dict = self.sub_command.get_settings_dict()

        return self.lookup(settings_files, settings_dict)

    def lookup(self, settings_files, settings_dict):
        """
        Replaces a setting values with !lookup
        in the setting files by values from
        other settings files.
        """

        cli.yamls.Lookup.settings = utils.generate_settings(settings_files)
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
    app = IRFactory.create('provisioner', CONF)
    if app:
        app.run()

if __name__ == '__main__':
    main()
