from ConfigParser import ConfigParser
from collections import OrderedDict
import datetime
import os
import shutil
import tempfile
import time
import yaml
import git
import github

# TODO(aopincar): Add pip to the project's requirements
import pip

from infrared.core.utils import logger
from infrared.core.utils.exceptions import IRFailedToAddPlugin, IRException
from infrared.core.utils.exceptions import IRFailedToRemovePlugin
from infrared.core.utils.exceptions import IRFailedToUpdatePlugin
from infrared.core.utils.exceptions import IRUnsupportedPluginType


DEFAULT_PLUGIN_INI = dict(
    supported_types=OrderedDict([
        ('provision', 'Provisioning plugins'),
        ('install', 'Installing plugins'),
        ('test', 'Testing plugins'),
        ('other', 'Other type plugins'),
    ])
)


MAIN_PLAYBOOK = "main.yml"
PLUGINS_DIR = os.path.abspath("./plugins")
LOG = logger.LOG
PLUGINS_REGISTRY_FILE = os.path.join(PLUGINS_DIR, "registry.yaml")

with open(PLUGINS_REGISTRY_FILE, "r") as fo:
    PLUGINS_REGISTRY = yaml.load(fo)


class InfraredPluginManager(object):
    PLUGINS_DICT = OrderedDict()
    SUPPORTED_TYPES_SECTION = 'supported_types'

    def __init__(self, plugins_conf=None):
        """
        :param plugins_conf: A path to the main plugins configuration file
        """
        self.config = plugins_conf
        self._load_plugins()

    def _load_plugins(self):
        self.__class__.PLUGINS_DICT.clear()
        for plugin_type_section in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            if self.config.has_section(plugin_type_section):
                for plugin_name, plugin_path in self.config.items(
                        plugin_type_section):
                    try:
                        plugin = InfraredPlugin(plugin_path)
                        self.__class__.PLUGINS_DICT[plugin_name] = plugin
                    except Exception as e:
                        LOG.warning("Failed to load %s plugin from %s due to "
                                    % (plugin_name, plugin_path, e))

    def get_installed_plugins(self, plugins_type=None):
        """Returns a dict with all installed plugins

        The return dictionary contains all installed plugins with their
        descriptions & categorized by plugin type.

        :param plugins_type: A specific type of plugins to return
        """
        plugins_dict = OrderedDict()

        for supported_type in self.supported_plugin_types:
            if plugins_type:
                if plugins_type != supported_type:
                    continue
                elif plugins_type not in self.supported_plugin_types:
                    raise IRUnsupportedPluginType(plugins_type)

            if not self.config.has_section(supported_type):
                continue
            else:
                plugins_dict[supported_type] = {}

            for plugin_name in self.config.options(supported_type):
                plugin_desc = self.PLUGINS_DICT[plugin_name].description

                plugins_dict[supported_type][plugin_name] = plugin_desc

        if plugins_type:
            return plugins_dict.get(plugins_type, {})

        return plugins_dict

    def get_all_plugins(self):
        """Returns a dict with all available plugins

        The return dictionary contains all available plugins (installed & not
        installed) with their descriptions & categorized by plugin type.
        """
        type_based_plugins_dict = self.get_installed_plugins()
        installed_plugins_set = \
            set([plugin_name for plugins_of_type in
                 type_based_plugins_dict.values() for plugin_name in
                 plugins_of_type])

        for plugin_name in PLUGINS_REGISTRY.keys():
            if plugin_name not in installed_plugins_set:
                plugin_type = PLUGINS_REGISTRY[plugin_name]['type']
                plugin_desc = PLUGINS_REGISTRY[plugin_name]['desc']
                if plugin_type not in type_based_plugins_dict:
                    type_based_plugins_dict[plugin_type] = {}
                type_based_plugins_dict[plugin_type][plugin_name] = plugin_desc

        return type_based_plugins_dict

    def get_github_organization_plugins(self, organization, no_forks=False):
        """
        Returns a dict with all plugins from a GitHub organization
        inspired from: https://gist.github.com/ralphbean/5733076
        :param organization: GitHub organization name
        :param no_forks: include / not include forks
        """
        plugins_dict = OrderedDict()

        try:
            gh = github.Github()
            gh.get_organization(organization)
            all_repos = gh.get_organization("rhos-infra").get_repos()
        except github.RateLimitExceededException:
            raise IRException("Github API rate limit exceeded")

        for repo in all_repos:

            try:
                # Don't print the urls for repos that are forks.
                if no_forks and repo.fork:
                    continue

                spec_file = repo.get_contents('plugin.spec').decoded_content

                plugin = InfraredPlugin.spec_content_validator(spec_file)
                plugin_name = plugin["subparsers"].keys()[0]
                plugin_type = plugin["plugin_type"]
                plugin_src = repo.clone_url
                plugin_desc = plugin["description"] \
                    if "description" in plugin \
                       and plugin["description"] is not None \
                    else "-"

                if plugin_type not in plugins_dict:
                    plugins_dict[plugin_type] = {}

                plugins_dict[plugin_type][plugin_name] = {
                    "src": plugin_src,
                    "desc": plugin_desc,
                }

            except github.RateLimitExceededException:
                raise IRException("Github API rate limit exceeded")
            except Exception:
                # skip repo failures
                continue

        return plugins_dict

    @property
    def config_file(self):
        return self._config_file

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, plugins_conf):
        plugins_conf_full_path = \
            os.path.abspath(os.path.expanduser(plugins_conf))

        init_plugins_conf = False
        if not os.path.isfile(plugins_conf_full_path):
            LOG.warning("Plugin conf ('{}') not found, creating it with "
                        "default data".format(plugins_conf_full_path))
            init_plugins_conf = True
            with open(plugins_conf_full_path, 'w') as fp:
                config = ConfigParser()

                for section, section_data in DEFAULT_PLUGIN_INI.items():
                    if not config.has_section(section):
                        config.add_section(section)
                    for option, value in section_data.items():
                        config.set(section, option, value)

                config.write(fp)

        self._config_file = plugins_conf_full_path

        with open(plugins_conf_full_path) as fp:
            self._config = ConfigParser()
            self.config.readfp(fp)

        # TODO(aopincar): Remove auto plugins installation when conf is missing
        if init_plugins_conf:
            self.add_all_available()

    def get_desc_of_type(self, s_type):
        """Returns the description of the given supported plugin type

        :param s_type: The type of the plugin you want the description
        :return: String of the supported plugin description
        """
        return self.config.get(self.SUPPORTED_TYPES_SECTION, s_type)

    @classmethod
    def get_plugin(cls, plugin_name):
        """Returns an instance of plugin based on name

        :param plugin_name: Plugin name
        :return: InfraredPlugin instance
        """
        return cls.PLUGINS_DICT[plugin_name]

    def __iter__(self):
        for plugin in self.PLUGINS_DICT.iteritems():
            yield plugin
        else:
            raise StopIteration

    @staticmethod
    def _clone_git_plugin(git_url, repo_plugin_path=None, rev=None,
                          dest_dir=None):
        """Clone a plugin into a given destination directory

        :param git_url: Plugin's Git URL
        :param dest_dir: destination where to clone a plugin into (if 'source'
          is a Git URL)
        :param repo_plugin_path: path in the Git repo where the infrared plugin
          is defined
        :param rev: git branch/tag/revision
        :return: Path to plugin cloned directory (str)
        """
        dest_dir = os.path.abspath(dest_dir or "plugins")
        plugin_git_name = os.path.split(git_url)[-1].split('.')[0]

        tmpdir = tempfile.mkdtemp(prefix="ir-")
        cwd = os.getcwdu()
        os.chdir(tmpdir)
        try:
            repo = git.Repo.clone_from(
                url=git_url, to_path=os.path.join(tmpdir, plugin_git_name))
            if rev is not None:
                repo.git.checkout(rev)
        except (git.exc.GitCommandError) as e:
            shutil.rmtree(tmpdir)
            raise IRFailedToAddPlugin(
                "Cloning git repo {} is failed: {}".format(git_url, e))

        plugin_tmp_source = os.path.join(tmpdir, plugin_git_name)
        if repo_plugin_path:
            plugin_tmp_source = os.path.join(plugin_tmp_source, repo_plugin_path)

        # validate & load spec data in order to pull the name of the plugin
        spec_data = InfraredPlugin.spec_validator(
            os.path.join(plugin_tmp_source, InfraredPlugin.PLUGIN_SPEC_FILE))
        # get the real plugin name from spec
        plugin_dir_name = spec_data["subparsers"].keys()[0]

        plugin_source = os.path.join(dest_dir, plugin_dir_name)
        if os.path.islink(plugin_source):
            LOG.debug("%s found as symlink pointing to %s, unlinking it, not touching the target.",
                      plugin_source,
                      os.path.realpath(plugin_source))
            os.unlink(plugin_source)
        elif os.path.exists(plugin_source):
            shutil.rmtree(plugin_source)

        shutil.copytree(os.path.join(tmpdir, plugin_git_name),
                        plugin_source)

        if repo_plugin_path:
            plugin_source = plugin_source + '/' + repo_plugin_path

        os.chdir(cwd)
        shutil.rmtree(tmpdir)

        return plugin_source

    def update_plugin(self, plugin_name, revision=None,
                      skip_reqs=False, hard_reset=False):
        """Updates a Git-based plugin

        Pulls changes from the remote, and checkout a specific revision.
        (will point to the tip of the branch if revision isn't given)
        :param plugin_name: Name of plugin to update.
        :param revision: Revision to checkout.
        :param skip_reqs: If True, will skip plugin requirements installation.
        :param hard_reset: Whether to drop all changes using git hard reset
        """
        if plugin_name not in self.PLUGINS_DICT:
            raise IRFailedToUpdatePlugin(
                "Plugin '{}' isn't installed".format(plugin_name))

        repo = plugin = None
        try:
            plugin = self.get_plugin(plugin_name)
            repo = git.Repo(plugin.path)

            # microseconds ('%f') required for unit testing
            timestamp = \
                datetime.datetime.fromtimestamp(
                    time.time()).strftime('%B-%d-%Y_%H-%M-%S-%f')
            update_string = \
                'IR_Plugin_update_{plugin_name}_{timestamp}' \
                ''.format(plugin_name=plugin_name, timestamp=timestamp)

            LOG.debug("Checking for changes of tracked files "
                      "in {}".format(plugin.path))
            changed_tracked_files = \
                repo.git.status('--porcelain', '--untracked-files=no')
            all_changed_files = repo.git.status('--porcelain')

            if changed_tracked_files and not hard_reset:
                raise IRFailedToUpdatePlugin(
                    "Failed to update plugin {}\n"
                    "Found changes in tracked files, "
                    "please go to {}, and manually save "
                    "your changes!".format(plugin_name, plugin.path))

            if hard_reset:
                if all_changed_files:
                    repo.git.stash('save', '-u', update_string)
                    LOG.warning("All changes have been "
                                "stashed - '{}'".format(update_string))
                repo.git.reset('--hard', 'HEAD')

            LOG.warning("Create a branch '{}' that will point "
                        "to the current HEAD".format(update_string))
            repo.git.branch(update_string)

            LOG.debug("Fetching changes from the "
                      "'{}' remote".format(repo.remote().name))
            repo.git.fetch(repo.remote().name)

            repo.git.pull('--rebase')
            if revision not in (None, 'latest'):
                repo.git.reset(revision)
                if hard_reset:
                    repo.git.reset('--hard', 'HEAD')

            if repo.git.status('--porcelain', '--untracked-files=no'):
                LOG.warning("Changes in tracked files have been found")

            if not skip_reqs:
                reqs_file = os.path.join(plugin.path, 'requirements.txt')
                if os.path.isfile(reqs_file):
                    pip.main(['install', '-r', reqs_file])

        except git.InvalidGitRepositoryError:
            raise IRFailedToUpdatePlugin(
                "Plugin '{}' isn't a Git-based plugin".format(plugin_name))
        except ValueError:
            raise IRFailedToUpdatePlugin(
                "Failed to update '{}' plugin to point to '{}'".format(
                    plugin_name, revision))
        except git.exc.GitCommandError as ex:
            repo.git.rebase('--abort')
            raise IRFailedToUpdatePlugin(
                "Failed to update plugin"
                "Failed to update plugin!\nPlease go to plugin dir ({})"
                " and manually resolve Git issues.\n"
                "{}\n{}".format(plugin.path, ex.stdout, ex.stderr))

    def add_plugin(self, plugin_source, rev=None, dest=None):
        """Adds (install) a plugin

        :param plugin_source: Plugin source.
          Can be:
            1. Plugin name (from available in registry)
            2. Path to a local directory
            3. Git URL
        :param dest: destination where to clone a plugin into (if 'source' is
          a Git URL)
        :param rev: git branch/tag/revision
        """
        plugin_data = {}
        # Check if a plugin is in the registry
        if plugin_source in PLUGINS_REGISTRY:
            plugin_data = PLUGINS_REGISTRY[plugin_source]
            plugin_source = PLUGINS_REGISTRY[plugin_source]['src']

        # Local dir plugin
        if os.path.exists(plugin_source):
            pass
        # Git Plugin
        else:
            if rev is None:
                rev = plugin_data.get('rev')
            plugin_src_path = plugin_data.get('src_path', '')
            plugin_source = self._clone_git_plugin(
                plugin_source, plugin_src_path, rev,
                dest)

        plugin = InfraredPlugin(plugin_source)
        plugin_type = plugin.config['plugin_type']
        # FIXME(yfried) validate spec and throw exception on missing input

        if plugin_type not in self.config.options(
                self.SUPPORTED_TYPES_SECTION):
            raise IRFailedToAddPlugin(
                "Unsupported plugin type: '{}'".format(plugin_type))

        if not self.config.has_section(plugin_type):
            self.config.add_section(plugin_type)
        elif self.config.has_option(plugin_type, plugin.name):
            raise IRFailedToAddPlugin(
                "Plugin with the same name & type already exists")

        self.config.set(plugin_type, plugin.name, plugin.path)

        with open(self.config_file, 'w') as fp:
            self.config.write(fp)

        self._install_requirements(plugin_source)
        self._load_plugins()

    def add_all_available(self):
        """Add all available plugins which aren't already installed"""
        for plugin in set(PLUGINS_REGISTRY) - \
                set(self.PLUGINS_DICT):
            self.add_plugin(plugin)
            LOG.warning(
                "Plugin '{}' has been successfully installed".format(plugin))

    def remove_plugin(self, plugin_name, forced=False):
        """Removes an installed plugin

        :param plugin_name: Plugin name to be removed
        """
        if plugin_name not in self.PLUGINS_DICT:
            if forced:
                return
            else:
                raise IRFailedToRemovePlugin(
                    "Plugin '{}' isn't installed and can't be removed".format(
                        plugin_name))

        plugin = InfraredPluginManager.get_plugin(plugin_name)

        self.config.remove_option(plugin.type, plugin_name)
        if not self.config.options(plugin.type):
            self.config.remove_section(plugin.type)
        with open(self.config_file, 'w') as fp:
            self.config.write(fp)
        self._load_plugins()

    def remove_all(self, forced=False):
        for plugin in self.PLUGINS_DICT:
            self.remove_plugin(plugin, forced=forced)
            LOG.warning(
                "Plugin '{}' has been successfully removed".format(plugin))

    @property
    def supported_plugin_types(self):
        return self.config.options(self.SUPPORTED_TYPES_SECTION)

    @staticmethod
    def _install_requirements(plugin_path):
        requirement_file = os.path.join(plugin_path, "plugin_requirements.txt")
        if os.path.isfile(requirement_file):
            LOG.info(
                "Installing requirements from: {}".format(requirement_file))
            pip_args = ['install', '-r', requirement_file]
            pip.main(args=pip_args)

    def freeze(self):
        for section in self.config.sections():
            if section == "supported_types":
                continue
            for name, path in self.config.items(section):
                if name not in PLUGINS_REGISTRY:
                    with open(os.path.join(path, "plugin.spec"), "r") as pls:
                        plugin_spec = yaml.load(pls)
                    PLUGINS_REGISTRY[name] = dict(
                        type=plugin_spec["plugin_type"],
                        desc=plugin_spec[
                            "subparsers"].items()[0][1]["description"])
                try:
                    repo = git.Repo(path)
                    PLUGINS_REGISTRY[name]["src"] = list(
                        repo.remote().urls)[-1].encode("ascii")
                    PLUGINS_REGISTRY[name]["rev"] = repo.head.commit.hexsha.encode("ascii")
                except git.InvalidGitRepositoryError:
                    PLUGINS_REGISTRY[name]["src"] = path.replace(
                        "".join([os.path.split(PLUGINS_DIR)[0],
                                 os.path.sep]), "")

        with open(PLUGINS_REGISTRY_FILE, "w") as fd:
            yaml.dump(PLUGINS_REGISTRY, fd, default_flow_style=False,
                      explicit_start=True, allow_unicode=True)


