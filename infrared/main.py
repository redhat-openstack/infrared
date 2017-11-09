import sys

import argcomplete
import os
import pkg_resources as pkg
from pbr import version


def inject_common_paths():
    """Discover the path to the common/ directory provided
       by infrared core.
    """
    def override_conf_path(common_path, envvar, specific_dir):
        conf_path = os.environ.get(envvar, '')
        additional_conf_path = os.path.join(common_path, specific_dir)
        if conf_path:
            full_conf_path = ':'.join([additional_conf_path, conf_path])
        else:
            full_conf_path = additional_conf_path
        os.environ[envvar] = full_conf_path

    version_info = version.VersionInfo('infrared')

    common_path = pkg.resource_filename(version_info.package,
                                        'common')
    override_conf_path(common_path, 'ANSIBLE_ROLES_PATH', 'roles')
    override_conf_path(common_path, 'ANSIBLE_FILTER_PLUGINS', 'filter_plugins')
    override_conf_path(common_path, 'ANSIBLE_CALLBACK_PLUGINS',
                       'callback_plugins')
    override_conf_path(common_path, 'ANSIBLE_LIBRARY', 'library')


# This needs to be called here because as soon as an ansible class is loaded
# the code in constants.py is triggered. That code reads the configuration
# settings from all sources (ansible.cfg, environment variables, etc).
# If the first include to ansible modules is moved deeper in the InfraRed
# code (or on demand), then this call can be moved as well in that place.
inject_common_paths()

from infrared.core.services import CoreServices  # noqa
from infrared.api import WorkspaceManagerSpec, PluginManagerSpec, SSHSpec, \
    InfraredPluginsSpec, SpecManager  # noqa


def main(args=None):
    CoreServices.setup()
    specs_manager = SpecManager()

    # Init Managers
    specs_manager.register_spec(
        WorkspaceManagerSpec('workspace',
                             description="Workspace manager. "
                                         "Allows to create and use an "
                                         "isolated environment for plugins "
                                         "execution."))
    specs_manager.register_spec(
        PluginManagerSpec('plugin',
                          description="Plugin management"))

    specs_manager.register_spec(
        SSHSpec(
            'ssh',
            description="Interactive ssh session to node from inventory."))

    # register all plugins
    for plugin in CoreServices.plugins_manager().PLUGINS_DICT.values():
        specs_manager.register_spec(InfraredPluginsSpec(plugin))

    argcomplete.autocomplete(specs_manager.parser)
    return specs_manager.run_specs(args) or 0

if __name__ == '__main__':
    sys.exit(int(main() or 0))
