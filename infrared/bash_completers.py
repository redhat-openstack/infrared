"""
argcomplete completers are callables, that accept 4 arguments:
    action
    prefix
    parser
    parsed_args

    and return list of names for bash completion.
    More about in https://pypi.python.org/pypi/argcomplete
    or https://github.com/kislyuk/argcomplete
"""


from infrared.core.services import CoreServices


def node_list(**kwargs):
    """Return node names list for active workspace"""
    workspace_manager = CoreServices.workspace_manager()
    ws = workspace_manager.get_active_workspace()
    nodes = [node[0] for node in workspace_manager.node_list(
        workspace_name=ws.name)]
    return nodes


def group_list(**kwargs):
    """Return node groups names list for workspace"""

    workspace_manager = CoreServices.workspace_manager()
    parsed_args = kwargs.get("parsed_args")
    # need to carefully check if we have name in parsed_args
    # which is of argprase.Namespace type
    if parsed_args and 'name' in parsed_args:
        ws_name = parsed_args.name
    else:
        ws_name = workspace_manager.get_active_workspace().name
    return [group[0] for group in workspace_manager.group_list(
        workspace_name=ws_name)]


def node_and_group_list(**kwargs):
    """Returns the list of nodes and groups."""

    return list(set(node_list(**kwargs) + group_list(**kwargs)))


def workspace_list(**kwargs):
    """Return workspace names list"""
    workspace_manager = CoreServices.workspace_manager()
    return [ws.name for ws in workspace_manager.list()]


def plugin_list(**kwargs):
    """Return plugins names list"""
    plugin_manager = CoreServices.plugins_manager()
    installed_plugins = plugin_manager.get_installed_plugins()
    completions = []
    for ptype, plugin in installed_plugins.iteritems():
        completions.extend(plugin.keys())
    return completions
