# (c) 2016 Matt Clay <matt@mystile.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
from six import add_metaclass
import time
import xml.etree.ElementTree as ET

from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text
from ansible.plugins.callback import CallbackBase
from junit_xml import decode

try:
    from junit_xml import TestCase
    from junit_xml import TestSuite
    from junit_xml import to_xml_report_string

    HAS_JUNIT_XML = True
except ImportError:
    HAS_JUNIT_XML = False

try:
    from collections import OrderedDict

    HAS_ORDERED_DICT = True
except ImportError:
    try:
        from ordereddict import OrderedDict

        HAS_ORDERED_DICT = True
    except ImportError:
        HAS_ORDERED_DICT = False

DOCUMENTATION = '''
    callback: junit_report
    type: aggregate
    short_description: write playbook output to a JUnit file.
    version_added: historical
    description:
      - This callback writes playbook output to a JUnit formatted XML file.
      - "Tasks show up in the report as follows:
        'ok': pass
        'failed' with 'EXPECTED FAILURE' in the task name: pass
        'failed' with 'TOGGLE RESULT' in the task name: pass
        'ok' with 'TOGGLE RESULT' in the task name: failure
        'failed' due to an exception: error
        'failed' for other reasons: failure
        'skipped': skipped"
    options:
      output_dir:
        name: JUnit output dir
        default: ~/.ansible.log
        description: Directory to write XML files to.
        env:
          - name: JUNIT_OUTPUT_DIR
      task_class:
        name: JUnit Task class
        default: False
        description: Configure the output to be one class per yaml file
        env:
          - name: JUNIT_TASK_CLASS
      fail_on_change:
        name: JUnit fail on change
        default: False
        description: Consider any tasks reporting "changed" as a
                     junit test failure
        env:
          - name: JUNIT_FAIL_ON_CHANGE
      fail_on_ignore:
        name: JUnit fail on ignore
        default: False
        description: Consider failed tasks as a junit test failure even if
                     ignore_on_error is set
        env:
          - name: JUNIT_FAIL_ON_IGNORE
      include_setup_tasks_in_report:
        name: JUnit include setup tasks in report
        default: True
        description: Should the setup tasks be included in the final report
        env:
          - name: JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT
    requirements:
      - whitelist in configuration
      - junit_xml (python lib)
'''


