from infrared.core.services import CoreServices


def node_list(**kwargs):
    workspace_manager = CoreServices.workspace_manager()
    ws = workspace_manager.get_active_workspace()
    nodes = [node[0] for node in workspace_manager.node_list(
        workspace_name=ws.name)]
    return nodes


def workspace_list(**kwargs):
    workspace_manager = CoreServices.workspace_manager()
    return [ws.name for ws in workspace_manager.list()]


def plugin_list(**kwargs):
    plugin_manager = CoreServices.plugins_manager()
    installed_plugins = plugin_manager.get_installed_plugins()
    completions = []
    for ptype, plugin in installed_plugins.iteritems():
        completions.extend(plugin.keys())
    return completions
