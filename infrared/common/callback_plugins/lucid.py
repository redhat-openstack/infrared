# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor, stringc
from ansible.module_utils._text import to_bytes, to_text
from ansible.utils.display import logger

import ansible
import six
import sys

class Message(six.text_type):
    """Message acts like string that can have attributes.
    """

    def __new__(cls, value, *args, **kwargs):
        # explicitly only pass value to the str constructor
        return super(Message, cls).__new__(cls, value)

    def __init__(self, value, *args, **kwargs):
        # ... and don't even call the str initializer
        self.__dict__ = kwargs

    def __add__(self, other):
        x = Message(self.__str__() + other)
        x.__dict__ = self.__dict__.copy()

        if hasattr(other, '__dict__'):
            x.__dict__.update(other.__dict__)
        return x


class CallbackModule(CallbackBase):

    '''
    This module is based on the original default callback interface, but it
    does completly replacing it with an implementation aimed around simplificty
    concept.

    The callback is named "lucid" in because there was already another one
    called 'simple' which didn't deliver on its promises.

    Goals:
    - console output should be minimized, as far as one line per task
    - details should go to log files, not console
    - errors should be made visible to console
    - any information that is *high* likely to be on console
    - any information that is *less* likely to needed should be in log files

    This module aims to used as a workaround until Ansible logging would be
    refactored in order to support multiple loggers/filters/formatters, current
    implementation is highly coupled to console, which was supposed to be
    just another handler.

    Sorin Sbarnea: While this callback may be doing some really
    ugly hacking behind the scene, including monkey patching, please keep in
    mind that was the only way to implement the missing functionality *now*.
    The ultimate goal is to bring simplcity to Ansible console, what goes under
    the hood can be improved in time, without affeting the
    user experience.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'lucid'

    def __init__(self):

        self._play = None
        self._last_task_banner = None
        super(CallbackModule, self).__init__()

        # monkey patching Display class to address some original design flaws
        def banner(self, msg, color=None, cows=True):
            msg = msg.strip()
            star_len = self.columns - len(msg)
            if star_len <= 3:
                star_len = 3
            stars = u"*" * star_len
            # self.display(u"\n%s %s" % (msg, stars), color=color)
            self.display(u"%s %s" % (msg, stars), color=color)

        ansible.utils.display.Display.banner = banner

        def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False):
            """ Display a message to the user

            Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
            """

            nocolor = msg
            if color:
                msg = stringc(msg, color)

            if not log_only:
                if not msg.endswith(u'\n'):
                    msg2 = msg + u'\n'
                else:
                    msg2 = msg

                msg2 = to_bytes(msg2, encoding=self._output_encoding(stderr=stderr))
                if sys.version_info >= (3,):
                    # Convert back to text string on python3
                    # We first convert to a byte string so that we get rid of
                    # characters that are invalid in the user's locale
                    msg2 = to_text(msg2, self._output_encoding(stderr=stderr), errors='replace')

                if not stderr:
                    fileobj = sys.stdout
                else:
                    fileobj = sys.stderr

                fileobj.write(msg2)

                try:
                    fileobj.flush()
                except IOError as e:
                    # Ignore EPIPE in case fileobj has been prematurely closed, eg.
                    # when piping to "head -n1"
                    if e.errno != errno.EPIPE:
                        raise

            if logger and not screen_only:
                msg2 = nocolor.lstrip(u'\n')

                # we add the message details if any
                if hasattr(self, 'detail'):
                    msg2 += self.detail

                msg2 = to_bytes(msg2)
                if sys.version_info >= (3,):
                    # Convert back to text string on python3
                    # We first convert to a byte string so that we get rid of
                    # characters that are invalid in the user's locale
                    msg2 = to_text(msg2, self._output_encoding(stderr=stderr))

                if color == C.COLOR_ERROR:
                    logger.error(msg2)
                else:
                    logger.info(msg2)

        ansible.utils.display.Display.display = display


    def v2_runner_on_failed(self, result, ignore_errors=False):

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                self._display.display("fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_ERROR)
            else:
                self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_ERROR)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)

    def v2_runner_on_ok(self, result):

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._clean_results(result._result, result._task.action)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        if result._task.action in ('include', 'include_role'):
            return
        elif result._result.get('changed', False):
            if delegated_vars:
                msg = Message("changed: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host']))
            else:
                msg = Message("changed: [%s]" % result._host.get_name())
            color = C.COLOR_CHANGED
        else:
            if delegated_vars:
                msg = Message("ok: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host']))
            else:
                msg = Message("ok: [%s]" % result._host.get_name())
            color = C.COLOR_OK

        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                msg.detail = " => %s" % (self._dump_results(result._result))
            self._display.display(msg, color=color)

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)

            if result._task.loop and 'results' in result._result:
                self._process_items(result)
            else:
                msg = Message("skipping: [%s]" % result._host.get_name())
                if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                    msg += " => %s" % self._dump_results(result._result)
                self._display.display(msg, color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            self._display.display("fatal: [%s -> %s]: UNREACHABLE! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)
        else:
            self._display.display("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_UNREACHABLE)

    def v2_playbook_on_no_hosts_matched(self):
        self._display.display("skipping: no hosts matched", color=C.COLOR_SKIP)

    def v2_playbook_on_no_hosts_remaining(self):
        self._display.banner("NO MORE HOSTS LEFT")

    def v2_playbook_on_task_start(self, task, is_conditional):

        if self._play.strategy != 'free':
            self._print_task_banner(task)

    def _print_task_banner(self, task):
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        args = ''
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = u', '.join(u'%s=%s' % a for a in task.args.items())
            args = u' %s' % args

        self._display.banner(u"TASK [%s%s]" % (task.get_name().strip(), args))
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self._display.display(u"task path: %s" % path, color=C.COLOR_DEBUG)

        self._last_task_banner = task._uuid

    def v2_playbook_on_cleanup_task_start(self, task):
        self._display.banner("CLEANUP TASK [%s]" % task.get_name().strip())

    def v2_playbook_on_handler_task_start(self, task):
        self._display.banner("RUNNING HANDLER [%s]" % task.get_name().strip())

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = Message(u"PLAY")
        else:
            msg = Message(u"PLAY [%s]" % name)

        self._play = play

        self._display.banner(msg)

    def v2_on_file_diff(self, result):
        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        self._display.display(diff)
        elif 'diff' in result._result and result._result['diff'] and result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self._display.display(diff)

    def v2_runner_item_on_ok(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if result._task.action in ('include', 'include_role'):
            return
        elif result._result.get('changed', False):
            msg = Message('changed', status='changed')
            color = C.COLOR_CHANGED
        else:
            msg = Message('ok', status='ok')
            color = C.COLOR_OK

        if delegated_vars:
            msg += ": [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += ": [%s]" % result._host.get_name()

        msg += " => (item=%s)" % (self._get_item(result._result),)

        if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
            msg.detail = " => %s" % self._dump_results(result._result)
        self._display.display(msg, color=color)

    def v2_runner_item_on_failed(self, result):

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._handle_exception(result._result)

        msg = Message("failed: ", status='failed')
        if delegated_vars:
            msg += "[%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += "[%s]" % (result._host.get_name())

        self._handle_warnings(result._result)
        self._display.display(msg + " (item=%s) => %s" % (self._get_item(result._result), self._dump_results(result._result)), color=C.COLOR_ERROR)

    def v2_runner_item_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            msg = Message("skipping: [%s] => (item=%s) " % (result._host.get_name(), self._get_item(result._result)))
            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
                msg += " => %s" % self._dump_results(result._result)
            self._display.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_include(self, included_file):
        msg = Message('included: %s for %s' % (included_file._filename, ", ".join([h.name for h in included_file._hosts])))
        self._display.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_stats(self, stats):
        self._display.banner("PLAY RECAP")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize(u'ok', t['ok'], None),
                colorize(u'changed', t['changed'], None),
                colorize(u'unreachable', t['unreachable'], None),
                colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        self._display.display("", screen_only=True)

        # print custom stats
        if C.SHOW_CUSTOM_STATS and stats.custom:
            self._display.banner("CUSTOM STATS: ")
            # per host
            #TODO: come up with 'pretty format'
            for k in sorted(stats.custom.keys()):
                if k == '_run':
                    continue
                self._display.display('\t%s: %s' % (k, self._dump_results(stats.custom[k], indent=1).replace('\n','')))

            # print per run custom stats
            if '_run' in stats.custom:
                self._display.display("", screen_only=True)
                self._display.display('\tRUN: %s' % self._dump_results(stats.custom['_run'], indent=1).replace('\n',''))
            self._display.display("", screen_only=True)

    def v2_playbook_on_start(self, playbook):
        if self._display.verbosity > 1:
            from os.path import basename
            self._display.banner("PLAYBOOK: %s" % basename(playbook._file_name))

        if self._display.verbosity > 3:
            if self._options is not None:
                for option in dir(self._options):
                    if option.startswith('_') or option in ['read_file', 'ensure_value', 'read_module']:
                        continue
                    val =  getattr(self._options,option)
                    if val:
                        self._display.vvvv('%s: %s' % (option,val))

    def v2_runner_retry(self, result):
        task_name = result.task_name or result._task
        msg = Message("FAILED - RETRYING: %s (%d retries left)." % (task_name, result._result['retries'] - result._result['attempts']))
        if (self._display.verbosity > 2 or '_ansible_verbose_always' in result._result) and not '_ansible_verbose_override' in result._result:
            msg += "Result was: %s" % self._dump_results(result._result)
        self._display.display(msg, color=C.COLOR_DEBUG)
