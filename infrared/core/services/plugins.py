from ConfigParser import ConfigParser
from collections import OrderedDict
import datetime
import os
import shutil
import tempfile
import time
import re
import yaml
import git
import github

# TODO(aopincar): Add pip to the project's requirements
import pip

from infrared.core.utils import logger
from infrared.core.utils.exceptions import IRFailedToAddPlugin, IRException, \
    IRSpecValidatorException, IRPluginExistsException
from infrared.core.utils.exceptions import IRFailedToRemovePlugin
from infrared.core.utils.exceptions import IRFailedToUpdatePlugin
from infrared.core.utils.exceptions import IRUnsupportedPluginType


DEFAULT_PLUGIN_INI = dict(
    supported_types=OrderedDict([
        ('provision', 'Provisioning plugins'),
        ('install', 'Installing plugins'),
        ('test', 'Testing plugins'),
        ('other', 'Other type plugins'),
        ('library', 'Library type plugins')
    ]),
    git_orgs=OrderedDict([
        # Git provider and a comma separated list of organizations
        ('github', 'rhos-infra')
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
    GIT_PLUGINS_ORGS_SECTION = "git_orgs"

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
                    plugin = InfraredPlugin(plugin_path)
                    self.__class__.PLUGINS_DICT[plugin_name] = plugin

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

    def get_all_git_plugins(self):
        """
        Returns a dict with all plugins from a all supported git providers
        """
        # mapping for supported fetcher functions
        supported_plugins_fetchers = {
            "github": self.get_github_organization_plugins
        }

        plugins_dict = OrderedDict()

        # make sure the git section exists
        if self.config.has_section(self.GIT_PLUGINS_ORGS_SECTION):
            for git_provider_type, git_orgs in self.config.items(
                    self.GIT_PLUGINS_ORGS_SECTION):
                # make sure we support this git provider type
                if git_provider_type not in supported_plugins_fetchers:
                    continue
                # get fetcher function
                fetcher = supported_plugins_fetchers[git_provider_type]
                # organizations can be a list separated by comma
                git_orgs = git_orgs.split(",")

                for git_org in git_orgs:
                    # dynamically call function based on the git_provider_type
                    plugins_dict.update(fetcher(git_org))

        return plugins_dict

    def get_github_organization_plugins(self, organization, no_forks=False):
        """
        Returns a dict with all plugins from a GitHub organization
        inspired from: https://gist.github.com/ralphbean/5733076
        :param organization: GitHub organization name
        :param no_forks: include / not include forks
        """
        plugins_dict = OrderedDict()
        spec_validator = SpecValidator()

        try:
            gh = github.Github()
            all_repos = gh.get_organization(organization).get_repos()
        except github.RateLimitExceededException:
            raise IRException("Github API rate limit exceeded")

        for repo in all_repos:

            try:
                # Don't print the urls for repos that are forks.
                if no_forks and repo.fork:
                    continue

                spec_file = repo.get_contents('plugin.spec').decoded_content

                plugin = spec_validator.validate_from_content(spec_file)
                plugin_name = plugin["subparsers"].keys()[0]
                plugin_src = repo.clone_url
                plugin_type = plugin["config"]["plugin_type"] \
                    if "config" in plugin \
                    else plugin["plugin_type"]
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
        spec_validator = SpecValidator()
        spec_data = spec_validator.validate_from_file(
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

    def add_plugin(self, plugin_source, rev=None, dest=None,
                   is_dependency=False):
        """Adds (install) a plugin

        :param plugin_source: Plugin source.
          Can be:
            1. Plugin name (from available in registry)
            2. Path to a local directory
            3. Git URL
        :param dest: destination where to clone a plugin into (if 'source' is
          a Git URL)
        :param rev: git branch/tag/revision
        :param is_dependency: boolean to indicate if the plugin is a dependency
          and will verify that it is a library type
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
        plugin_type = plugin.type
        # FIXME(yfried) validate spec and throw exception on missing input

        if plugin_type not in self.supported_plugin_types:
            raise IRUnsupportedPluginType(plugin_type)

        if is_dependency and plugin_type != "library":
            reason_str = "Plugin dependency must be a 'library' type"
            raise IRUnsupportedPluginType(plugin_type=plugin_type,
                                          additional_reason_str=reason_str)

        if not self.config.has_section(plugin_type):
            self.config.add_section(plugin_type)
        elif self.config.has_option(plugin_type, plugin.name):
            raise IRPluginExistsException(
                "Plugin with the same name & type already exists")

        self._install_dependencies(plugin)

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

    def remove_plugin(self, plugin_name):
        """Removes an installed plugin

        :param plugin_name: Plugin name to be removed
        """
        if plugin_name not in self.PLUGINS_DICT:
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

    def remove_all(self):
        for plugin in self.PLUGINS_DICT:
            self.remove_plugin(plugin)
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

    def _install_dependencies(self, plugin):
        """
        Install plugin dependencies based on the dependencies specified in spec
        :param plugin: InfraredPlugin object
        """
        if not plugin.dependencies:
            return

        # install all dependencies recursively
        for dependency in plugin.dependencies:
            plugin_source = dependency["plugin"]
            plugin_rev = dependency["revision"] \
                if "revision" in dependency else None

            try:
                # try to add the plugin
                self.add_plugin(plugin_source=plugin_source,
                                rev=plugin_rev,
                                is_dependency=True)

            except IRPluginExistsException:
                # dependency plugin already exists so we can skip it
                continue

    def freeze(self):
        for section in self.config.sections():
            if section == "supported_types":
                continue
            for name, path in self.config.items(section):
                if name not in PLUGINS_REGISTRY:
                    with open(os.path.join(path, "plugin.spec"), "r") as pls:
                        plugin_spec = yaml.load(pls)
                    # support two types of possible plugin spec files
                    plugin_type = plugin_spec["config"]["plugin_type"] \
                        if "config" in plugin_spec \
                        else plugin_spec["plugin_type"]

                    PLUGINS_REGISTRY[name] = dict(
                        type=plugin_type,
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
        spec_validator = SpecValidator()
        self._config = spec_validator.validate_from_file(plugin_spec)

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
        try:
            return self.config['config']['plugin_type']
        except KeyError:
            return self.config['plugin_type']

    @property
    def description(self):
        try:
            return self.config['subparsers'][self.name]['description']
        except KeyError:
            return self.config['description']

    @property
    def dependencies(self):
        try:
            return self.config['config']['dependencies']
        except KeyError:
            return ""

    def __repr__(self):
        return self.name


class SpecValidator(object):
    """
    Class for validating that a plugin spec (YAML) has all required fields
    """
    GIT_URL_PATTERN = \
        r'(?:git|ssh|https?|git@[-\w.]+)' \
        r':(\/\/)?(.*?)(\.git)(\/?|\#[-\d\w._]+?)$'

    def __init__(self, spec_file=None, spec_content=None):
        self.spec_file = spec_file
        self.spec_content = spec_content

    def validate_from_file(self, spec_file=None):
        """Loads & validates that spec (YAML) file has all required fields

        :param spec_file: Path to plugin's spec file
        :raise IRSpecValidatorException: when mandatory
        data is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        if spec_file is not None:
            self.spec_file = spec_file

        if self.spec_file is None:
            raise IRSpecValidatorException(
                "Plugin spec file is missing")

        if not os.path.isfile(spec_file):
            raise IRSpecValidatorException(
                "Plugin spec doesn't exist: {}".format(self.spec_file))

        with open(spec_file) as fp:
            spec_dict = self.validate_from_content(fp)

        return spec_dict

    def validate_from_content(self, spec_content=None):
        """validates that spec (YAML) content has all required fields

        :param spec_content: content of spec file
        :raise IRSpecValidatorException: when mandatory data
        is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        if spec_content is not None:
            self.spec_content = spec_content

        if self.spec_content is None:
            raise IRSpecValidatorException(
                "Plugin spec content is missing")

        spec_dict = yaml.load(self.spec_content)

        if not isinstance(spec_dict, dict):
            raise IRSpecValidatorException(
                "Spec file is empty or corrupted: {}".format(
                    self.spec_content))

        # check if new spec file structure
        if "config" in spec_dict:
            self._validate_config_section(spec_dict)
        else:
            self._validate_key(spec_dict=spec_dict,
                               key="plugin_type",
                               instance=str)

        subparsers_key = "subparsers"
        if subparsers_key not in spec_dict:
            raise IRSpecValidatorException(
                "'{}' key is missing in spec file: {}".format(
                    subparsers_key, self.spec_content))
        if not isinstance(spec_dict[subparsers_key], dict):
            raise IRSpecValidatorException(
                "Value of '{}' should be 'dict' type in spec "
                "file: {}".format(subparsers_key, self.spec_content))

        if "description" not in spec_dict \
                and "description" not in spec_dict[subparsers_key].values()[0]:
            raise IRSpecValidatorException(
                "Required key 'description' is missing for supbarser '{}' in "
                "spec file: {}".format(
                    spec_dict[subparsers_key].keys()[0], self.spec_content))
        if len(spec_dict[subparsers_key]) != 1:
            raise IRSpecValidatorException(
                "One subparser should be defined under '{}' in "
                "spec file: {}".format(subparsers_key, self.spec_content))
        if not isinstance(spec_dict[subparsers_key].values()[0], dict):
            raise IRSpecValidatorException(
                "Subparser '{}' should be 'dict' type and not '{}' type in "
                "spec file: {}".format(
                    spec_dict[subparsers_key].keys()[0],
                    type(spec_dict[subparsers_key].values()[0]),
                    self.spec_content))
        if spec_dict[subparsers_key].keys()[0].lower() == 'all':
            raise IRSpecValidatorException(
                "Adding a plugin named 'all' isn't allowed")

        return spec_dict

    def _validate_config_section(self, spec_dict):
        config_key = "config"
        if not isinstance(spec_dict[config_key], dict):
            raise IRSpecValidatorException(
                "Value of '{}' should be 'dict' type in spec "
                "file: {}".format(config_key, self.spec_content))

        # validate plugin type
        self._validate_key(spec_dict=spec_dict[config_key],
                           key="plugin_type",
                           instance=str)
        # validate dependencies section if exists
        dependencies_key = "dependencies"
        if dependencies_key in spec_dict[config_key]:
            dependencies_list = spec_dict[config_key][dependencies_key]

            if not isinstance(dependencies_list, list):
                raise IRSpecValidatorException(
                    "Value of 'list' is expected for key '{}' in spec "
                    "file: {}".format(dependencies_key, self.spec_content))
            if not len(dependencies_list):
                raise IRSpecValidatorException(
                    "Value of key '{}' can't be empty in plugin spec "
                    "file: {}".format(dependencies_key, self.spec_content))

            for dependency_dict in dependencies_list:
                if not isinstance(spec_dict[config_key], dict):
                    raise IRSpecValidatorException(
                        "Value of '{}' should be 'dict' type in spec "
                        "file: {}".format(config_key, self.spec_content))

                # validate the plugin source
                self._validate_key(spec_dict=dependency_dict,
                                   key="plugin",
                                   instance=str)

                # if the plugin value is git url validate the revision key
                git_dependency_match = re.match(self.GIT_URL_PATTERN,
                                                dependency_dict["plugin"],
                                                re.M | re.I)

                if git_dependency_match and git_dependency_match.group():
                    self._validate_key(spec_dict=dependency_dict,
                                       key="revision",
                                       instance=str)

        return True

    def _validate_key(self, spec_dict, key, instance):
        """
        Validate that a specific key exists, its instance and not empty
        :param spec_dict: The dict content to validate
        :param instance: The expected instance of the key
        :raise IRSpecValidatorException: when mandatory data
        is missing in spec file
        """
        if key not in spec_dict:
            raise IRSpecValidatorException(
                "Required key '{}' is missing in plugin spec "
                "file: {}".format(key, self.spec_content))
        if not isinstance(spec_dict[key], instance):
            raise IRSpecValidatorException(
                "Value of {} is expected for key '{}' in spec "
                "file: {}".format(instance, key, self.spec_content))
        if not len(spec_dict[key]):
            raise IRSpecValidatorException(
                "Value of key '{}' can't be empty in plugin spec "
                "file: {}".format(key, self.spec_content))

        return True