class RPTestCase(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.multiple_stdout = []

    def add_stdout_element(self, elem_info):
        self.multiple_stdout.append(elem_info)


class RPTestSuite(TestSuite):

    def __init__(self, *args, **kwargs):
        self.multiple_stdout = []
        super(self.__class__, self).__init__(*args, **kwargs)

    def build_xml_doc(self, encoding=None):
        xml_element = \
            super(self.__class__, self).build_xml_doc(encoding=encoding)

        for idx, case in enumerate(xml_element):
            for stdout in self.test_cases[idx].multiple_stdout:
                stdout_element = ET.SubElement(case, "system-out")
                stdout_element.text = decode(stdout, encoding)

        return xml_element


class CallbackModule(CallbackBase):
    """This callback writes playbook output to a JUnit formatted XML file.

    Tasks show up in the report as follows:
        'ok': pass
        'failed' with 'EXPECTED FAILURE' in the task name: pass
        'failed' with 'TOGGLE RESULT' in the task name: pass
        'ok' with 'TOGGLE RESULT' in the task name: failure
        'failed' due to an exception: error
        'failed' for other reasons: failure
        'skipped': skipped

    This plugin makes use of the following environment variables:
        JUNIT_OUTPUT_DIR (optional): Directory to write XML files to.
                                     Default: ~/.ansible.log
        JUNIT_TASK_CLASS (optional): Configure the output to be one class per
                                     yaml file
                                     Default: False
        JUNIT_FAIL_ON_CHANGE (optional): Consider any tasks reporting "changed"
                                         as a junit test failure
                                     Default: False
        JUNIT_FAIL_ON_IGNORE (optional): Consider failed tasks as a junit test
                                         failure even if ignore_on_error is set
                                     Default: False
        JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT (optional): Should the setup tasks
                                               be included in the final report
                                     Default: True

    Requires:
        junit_xml

    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'junit_report'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self._output_dir = os.getenv('JUNIT_OUTPUT_DIR',
                                     os.path.expanduser('~/.ansible.log'))
        self._task_class = os.getenv('JUNIT_TASK_CLASS', 'False').lower()
        self._fail_on_change = os.getenv('JUNIT_FAIL_ON_CHANGE',
                                         'False').lower()
        self._fail_on_ignore = os.getenv('JUNIT_FAIL_ON_IGNORE',
                                         'False').lower()
        self._include_setup_tasks_in_report = os.getenv(
            'JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT', 'True').lower()
        self._playbook_path = None
        self._playbook_name = os.getenv('JUNIT_PLAYBOOK_NAME', '').lower()
        self._play_name = None
        self._task_data = None

        self.disabled = False

        if not HAS_JUNIT_XML:
            self.disabled = True
            self._display.warning(
                'The `junit_xml` python module is not installed. '
                'Disabling the `junit` callback plugin.')

        if HAS_ORDERED_DICT:
            self._task_data = OrderedDict()
        else:
            self.disabled = True
            self._display.warning(
                'The `ordereddict` python module is not installed. '
                'Disabling the `junit` callback plugin.')

        if not os.path.exists(self._output_dir):
            os.mkdir(self._output_dir)

    def _start_task(self, task):
        """Record the start of a task for one or more hosts."""

        uuid = task._uuid

        if uuid in self._task_data:
            return

        self._task_data[uuid] = TaskData(task, self._play_name)

    def _finish_task(self, status, result):
        """Record the results of a task for a single host."""

        task_uuid = result._task._uuid

        if hasattr(result, '_host'):
            host_uuid = result._host._uuid
            host_name = result._host.name
        else:
            host_uuid = 'include'
            host_name = 'include'

        task_data = self._task_data[task_uuid]

        if self._fail_on_change == 'true' and status == 'ok' and \
                result._result.get('changed', False):
            status = 'failed'

        # ignore failure if expected and toggle result if asked for
        if status == 'failed' and 'EXPECTED FAILURE' in task_data.name:
            status = 'ok'
        elif 'TOGGLE RESULT' in task_data.name:
            if status == 'failed':
                status = 'ok'
            elif status == 'ok':
                status = 'failed'

        task_data.add_host(HostData(host_uuid, host_name, status, result))

    @staticmethod
    def get_task_details(task, host):

        if task.task.no_log:
            args = "'no_log' is true, output is hidden"
        else:
            args = ','.join(
                ('\n\t%s = %s' % arg for arg in task.task.args.items()))

        details = \
            """Ansible Task Details:
---------------------
    Name: {task_name}
    Original Name: {org_name}
    UUID: {task_uuid}
    Action: {action}
    File: {task_file}
    Play: {task_play}
    Line: {task_line}
    Role: {role}
    Host: {host_name}
    Status: {host_status}

    {args}
        """.format(
                task_name=task.name,
                org_name=task.task.get_name().strip(),
                task_uuid=task.uuid,
                action=task.action,
                task_file=task.file[0],
                task_play=task.play,
                task_line=task.line[0],
                role=task.role,
                host_name=host.name,
                host_status=host.status,
                args='Task Args:  ' + args,
            )

        return details

    def _build_test_case(self, task_data, host_data):
        """Build a TestCase from the given TaskData and HostData."""

        name = task_data.name
        duration = host_data.finish - task_data.start

        if self._task_class == 'true':
            junit_classname = re.sub(r'\.yml:[0-9]+$', '', task_data.path)
        else:
            junit_classname = task_data.path

        test_case = RPTestCase(
            name=name,
            classname=junit_classname,
            elapsed_sec=duration,
            allow_multiple_subelements=True
        )

        test_case.add_stdout_element(
            self.__class__.get_task_details(task=task_data, host=host_data))

        if host_data.status == 'included':
            test_case.add_stdout_element(host_data.result)
            return test_case

        res = host_data.result._result
        rc = res.get('rc', 0)
        dump = self._dump_results(res, indent=0)
        dump = self._cleanse_string(dump)

        if host_data.status == 'ok':
            test_case.add_stdout_element(dump)
            return test_case

        if host_data.status == 'failed':
            if 'exception' in res:
                message = res['exception'].strip().split('\n')[-1]
                output = res['exception']
                test_case.add_error_info(message, output)
            elif 'msg' in res:
                message = res['msg']
                test_case.add_failure_info(message, dump)
            else:
                test_case.add_failure_info('rc=%s' % rc, dump)
        elif host_data.status == 'skipped':
            if 'skip_reason' in res:
                message = res['skip_reason']
            else:
                message = 'skipped'
            test_case.add_skipped_info(message)

        return test_case

    def _cleanse_string(self, value):
        """Cleanse string.

        Convert surrogate escapes to the unicode replacement
        character to avoid XML encoding errors.
        """
        return to_text(to_bytes(value, errors='surrogateescape'),
                       errors='replace')

    def _generate_report(self):
        """Generate a TestSuite report.

        Generate a TestSuite report from the collected TaskData and HostData.
        """
        test_cases = []

        for task_uuid, task_data in self._task_data.items():
            if task_data.action == 'setup' and \
                    self._include_setup_tasks_in_report == 'false':
                continue

            for host_uuid, host_data in task_data.host_data.items():
                test_cases.append(self._build_test_case(task_data, host_data))

        test_suite = RPTestSuite(self._playbook_name, test_cases)
        report = to_xml_report_string([test_suite])

        output_file = os.path.join(self._output_dir, '%s-%s.xml' % (
            self._playbook_name, time.time()))

        with open(output_file, 'wb') as xml:
            xml.write(to_bytes(report, errors='surrogate_or_strict'))

    def v2_playbook_on_start(self, playbook):
        self._playbook_path = playbook._file_name
        if not self._playbook_name:
            self._playbook_name = \
                os.path.splitext(os.path.basename(self._playbook_path))[0]

    def v2_playbook_on_play_start(self, play):
        self._play_name = play.get_name()

    def v2_runner_on_no_hosts(self, task):
        self._start_task(task)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._start_task(task)

    def v2_playbook_on_cleanup_task_start(self, task):
        self._start_task(task)

    def v2_playbook_on_handler_task_start(self, task):
        self._start_task(task)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors and self._fail_on_ignore != 'true':
            self._finish_task('ok', result)
        else:
            self._finish_task('failed', result)

    def v2_runner_on_ok(self, result):
        self._finish_task('ok', result)

    def v2_runner_on_skipped(self, result):
        self._finish_task('skipped', result)

    def v2_playbook_on_include(self, included_file):
        self._finish_task('included', included_file)

    def v2_playbook_on_stats(self, stats):
        self._generate_report()


@add_metaclass(type)
class TaskData(object):
    """Data about an individual task."""

    executed_tasks = {}

    def __init__(self, task, play_name):
        self.task = task

        # Adding counter to the task name in case it (or other task with the
        # same name) was already called so ReportPortal will be able to show
        # the history of the task (test) as expected
        name = task.get_name().strip()
        if name not in self.__class__.executed_tasks:
            self.__class__.executed_tasks[name] = 1
            self.name = name
        else:
            self.__class__.executed_tasks[name] += 1
            self.name = name + '  -  #{exec_cnt}'.format(
                exec_cnt=self.__class__.executed_tasks[name])

        self.uuid = task._uuid
        self.path = task.get_path()
        self.file = task.get_path().split(':')[0],
        self.line = int(task.get_path().split(':')[-1]),
        self.play = play_name
        self.start = time.time()
        self.action = task.action
        self.role = str(task._role)
        self.host_data = OrderedDict()

    def add_host(self, host):
        if host.uuid in self.host_data:
            if host.status == 'included':
                # concatenate task include output from multiple items
                host.result = '%s\n%s' % (
                    self.host_data[host.uuid].result, host.result)
            else:
                raise Exception('%s: %s: %s: duplicate host callback: %s' % (
                    self.path, self.play, self.name, host.name))

        self.host_data[host.uuid] = host

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def play(self):
        return self._play

    @play.setter
    def play(self, play):
        self._play = play

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, action):
        self._action = action

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role


@add_metaclass(type)
class HostData(object):
    """Data about an individual host."""

    def __init__(self, uuid, name, status, result):
        self.uuid = uuid
        self.name = name
        self.status = status
        self.result = result
        self.finish = time.time()
