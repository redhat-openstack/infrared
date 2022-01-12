#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import textwrap
import yaml


def print_help():
    print(textwrap.dedent("""
        This tool checks that all plays have 'any_errors_fatal' defined.

          ./tox-check-any_errors_fatal.py [--help] [-v|-q] SOME_YAML...

        Specify as cli args path of yaml file(s) to test.
        If dash ('-') is provided instead of file paths
        it will read list of files from stdin.

        Only other possible cli args are '--help', '-v' and '-n'.

        -v  Verbose, list of also test-passing plays will be printed on stdout.
            And on stderr will be full yaml dump of these which fail.
        -q  Quiet, will print on stdout just file names where
            there are any failures, hides parsing errors, overrides -v.
            Use for example to open all at once:
            $ find ... | ./tox-check-any_errors_fatal.py -q | xargs vim -p


        All files will be loaded as yaml and validated as:

        * if they do contain top level list (as playbook yamls do)
        * each of the elements will be tested
        * if that element is dict and has 'hosts' property (a play)
        * if value of that element['hosts'] is not 'localhost'
          (only known safe for sure)
        * it will be asserted that it has 'any_errors_fatal' key
          (whatever the value, just required it's explicitly specified)

        Any failing element will be printed to stdout as:
          FAIL: file_path # element[name] # element[hosts]
        In case of -v even it's yaml will be printed out (stderr).
        """))


def print_explanation():
    print(yellow(textwrap.dedent(
        """
        To pass this test, ALL ansible PLAYS in this repo need to have
        any_errors_fatal explicitly defined.

        And in most cases in infrared set to true, e.g.:

        - name: blah
          hosts: compute
          any_errors_fatal: true  # <-- this
          tasks:
              ...
          roles:
              ...

        http://docs.ansible.com/ansible/playbooks_error_handling.html#aborting-the-play
        """)), file=sys.stderr)


def short_play_name(result):
    return '%s # %s # %s' % (
        result['file'],
        result['dict'].get('name', '--name-missing--'),
        result['dict'].get('hosts', '--hosts-missing--'))


def indented_play_yaml(result):
    return (' >  ' +
            '\n >  '.join(
                yaml.dump(result['dict']).split('\n')))


def clr(color, text, force=False):
    if force or sys.stdout.isatty():
        return '\033[%sm%s\033[0m' % (color, text)
    else:
        return text


def red(text):
    return clr('1;31', text)


def green(text):
    return clr('0;32', text)


def yellow(text):
    return clr('1;33', text)


def test_playbook(file_path):

    results = []
    with open(file_path) as yaml_file:

        content = yaml.safe_load(yaml_file)
        if not isinstance(content, list):
            return results
        for elem in content:
            if not isinstance(elem, dict):
                continue
            if 'hosts' not in elem:
                continue
            elem_res = {'dict': elem, 'file': file_path}
            if elem['hosts'] == 'localhost':
                elem_res['passed'] = True
            else:
                elem_res['passed'] = ('any_errors_fatal' in elem)
            results.append(elem_res)
    return results


def print_out(results, verbose, quiet):
    for result in results:
        if not result['passed']:
            if not quiet:
                print(red('FAIL: %s' % short_play_name(result)),
                      file=sys.stderr)
            if verbose:
                print(indented_play_yaml(result), file=sys.stderr)
        elif verbose:
            print(green('PASS: %s' % short_play_name(result)))


def run_tests(paths, verbose=False, quiet=False):
    any_failure = False
    for path in paths:
        try:
            if verbose:
                print('Validating %s ...' % path)
            results = test_playbook(path)
            had_failure = any([res for res in results if not res['passed']])
            if quiet and had_failure:
                print(path)
            else:
                print_out(results, verbose, quiet)
            any_failure |= had_failure
        except yaml.scanner.ScannerError:
            if not quiet:
                print(red('ERROR: seems %s is not valid yaml file!' % path),
                      file=sys.stderr)
            any_failure = True
    if not quiet:
        print('')
        if not any_failure:
            print(green('All good, everything passed.'))
        else:
            print(red('There were some failures, see above.'), file=sys.stderr)
            print_explanation()

    return any_failure


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '--help' in args:
        print_help()
        sys.exit(0)

    opts = ('-v', '-q')

    verbose = ('-v' in args)
    quiet = ('-q' in args)
    if quiet and verbose:
        print("Overriding verbose due to quiet (names-only).", file=sys.stderr)
        verbose = False
    paths = [arg for arg in args if arg not in (opts)]
    if len(paths) == 1 and paths[0] == '-':
        paths = [path.strip() for path in sys.stdin.readlines()]
    invalid = [path for path in paths if not os.path.isfile(path)]
    if any(invalid):
        print(red('Seems some specified files does not exist:'),
              file=sys.stderr)
        print('\n'.join(invalid), file=sys.stderr)
        sys.exit(1)

    sys.exit(int(run_tests(paths, verbose, quiet)))
