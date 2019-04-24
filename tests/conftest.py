import os
import tarfile
from six.moves import configparser

import pytest
import git

from infrared.core.cli import cli
from infrared.core.services import CoreServices, ServiceName
from infrared.core.services import plugins
from infrared.core.services import workspaces
import tests


def create_file_type(root_dir, type_class):
    return type_class("arg-name",
                      (root_dir.join('vars').strpath,
                       root_dir.join('defaults').strpath),
                      None,
                      None)


@pytest.fixture
def list_value_type():
    """
    Create a new list value complex type
    """
    return cli.ListValue("test", [os.getcwd(), ], 'cmd', None)


@pytest.fixture
def dict_type():
    """Create a new IniType complex type
    """
    return cli.Dict("TestDict", None, None, None)


@pytest.fixture
def nested_dict():
    """Create a new IniType complex type
    """
    return cli.NestedDict("TestNestedDict", None, None, None)


@pytest.fixture
def flag_type():
    """Create a new Flag complex type
    """
    return cli.Flag("test", None, None, None)


@pytest.fixture
def file_type(file_root_dir, request):
    return create_file_type(file_root_dir, request.param)


@pytest.fixture
def dir_type(dir_root_dir, request):
    return create_file_type(dir_root_dir, request.param)


@pytest.fixture(scope="module")
def file_root_dir(tmpdir_factory):
    """Prepares the testing dirs for file tests"""
    root_dir = tmpdir_factory.mktemp('complex_file_dir')

    for file_path in ['file1.yml',
                      'arg/name/file2',
                      'defaults/arg/name/file.yml',
                      'defaults/arg/name/file2',
                      'vars/arg/name/file1.yml',
                      'vars/arg/name/file3.yml',
                      'vars/arg/name/nested/file4.yml']:
        root_dir.join(file_path).ensure()

    return root_dir


@pytest.fixture(scope="module")
def dir_root_dir(tmpdir_factory):
    """Prepares the testing dirs for dir tests"""
    root_dir = tmpdir_factory.mktemp('complex_dir')

    for dir_path in ['dir0/1.file',
                     'arg/name/dir1/1.file',
                     'vars/arg/name/dir2/1.file',
                     'defaults/arg/name/dir3/1.file']:
        # creating a file will create a dir
        root_dir.join(dir_path).ensure()

    return root_dir


@pytest.fixture(scope="session")
def spec_fixture():
    """Generates plugin spec for testing, using tests/example plugin dir. """
    plugin_dir = os.path.join(os.path.abspath(os.path.dirname(tests.__file__)),
                              'example')
    test_plugin = plugins.InfraredPlugin(plugin_dir=plugin_dir)
    from infrared.api import InfraredPluginsSpec
    spec = InfraredPluginsSpec(test_plugin)
    yield spec


@pytest.fixture(scope="session")
def workspace_manager_fixture(tmpdir_factory):
    """Sets the default workspace direcotry to the temporary one. """

    temp_workspace_dir = tmpdir_factory.mktemp('pmtest')
    workspace_manager = workspaces.WorkspaceManager(str(temp_workspace_dir))
    from infrared.core.services import CoreServices
    CoreServices.register_service("workspace_manager", workspace_manager)
    yield workspace_manager


@pytest.fixture()
def test_workspace(workspace_manager_fixture):
    """Creates test workspace in the temp directory. """

    name = 'test_workspace'
    yield workspace_manager_fixture.create(name)
    if workspace_manager_fixture.has_workspace(name):
        workspace_manager_fixture.delete(name)


@pytest.fixture()
def test_workspace_ssh(workspace_manager_fixture):
    """Creates test workspace in the temp directory. """

    name = 'test_workspace'
    test_workspace = workspace_manager_fixture.create(name)
    workspace_manager_fixture.activate(test_workspace.name)
    test_workspace.inventory = "tests/example/test_ssh_inventory"
    yield test_workspace
    if workspace_manager_fixture.has_workspace(name):
        workspace_manager_fixture.delete(name)


@pytest.fixture
def infrared_home(tmpdir):
    new_home = str(tmpdir.mkdir("ir_home"))
    os.environ['IR_HOME'] = new_home
    yield new_home
    del os.environ['IR_HOME']


@pytest.fixture()
def plugins_conf_fixture(tmpdir):
    """Creates temporary IR

    :param tmpdir: builtin pytest fixtures to create temporary files & dirs
    :return: plugins conf file as a LocalPath object (py.path)
    """

    # Creates temporary plugins conf file
    lp_dir = tmpdir.mkdir('test_tmp_dir')
    lp_file = lp_dir.join('.plugins.ini')

    try:
        yield lp_file
    finally:
        lp_dir.remove()


@pytest.fixture()
def plugin_manager_fixture(plugins_conf_fixture):
    """Creates a PluginManager fixture

    Creates a fixture which returns a PluginManager object based on
    temporary plugins conf with default values(sections - provision, install &
    test)
    :param plugins_conf_fixture: fixture that returns a path of a temporary
    plugins conf
    """

    lp_file = plugins_conf_fixture

    def plugin_manager_helper(plugins_conf_dict=None):

        if plugins_conf_dict is None:
            plugins_conf_dict = {}

        plugins_conf_dict.update(tests.constants.SUPPORTED_TYPES_DICT)

        with lp_file.open(mode='w') as fp:
            config = configparser.ConfigParser()
            for section, section_data in plugins_conf_dict.items():
                config.add_section(section)
                for option, value in section_data.items():
                    config.set(section, option, value)
            config.write(fp)

        CoreServices.register_service(
            ServiceName.PLUGINS_MANAGER, plugins.InfraredPluginManager(
                lp_file.strpath,
                os.path.join(lp_file.dirname, "plugins")))
        return CoreServices.plugins_manager()

    yield plugin_manager_helper


@pytest.fixture()
def git_plugin_manager_fixture(tmpdir, plugin_manager_fixture):
    """Yields an IRPluginManager obj configured with git plugin

    Just like plugin_manager_fixture but also create two temporary directories
    that will be used to mimic local and remote git repos of an InfraRed's
    plugin. The IRPluginManager that will be returned, will be configured with
    this InfraRed git plugin.
    :param tmpdir: builtin pytest fixtures to create temporary files & dirs
    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """
    plugin_tar_gz = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'example/plugins/git_plugin/git_plugin_repo.tar.gz')

    plugin_repo_dir = tmpdir.mkdir('plugin_repo_dir')
    plugin_install_dir = tmpdir.mkdir('plugin_install_dir')

    t_file = tarfile.open(plugin_tar_gz)
    t_file.extractall(path=str(plugin_repo_dir))

    repo = git.Repo.clone_from(
        url=str(plugin_repo_dir),
        to_path=str(plugin_install_dir))

    repo.git.config('user.name', 'dummy-user')
    repo.git.config('user.email', 'dummy@email.com')

    plugin_spec_dict = tests.test_plugins.get_plugin_spec_flatten_dict(
        str(plugin_install_dir))

    try:
        plugin_manager = plugin_manager_fixture({
            plugin_spec_dict['type']: {
                plugin_spec_dict['name']: str(plugin_install_dir)}
        })
        yield plugin_manager
    finally:
        plugin_repo_dir.remove()
        plugin_install_dir.remove()
