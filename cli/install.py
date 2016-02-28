#!/usr/bin/env python

import logging

import os

import clg
import sys
import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import options as cli_options
from cli import execute
from cli import exceptions
from cli import parse
from cli import utils
import cli.yamls

LOG = logger.LOG
CONF = conf.config

NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                        'input-files', 'dry-run', 'cleanup']


# todo(yfried): remove this
TMP_SETTINGS_DIR = "/home/yfried/workspace/git/InfraRed/tmp_ospd_prov"


def get_args(spec, args=None):
    """
    :return args: return loaded arguments from CLI
    """

    cmd = clg.CommandLine(yaml.load(spec))
    args = cmd.parse(args)
    return args


def main():
    settings_files = []
    settings_dir = utils.validate_settings_dir(TMP_SETTINGS_DIR)

    spec_file = open(os.path.join(TMP_SETTINGS_DIR, "ospd", "ospd.spec"))
    args = get_args(spec=spec_file)

    verbose = int(args.verbose)

    if args.verbose == 0:
        args.verbose = logging.WARNING
    elif args.verbose == 1:
        args.verbose = logging.INFO
    else:
        args.verbose = logging.DEBUG

    LOG.setLevel(args.verbose)

    installer_dir = os.path.join(TMP_SETTINGS_DIR, args['command0'])

    for input_file in args['input-files'] or []:
        settings_files.append(utils.normalize_file(input_file))

    settings_files.append(os.path.join(installer_dir,
                                       args['command0'] + '.yml'))

    # for key, val in vars(args).iteritems():
    #     if val is not None and key not in NON_SETTINGS_OPTIONS:
    #         settings_file = os.path.join(provision_dir, key, val + '.yml')
    #         LOG.debug('Searching settings file for the "%s" key...' % key)
    #         if not os.path.isfile(settings_file):
    #             settings_file = utils.normalize_file(val)
    #         settings_files.append(settings_file)
    #         LOG.debug('"%s" was added to settings files list as an argument '
    #                   'for "%s" key' % (settings_file, key))

    # LOG.debug("All settings files to be loaded:\n%s" % settings_files)

    # todo(yfried): ospd specific
    settings_dict = set_product_repo(args)
    settings_dict.update(set_network_details(args))
    settings_dict.update(set_image(args))
    net_template = yaml.load(
        open(set_network_template(args["network-template"])))
    settings_dict["installer"]["overcloud"]["network"]["template"] = \
        net_template
    cli.yamls.Lookup.settings = utils.generate_settings(settings_files,
                                                        args['extra-vars'])
    # todo(yfried): ospd specific
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
        args_list = ["execute"]
        if verbose:
            args_list.append('-%s' % ('v' * verbose))
        args_list.append('--inventory=local_hosts')
        args_list.append('--install')
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

def set_product_repo(args):
    """Get Arguments for repo. """

    product = {}
    version = args["version"].split(".", 1)
    # If minor version is provided, set build. else default build to latest
    build = "Y" + str(version[1]) if len(version) == 2 else "latest"
    # save major version
    product["version"] = version[0]
    product["build"] = args["build"] or build
    if args["core-version"]:
        product.setdefault("core", {})["version"] = args["core-version"]
    if args["core-build"]:
        product.setdefault("core", {})["build"] = args["core-build"]
    if product.get("core"):
        product["core"].setdefault("version", product["version"])
        if product["version"] != product["core"]["version"]:
            product["core"].setdefault("build", "latest")
        product["core"].setdefault("build", product["build"])
    return {"installer": {"product": product}}


def set_network_details(args):
    # todo(yfried): consider moving this to conf file when supporting options.
    isolation = dict(
        no=dict(enable="no"),
        yes=dict(enable="yes",
                 type="three-nics-vlans",
                 file="environments/net-three-nic-with-vlans.yaml")
    )
    network = dict(
        protocol=args["network-protocol"],
        backend=args["network-variant"],
        isolation=isolation[args["network-isolation"]],
        ssl=args["ssl"],
    )

    return {"installer": {"overcloud": {"network": network}}}


def set_network_template(filename):
    """Find network template. search default path first. """
    default_path = os.path.join(TMP_SETTINGS_DIR, "ospd", "network",
                                "templates")
    filename = os.path.join(default_path, filename) if os.path.exists(
        os.path.join(default_path, filename)) else filename
    if os.path.exists(os.path.abspath(filename)):
        LOG.debug("Loading Heat network template: %s" %
                  os.path.abspath(filename))
        return os.path.abspath(filename)
    raise exceptions.IRFileNotFoundException(
        file_path=os.path.abspath(filename))


def set_image(args):
    # todo(yfried): add support for build image mode
    if not args["image-server"]:
        raise exceptions.IRNotImplemented(message="No support for "
                                                  "build images")
    LOG.debug("Import files from server %s: " % args["image-server"])
    files = {"7": dict(discovery="discovery-ramdisk.tar",
                       deployment="deploy-ramdisk-ironic.tar",
                       overcloud="overcloud-full.tar"),
             # any version above 7:
             "8": dict(discovery="ironic-python-agent.tar",
                       overcloud="overcloud-full.tar")}
    return {"installer": {"overcloud": {"images": {
        "server": args["image-server"],
        "files": files["7"] if args["version"] == "7" else files["8"]
    }}}}


if __name__ == '__main__':
    main()
