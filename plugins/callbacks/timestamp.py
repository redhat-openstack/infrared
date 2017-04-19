# from https://github.com/ginsys/ansible-plugins/blob/devel/callback_plugins/timestamp.py

# (C) 2012-2013, Michael DeHaan, <michael.dehaan@gmail.com>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.plugins.callback import CallbackBase
import datetime

# define start time
t0 = tn = datetime.datetime.utcnow()

def filled(msg, fchar="*"):

    if len(msg) == 0:
        width = 79
    else:
        msg = "%s " % msg
        width = 79 - len(msg)
    if width < 3:
        width = 3 
    filler = fchar * width
    return "%s%s " % (msg, filler)

def timestamp():

    global tn
    time_current = datetime.datetime.utcnow()
    time_elapsed = (time_current - tn).total_seconds()
    time_total_elapsed = (time_current - t0).total_seconds()
    print( filled( '%s (delta: %s) %s elapsed: %s' % (time_current.isoformat(),
                                    time_elapsed, ' ' * 7, time_total_elapsed )))
    tn = datetime.datetime.utcnow()



class CallbackModule(CallbackBase):

    """
    this is an example ansible callback file that does nothing.  You can drop
    other classes in the same directory to define your own handlers.  Methods
    you do not use can be omitted.

    example uses include: logging, emailing, storing info, etc
    """


    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    def runner_on_ok(self, host, res):
        pass

    def runner_on_error(self, host, msg):
        pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        timestamp()
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        timestamp()
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        timestamp()
        self._display.display(filled("", fchar="="))
        pass

    def playbook_on_stats(self, stats):
        timestamp()
        self._display.display(filled("", fchar="="))
        pass
