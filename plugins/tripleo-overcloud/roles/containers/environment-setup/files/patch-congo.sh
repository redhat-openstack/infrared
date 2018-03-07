#!/bin/bash

set -x
patch /usr/share/openstack-tripleo-common-containers/container-images/overcloud_containers.yaml.j2 <<EOF
132,138d131
< - imagename: {% raw %}"{{namespace}}/{{name_prefix}}congress-api{{name_suffix}}:{{tag}}"{% endraw %}
<   params:
<   - DockerCongressApiImage
<   - DockerCongressConfigImage
<   services:
<   - OS::TripleO::Services::Congress
<
EOF
sed -i '/.*congress-api/d' /usr/share/openstack-tripleo-common-containers/container-images/overcloud_containers.yaml
grep -i congr /usr/share/openstack-tripleo-common-containers/container-images/overcloud_containers.yaml.j2
grep -i congr /usr/share/openstack-tripleo-common-containers/container-images/overcloud_containers.yaml
exit 0
