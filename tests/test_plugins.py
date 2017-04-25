import ConfigParser
import os
import subprocess
import yaml

import pytest

from infrared.core.utils.exceptions import IRFailedToAddPlugin
from infrared.core.utils.exceptions import IRFailedToRemovePlugin
from infrared.core.utils.exceptions import IRUnsupportedSpecOptionType
from infrared.core.utils.dict_utils import dict_insert
import infrared.core.services.plugins
from infrared.core.services.plugins import InfraredPluginManager
from infrared.core.services.plugins import InfraredPlugin
from infrared.core.services import CoreServices, ServiceName

PLUGIN_SPEC = 'plugin.spec'
SAMPLE_PLUGINS_DIR = 'tests/example/plugins'

SUPPORTED_TYPES_DICT = dict(
    supported_types=dict(
        supported_type1='Tools of supported_type1',
        supported_type2='Tools of supported_type2',
        provision='Provisioning plugins',
        install='Installing plugins',
        test='Testing plugins'
    )
)


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

        plugins_conf_dict.update(SUPPORTED_TYPES_DICT)

        with lp_file.open(mode='w') as fp:
            config = ConfigParser.ConfigParser()
            for section, section_data in plugins_conf_dict.items():
                config.add_section(section)
                for option, value in section_data.items():
                    config.set(section, option, value)
            config.write(fp)

        # replace core service with or test service
        CoreServices.register_service(ServiceName.PLUGINS_MANAGER,
                                      InfraredPluginManager(lp_file.strpath))
        return CoreServices.plugins_manager()

    yield plugin_manager_helper


def get_plugin_spec_flatten_dict(plugin_dir):
    """Creates a flat dict from the plugin spec

    :param plugin_dir: A path to the plugin's dir
    :return: A flatten dictionary contains the plugin's properties
    """
    with open(os.path.join(plugin_dir, PLUGIN_SPEC)) as fp:
        spec_yaml = yaml.load(fp)

    plugin_spec_dict = dict(
        name=spec_yaml['subparsers'].keys()[0],
        dir=plugin_dir,
        description=spec_yaml['description'],
        type=spec_yaml['plugin_type']
    )

    return plugin_spec_dict


def plugin_in_conf(plugins_conf, plugin_type, plugin_name):
    """Checks if a plugin exists in a conf file

    :param plugins_conf: A path to the plugins conf file
    :param plugin_type: The plugin's type
    :param plugin_name: The Plugin's name
    :return: True if plugin is in the conf file, otherwise False
    """
    config = ConfigParser.ConfigParser()
    with open(plugins_conf) as fp:
        config.readfp(fp)

    return config.has_option(plugin_type, plugin_name)


def test_add_plugin(plugin_manager_fixture):
    """Tests the ability to add plugins

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_manager = plugin_manager_fixture()

    for plugin_dir, plugins_cnt in (
            ('type1_plugin1', 1),   # Add a plugin
            ('type1_plugin2', 2),   # Add a plugin - same type
            ('type2_plugin1', 3)):  # Add a plugin - different type

        plugin_dict = get_plugin_spec_flatten_dict(
            os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

        plugin_manager.add_plugin(plugin_dict['dir'])

        assert plugin_dict['name'] in plugin_manager.PLUGINS_DICT,\
            "Plugin wasn't added to the plugins manager."
        assert plugin_in_conf(
            plugins_conf=plugin_manager.config_file,
            plugin_type=plugin_dict['type'],
            plugin_name=plugin_dict['name']), \
            "Plugin wasn't added to conf file."
        assert len(plugin_manager.PLUGINS_DICT) == plugins_cnt


def test_load_plugin(plugin_manager_fixture):
    """Test that an existing plugin can be loaded and it's properties

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_dir = 'type1_plugin1'
    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(os.path.abspath(SAMPLE_PLUGINS_DIR), plugin_dir))

    plugin_manager = plugin_manager_fixture({
        plugin_dict['type']: {
            plugin_dict['name']: plugin_dict['dir']}
    })

    plugin = plugin_manager.get_plugin(plugin_name=plugin_dict['name'])

    assert type(plugin) is InfraredPlugin, "Failed to add a plugin"
    assert plugin.name == plugin_dict['name'], "Wrong plugin name"
    assert plugin.description == plugin_dict['description'], \
        'Wrong plugin description'


