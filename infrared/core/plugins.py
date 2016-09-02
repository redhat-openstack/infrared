import os
import tempfile
import shutil
import ConfigParser
import yaml
import git

from infrared.core.utils import logger

LOG = logger.LOG


class Plugin(object):
    def __init__(self, name, root_dir, config):
        self.config = config
        self.root_dir = root_dir
        self.name = name

    def settings_folders(self):
        return [os.path.join(self.root_dir, sf)
                for sf in self.config['settings'].split(os.pathsep)]

    @property
    def cleanup_playbook(self):
        return os.path.join(
            self.root_dir,
            self.config['playbooks'],
            self.config['entry_points']['cleanup'])

    @property
    def main_playbook(self):
        return os.path.join(
            self.root_dir,
            self.config['playbooks'],
            self.config['entry_points']['main'])

    @property
    def modules_dir(self):
        return os.path.join(self.root_dir, self.config['modules'])

    @classmethod
    def from_settings(cls, name, plugin_settings):
        """
        Creates pluigins from the settings dict.
        """
        return Plugin(
            name,
            plugin_settings['root_dir'],
            plugin_settings['config'])

    def subcommand_settings_files(self, subcommand_name, extension='.yml'):
        result = []
        for sf in self.settings_folders():
            settings_file = os.path.join(
                sf, subcommand_name, subcommand_name + extension)

        if os.path.exists(settings_file):
            result.append(settings_file)

        return result

    def __repr__(self):
        return repr(dict(
            name=self.name,
            root_dir=self.root_dir,
            config=self.config))


class PluginsManager(object):
    PLUGIN_SETTINGS = 'plugins/settings.yml'
    PLUGIN_CONFIG_FILE_NAME = 'infrared.cfg'

    @classmethod
    def get_settings(cls):
        with open(cls.PLUGIN_SETTINGS, 'r') as stream:
            settings = yaml.load(stream)
            if settings is None:
                settings = dict()
            return settings

    @classmethod
    def write_settings(cls, settings):
        with open(cls.PLUGIN_SETTINGS, 'w') as stream:
            yaml.dump(settings, stream, default_flow_style=False)

    @classmethod
    def add(cls, name, uri, branch=None):
        """
        Adds new plugins to the settings.
        """
        settings = cls.get_settings()
        if name not in settings:
            settings[name] = dict(
                uri=uri,
                branch=branch or ''
            )

            cls.write_settings(settings)
            LOG.info('Pluging added: %s', name)
        else:
            LOG.warn("Plugin '%s' already exists", name)

    @classmethod
    def iter_plugins(cls):
        settings = cls.get_settings()
        for name, plugin_settings in settings.items():
            yield Plugin.from_settings(name, plugin_settings)

    @classmethod
    def get_plugin(cls, name):
        settings = cls.get_settings()
        return Plugin.from_settings(name, settings[name])
    #
    # @classmethod
    # def update(cls, name):
    #     settings = cls.get_settings()
    #     plugin_settings = settings[name]
    #     tempdir = tempfile.mkdtemp()
    #
    #     try:
    #         # clone
    #         uri = plugin_settings['uri']
    #         branch = plugin_settings.get('branch', '')
    #         LOG.info("Cloning '%s' into '%s'", uri, tempdir)
    #         repo = git.Repo.clone_from(
    #             uri,
    #             tempdir)
    #         if branch:
    #             repo.git.checkout(branch)
    #         # check for config file
    #         plugin_config = os.path.join(tempdir, cls.PLUGIN_CONFIG_FILE_NAME)
    #         if not os.path.isfile(plugin_config):
    #             raise Exception("Plugin config '%s' was not found".format(
    #                 cls.PLUGIN_CONFIG_FILE_NAME))
    #         else:
    #             LOG.info("Plugin config found: '%s'", plugin_config)
    #         config = ConfigParser.ConfigParser()
    #         config.has_option
    #         with open(plugin_config) as fd:
    #             config.readfp(fd)
    #             # copy plugin folders
    #
    #             cls.copy_plugin(
    #                 os.path.join('./plugins', name),
    #                 settings=os.path.join(tempdir, cls._get_conf_option(
    #                     config, 'defaults', 'settings', 'settings')),
    #                 modules=os.path.join(tempdir, cls._get_conf_option(
    #                     config, 'defaults', 'modules', 'modules')),
    #                 roles=os.path.join(tempdir, cls._get_conf_option(
    #                     config, 'defaults', 'roles', 'roles')),
    #                 playbooks=os.path.join(tempdir, cls._get_conf_option(
    #                     config, 'defaults', 'playbooks', 'playbooks')),
    #                 templates=os.path.join(tempdir, cls._get_conf_option(
    #                     config, 'defaults', 'templates', 'templates'))
    #             )
    #
    #     finally:
    #         if os.path.isdir(tempdir):
    #             LOG.info("Cleaning temporary git repo...")
    #             shutil.rmtree(tempdir)
    #         pass
    #
    # @classmethod
    # def copy_plugin(cls, target_folder, settings, modules, roles,
    #                 playbooks, templates):
    #     # cleanup plugin folder
    #     if os.path.isdir(target_folder):
    #         shutil.rmtree(target_folder)
    #
    #     folders = {
    #         os.path.join(target_folder, "settings"): settings,
    #         os.path.join(target_folder, "modules"): modules,
    #         os.path.join(target_folder, "roles"): roles,
    #         os.path.join(target_folder, "playbooks"): playbooks,
    #         os.path.join(target_folder, "templates"): templates,
    #     }
    #     for dest, src in folders.items():
    #         if os.path.isdir(src):
    #             LOG.info("Copying '%s'", dest)
    #             shutil.copytree(src, dest)

    @classmethod
    def _get_conf_option(cls, config, section, option, default):
        value = None
        if config.has_option(section, option):
            value = config.get(section, option)
        else:
            value = default
        return value
