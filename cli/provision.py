#!/usr/bin/env python

import os

import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import utils
from cli.install import set_network_template as set_network
from cli.install import get_args, get_settings_dir, set_logger_verbosity
import cli.yamls
import cli.execute

LOG = logger.LOG
CONF = conf.config

ENTRY_POINT = 'provisioner'


def main():
    args = get_args(ENTRY_POINT)

    settings_files = []

    set_logger_verbosity(args.verbose)

    for input_file in args['input-files'] or []:
        settings_files.append(utils.normalize_file(input_file))

    settings_files.append(os.path.join(get_settings_dir(ENTRY_POINT, args),
                                       args["command0"] + '.yml'))

    # todo(aopincar): virsh specific
    settings_dict = set_image_source(args)
    utils.dict_merge(settings_dict, set_host(args))

    for arg_dir in ('network', 'topology'):
        with open(set_network(args[arg_dir], os.path.join(
                get_settings_dir(ENTRY_POINT, args), arg_dir))) as \
                settings_file:
            settings = yaml.load(settings_file)
        utils.dict_merge(settings_dict, settings)

    LOG.debug("All settings files to be loaded:\n%s" % settings_files)
    cli.yamls.Lookup.settings = utils.generate_settings(settings_files,
                                                        args['extra-vars'])
    # todo(aopincar): virsh specific
    cli.yamls.Lookup.settings = cli.yamls.Lookup.settings.merge(settings_dict)

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
        vars(args)['settings'] = yaml.load(yaml.safe_dump(
            cli.yamls.Lookup.settings, default_flow_style=False))
        if not args['cleanup']:
            vars(args)['provision'] = True

        cli.execute.ansible_wrapper(args)


def set_image_source(args):
    image = dict(
        name=args['image-file'],
        base_url=args['image-server']
    )
    return {'provisioner': {'image': image}}


def set_host(args):
    host = dict(
        ssh_host=args['host'],
        ssh_user=args['ssh-user'],
        ssh_key_file=args['ssh-key']
    )
    return {'provisioner': {'hosts': {'host1': host}}}


if __name__ == '__main__':
    main()