def test_add_plugin_with_same_name(plugin_manager_fixture):
    """Tests that it not possible to add a plugin with a name that already
    exists

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_dir = 'type1_plugin1'
    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

    plugin_manager = plugin_manager_fixture({
        plugin_dict['type']: {
            plugin_dict['name']: plugin_dict['dir']}
    })

    plugins_cfg_mtime_before_add = os.path.getmtime(plugin_manager.config_file)
    plugins_cnt_before_try = len(plugin_manager.PLUGINS_DICT)

    with pytest.raises(IRFailedToAddPlugin):
        plugin_manager.add_plugin(plugin_dict['dir'])

    assert plugins_cnt_before_try == len(plugin_manager.PLUGINS_DICT)
    assert os.path.getmtime(
        plugin_manager.config_file) == plugins_cfg_mtime_before_add, \
        "Plugins configuration file has been modified."


def test_add_plugin_unsupported_type(plugin_manager_fixture):
    """Test that it's not possible to add a plugin from unsupported type

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_manager = plugin_manager_fixture()

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, 'unsupported_plugin'))

    plugins_cfg_mtime_before_add = os.path.getmtime(plugin_manager.config_file)
    plugins_cnt_before_try = len(plugin_manager.PLUGINS_DICT)

    with pytest.raises(IRFailedToAddPlugin):
        plugin_manager.add_plugin(plugin_dict['dir'])

    assert not plugin_in_conf(
        plugins_conf=plugin_manager.config_file,
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name']), \
        "Plugin was added to conf file."
    assert plugins_cnt_before_try == len(plugin_manager.PLUGINS_DICT)
    assert os.path.getmtime(
        plugin_manager.config_file) == plugins_cfg_mtime_before_add, \
        "Plugins configuration file has been modified."


def test_remove_plugin(plugin_manager_fixture):
    """ Tests the ability to remove a plugin

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugins_conf = {}
    for plugin_dir in ('type1_plugin1', 'type1_plugin2', 'type2_plugin1'):
        plugin_dict = get_plugin_spec_flatten_dict(
            os.path.join(os.path.abspath(SAMPLE_PLUGINS_DIR), plugin_dir))
        dict_insert(plugins_conf,
                    plugin_dict['dir'],
                    plugin_dict['type'],
                    plugin_dict['name'],)

    plugin_manager = plugin_manager_fixture(plugins_conf)

    for plugin_dir, plugins_cnt in (
            ('type1_plugin1', 2),
            ('type2_plugin1', 1),
            ('type1_plugin2', 0)):
        plugin_dict = get_plugin_spec_flatten_dict(
            os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

        assert plugin_dict['name'] in plugin_manager.PLUGINS_DICT, \
            "Can't remove unexisting plugin"

        plugin_manager.remove_plugin(plugin_dict['name'])

        with pytest.raises(KeyError):
            plugin_manager.get_plugin(plugin_name=plugin_dict['name'])

        assert not plugin_in_conf(
            plugins_conf=plugin_manager.config_file,
            plugin_type=plugin_dict['type'],
            plugin_name=plugin_dict['name']), \
            "Plugin wasn't removed from conf file."
        assert len(plugin_manager.PLUGINS_DICT) == plugins_cnt


def test_remove_unexisting_plugin(plugin_manager_fixture):
    """Tests the behavior of removing unexisting plugin

    Checks that no exception is being raised and no changes in
    InfraredPluginManager dict and configuration file
    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_manager = plugin_manager_fixture()

    plugins_cfg_mtime_before_add = os.path.getmtime(plugin_manager.config_file)
    plugins_cnt_before_try = len(plugin_manager.PLUGINS_DICT)

    with pytest.raises(IRFailedToRemovePlugin):
        plugin_manager.remove_plugin('unexisting_plugin')

    assert plugins_cnt_before_try == len(plugin_manager.PLUGINS_DICT)
    assert os.path.getmtime(
        plugin_manager.config_file) == plugins_cfg_mtime_before_add, \
        "Plugins configuration file has been modified."


@pytest.mark.parametrize("input_args, plugins_conf", [
    ("plugin list", None),
    ("plugin add tests/example/plugins/type1_plugin1", None),
    ("plugin remove type1_plugin1", dict(
        supported_type1=dict(
            type1_plugin1='tests/example/plugins/type1_plugin1'))),
])
def test_plugin_cli(plugin_manager_fixture, input_args, plugins_conf):
    """Tests that plugin CLI works

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    :param input_args: infrared's testing arguments
    :param plugins_conf: Plugins conf data as a dictionary
    """
    plugin_manager_fixture(plugins_conf)

    from infrared.main import main as ir_main
    rc = ir_main(input_args.split())

    assert rc == 0, \
        "Return code ({}) != 0, cmd='infrared {}'".format(rc, input_args)


def test_add_plugin_no_spec(plugin_manager_fixture):
    """Tests that it's not possible to add plugin without a spec file

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """

    plugin_dir = os.path.join(SAMPLE_PLUGINS_DIR, 'plugin_without_spec')

    plugin_manager = plugin_manager_fixture({})

    plugins_cfg_mtime_before_add = os.path.getmtime(plugin_manager.config_file)
    plugins_cnt_before_try = len(plugin_manager.PLUGINS_DICT)

    with pytest.raises(IRFailedToAddPlugin):
        plugin_manager.add_plugin(plugin_dir)

    assert plugins_cnt_before_try == len(plugin_manager.PLUGINS_DICT)
    assert os.path.getmtime(
        plugin_manager.config_file) == plugins_cfg_mtime_before_add, \
        "Plugins configuration file has been modified."


@pytest.mark.parametrize("description, plugin_spec", [
    ('no_description', {
        'plugin_type': 'supported_type',
        'subparsers': {
            'sample_plugin1:': {}}}),
    ('no_type', {
        'description': 'some plugin description',
        'subparsers': {
            'sample_plugin1:': {}}}),
    ('no_value', {
        'plugin_type': '',
        'subparsers': {
            'sample_plugin1:': {}}}),
    ('no_subparsers_key', {
        'plugin_type': 'supported_type',
        'description': 'some plugin description'}),
    ('no_subparsers_value', {
        'plugin_type': 'supported_type',
        'description': 'some plugin description',
        'subparsers': ''}),
])
def test_add_plugin_corrupted_spec(tmpdir_factory, description, plugin_spec):
    """Tests that it's not possible to add a plugin with invalid spec file

    :param tmpdir_factory: pytest builtin fixture for creating temp dirs
    :param description: test description (adds a description in pytest run)
    :param plugin_spec: dictionary with data for spec file
    :return:
    """

    lp_dir = tmpdir_factory.mktemp('test_tmp_dir')
    lp_file = lp_dir.join('plugin.spec')

    with open(lp_file.strpath, 'w') as fp:
        yaml.dump(plugin_spec, fp, default_flow_style=True)

    try:
        with pytest.raises(IRFailedToAddPlugin):
            InfraredPlugin.spec_validator(lp_file.strpath)
    finally:
        lp_dir.remove()


def test_plugin_with_unsupporetd_option_type_in_spec(plugin_manager_fixture):
    """Tests that the user get a proper error

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """
    plugin_dir = os.path.join(SAMPLE_PLUGINS_DIR,
                              'plugin_with_unsupported_option_type_in_spec')
    plugin_dict = get_plugin_spec_flatten_dict(plugin_dir)

    plugin_manager = plugin_manager_fixture()
    plugin_manager.add_plugin(plugin_dir)

    from infrared.main import main as ir_main
    with pytest.raises(IRUnsupportedSpecOptionType):
        ir_main([plugin_dict['name'], '--help'])


@pytest.mark.parametrize("dest,real_dest", [(
    SAMPLE_PLUGINS_DIR, SAMPLE_PLUGINS_DIR),
    (None, "plugins")])
def test_add_plugin_from_git(plugin_manager_fixture, mocker, dest, real_dest):

    plugin_manager = plugin_manager_fixture()

    mock_subprocess = mocker.patch(
        "infrared.core.services.plugins.subprocess")
    mock_os = mocker.patch("infrared.core.services.plugins.os")
    mock_os.path.exists.return_value = False
    mock_os.listdir.return_value = ["sample_plugin"]
    mock_tempfile = mocker.patch("infrared.core.services.plugins.tempfile")
    mock_shutil = mocker.patch("infrared.core.services.plugins.shutil")

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, 'type1_plugin1'))
    mock_os.path.join.return_value = os.path.join(plugin_dict["dir"],
                                                  PLUGIN_SPEC)

    # add_plugin call
    plugin_manager.add_plugin(
        "https://sample_github.null/plugin_repo.git", dest)

    mock_os.path.abspath.assert_has_calls([mocker.call(real_dest)])

    mock_tempfile.mkdtemp.assert_called_once()
    mock_os.getcwdu.assert_called_once()
    mock_os.chdir.assert_has_calls(mock_tempfile.mkdtemp.return_value)
    mock_subprocess.check_output.assert_called_with(
        ['git', 'clone', 'https://sample_github.null/plugin_repo.git'])
    mock_os.listdir.assert_called_once()
    mock_os.join.has_call(real_dest, mock_os.listdir.return_value[0])
    mock_os.join.has_call(mock_tempfile.mkdtemp.return_value,
                          mock_os.listdir.return_value[0])
    mock_shutil.copytree.assert_called_with(mock_os.path.join.return_value,
                                            mock_os.path.join.return_value)
    mock_os.chdir.assert_has_calls(mock_os.getcwdu.return_value)
    mock_shutil.rmtree.assert_called_with(mock_tempfile.mkdtemp.return_value)


