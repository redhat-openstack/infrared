# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
""" debug module is the new name of the human_readably module """

from __future__ import (absolute_import, division, print_function)
from ansible.plugins.callback.default \
    import CallbackModule as CallbackModule_default

__metaclass__ = type


class CallbackModule(CallbackModule_default):  # pylint: \
    # disable=too-few-public-methods,no-init
    '''
    Override for the default callback module.

    Render cmd and stderr/out outside of the rest of the result
    which it prints with indentation.

    It is done by overriding default callback,
    removing few fields from result before letting default callback process it,
    extending generated output with nicely presentation of those fields
    and then returning them back to result before returning from this module.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'debug'

    # List of keys which we want to hide from default output handler
    HIDE_KEYS = ['stdout_lines', 'stderr_lines']
    # List of keys which we want to print out nicely formatted at the end
    PRETTIFY_KEYS = ['cmd', 'stdout', 'stderr', 'msg']

    def _dump_results(self, result):
        '''Return the text to output for a result.'''

        # Enable JSON identation
        result['_ansible_verbose_always'] = True

        # Save keys we handle in custom way
        # (so we can return them back at the end)
        save = {}
        for key in (self.HIDE_KEYS + self.PRETTIFY_KEYS):
            if key in result:
                save[key] = result.pop(key)

        # Let default handler print the rest (without keys we handle here)
        output = CallbackModule_default._dump_results(self, result)

        # And now print nicely formatted those keys we have extra interest in
        for key in self.PRETTIFY_KEYS:
            if key in save and save[key]:
                output += '\n\n%s:\n\n%s\n' % (key.upper(), save[key])

        # Now return original keys/values back to result
        # to be transparent for rest of ansible
        for key, value in save.items():
            result[key] = value

        return output
