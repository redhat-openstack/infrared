#!/usr/bin/python

# (c) 2017, Red Hat, Inc.
# Oleksii Baranov <obaranov@redhat.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import requests

DOCUMENTATION = '''
---
module: list_builds-release
description:
    - Lists RHEL-OSP repo files on RHEL systems
options:
    base_url:
        description:
            - The base url where all the OSP puddles are storred
        required: yes
    version:
        description:
            - The version of the OSP product (10, 11, 12, etc)
        required: yes
    rhel_version:
        description:
            - The major version of the RHEL.
        required: yes
    subtype:
        description:
            - The puddle subtype. Can be 'director', 'testing', etc.
        required: no
    date_format:
        description:
            - The date format displayed for the build on base_url
        default: '%d-%b-%Y'
    time_format:
        description:
            - The time format displayed for the build on base_url
        default: '%H:%M'
'''

EXAMPLE = '''
- name: List all the builds for 11
  list_builds:
      base_url: https://url.corp.redhat.com/puddles
      version: 11
      rhel_version: 7
'''


def main():
    """ Main """
    module = AnsibleModule(
        argument_spec=dict(
            base_url=dict(),
            version=dict(),
            rhel_version=dict(),
            subtype=dict(default=''),
            date_format=dict(default='%d-%b-%Y'),
            time_format=dict(default='%H:%M'),
        )
    )

    base_url = module.params['base_url']
    version = module.params['version']
    rhel_version = module.params['rhel_version']
    subtype = module.params['subtype']
    date_format = module.params['date_format']
    time_format = module.params['time_format']

    try:
        # check if base url is redirected
        req = requests.get(base_url, verify=False)

        # construct full url
        request_url = "{url}/{version}-RHEL-{rhel_version}{subtype}".format(
            url=req.url,
            version=(version + ".0" if '.' not in version else version),
            rhel_version=rhel_version,
            subtype=('-' + subtype if subtype else '')
        )
        data_req = requests.get(request_url, verify=False)

        # get all folders
        pattern = re.compile(
            "icons\/folder.*<a.*>(?P<puddle_name>.*)\/<\/a>[\s]*" +
            "(?P<date>\S+) (?P<time>\S+)")
        results = [{'name': puddle_name,
                    'date': "{0} {1}".format(date, time)}
                   for puddle_name, date, time in
                   pattern.findall(data_req.content)]

        # order results by date
        results.sort(key=lambda r: datetime.datetime.strptime(
            r['date'], "{0} {1}".format(date_format, time_format)),
                     reverse=True)

        module.exit_json(changed=True, builds=results)

    except Exception as ex:
        module.fail_json(msg=ex.message)


from ansible.module_utils.basic import *

main()
