#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2021, Ariel Opincaru <aopincar@redhat.com>
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

import os
import re

from lxml import etree

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: junitxml
version_added: "0.1"
short_description: JUnitXML editor
description:
    - Edits JUnitXML files
options:
    src:
        description:
            - The JUnitXML file with the content that need to be changed
        required: true
        type: str
    dst:
        description:
            - The new JUnitXML file to create.
            If not given, the source file will be updated with the changes.
            (All parents directories will be created automatically)
        required: false
        type: str
    indent:
        description:
        - The indentation that will be used when creating the XML file
        required: false
        type: str
    prepend-classname:
        description:
            - Prepends the classname to test in each testcase
            Example:
                In:  <testcase classname="X" test="Y" time=>"0.01"</testcase>
                Out: <testcase classname="X" test="X.Y" time=>"0.01"</testcase>
        default: true
        type: bool
    remove-testcase-id:
        description:
            - Removes the test ID from the 'name' attribute of all testcase
            elements.
            'Test ID' considered as square brackets and everything inside them.
            Example:
                In:  <testcase ... name="testname[id-xxx-yyy-zzz]"><testcase>
                Out: <testcase ... name="testname"><testcase>
        default: false
        type: bool
    testcase-prefix:
        description:
            - A prefix to add to the name attribute of each testcase element.
            (Uses the 'testcase-prefix-sep' value as a separator)
            Example:
                In:  <testcase ... name="testname"><testcase>
                Out: <testcase ... name="myprefix-testname"><testcase>
        type: str
        required: false
    testcase-prefix-sep:
        description: The separator that will be used for testcase prefix.
        type: str
        default: '-'
    testcase-prefix-no-dots:
        description: Whether or not to remove dot ('.') chars from the given
        testcase prefix.
        type: bool
        default: true
    testsuite-prefix:
        description:
            - A comma separated value of prefixes to add to testsuite elements.
            Please be aware of the following scenarios:
            1. In case the number of testsuites and prefixes are equal, a
            corresponding prefix will be added to each testsuite's name (index
            based).
            2. In case multiple testsuites exist and only one prefix is
            given, a counter number will be add at the end of each prefix.
            Attention: In any other case, a RunTime Error will be raised!

            Examples:
            1. Number of testsuites: 2, testsuite-prefixes=XXX,YYY
            <testsuites>
                <testsuite name='first_testsuite'><testsuite>
                <testsuite name='second_testsuite'><testsuite>
            </testsuites>

            Outcome:
            <testsuites>
                <testsuite name='XXX-first_testsuite'><testsuite>
                <testsuite name='YYY-second_testsuite'><testsuite>
            </testsuites>

            2. Number of testsuites: 3, testsuite-prefixes=ZZZ
            <testsuites>
                <testsuite name='first_testsuite'><testsuite>
                <testsuite name='second_testsuite'><testsuite>
                <testsuite name='third_testsuite'><testsuite>
            </testsuites>

            Outcome:
            <testsuites>
                <testsuite name='ZZZ1-first_testsuite'><testsuite>
                <testsuite name='ZZZ2-second_testsuite'><testsuite>
                <testsuite name='ZZZ3-third_testsuite'><testsuite>
            </testsuites>
        type: str
        required: false
    testcase-prefix-sep:
        description: The separator that will be used for testsuite prefix.
        type: str
        default: '-'