class InfraredPlugin(object):
    PLUGIN_SPEC_FILE = 'plugin.spec'

    # PLUGIN_DIRS = dict(
    #     settings='settings',
    #     modules='library',
    #     roles='roles',
    #     playbooks='playbooks'
    # )

    def __init__(self, plugin_dir):
        """InfraredPlugin initializer

        :param plugin_dir: A path to the plugin's root dir
        """
        self.path = plugin_dir
        self.config = os.path.join(self.path, self.PLUGIN_SPEC_FILE)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, plugin_dir):
        full_path = os.path.abspath(os.path.expanduser(plugin_dir))
        if not os.path.isdir(full_path):
            raise IRFailedToAddPlugin(
                "Path to plugin dir '{}' doesn't exist".format(plugin_dir))
        self._path = full_path

    @property
    def vars_dir(self):
        return os.path.join(self.path, 'vars')

    @property
    def defaults_dir(self):
        return os.path.join(self.path, 'defaults')

    @property
    def playbook(self):
        """Plugin's main playbook"""
        return os.path.join(self.path, MAIN_PLAYBOOK)

    @property
    def spec(self):
        if not getattr(self, '_spec', None):
            self._spec = os.path.join(self.path, self.PLUGIN_SPEC_FILE)
        return self._spec

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, plugin_spec):
        self._config = self.spec_validator(plugin_spec)

    @property
    def name(self):
        subparsers = self.config['subparsers']
        plugins = subparsers.keys()
        if len(plugins) != 1:
            # TODO(aopincar): Replace with a proper infrared exception
            raise Exception("Only one plugin should be defined in spec")
        return plugins[0]

    @property
    def type(self):
        return self.config['plugin_type']

    @property
    def description(self):
        try:
            return self.config['subparsers'][self.name]['description']
        except KeyError:
            return self.config['description']

    @staticmethod
    def spec_validator(spec_file):
        """Loads & validates that spec (YAML) file has all required fields

        :param spec_file: Path to plugin's spec file
        :raise IRFailedToAddPlugin: when mandatory data is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        if not os.path.isfile(spec_file):
            raise IRFailedToAddPlugin(
                "Plugin spec doesn't exist: {}".format(spec_file))

        with open(spec_file) as fp:
            spec_dict = InfraredPlugin.spec_content_validator(fp)

        return spec_dict

    @staticmethod
    def spec_content_validator(spec_content):
        """validates that spec (YAML) file has all required fields

        :param spec_content: content of spec file
        :raise IRFailedToAddPlugin: when mandatory data is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        spec_dict = yaml.load(spec_content)

        if not isinstance(spec_dict, dict):
            raise IRFailedToAddPlugin(
                "Spec file is empty or corrupted: '{}'".format(spec_content))

        plugin_type_key = 'plugin_type'
        if plugin_type_key not in spec_dict:
            raise IRFailedToAddPlugin(
                "Required key '{}' is missing in plugin spec "
                "file: {}".format(plugin_type_key, spec_content))
        if not isinstance(spec_dict[plugin_type_key], str):
            raise IRFailedToAddPlugin(
                "Value of 'str' is expected for key '{}' in spec "
                "file '{}'".format(plugin_type_key, spec_content))
        if not len(spec_dict[plugin_type_key]):
            raise IRFailedToAddPlugin(
                "String value of key '{}' in spec file '{}' can't "
                "be empty.".format(plugin_type_key, spec_content))

        subparsers_key = 'subparsers'
        if subparsers_key not in spec_dict:
            raise IRFailedToAddPlugin(
                "'{}' key is missing in spec file: '{}'".format(
                    subparsers_key, spec_content))
        if not isinstance(spec_dict[subparsers_key], dict):
            raise IRFailedToAddPlugin(
                "Value of '{}' in spec file '{}' should be "
                "'dict' type".format(subparsers_key, spec_content))
        if 'description' not in spec_dict \
                and 'description' not in spec_dict[subparsers_key].values()[0]:
            raise IRFailedToAddPlugin(
                "Required key 'description' is missing for supbarser '{}' in "
                "spec file '{}'".format(
                    spec_dict[subparsers_key].keys()[0], spec_content))
        if len(spec_dict[subparsers_key]) != 1:
            raise IRFailedToAddPlugin(
                "One subparser should be defined under '{}' in "
                "spec file '{}'".format(subparsers_key, spec_content))
        if not isinstance(spec_dict[subparsers_key].values()[0], dict):
            raise IRFailedToAddPlugin(
                "Subparser '{}' should be 'dict' type and not '{}' type in "
                "spec file '{}'".format(
                    spec_dict[subparsers_key].keys()[0],
                    type(spec_dict[subparsers_key].values()[0]), spec_content))
        if spec_dict[subparsers_key].keys()[0].lower() == 'all':
            raise IRFailedToAddPlugin(
                "Adding a plugin named 'all' isn't allowed")

        return spec_dict

    def __repr__(self):
        return self.name
