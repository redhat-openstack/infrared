import datetime
import git
import github
import os
import shutil
import sys
import tempfile
import tenacity
import time

from collections import OrderedDict
from distutils.util import strtobool
from six.moves import configparser


from pip._internal.main import main as pip_main
import urllib3
import yaml

from infrared.core.utils.exceptions import IRException
from infrared.core.utils.exceptions import IRFailedToAddPlugin
from infrared.core.utils.exceptions import IRFailedToImportPlugins
from infrared.core.utils.exceptions import IRFailedToRemovePlugin
from infrared.core.utils.exceptions import IRFailedToUpdatePlugin
from infrared.core.utils.exceptions import IRGalaxyRoleInstallFailedException
from infrared.core.utils.exceptions import IRPluginExistsException
from infrared.core.utils.exceptions import IRUnsupportedPluginType
from infrared.core.utils import logger
from infrared.core.utils.validators import RegistryValidator
from infrared.core.utils.validators import SpecValidator
from infrared import PLUGINS_REGISTRY

DEFAULT_PLUGIN_INI = dict(
    supported_types=OrderedDict([
        ('provision', 'Provisioning plugins'),
        ('install', 'Installing plugins'),
        ('test', 'Testing plugins'),
        ('other', 'Other type plugins'),
    ]),
    git_orgs=OrderedDict([
        # Git provider and a comma separated list of organizations
        ('github', 'rhos-infra')
    ])
)

LOG = logger.LOG


