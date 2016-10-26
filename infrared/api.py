# provides AP Ito run plugins
import argparse
import logging
import multiprocessing
import os
import yaml

from infrared import SHARED_GROUPS
from infrared.core.inspector.inspector import SpecParser
from infrared.core.settings import SettingsManager
from infrared.core.utils import logger

LOG = logger.LOG


class SpecObject(object):
    """
    Base object to describe basic specification.
    """
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def get_name(self):
        return self.name

    def extend_cli(self, root_subparsers):
        """
        Adds the spec cli options to to the main entry point.
        :param root_subparsers: the subprasers objects to extend.
        """
        pass

    def spec_handler(self, parser, args):
        """
        The main method for the spec.

        This method will be called by the spec managers once the subcommand
        with the spec name is called from cli.
        :param parser:
        :param args:
        :return:
        """
        raise NotImplemented()


class DefaultInfraredPluginSpec(SpecObject):
    add_base_groups = True

    def __init__(self, plugin):
        self.plugin = plugin
        self.specification = None
        super(DefaultInfraredPluginSpec, self).__init__(self.plugin.name)

    def extend_cli(self, root_subparsers):
        user_dict = {}
        if self.add_base_groups:
            user_dict = dict(
                description=self.plugin.description,
                shared_groups=SHARED_GROUPS)
        self.specification = SpecParser.from_folder(
            self.plugin.settings_folders(),
            self.plugin.name,
            user_dict=user_dict,
            subparser=root_subparsers)

    def spec_handler(self, parser, args):
        if self.specification is None:
            raise Exception("Unable to create specification for '{}' plugin."
                            "Check plugin config and settings folders".format(
                             self.name))
        # perform additional arguments validation for a plugin.
        pargs = self.specification.parse_args(parser)
        nested_args = pargs[0]
        control_args = pargs[1]
        unknown_args = pargs[2]
        subcommand_name = control_args['command0']

        if control_args.get('debug', None):
            logger.LOG.setLevel(logging.DEBUG)

        settings = SettingsManager.generate_settings(
            self.plugin.name,
            nested_args,
            self.plugin.subcommand_settings_files(subcommand_name),
            input_files=control_args.get('input', []),
            extra_vars=control_args.get('extra-vars', None),
            dump_file=control_args.get('output', None))

        if not control_args.get('dry-run'):
            playbook_settings = yaml.load(yaml.safe_dump(
                settings,
                default_flow_style=False))

            if control_args.get('cleanup', None):
                playbook = self.plugin.cleanup_playbook
            else:
                playbook = self.plugin.main_playbook

            inventory = control_args.get('inventory', 'local_hosts')

            # try to find file within the plugin folder
            # TODO(obaranov) probably this is not a good idea.
            # but it simplifies
            if not os.path.isfile(inventory):
                plugin_rel_invnetory = os.path.join(self.plugin.root_dir, inventory)
                if os.path.isfile(plugin_rel_invnetory):
                    inventory = plugin_rel_invnetory
                    LOG.warn("Using inventory file from the plugin folder: %s", inventory)
            inventory = self.__expand_path(inventory)

            proc = multiprocessing.Process(
                target=self._ansible_worker,
                args=(self.plugin.root_dir, playbook,),
                kwargs=dict(
                    module_path=self.plugin.modules_dir,
                    verbose=control_args.get('verbose', None),
                    settings=playbook_settings,
                    inventory=inventory
                ))
            proc.start()
            proc.join()
            if proc.exitcode:
                # soemthing wrong happened in child process.
                exit(proc.exitcode)

    @staticmethod
    def _ansible_worker(root_dir, playbook,
                        module_path, verbose, settings, inventory):
        # hack to change cwd to the plugin root folder
        os.environ['PWD'] = os.path.abspath(root_dir)
        os.chdir(root_dir)
        # import here cause it will init ansible in correct plugin folder.
        from infrared.core import execute
        execute.ansible_playbook(playbook,
                                 module_path=module_path,
                                 verbose=verbose,
                                 settings=settings,
                                 inventory=inventory)

    def __expand_path(self, path):
        """
        Returns the absolute path or None
        """
        res = None
        if path:
            res = os.path.abspath(path)
        return res


class SpecManager(object):
    """
    Manages all the available specifications (specs).
    """

    def __init__(self):
        # create entry point
        self.parser = argparse.ArgumentParser(
            description='Infrared entry point')
        self.root_subparsers = self.parser.add_subparsers(dest="subcommand")
        self.spec_objects = {}

    def register_spec(self, spec_object):
        spec_object.extend_cli(self.root_subparsers)
        self.spec_objects[spec_object.get_name()] = spec_object

    def run_specs(self):
        args = vars(self.parser.parse_args())
        subcommand = args.get('subcommand', '')

        if subcommand in self.spec_objects:
            self.spec_objects[subcommand].spec_handler(self.parser, args)
