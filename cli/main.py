#!/usr/bin/env python

import logging
import os

import clg
import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import utils
import cli.yamls
import cli.execute

LOG = logger.LOG
CONF = conf.config

NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                        'input-files', 'dry-run', 'cleanup', 'inventory']


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
        vars(args)['settings'] = cli.yamls.Lookup.settings
        if not args['cleanup']:
            vars(args)['provision'] = True

        cli.execute.ansible_wrapper(args)


if __name__ == '__main__':
    main()
