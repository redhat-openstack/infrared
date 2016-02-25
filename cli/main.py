#!/usr/bin/env python

import logging
import os

import clg
import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import options as cli_options
from cli import execute
from cli import parse
from cli import utils
import cli.yamls

LOG = logger.LOG
CONF = conf.config

NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                        'input-files', 'dry-run', 'cleanup']


def main():
    settings_files = []

    settings_dir = utils.validate_settings_dir(
        CONF.get('defaults', 'settings'))

    spec_file = 'provisioner/virsh/virsh.spec'
    cmd = clg.CommandLine(yaml.load(open(os.path.join(CONF.get(
        'defaults', 'settings'), spec_file))))
    args = cmd.parse()

    verbose = int(args.verbose)

    if args.verbose == 0:
        args.verbose = logging.WARNING
    elif args.verbose == 1:
        args.verbose = logging.INFO
    else:
        args.verbose = logging.DEBUG

    LOG.setLevel(args.verbose)

    provision_dir = os.path.join(settings_dir, 'provisioner', args['command0'])

    for input_file in args['input-files'] or []:
        settings_files.append(utils.normalize_file(input_file))

    settings_files.append(os.path.join(provision_dir,
                                       args['command0'] + '.yml'))

    for key, val in vars(args).iteritems():
        if val is not None and key not in NON_SETTINGS_OPTIONS:
            settings_file = os.path.join(provision_dir, key, val + '.yml')
            LOG.debug('Searching settings file for the "%s" key...' % key)
            if not os.path.isfile(settings_file):
                settings_file = utils.normalize_file(val)
            settings_files.append(settings_file)
            LOG.debug('"%s" was added to settings files list as an argument '
                      'for "%s" key' % (settings_file, key))

    LOG.debug("All settings files to be loaded:\n%s" % settings_files)

    cli.yamls.Lookup.settings = utils.generate_settings(settings_files,
                                                        args['extra-vars'])

    cli.yamls.Lookup.in_string_lookup()

    LOG.debug("Dumping settings...")

    output = yaml.safe_dump(cli.yamls.Lookup.settings,
                            default_flow_style=False)

    if args['output-file']:
        with open(args['output-file'], 'w') as output_file:
            output_file.write(output)
    else:
        print output

    # playbook execution stage
    if not args['dry-run']:
        args_list = ["execute"]
        if verbose:
            args_list.append('-%s' % ('v' * verbose))
        args_list.append('--inventory=local_hosts')
        if args['cleanup']:
            args_list.append('--cleanup')
        else:
            args_list.append('--provision')
        if args['output-file']:
            LOG.debug('Using the newly created settings file: "%s"'
                      % args['output-file'])
            args_list.append('--settings=%s' % args['output-file'])
        else:
            with open(conf.TMP_OUTPUT_FILE, 'w') as output_file:
                output_file.write(output)
            LOG.debug('Temporary settings file "%s" has been created for '
                      'execution purpose only.' % conf.TMP_OUTPUT_FILE)
            args_list.append('--settings=%s' % conf.TMP_OUTPUT_FILE)

        parser = cli.parse.create_parser(list())
        execute_args = parser.parse_args(args_list)

        LOG.debug("execute parser args: %s" % execute_args)
        execute_args.func(execute_args)

        if not args['output-file']:
            LOG.debug('Temporary settings file "%s" has been deleted.'
                      % conf.TMP_OUTPUT_FILE)
            os.remove(conf.TMP_OUTPUT_FILE)


if __name__ == '__main__':
    main()
