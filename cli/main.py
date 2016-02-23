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
                        'input-files']


def main():
    settings_files = []
    settings_dir = utils.validate_settings_dir(
        CONF.get('DEFAULTS', 'SETTINGS_DIR'))

    cmd = clg.CommandLine(yaml.load(open(CONF.get('DEFAULTS', 'SPEC_FILE'))))
    args = cmd.parse()

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

    for key, val in vars(args).iteritems():
        if val is not None and key not in NON_SETTINGS_OPTIONS:
            if key == 'distro':
                settings_files.append(os.path.join(settings_dir, 'distro',
                                                   val + '.yml'))
            else:
                settings_files.append(os.path.join(provision_dir, key,
                                                   val + '.yml'))

    LOG.debug("All settings files to be loaded:\n%s" % settings_files)

    cli.yamls.Lookup.settings = utils.generate_settings(settings_files,
                                                        args['extra-vars'])

    cli.yamls.Lookup.in_string_lookup()

    LOG.debug("Dumping settings...")

    output = yaml.safe_dump(cli.yamls.Lookup.settings,
                            default_flow_style=False)

    if args['output-file']:
        with open(args.output_file, 'w') as output_file:
            output_file.write(output)
    else:
        print output


if __name__ == '__main__':
    main()
