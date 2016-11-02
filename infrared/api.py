# provides API to run plugins
import argparse
import logging
import multiprocessing
import os
import sys
import yaml

from infrared import SHARED_GROUPS
from infrared.core.inspector.inspector import SpecParser
from infrared.core.settings import SettingsManager
from infrared.core.services import CoreServices
from infrared.core.utils import exceptions
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
    """Infrared plugin specification."""

    add_base_groups = True

    ANSIBLE_FOLDERS = ["library", "callbacks", "plugins", "templates"]
    ANSIBLE_FILES = ["ansible.cfg"]

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

        # '--generate-conf-file' - Finish execution after creation of conf file
        if pargs is None:
            return

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

            inventory = control_args.get('inventory', 'hosts')

            # copy all the required data to the plugin folder
            active_profile = CoreServices.profile_manager().get_active_profile()

            if not active_profile:
                raise exceptions.IRNoActiveProfileFound()

            invnetory_name = self.capture_plugin_to_profile(
                active_profile, inventory)

            LOG.debug("Inventory file used: %s", invnetory_name)
            proc = multiprocessing.Process(
                target=self._ansible_worker,
                args=(active_profile.path, playbook,),
                kwargs=dict(
                    module_path=self.plugin.modules_dir,
                    verbose=control_args.get('verbose', None),
                    settings=playbook_settings,
                    inventory=invnetory_name
                ))
            proc.start()
            proc.join()
            if proc.exitcode:
                # soemthing wrong happened in child process.
                exit(proc.exitcode)

    def capture_plugin_to_profile(self, profile, inventory):
        """
        Copies a plugin data to the profile folder.

        Returns the profile path and new inventory path.
        """
        LOG.debug("Initializing the '%s' profile...", profile.name)

        # clear data from previous run
        profile.clear_links()

        # get the plugin configured folders
        folders = []
        for _, fodlers in self.plugin.folders_config.items():
            folders.extend(fodlers.split(os.pathsep))
        folders.extend(self.ANSIBLE_FOLDERS)

        for lib in folders:
            lib_abs_path = os.path.join(os.path.abspath(
                self.plugin.root_dir), lib)
            if os.path.exists(lib_abs_path):
                profile.link_file(lib_abs_path)

        # ansible cfg can be changes by executor/playbooks.
        # so keep it copy
        for plugin_file in self.ANSIBLE_FILES:
            file_abs_path = os.path.join(
                os.path.abspath(self.plugin.root_dir), plugin_file)
            profile.copy_file(file_abs_path)

        # resolve invnetory file
        # first look in the current dir, then in plugin dir, then in profile dir
        new_inventory = profile.copy_file(
            inventory, additional_lookup_dirs=(self.plugin.root_dir, profile.path))

        return new_inventory

    @staticmethod
    def _ansible_worker(root_dir, playbook,
                        module_path, verbose, settings, inventory):
        # hack to change cwd to the plugin root folder
        os.environ['PWD'] = os.path.abspath(root_dir)
        os.chdir(root_dir)
        # import here cause it will init ansible in correct plugin folder.
        from infrared.core import execute
        result = execute.ansible_playbook(playbook,
                                          module_path=module_path,
                                          verbose=verbose,
                                          settings=settings,
                                          inventory=inventory)
        sys.exit(result)


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