def test_add_plugin_from_git_exception(plugin_manager_fixture, mocker):

    plugin_manager = plugin_manager_fixture()

    mock_subprocess = mocker.patch(
        "infrared.core.services.plugins.subprocess")
    mock_subprocess.check_output.side_effect = subprocess.CalledProcessError(
        1, "some_git_cmd")
    mock_subprocess.CalledProcessError = subprocess.CalledProcessError
    mock_tempfile = mocker.patch("infrared.core.services.plugins.tempfile")
    mock_shutil = mocker.patch("infrared.core.services.plugins.shutil")
    mock_os = mocker.patch("infrared.core.services.plugins.os")
    mock_os.path.exists.return_value = False

    # add_plugin call
    with pytest.raises(IRFailedToAddPlugin):
        plugin_manager.add_plugin(
            "https://sample_github.null/plugin_repo.git")

    mock_shutil.rmtree.assert_called_with(mock_tempfile.mkdtemp.return_value)


def validate_plugins_presence_in_conf(
        plugin_manager, plugins_dict, present=True):
    """Validate presence of plugins in the configuration file

    :param plugin_manager: InfraredPluginManager object
    :param plugins_dict:  Dict of plugins
    {plugin_name: plugin_dir_path, ...}
    :param present: Whether all plugins in the dict should be present in the
    plugins configuration file or not.
    """
    assert present in (True, False), \
        "'absent' accept only Boolean values, got: '{}'".format(str(present))

    with open(plugin_manager.config_file) as config_file:
        plugins_cfg = ConfigParser.ConfigParser()
        plugins_cfg.readfp(config_file)

        for plugin_path in plugins_dict.values():
            plugin = InfraredPlugin(plugin_path['src'])

            if present:
                assert plugins_cfg.has_option(plugin.type, plugin.name), \
                    "Plugin '{}' was suppose to be in the plugins " \
                    "configuration file".format(plugin.name)
            else:
                assert not plugins_cfg.has_option(plugin.type, plugin.name), \
                    "Plugin '{}' wasn't suppose to be in the plugins " \
                    "configuration file".format(plugin.name)


