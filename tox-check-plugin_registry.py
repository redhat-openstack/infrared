#!/usr/bin/env python

from __future__ import print_function
import textwrap
import os
import sys
import yaml

def print_help():
    print(textwrap.dedent("""
        This tool checks that all plugin registry doesn't contain revision
        for plugins.

          ./tox-check-plugin_registry.py [--help] SOME_YAML...

        Specify as cli args path of registry yaml file(s) to test.

        Any failing element will be printed to stdout as:
          FAIL: plugin_name # file_path
        In case of -v even it's yaml will be printed out (stderr).
        """))

def test_revision(file_path):

    with open(file_path) as yaml_file:

        results = []
        content = yaml.safe_load(yaml_file)
        for elem in content:
            if 'rev' in content[elem]:
                elem_res = {'dict': elem, 'file': file_path}
                results.append(elem_res)
    return results


def clr(color, text, force=True):
    if force or sys.stdout.isatty():
        return '\033[%sm%s\033[0m' % (color, text)
    else:
        return text


def red(text):
    return clr('1;31', text)


def print_out(results, verbose):
    if verbose:
        for result in results:
            print(red('FAIL: %s, %s' % (result['dict'],result['file'])))


def run_tests(paths, verbose=False):
    any_failure = False
    for path in paths:
        try:
            if verbose:
                print('Validating %s ...' % path)
            results = test_revision(path)
            if len(results) != 0:
                any_failure = True
                print_out(results, verbose)
        except yaml.scanner.ScannerError:
            print(red('ERROR: seems %s is not valid yaml file!') % path)
            any_failure = True
    return any_failure


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '--help' in args:
        print_help()
        sys.exit(0)

    opts = ('-v')
    verbose = ('-v' in args)

    paths = [arg for arg in args if arg not in (opts)]
    if len(paths) == 1 and paths[0] == '-':
        paths = [path.strip() for path in sys.stdin.readlines()]
    invalid = [path for path in paths if not os.path.isfile(path)]
    if any(invalid):
        print(red('Seems some specified files does not exist:'),
              file=sys.stderr)
        print('\n'.join(invalid), file=sys.stderr)
        sys.exit(1)

    sys.exit(int(run_tests(paths, verbose)))