import ConfigParser
import os
import yaml

import pytest

from infrared.core.utils.exceptions import IRFailedToAddPlugin
from infrared.core.utils.utils import dict_insert
from infrared.core.services.plugins import InfraRedPluginManager
from infrared.core.services.plugins import InfraRedPlugin


PLUGIN_SPEC = 'plugin.spec'
SAMPLE_PLUGINS_DIR = 'tests/example/plugins'

SUPPORTED_TYPES_DICT = dict(
    supported_types=dict(
        supported_type1='Tools of supported_type1',
        supported_type2='Tools of supported_type2',
    )
)


@pytest.fixture(scope='function')
def plugin_manager_fixture(tmpdir_factory):
    """
    Creates a fixture which returns a PluginManager object based on temporary
    plugins conf with default values(sections - provision, install & test)
    """

    lp_dir = tmpdir_factory.mktemp('test_tmp_dir')
    lp_file = lp_dir.join('.plugins.ini')

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

        print lp_file.strpath
        return InfraRedPluginManager(lp_file.strpath)

    print lp_file.strpath
    yield plugin_manager_helper
    # lp_dir.remove()


def get_plugin_spec_flatten_dict(plugin_dir):
    """Creates a flatten dict from the plugin spec

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
    InfraRedPluginManger object
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
    InfraRedPluginManger object
    """

    plugin_dir = 'type1_plugin1'
    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(os.path.abspath(SAMPLE_PLUGINS_DIR), plugin_dir))
    print plugin_dict['dir']

    plugin_manager = plugin_manager_fixture({
        plugin_dict['type']: {
            plugin_dict['name']: plugin_dict['dir']}
    })

    plugin = plugin_manager.get_plugin(plugin_name=plugin_dict['name'])

    assert type(plugin) is InfraRedPlugin, "Failed to add a plugin"
    assert plugin.name == plugin_dict['name'], "Wrong plugin name"
    assert plugin.description == plugin_dict['description'], \
        'Wrong plugin description'


def test_add_plugin_with_same_name(plugin_manager_fixture):
    """Tests that it not possible to add a plugin with a name that already
    exists

    :param plugin_manager_fixture: Fixture object which yields
    InfraRedPluginManger object
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
    InfraRedPluginManger object
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
    InfraRedPluginManger object
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

        print plugin_manager.PLUGINS_DICT
        plugin_manager.remove_plugin(plugin_dict['type'], plugin_dict['name'])
        print plugin_manager.PLUGINS_DICT

        plugin = plugin_manager.get_plugin(plugin_name=plugin_dict['name'])

        assert plugin is None, "Failed to remove a plugin"
        assert not plugin_in_conf(
            plugins_conf=plugin_manager.config_file,
            plugin_type=plugin_dict['type'],
            plugin_name=plugin_dict['name']), \
            "Plugin wasn't removed from conf file."
        assert len(plugin_manager.PLUGINS_DICT) == plugins_cnt
