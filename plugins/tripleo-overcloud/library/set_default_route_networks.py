DOCUMENTATION = '''
---
module: set_default_route_networks
short_description: Modify default_route_networks in roles_data
description:
  - Modify the value for default_route_networks in roles_data YAML file
options:
  roles_file:
    description:
    - The roles data file that is the target of the modifications.
    required: true
    default: None
  value:
    description:
      - The incoming value, if this is a string it will be appended to the exsing value. If a list value is used the value is replaced/added.
    required: true
    type: raw
    default: None
  backup:
    description:
    - Whether to make a backup copy of the current file when performing an edit.
    required: false
    default: true
author:
- "Harald Jensås <hjensas@redhat.com>"
extends_documentation_fragment: []
'''

EXAMPLES = '''
- name: Append 'ControlPlane' to default_route_networks
  set_default_route_networks:
    src: "{{ template_base }}/roles/roles_data.yaml"
    value: ControlPlane
    backup: true
- name: Set '[InternalApi, Management]' as default_route_networks
  set_default_route_networks:
    src: "{{ template_base }}/roles/roles_data.yaml"
    value:
    - InternalApi
    - Management
    backup: true
'''

import collections
import os
import shutil
import yaml


class TemplateDumper(yaml.SafeDumper):
    def represent_ordered_dict(self, data):
        return self.represent_dict(data.items())

    def description_presenter(self, data):
        if not len(data) > 80:
            return self.represent_scalar('tag:yaml.org,2002:str', data)
        return self.represent_scalar('tag:yaml.org,2002:str', data, style='|')


class TemplateLoader(yaml.SafeLoader):
    def construct_mapping(self, node):
        self.flatten_mapping(node)
        return collections.OrderedDict(self.construct_pairs(node))


TemplateDumper.add_representer(str, TemplateDumper.description_presenter)
TemplateDumper.add_representer(bytes, TemplateDumper.description_presenter)
TemplateDumper.add_representer(collections.OrderedDict,
                               TemplateDumper.represent_ordered_dict)
TemplateLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                               TemplateLoader.construct_mapping)


def main():
    result = dict(
        success=False,
        changed=False,
        error="",
        environment={},
    )

    module = AnsibleModule(
        argument_spec=dict(
            roles_file=dict(default=None, type='str'),
            value=dict(type='raw'),
            backup=dict(default=True, type='bool'),
        )
    )

    roles_file = os.path.abspath(module.params['roles_file'])
    backup = module.params['backup']
    value = module.params['value']

    if not os.path.exists(roles_file):
        module.fail('File does not exists {}'.format(roles_file))

    with open(roles_file, 'r') as file:
        roles = yaml.load(file.read(),  Loader=TemplateLoader)

    for role in roles:
        default_route_networks = role.setdefault('default_route_networks', [])
        if isinstance(value, str):
            default_route_networks.append(value)
        elif isinstance(value, list):
            role['default_route_networks'] = value
        else:
            module.fail('value must be string or list')

    if backup:
        shutil.copy(roles_file, roles_file + '.orig')

    with open(roles_file, 'w') as file:
        yaml.dump(roles, file, TemplateDumper)

    result['success'] = True
    result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    main()
