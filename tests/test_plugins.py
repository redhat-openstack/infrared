import ConfigParser
import imp
import os
import yaml

import pip
import pytest

from infrared.core.services.plugins import InfraRedPluginManager
from infrared.core.services.plugins import InfraRedPlugin
from infrared.core.services.plugins import DEFAULT_PLUGIN_INI


PLUGIN_SPEC = 'plugin.spec'
SAMPLE_PLUGINS_DIR = 'tests/example/plugins'


@pytest.fixture(scope="session")
def plugin_manager(tmpdir_factory):
    """
    Creates a fixture which returns a PluginManager object based on temporary
    plugins conf with default values(sections - provision, install & test)
    """
    lp_dir = tmpdir_factory.mktemp('test_tmp_dir')
    lp_file = lp_dir.join('.plugins.ini')

    with lp_file.open(mode='w') as fp:
        config = ConfigParser.ConfigParser()
        for section, section_data in DEFAULT_PLUGIN_INI.items():
            config.add_section(section)
            for option, value in section_data.items():
                config.set(section, option, value)
        config.write(fp)

    yield InfraRedPluginManager(lp_file.strpath)
    lp_dir.remove()


def get_plugin_spec_flatten_dict(plugin_dir):
    """
    Creates a flatten dict from the plugin spec
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


def does_plugin_in_conf_file(plugins_conf, plugin_type, plugin_name):
    """
    Checks if a plugin exists in a conf file
    :param plugins_conf: A path to the plugins conf file
    :param plugin_type: The plugin's type
    :param plugin_name: The Plugin's name
    :return: True if plugin is in the conf file, otherwise False
    """
    config = ConfigParser.ConfigParser()
    with open(plugins_conf) as fp:
        config.readfp(fp)

    return config.has_option(plugin_type, plugin_name)


@pytest.mark.parametrize(('plugin_dir', 'plugins_cnt'), [
    ('provision_plugin1', 1),  # Add a plugin
    ('provision_plugin2', 2),  # Add a plugin - same type
    ('install_plugin', 3)  # Add a plugin - different type
])
def test_add_plugin(plugin_manager, plugin_dir, plugins_cnt):
    """
    Tests the ability to add a plugin
    :param plugin_manager: Fixture object which yields InfraRedPluginManger
    object
    :param plugin_dir: Plugin's dir
    :param plugins_cnt: Plugins count after addition
    """

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

    plugin_manager.add_plugin(plugin_dict['dir'])

    assert plugin_dict['name'] in plugin_manager.PLUGINS_DICT[
        plugin_dict['type']], "Plugin wasn't added to the plugins manager."
    assert does_plugin_in_conf_file(
        plugins_conf=plugin_manager.config_file,
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name']),\
        "Plugin wasn't added to conf file."
    assert len(plugin_manager.get_all_plugins()) == plugins_cnt


@pytest.mark.parametrize('plugin_dir', [
    'provision_plugin1',
    'provision_plugin2',
    'install_plugin'
])
def test_load_plugin(plugin_manager, plugin_dir):
    """
    Test that an existing plugin can be loaded and it's properties
    :param plugin_manager: Fixture object which yields InfraRedPluginManger
    object
    :param plugin_dir: Plugin's dir (to get its details)
    """

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

    plugin = plugin_manager.get_plugin(
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name'])

    assert type(plugin) is InfraRedPlugin, "Failed to add a plugin"
    assert plugin.name == plugin_dict['name'], "Wrong plugin name"
    assert plugin.description == plugin_dict['description'],\
        'Wrong plugin description'


@pytest.mark.parametrize('plugin_dir', ['provision_plugin1'])
def test_requirements_installed(plugin_dir):
    """
    Tests that requirements were installed when adding a plugin
    :param plugin_dir: Plugin's dir
    """

    # Refreshing "pkg_resources"
    pip.utils.pkg_resources = imp.reload(pip.utils.pkg_resources)

    installed_packages = \
        {i.key: i.version for i in pip.get_installed_distributions()}

    requirements_file = \
        os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir, 'plugin_requirements.txt')
    with open(requirements_file) as fp:
        requirements = fp.read().splitlines()

    for requirement in requirements:
        assert requirement.lower() in installed_packages, \
            "Requirements were not installed: {}".format(requirement.lower())


def test_add_plugin_unsupported_type(plugin_manager):
    """
    Test that it's not possible to add a plugin from unsupported type
    :param plugin_manager: Fixture object which yields InfraRedPluginManger
    object
    """

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, 'unsupported_plugin'))

    plugins_cnt_before_try = len(plugin_manager.get_all_plugins())

    with pytest.raises(Exception):
        plugin_manager.add_plugin(plugin_dict['dir'])

    assert plugin_dict['type'] not in plugin_manager.PLUGINS_DICT
    assert not does_plugin_in_conf_file(
        plugins_conf=plugin_manager.config_file,
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name']),\
        "Plugin was added to conf file."
    assert plugins_cnt_before_try == len(plugin_manager.get_all_plugins())


@pytest.mark.parametrize(('plugin_dir', 'plugins_cnt'), [
    ('provision_plugin2', 2),
    ('install_plugin', 1),
    ('provision_plugin1', 0)
])
def test_remove_plugin(plugin_manager, plugin_dir, plugins_cnt):
    """
    Tests the ability to remove a plugin
    :param plugin_manager: Fixture object which yields InfraRedPluginManger
    object
    :param plugin_dir: Plugin's dir (to get its details)
    :param plugins_cnt: Plugins count after removal
    """

    plugin_dict = get_plugin_spec_flatten_dict(
        os.path.join(SAMPLE_PLUGINS_DIR, plugin_dir))

    plugin_manager.remove_plugin(plugin_dict['type'], plugin_dict['name'])

    plugin = plugin_manager.get_plugin(
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name'])

    assert plugin is None, "Failed to remove a plugin"
    assert not does_plugin_in_conf_file(
        plugins_conf=plugin_manager.config_file,
        plugin_type=plugin_dict['type'],
        plugin_name=plugin_dict['name']),\
        "Plugin wasn't removed from conf file."
    assert len(plugin_manager.get_all_plugins()) == plugins_cnt