class InfraredPluginManager(object):
    PLUGINS_DICT = OrderedDict()
    SUPPORTED_TYPES_SECTION = 'supported_types'
    GIT_PLUGINS_ORGS_SECTION = "git_orgs"

    def __init__(self, plugins_conf, plugins_dir, install_plugins=True):
        """Constructor.

        :param plugins_conf: A path to the main plugins configuration file
        :param plugins_dir: the plugins directory location
        :param install_plugins: Specifies if core plugins should be installed
        at start.
        """
        # create plugins directory
        self.plugins_dir = plugins_dir
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)

        self._config_file = os.path.abspath(os.path.expanduser(plugins_conf))
        self._install_plugins_required = install_plugins
        self._configure()
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
        """Returns a dict with all plugins from all supported git providers."""
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

    @staticmethod
    def get_github_organization_plugins(organization, no_forks=False):
        """Returns a dict with all plugins from a GitHub organization.

        Inspired from: https://gist.github.com/ralphbean/5733076

        :param organization: GitHub organization name
        :param no_forks: include / not include forks
        """
        plugins_dict = OrderedDict()

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

                plugin = SpecValidator.validate_from_content(spec_file)
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

    def _configure(self):
        init_plugins_conf = False
        if not os.path.isfile(self._config_file):
            LOG.warning("Plugin conf ('{}') not found, creating it with "
                        "default data".format(self._config_file))
            init_plugins_conf = True
            with open(self._config_file, 'w') as fp:
                config = configparser.ConfigParser()

                for section, section_data in DEFAULT_PLUGIN_INI.items():
                    if not config.has_section(section):
                        config.add_section(section)
                    for option, value in section_data.items():
                        config.set(section, option, value)

                config.write(fp)

        with open(self._config_file) as fp:
            self._config = configparser.ConfigParser()
            if (sys.version_info > (3, 2)):
                self._config.read_file(fp)
            else:
                self._config.readfp(fp)

        # TODO(aopincar): Remove auto plugins installation when conf is missing
        if self._install_plugins_required and init_plugins_conf:
            self.add_all_available()

    @classmethod
    def get_plugin(cls, plugin_name):
        """Returns an instance of plugin based on name

        :param plugin_name: Plugin name
        :return: InfraredPlugin instance
        """
        return cls.PLUGINS_DICT[plugin_name]

    def get_plugin_version(self, plugin_name):
        try:
            repo = git.Repo(os.path.join(self.plugins_dir, plugin_name))
            return str(repo.active_branch) + " / " + str(
                repo.head.commit.hexsha)
        except git.InvalidGitRepositoryError:
            return 'builtin'

    def __iter__(self):
        for plugin in self.PLUGINS_DICT.items():
            yield plugin
        else:
            raise StopIteration

    @staticmethod
    @tenacity.retry(reraise=True, wait=tenacity.wait_exponential(),
                    stop=tenacity.stop_after_attempt(3))
    def _clone_git_plugin(git_url, rev=None):
        """Clone a plugin into a given destination directory

        :param git_url: Plugin's Git URL
        :param rev: git branch/tag/revision
        :return: Path to plugin cloned directory (str)
        """
        plugin_git_name = os.path.split(git_url)[-1].split('.')[0]

        tmpdir = tempfile.mkdtemp(prefix="ir-")
        plugin_tmp_source = os.path.join(tmpdir, plugin_git_name)
        try:
            repo = git.Repo.clone_from(
                url=git_url,
                to_path=plugin_tmp_source,
                kill_after_timeout=300)
            if rev is not None:
                repo.git.checkout(rev)
        except (git.exc.GitCommandError) as e:
            shutil.rmtree(tmpdir)
            raise IRFailedToAddPlugin(
                "Cloning git repo {} is failed: {}".format(git_url, e))

        return plugin_tmp_source

    @staticmethod
    def _checkout_git_plugin_revision(repo, revision, update_string):
        """Checkout a specific revision for a git plugin.

        Before checking out the new branch a new backup branch will be created.

        :param repo: Repo object that points to plugin local repo
        :param revision: revision to checkout
        :param update_string: name of the backup branch
        :return:
        """
        LOG.warning("Create a branch '{}' that will point "
                    "to the current HEAD".format(update_string))
        repo.git.branch(update_string)

        LOG.debug("Fetching changes from the "
                  "'{}' remote".format(repo.remote().name))
        repo.git.fetch(repo.remote().name)

        try:
            if revision not in (None, 'latest'):
                LOG.debug("Checking out revision {}".format(revision))
                repo.git.checkout(revision)
        except git.exc.GitCommandError:
            raise IRFailedToUpdatePlugin(
                "Failed to update plugin!\n"
                "revision '{}' could not be checked out".format(revision))

    @staticmethod
    def _pull_git_plugin_changes(repo):
        """Pull changes on a git plugin

        :param repo: Repo object that points to plugin local repo
        :return:
        """
        try:
            # only pull if not detached
            if not repo.head.is_detached:
                for ref in repo.remotes.origin.refs:
                    # check if active branch has a remote branch to pull from
                    if repo.active_branch.name in ref.name:
                        LOG.debug("Pulling changes from the "
                                  "'{}' remote".format(repo.remote().name))
                        repo.git.pull('--rebase')
                        break
        except git.exc.GitCommandError as ex:
            repo.git.rebase('--abort')
            raise IRFailedToUpdatePlugin(
                "Failed to update plugin!\nPlease go to plugin dir ({})"
                " and manually resolve Git issues.\n"
                "{}\n{}".format(repo.working_dir, ex.stdout, ex.stderr))

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

        plugin = self.get_plugin(plugin_name)

        try:
            repo = git.Repo(plugin.path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise IRFailedToUpdatePlugin(
                "Plugin '{}' isn't a Git-based plugin".format(plugin_name))

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

        # checkout revision
        self._checkout_git_plugin_revision(repo, revision, update_string)

        if not hard_reset:
            # pull changes
            self._pull_git_plugin_changes(repo)

        if repo.git.status('--porcelain', '--untracked-files=no'):
            LOG.warning("Changes in tracked files have been found")

        if not skip_reqs:
            reqs_file = os.path.join(plugin.path, 'requirements.txt')
            if os.path.isfile(reqs_file):
                pip_main(['install', '-r', reqs_file])

    def add_plugin(self, plugin_source, rev=None, plugins_registry=None,
                   plugin_src_path=None, skip_roles=False, link_roles=False):
        """Adds (install) a plugin

        :param plugin_source: Plugin source.
          Can be:
            1. Plugin name (from available in registry)
            2. Path to a local directory
            3. Git URL
        :param rev: git branch/tag/revision
        :param plugins_registry: content of plugin registry dictionary
        :param plugin_src_path: relative path to the plugin location inside the
               source
        :param skip_roles: Skip the from file roles installation
        :param link_roles: Auto create symlink from {plugin_src_path}/roles to
               the 'roles' directory inside the plugin root dir or to the
               plugin root dir itself
        """
        plugins_registry = plugins_registry or PLUGINS_REGISTRY
        plugin_data = {}
        # Check if a plugin is in the registry
        if plugin_source in plugins_registry:
            plugin_data = plugins_registry[plugin_source]
            plugin_source = plugins_registry[plugin_source]['src']

        if plugin_src_path is None:
            plugin_src_path = plugin_data.get('src_path', '')

        _link_roles = link_roles or bool(strtobool(
            plugin_data.get('link_roles', 'false')))

        # Local dir plugin
        if os.path.exists(plugin_source):
            rm_source = False
        # Git Plugin
        else:
            if rev is None:
                rev = plugin_data.get('rev')
            plugin_source = \
                self._clone_git_plugin(plugin_source, rev)
            rm_source = True

        plugin = InfraredPlugin(os.path.join(plugin_source, plugin_src_path))
        plugin_type = plugin.type

        if plugin_type not in self.supported_plugin_types:
            raise IRUnsupportedPluginType(plugin_type)

        if not self.config.has_section(plugin_type):
            self.config.add_section(plugin_type)
        elif self.config.has_option(plugin_type, plugin.name):
            raise IRPluginExistsException(
                "Plugin with the same name & type already exists")

        dest = os.path.join(self.plugins_dir, plugin.name)
        if os.path.abspath(plugin_source) != os.path.abspath(dest):
            # copy only if plugin was added from a location which is
            # different from the location of the plugins dir
            if os.path.islink(dest):
                LOG.debug("%s found as symlink pointing to %s, "
                          "unlinking it, not touching the target.",
                          dest,
                          os.path.realpath(dest))
                os.unlink(dest)
            elif os.path.exists(dest):
                shutil.rmtree(dest)

            shutil.copytree(plugin_source, dest)

        if rm_source:
            shutil.rmtree(plugin_source)

        if _link_roles:
            if not plugin_src_path:
                raise IRFailedToAddPlugin(
                    "'--src-path' is required with '--link-roles'")

            roles_dir = os.path.join(dest, plugin_src_path, 'roles')
            if os.path.exists(roles_dir):
                raise IRFailedToAddPlugin(
                    "Can't create a symbolic link to a 'roles' directory in "
                    "'{roles_dir}', because one is already exists".format(
                        roles_dir=roles_dir
                    ))

            src_dir = dest
            if os.path.exists(dest + '/roles'):
                if not os.path.isdir(dest + '/roles'):
                    raise IRFailedToAddPlugin(
                        "The plugin directory ('{dest}') contains"
                        "a 'roles' file that can't be sym-linked".format(
                            dest=dest
                        ))
                src_dir += '/roles'

            os.mkdir(roles_dir)
            dest_dir = roles_dir + '/' + dest.split('/')[-1]
            os.symlink(src_dir, dest_dir)

        self.config.set(plugin_type, plugin.name,
                        os.path.join(dest, plugin_src_path))

        with open(self.config_file, 'w') as fp:
            self.config.write(fp)

        self._install_requirements(dest)
        if not skip_roles:
            # roles are skipped only in infrared's internal tests
            # param for this is not exposed in cli/spec files
            self._install_roles_from_file(dest)
        self._load_plugins()

    def add_all_available(self, plugins_registry=None, skip_roles=False):
        """Add all available plugins which aren't already installed.

        :param plugins_registry: content of plugin registry yml file
        :param skip_roles: Skip the from file roles installation
        """
        plugins_registry = plugins_registry or PLUGINS_REGISTRY
        for plugin in set(plugins_registry) - \
                set(self.PLUGINS_DICT):
            self.add_plugin(plugin, plugins_registry=plugins_registry,
                            skip_roles=skip_roles)
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
        for plugin in list(self.PLUGINS_DICT):
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
            pip_main(args=pip_args)

    @staticmethod
    @tenacity.retry(reraise=True, wait=tenacity.wait_exponential(),
                    stop=tenacity.stop_after_attempt(5))
    def _install_roles_from_file(plugin_path):
        # Ansible Galaxy - install roles from file
        for req_file in ['requirements.yml', 'requirements.yaml']:
            galaxy_reqs_file = os.path.join(plugin_path, req_file)
            if not os.path.isfile(galaxy_reqs_file):
                continue
            LOG.debug("Installing Ansible Galaxy "
                      "requirements from file... ({})".format(galaxy_reqs_file))
            from ansible.cli.galaxy import GalaxyCLI
            from ansible.errors import AnsibleError

            glxy_cli_params = ['ansible-galaxy',
                               'role',
                               'install',
                               '-r',
                               galaxy_reqs_file]
            if InfraredPluginManager._is_collection_requirements(galaxy_reqs_file):
                glxy_cli_params[1] = 'collection'
            LOG.debug("Ansible Galaxy command: {}".format(glxy_cli_params))
            glxy_cli = GalaxyCLI(glxy_cli_params)
            glxy_cli.parse()

            LOG.debug("Trying to install Ansible Galaxy required "
                      "collection 5 times to circumvent potential network issues")
            try:
                glxy_cli.run()
            except AnsibleError as e:
                raise IRGalaxyRoleInstallFailedException(
                    "Failed to install Ansible Galaxy requirements, aborting! Error: {}".format(e))
        else:
            LOG.debug("Ansible Galaxy requirements files weren't found.")

    @staticmethod
    def _is_collection_requirements(requirements_path):
        reqs_yaml = {}
        with open(requirements_path) as content:
            reqs_yaml = yaml.load(content, Loader=yaml.FullLoader)
        return ('collections' in reqs_yaml)

    def freeze(self):
        registry = {}
        for section in self.config.sections():
            if section in ["supported_types", "git_orgs"]:
                continue
            for name, path in self.config.items(section):
                if name not in registry:
                    with open(os.path.join(path, "plugin.spec"), "r") as pls:
                        plugin_spec = yaml.safe_load(pls)
                    # support two types of possible plugin spec files
                    plugin_type = plugin_spec["config"]["plugin_type"] \
                        if "config" in plugin_spec \
                        else plugin_spec["plugin_type"]
                    registry[name] = dict(
                        type=plugin_type,
                        desc=plugin_spec[
                            "subparsers"].items()[0][1]["description"])
                try:
                    repo = git.Repo(path)
                    registry[name]["src"] = list(
                        repo.remote().urls)[-1].encode("ascii")
                    registry[name]["rev"] = repo.head.commit.hexsha.encode(
                        "ascii")
                except git.InvalidGitRepositoryError:
                    registry[name]["src"] = path

        for plugin_name, plugin_dict in registry.items():
            print(yaml.dump({plugin_name: plugin_dict},
                            default_flow_style=False,
                            explicit_start=False, allow_unicode=True))

    def import_plugins(self, plugins_registry):
        """Import and install plugins from registry yml file.

        :param plugins_registry: Path/URL to plugin registry yml file
        """
        try:
            if not os.path.exists(plugins_registry):
                # if path was not found locally attempt to download it
                http = urllib3.PoolManager()
                urllib_ret = http.request('GET', plugins_registry)
                if urllib_ret.status != 200:
                    # make sure we received OK status code from url
                    raise IRFailedToImportPlugins(
                        'Got unexpected returned code ({}) from registry '
                        'URL ({})'.format(urllib_ret.status, plugins_registry))
                # load registry from the url
                plugins_registry = \
                    RegistryValidator.validate_from_content(urllib_ret.data)
            else:
                # validate from local path
                plugins_registry = \
                    RegistryValidator.validate_from_file(plugins_registry)

        except urllib3.exceptions.HTTPError:
            raise IRFailedToImportPlugins(
                'Registry URL not found - ({}) '.format(plugins_registry))

        for plugin in set(plugins_registry):
            # if plugin exists remove it and then add from new registry
            if plugin in self.PLUGINS_DICT:
                self.remove_plugin(plugin)
                LOG.warning(
                    "Plugin '{}' has been successfully removed".format(plugin))
            # add the plugin
            self.add_plugin(plugin_source=plugin,
                            plugins_registry=plugins_registry)
            LOG.warning(
                "Plugin '{}' has been successfully installed".format(plugin))


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
        return os.path.join(self.path, self.entry_point)

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
        self._config = SpecValidator.validate_from_file(plugin_spec)

    @property
    def name(self):
        subparsers = self.config['subparsers']
        plugins = subparsers.keys()
        if len(plugins) != 1:
            # TODO(aopincar): Replace with a proper infrared exception
            raise Exception("Only one plugin should be defined in spec")
        return list(plugins)[0]

    @property
    def entry_point(self):
        if "entry_point" in self.config:
            return self.config['entry_point']
        elif "config" in self.config and "entry_point" in self.config['config']:
            return self.config['config']['entry_point']
        else:
            return "main.yml"

    @property
    def type(self):
        try:
            return self.config['config']['plugin_type']
        except KeyError:
            return self.config['plugin_type']

    @property
    def roles_path(self):
        try:
            return self.config['config']['roles_path']
        except KeyError:
            try:
                return self.config['roles_path']
            except KeyError:
                return ''

    @property
    def description(self):
        try:
            return self.config['subparsers'][self.name]['description']
        except KeyError:
            return self.config['description']

    def __repr__(self):
        return self.name
