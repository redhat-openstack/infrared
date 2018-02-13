#!/usr/bin/env python

from __future__ import print_function
import textwrap
import sys
from infrared import PLUGINS_REGISTRY

def print_help():
    print(textwrap.dedent("""
        This tool checks that all plugin registry doesn't contain revision
        for plugins.

          ./tox-check-plugin_registry.py [--help] ...

        Loads plugins registry to test.

        Any failing element will be printed to stdout as:
          FAIL: plugin_name
        In case of -v even it's yaml will be printed out (stderr).
        """))

def test_revision(plugins):

    results = []

    for elem in plugins:
        if 'rev' in plugins[elem]:
            elem_res = {'dict': elem}
            results.append(elem_res)
    return results


def clr(color, text, force=True):
    if force or sys.stdout.isatty():
        return '\033[%sm%s\033[0m' % (color, text)
    else:
        return text


def red(text):
    return clr('1;31', text)


def print_out(results,):
    for result in results:
        print(red('FAIL: %s' % (result['dict'])))


def run_tests(plugins):
    any_failure = False
    try:
        print('Validating plugins: %s ...' % plugins)
        results = test_revision(plugins)
        if len(results) != 0:
            any_failure = True
            print_out(results)
    except:
        print(red('ERROR: seems %s has revision.') % plugins)
        any_failure = True
    return any_failure


if __name__ == '__main__':
    plugins = PLUGINS_REGISTRY
    if '--help' in plugins:
        print_help()
        sys.exit(0)

    sys.exit(int(run_tests(plugins)))
