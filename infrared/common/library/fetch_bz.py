#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Ariel Opincaru <aopincar@redhat.com>
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

import json
import xmlrpclib

import bugzilla
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: fetch_bz
version_added: "2.4"
short_description: Fetches details of bugs from Bugzilla instance
description:
   - This module makes use of the [*] 'python-bugzilla' package to talk with
     Bugzilla instance over XMLRPC in order to fetch information on bugs
     [*] https://pypi.org/project/python-bugzilla/
options:
    id:
      description:
          - An ID of a bug
      required: true
      type: int
    url:
      description:
          - The URL of the Bugzilla instance to talk with
      required: False
      default: https://bugzilla.redhat.com (Red Hat’s Bugzilla instance)
      type: str
    user:
      description:
          - Username to connect with
      required: False
      type: str
    password:
      description:
          - Password for the username connecting with
      required: False
      type: str
    sslverify:
      description:
          - Whether to enable SSL verification
      required: False
      default: True
      type: bool

requirements:
    - "python-bugzilla"
'''

URL = "https://bugzilla.redhat.com"


def is_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False


def main():

    result = {}

    module_args = dict(
        id=dict(type='int', required=True),
        url=dict(type='str', required=False, default=URL),
        user=dict(type='str', rebuild=False, default=None),
        password=dict(type='str', rebuild=False, default=None, no_log=True),
        sslverify=dict(type='bool', required=False, default=True),)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,)

    bz_id = module.params.pop('id')

    try:
        bzapi = bugzilla.Bugzilla(**module.params)
        bug = bzapi.getbug(objid=bz_id)

        result.update(
            {key: val for key, val in vars(bug).iteritems()
             if is_serializable(val)})

    # Raised when the user is not authorized or not logged in
    except xmlrpclib.Fault as ex:
        result['msg'] = ' '.join((str(ex.faultCode), ex.faultString))
        module.fail_json(**result)
    except Exception as ex:
        result['msg'] = ex.message
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
