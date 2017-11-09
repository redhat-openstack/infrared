import shutil
import tempfile

import git
import os
import pip

from infrared.core.utils.exceptions import IRFailedToAddPluginDependency
from infrared.core.utils import logger

LOG = logger.LOG


class PluginDependencyManager(object):
    """
    Manages plugin dependencies.

    A plugin dependency is a folder that contains directories for common
    Ansible resources (callback plugins, filter plugins, roles, libraries)
    """
    REQUIRED_DIRS = \
        {"callback_plugins", "filter_plugins", "library", "roles"}

    def __init__(self, library_root_dir):
        # create library dependencies directory
        self.library_root_dir = library_root_dir
        if not os.path.exists(library_root_dir):
            os.makedirs(library_root_dir)

    def install_plugin_dependencies(self, plugin):
        """
        Install plugin dependencies based on the dependencies specified in spec
        :param plugin: InfraredPlugin object
        """
        # install all dependencies
        for dependency in plugin.dependencies:
            self.install_dependency(dependency)

    def _get_destination(self, dependency):
        """
        Get the destination for the dependency.
        :param dependency: the dependency ob
        :return:
        """
        return os.path.join(self.library_root_dir, dependency.name)

    def inject_libraries(self):
        """
        Injects all the libraries to the ansible environment.

        Should be called prior the import of the ansible modules!!!
        :return:
        """

        if not os.path.isdir(self.library_root_dir):
            return

        for dependency_library in os.listdir(self.library_root_dir):
            dependency_library = os.path.join(self.library_root_dir,
                                              dependency_library)
            PluginDependencyManager._override_conf_path(
                dependency_library, 'ANSIBLE_ROLES_PATH', 'roles')
            PluginDependencyManager._override_conf_path(
                dependency_library, 'ANSIBLE_FILTER_PLUGINS', 'filter_plugins')
            PluginDependencyManager._override_conf_path(
                dependency_library, 'ANSIBLE_CALLBACK_PLUGINS', 'callback_plugins')
            PluginDependencyManager._override_conf_path(
                dependency_library, 'ANSIBLE_LIBRARY', 'library')

    def install_dependency(self, dependency):
        """
        Installs single plugin dependency from git or local path
        :param dependency: PluginDependency object
        """
        LOG.debug(
            "Installing plugin dependency: '{}".format(dependency.source))

        # add the dependency
        if os.path.exists(dependency.source):
            perform_post_actions = self._install_local_dependency(dependency)
        else:
            perform_post_actions = self._install_git_dependency(dependency)

        if perform_post_actions:
            self._validate_dependency_folder(dependency)
            self._install_requirements(
                os.path.join(self._get_destination(dependency),
                             'requirements.txt'))

    @staticmethod
    def _override_conf_path(dependency_path, envvar, specific_dir):
        """
        Overrides the environment variable.
        :param envvar:
        :param specific_dir:
        :return:
        """
        conf_path = os.environ.get(envvar, '')
        additional_conf_path = os.path.join(dependency_path, specific_dir)

        # return if the env path does not exists
        if not os.path.exists(additional_conf_path):
            return

        if conf_path:
            full_conf_path = ':'.join([additional_conf_path, conf_path])
        else:
            full_conf_path = additional_conf_path
        os.environ[envvar] = full_conf_path

    def _install_local_dependency(self, dependency):
        """
        Install a dependency from local path
        :param dependency: PluginDependency object
        :return True if succeeded or False if already exist
        """
        if os.path.exists(self._get_destination(dependency)):
            LOG.debug("Skipping an already exist dependency.")
            return False

        # copy the library plugin
        shutil.copytree(dependency.source, self._get_destination(dependency))
        return True

    def _install_git_dependency(self, dependency):
        """
        Install a dependency from git
        :param dependency: PluginDependency object
        :return True if succeeded or False if already exist
        """
        try:
            tmpdir = tempfile.mkdtemp(prefix="ir-")
            cloned_repo = git.Repo.clone_from(
                url=dependency.source,
                to_path=tmpdir)
            if dependency.revision is not None:
                cloned_repo.git.checkout(dependency.revision)

            # check if the dependency already exists and compare rev
            if os.path.exists(self._get_destination(dependency)):
                existed_repo = git.Repo(self._get_destination(dependency))
                dependency_rev = existed_repo.head.ref.commit.name_rev
                existed_rev = cloned_repo.head.ref.commit.name_rev

                if dependency_rev != existed_rev:
                    raise IRFailedToAddPluginDependency(
                        "Dependency '{}' already exists but with "
                        "different revision. Revision is '{}'"
                        "instead of '{}' ".format(dependency.source,
                                                  dependency_rev,
                                                  existed_rev))
                LOG.debug("Skipping an already exist dependency.")
                return False
            else:
                shutil.copytree(tmpdir, self._get_destination(dependency))
                return True
        except git.exc.GitCommandError as e:
            raise IRFailedToAddPluginDependency(
                "Cloning git repo {} has failed: {}".format(
                    dependency.source, e))

    def _validate_dependency_folder(self, dependency):
        """
        Check the dependency folder contains at least one of the req dirs
        :return:
        """
        if not os.path.isdir(self._get_destination(dependency)):
            raise IRFailedToAddPluginDependency(
                "Dependency library '{}' does not exists".format(
                    dependency.source))

        if not (set(os.listdir(
                self._get_destination(dependency))) & self.REQUIRED_DIRS):
            shutil.rmtree(self._get_destination(dependency))
            raise IRFailedToAddPluginDependency(
                "Dependency library '{}' must contain at least "
                "one of the following folders: {}".format(
                    dependency.source, self.REQUIRED_DIRS))

    @staticmethod
    def _install_requirements(requirement_file):
        """
        Install python requirements from a given requirement file
        :param requirement_file: The python requirement file
        """
        if os.path.isfile(requirement_file):
            LOG.info(
                "Installing requirements from: {}".format(requirement_file))
            pip_args = ['install', '-r', requirement_file]
            pip.main(args=pip_args)


class PluginDependency(object):
    """
    Class which defines a plugin dependency
    """

    def __init__(self, dependency_dict):
        """
        :param dependency_dict: dictionary of dependency which contains source
        and revision as optional
        """
        self._source = dependency_dict["source"]
        self._revision = dependency_dict.get('revision')

    @property
    def source(self):
        """
        The dependency source can be either local path or git url
        :return: source of dependency
        """
        return self._source

    @property
    def revision(self):
        """
        Dependency git revision
        :return: the git revision or None if not exists
        """
        return self._revision

    @property
    def name(self):
        """
        Split the name of the dependency from the source path
        :return: dependency name
        """
        return os.path.split(self.source)[-1].split('.')[0]