'''


class JUnintXML:

    def __init__(self, src_file, dst_file=None):
        self.src_file = src_file
        self.dst_file = dst_file

        self.tree = etree.parse(src_file)
        self.indent = ''

        self.element_changed = False
        self.file_changed = False
        self.write_needed = False

    @staticmethod
    def __get_full_path(path):
        return os.path.abspath(os.path.expanduser(path))

    @property
    def src_file(self):
        return self.__class__.__get_full_path(self.__src_file)

    @src_file.setter
    def src_file(self, src_file):
        self.__src_file = src_file

    @property
    def dst_file(self):
        if self.__dst_file is None:
            return None
        return self.__class__.__get_full_path(self.__dst_file)

    @dst_file.setter
    def dst_file(self, dst_file):
        self.__dst_file = dst_file

    def prepend_classname_to_name(self):
        """Prepends the classname to the name attribute for each testcase
        element"""
        def _prepend_classname_to_name(elem):
            classname = elem.get('classname')
            if classname:
                elem.set('name', f"{classname}.{elem.get('name')}")
                return True

            return False

        self.__process(action_func=_prepend_classname_to_name)

    def remove_id_from_testcase_name(self):
        """Removes the ID from testcases 'name' attribute"""
        def _remove_id_from_name(elem):
            name = elem.get('name')
            new_name = re.sub(r'\[.*\]', '', name)
            if new_name != name:
                elem.set('name', new_name)
                return True

            return False

        self.__process(action_func=_remove_id_from_name)

    def add_prefix_to_testcase(self, tc_prefix, tc_prefix_sep):
        """Adds a prefix to each testcase 'name' attribute

        :param tc_prefix: A prefix to add to the name attribute of each
        testcase element
        :param tc_prefix_sep: A separator between the prefix and the testcase
        name
        """
        def _add_prefix(elem, prefix, prefix_sep):
            name = elem.get('name')
            if prefix:
                new_name = prefix + prefix_sep + name
                elem.set('name', new_name)
                return True

            return False

        self.__process(
            action_func=_add_prefix,
            prefix=tc_prefix,
            prefix_sep=tc_prefix_sep)

    def __process(self, action_func, **kwargs):

        changed = self.__class__.__process_testcases(
            self.tree.getroot(),
            func=action_func,
            **kwargs)

        if changed:
            self.element_changed = True
            self.write_needed = True

    @staticmethod
    def __process_testcases(elem, func, **kwargs):
        element_changed = False
        if elem.tag == 'testcase':
            element_changed = func(elem, **kwargs) or element_changed

        for child in list(elem):
            element_changed = JUnintXML.__process_testcases(
                child, func, **kwargs) or element_changed

        return element_changed

    def add_testsuite_prefixes(self, prefixes, prefixes_sep):
        """Adds prefixes to the name of testsuite elements

        :param prefixes: A comma separated string of prefixes
        :param prefixes_sep: A separator between the prefix and the testsuite
        name
        """
        ts_list = []
        prefix_list = prefixes.split(',')

        def get_all_testsuites(elem):
            if elem.tag == 'testsuite':
                ts_list.append(elem)

            for child in list(elem):
                get_all_testsuites(child)

        get_all_testsuites(self.tree.getroot())

        len_ts = len(ts_list)
        len_prefix = len(prefix_list)

        if not len_ts:
            return

        cnt = 1
        for idx, ts in enumerate(ts_list):
            name = ts.get('name')

            if len_ts == 1 and len_prefix == 1:
                prefix = prefix_list[0]
            elif len_ts > 1 and len_prefix == 1:
                prefix = prefix_list[0] + str(cnt)
                cnt += 1
            elif len_ts == len_prefix:
                prefix = prefix_list[idx]
            else:
                raise RuntimeError(
                    f"Mismatch number of Test Suites '{len_ts}' and prefixes "
                    f"'{len_prefix}' in '{self.src_file}'")

            new_name = f"{prefix}{prefixes_sep}{name}"
            ts.set('name', new_name)

        self.element_changed = True

    def write(self, dst_file=None):
        """Writes changes to a file

        :param dst_file: A path to the output file (src_file will be updated if
        not given)
        """
        self.dst_file = dst_file if dst_file else self.src_file

        dirname = os.path.dirname(self.dst_file)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
            self.file_changed = True

        self.tree.write(self.dst_file)

        if self.src_file != self.dst_file:
            self.file_changed = True
        elif self.element_changed:
            self.file_changed = True

    @property
    def changed(self):
        return self.file_changed

    @property
    def indent(self):
        return self.__space

    @indent.setter
    def indent(self, space):
        self.__space = space
        etree.indent(self.tree, space=space)


def main():
    module = AnsibleModule(
        argument_spec={
            'src': dict(required=True),
            'dst': dict(required=False),
            'indent': dict(required=False),
            'prepend-classname': dict(default=False, type='bool'),
            'remove-testcase-id': dict(default=False, type='bool'),
            'testcase-prefix': dict(required=False),
            'testcase-prefix-sep': dict(default='-'),
            'testcase-prefix-no-dots': dict(default=True, type='bool'),
            'testsuite-prefixes': dict(required=False),
            'testsuite-prefixes-sep': dict(default='-'),
        }
    )

    juxml = JUnintXML(src_file=module.params['src'])

    if module.params['remove-testcase-id']:
        juxml.remove_id_from_testcase_name()

    if module.params['prepend-classname']:
        juxml.prepend_classname_to_name()

    if module.params['testcase-prefix']:
        tc_prefix = module.params['testcase-prefix']
        if module.params['testcase-prefix-no-dots']:
            tc_prefix = tc_prefix.replace('.', '')
        juxml.add_prefix_to_testcase(
            tc_prefix=tc_prefix,
            tc_prefix_sep=module.params['testcase-prefix-sep'])

    if module.params['testsuite-prefixes']:
        juxml.add_testsuite_prefixes(
            prefixes=module.params['testsuite-prefixes'],
            prefixes_sep=module.params['testsuite-prefixes-sep'])

    if module.params['indent'] is not None:
        juxml.indent = module.params['indent']

    if juxml.write_needed:
        juxml.write(dst_file=module.params['dst'])

    module.exit_json(
        changed=juxml.changed,
        src_file=juxml.src_file,
        dst_file=juxml.dst_file or juxml.src_file,
        content_changed=juxml.element_changed and juxml.file_changed)


if __name__ == '__main__':
    main()
