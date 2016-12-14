import ConfigParser
import os

import pytest

from infrared.core.services.plugins import InfraRedPluginManager
from infrared.core.services.plugins import InfraRedPlugin
from infrared.core.services.plugins import DEFAULT_PLUGIN_INI
from infrared.main import PluginManagerSpec

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


def generate_formated_plugins_list(provision=None, install=None, test=None):
    """
    Creates and returns a string that mimic the return value of
    'get_formatted_plugins_list' method.
    :param provision: List of plugins of 'provision' type
    :param install: List of plugins of 'install' type
    :param test: List of plugins of 'test' type
    """
    provision = provision or []
    install = install or []
    test = test or []

    formatted_list = '  install         {{{}}}\n' \
                     '  provision       {{{}}}\n' \
                     '  test            {{{}}}\n'.format(','.join(install),
                                                         ','.join(provision),
                                                         ','.join(test))

    return formatted_list


def test_list_plugins_before_add(plugin_manager):
    """
    Tests list plugins before adding any plugins
    """
    expected_result_str = generate_formated_plugins_list()

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str


def test_add_plugin(plugin_manager):
    """
    Tests the ability to add a plugin
    """
    plugin_manager.add_plugin(os.path.join(SAMPLE_PLUGINS_DIR, 'prov_plugin1'))

    plugin = plugin_manager.get_plugin(
        plugin_type='provision',
        plugin_name='provision_example1')

    assert type(plugin) is InfraRedPlugin, "Failed to add a plugin"
    assert plugin.name == 'provision_example1', "Wrong plugin name"
    assert plugin.description == 'Example1 provisioner plugin', \
        'Wrong plugin description'


def test_plugin_list_after_first_add(plugin_manager):
    """
    Tests list plugins after adding a plugin
    """
    expected_result_str = generate_formated_plugins_list(
        provision=['provision_example1'])

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str


def test_add_another_plugin_same_type(plugin_manager):
    """
    Tests the ability to add a plugin
    """
    plugin_manager.add_plugin(os.path.join(SAMPLE_PLUGINS_DIR, 'prov_plugin2'))

    plugin = plugin_manager.get_plugin(
        plugin_type='provision',
        plugin_name='provision_example2')

    assert type(plugin) is InfraRedPlugin, "Failed to add a plugin"
    assert plugin.name == 'provision_example2', "Wrong plugin name"
    assert plugin.description == 'Example2 provisioner plugin', \
        'Wrong plugin description'


def test_plugin_list_after_second_add(plugin_manager):
    """
    Tests list plugins after adding a plugin
    """
    expected_result_str = generate_formated_plugins_list(
        provision=['provision_example1', 'provision_example2'])

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str


def test_add_another_plugin_different_type(plugin_manager):
    """
    Tests the ability to add a plugin
    """
    plugin_manager.add_plugin(os.path.join(
        SAMPLE_PLUGINS_DIR, 'install_plugin1'))

    plugin = plugin_manager.get_plugin(
        plugin_type='install',
        plugin_name='install_example1')

    assert type(plugin) is InfraRedPlugin, "Failed to add a plugin"
    assert plugin.name == 'install_example1', "Wrong plugin name"
    assert plugin.description == 'Example1 install plugin', \
        'Wrong plugin description'


def test_plugin_list_after_third_add(plugin_manager):
    """
    Tests list plugins after adding a plugin
    """
    expected_result_str = generate_formated_plugins_list(
        provision=['provision_example1', 'provision_example2'],
        install=['install_example1'])

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str


def test_add_plugin_unsupported_type(plugin_manager):
    """
    Tests the ability to add a plugin
    """
    with pytest.raises(Exception):
        plugin_manager.add_plugin(os.path.join(
            SAMPLE_PLUGINS_DIR, 'unsupported_type_plugin'))


def test_plugin_list_after_unsupported_plugin_add(plugin_manager):
    """
    Tests list plugins after trying to add an unsupported plugin
    """
    expected_result_str = generate_formated_plugins_list(
        provision=['provision_example1', 'provision_example2'],
        install=['install_example1'])

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str


def test_remove_plugin(plugin_manager):
    """
    Tests the ability to remove a plugin
    """
    plugin_manager.remove_plugin('provision', 'provision_example1')

    plugin = plugin_manager.get_plugin(
        plugin_type='provision',
        plugin_name='provision_example1')

    assert plugin is None, "Failed to remove a plugin"


def test_plugin_list_after_first_remove(plugin_manager):
    """
    Tests list plugins after removing a plugin
    """
    expected_result_str = generate_formated_plugins_list(
        provision=['provision_example2'],
        install=['install_example1'])

    actual_plugins_list = \
        PluginManagerSpec.get_formatted_plugins_list(plugin_manager)

    assert actual_plugins_list == expected_result_str
