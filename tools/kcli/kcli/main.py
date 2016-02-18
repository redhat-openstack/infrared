#!/usr/bin/env python

import logging
import os

import yaml

# logger creation is first thing to be done
from kcli import logger

from kcli import conf
from kcli import options as kcli_options
from kcli.execute import PLAYBOOKS
from kcli import parse
from kcli import utils
import kcli.yamls

LOG = logger.LOG
CONF = conf.config


def main():
    options_trees = []
    settings_files = []
    settings_dir = utils.validate_settings_dir(
        CONF.get('DEFAULTS', 'SETTINGS_DIR'))

    for option in CONF.options('ROOT_OPTS'):
        options_trees.append(kcli_options.OptionsTree(settings_dir, option))

    parser = parse.create_parser(options_trees)
    args = parser.parse_args()

    verbose = int(args.verbose)

    if args.verbose == 0:
        args.verbose = logging.WARNING
    elif args.verbose == 1:
        args.verbose = logging.INFO
    else:
        args.verbose = logging.DEBUG

    LOG.setLevel(args.verbose)

    # settings generation stage
    if args.which.lower() != 'execute':
        for input_file in args.input:
            settings_files.append(utils.normalize_file(input_file))

        for options_tree in options_trees:
            options = {key: value for key, value in vars(args).iteritems()
                       if value and key.startswith(options_tree.name)}

            settings_files += (options_tree.get_options_ymls(options))

        LOG.debug("All settings files to be loaded:\n%s" % settings_files)

        kcli.yamls.Lookup.settings = utils.generate_settings(settings_files,
                                                             args.extra_vars)

        output = yaml.safe_dump(kcli.yamls.Lookup.settings,
                                default_flow_style=False)

        if args.output_file:
            with open(args.output_file, 'w') as output_file:
                output_file.write(output)
        else:
            print output

    exec_playbook = (args.which == 'execute') or \
                    (not args.dry_run and args.which in CONF.options(
                        'AUTO_EXEC_OPTS'))

    # playbook execution stage
    if exec_playbook:
        if args.which == 'execute':
            execute_args = parser.parse_args()
        elif args.which not in PLAYBOOKS:
            LOG.debug("No playbook named \"%s\", nothing to execute.\n"
                      "Please choose from: %s" % (args.which, PLAYBOOKS))
            return
        else:
            args_list = ["execute"]
            if verbose:
                args_list.append('-%s' % ('v' * verbose))
            if 'inventory' in args:
                inventory = args.inventory
            else:
                inventory = 'local_hosts' if args.which == 'provision' \
                    else 'hosts'
            args_list.append('--inventory=%s' % inventory)
            args_list.append('--' + args.which)
            args_list.append('--collect-logs')
            if args.output_file:
                LOG.debug('Using the newly created settings file: "%s"'
                          % args.output_file)
                args_list.append('--settings=%s' % args.output_file)
            else:
                with open(conf.TMP_OUTPUT_FILE, 'w') as output_file:
                    output_file.write(output)
                LOG.debug('Temporary settings file "%s" has been created for '
                          'execution purpose only.' % conf.TMP_OUTPUT_FILE)
                args_list.append('--settings=%s' % conf.TMP_OUTPUT_FILE)

            execute_args = parser.parse_args(args_list)

        LOG.debug("execute parser args: %s" % args)
        execute_args.func(execute_args)

        if not args.output_file and args.which != 'execute':
            LOG.debug('Temporary settings file "%s" has been deleted.'
                      % conf.TMP_OUTPUT_FILE)
            os.remove(conf.TMP_OUTPUT_FILE)


if __name__ == '__main__':
    main()
