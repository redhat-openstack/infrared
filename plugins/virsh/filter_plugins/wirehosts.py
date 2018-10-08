
from __future__ import print_function

from ansible import errors


def create_ifaces(source_node, target_node, bridge_pattern, iface):
    for dst_cnt in range(target_node.get('num', 1)):
        source_iface = iface.copy()
        source_iface['model'] = source_iface['src_model']
        for key in ['src_model', 'connect_to']:
            try:
                del source_iface[key]
            except KeyError:
                pass
        if source_node.get('num', 1) == 1:
            source_iface['network'] = bridge_pattern.format("0", str(dst_cnt))
        else:
            source_iface['network'] = bridge_pattern.format("%s", str(dst_cnt))
            source_iface['needs_formatting'] = True
        source_node['interfaces'].append(source_iface)

    for src_cnt in range(source_node.get('num', 1)):
        target_iface = iface.copy()
        for key in ['src_model', 'connect_to']:
            try:
                del target_iface[key]
            except KeyError:
                pass
        if target_node.get('num', 1) == 1:
            target_iface['network'] = bridge_pattern.format(str(src_cnt), "0")
        else:
            target_iface['network'] = bridge_pattern.format(str(src_cnt), "%s")
            target_iface['needs_formatting'] = True
        target_node['interfaces'].append(target_iface)


def wire_node(nodes, node):
    if 'interfaces' not in node:
        return node

    interfaces = node['interfaces']
    node['interfaces'] = []

    for iface in interfaces:
        if 'connect_to' in iface:
            try:
                remote_node = nodes[iface['connect_to']]
            except KeyError:
                raise errors.AnsibleRuntimeError(
                    "Node %s does not exist in this topology!" %
                    iface['connect_to'])
            bridge_pattern = "{:s}{{:s}}{:s}{{:s}}".format(
                node['name'][:4], iface['connect_to'][:4])
            create_ifaces(node, remote_node, bridge_pattern, iface)
        else:
            node['interfaces'].append(iface)


def wire_nodes(nodes):
    for node in nodes.values():
        wire_node(nodes, node)

    return nodes


class FilterModule(object):
    ''' Wire nodes filter '''

    def filters(self):
        return {
            'wirenodes': wire_nodes
        }