def test_plugin_add_all(plugin_manager_fixture):
    """Tests the add and remove all plugins functioning

    :param plugin_manager_fixture: Fixture object which yields
    InfraredPluginManger object
    """
    tests_plugins = (
        'provision_plugin1', 'provision_plugin2',
        'install_plugin1', 'install_plugin2',
        'test_plugin1', 'test_plugin2'
    )
    tests_plugins_dir = 'tests/example/plugins/add_remove_all_plugins/'

    infrared.core.services.plugins.PLUGINS_REGISTRY = {
        plugin_name: {'src': os.path.join(tests_plugins_dir, plugin_name)}
        for plugin_name in tests_plugins
        }

    plugins_registry = infrared.core.services.plugins.PLUGINS_REGISTRY
    plugin_manager = plugin_manager_fixture()

    # Validates that plugins aren't in configuration file from the beginning
    validate_plugins_presence_in_conf(
        plugin_manager, plugins_registry, present=False)

    # Validates all plugins are in the configuration file
    plugin_manager.add_all_available()
    validate_plugins_presence_in_conf(
        plugin_manager, plugins_registry, present=True)

    # Validates all plugins are no longer in the configuration file
    plugin_manager.remove_all()
    validate_plugins_presence_in_conf(
        plugin_manager, plugins_registry, present=False)
