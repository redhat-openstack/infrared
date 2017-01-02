# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Inspired from: https://gist.github.com/cliffano/9868180
# Further improved output and added results field

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import simplejson as json
except ImportError:
    import json

try:
    from ansible.plugins.callback import CallbackBase
    ANSIBLE2 = True
except ImportError:
    ANSIBLE2 = False

# Fields to reformat output for
FIELDS = ['cmd', 'command', 'start', 'end', 'delta', 'msg', 'stdout',
          'stderr', 'results']


class CallbackModule(CallbackBase if ANSIBLE2 else object):
    def human_log(self, data):
        if type(data) == dict:
            for field in FIELDS:
                if field in data.keys() and data[field]:
                    output = self._format_output(data[field])
                    output_replace = output.replace("\\n", "\n")
                    print("\n{0}: {1}".format(field, output_replace))

    def _format_output(self, output):
        # Strip unicode
        if type(output) == unicode:
            output = output.encode('ascii', 'replace')

        # If output is a dict
        if type(output) == dict:
            return json.dumps(output, indent=2)

        # If output is a list of dicts
        if type(output) == list and type(output[0]) == dict:
            # This gets a little complicated because it potentially means
            # nested results, usually because of with_items.
            real_output = list()
            for index, item in enumerate(output):
                copy = item
                if type(item) == dict:
                    for field in FIELDS:
                        if field in item.keys():
                            copy[field] = self._format_output(item[field])
                real_output.append(copy)
            return json.dumps(output, indent=2)

        # If output is a list of strings
        if type(output) == list and type(output[0]) != dict:
            # Strip newline characters
            real_output = list()
            for item in output:
                if "\n" in item:
                    for string in item.split("\n"):
                        real_output.append(string)
                else:
                    real_output.append(item)

            # Reformat lists with line breaks only if the total length is
            # >75 chars
            if len("".join(real_output)) > 75:
                return "\n" + "\n".join(real_output)
            else:
                return " ".join(real_output)

        # Otherwise it's a string, (or an int, float, etc.) just return it
        return str(output)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.human_log(res)

    def runner_on_ok(self, host, res):
        self.human_log(res)

    def runner_on_error(self, host, msg):
        pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        self.human_log(res)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        self.human_log(res)

    def runner_on_async_ok(self, host, res, jid):
        self.human_log(res)

    def runner_on_async_failed(self, host, res, jid):
        self.human_log(res)

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        pass

    def playbook_on_stats(self, stats):
        pass
