#!/usr/bin/env python

import logging
import os

import yaml

from cli import logger  # logger creation is first thing to be done
from cli import conf
from cli import exceptions
from cli import utils
import cli.yamls
import cli.execute

ENTRY_POINT = "installer"

LOG = logger.LOG
CONF = conf.config

NON_SETTINGS_OPTIONS = ['command0', 'verbose', 'extra-vars', 'output-file',
                        'input-files', 'dry-run', 'cleanup', 'inventory']


def get_settings_dir(args=None):
    """Retrieve settings dir.

    :param args: Namespace of argument parser
    :returns: path to settings dir. if args, return path to parser settings
        dir. If args.command0 exists, return path to subparser settings dir.
    """
    settings_dir = utils.validate_settings_dir(
        CONF.get('defaults', 'settings'))
    if args:
        settings_dir = os.path.join(settings_dir,
                                    ENTRY_POINT)
    if hasattr(args, "command0"):
        settings_dir = os.path.join(settings_dir,
                                    args['command0'])
    return settings_dir


def get_args(args=None):
    """
    :return args: return loaded arguments from CLI
    """

    spec_manager = conf.SpecManager(CONF)
    args = spec_manager.parse_args(ENTRY_POINT, args=args)
    return args


def set_logger_verbosity(level):
    """
    Set the logger verbosity level

    :param level: verbosity level (int)
    """
    from logging import WARNING, INFO, DEBUG
    LOG.setLevel((WARNING, INFO)[level] if level < 2 else DEBUG)


def main():
    args = get_args()

    settings_files = []

    set_logger_verbosity(args.verbose)

    for input_file in args['input-files'] or []:
        settings_files.append(utils.normalize_file(input_file))

    settings_files.append(os.path.join(get_settings_dir(args),
                                       args["command0"] + '.yml'))

    # todo(yfried): ospd specific
    settings_dict = set_product_repo(args)
    utils.dict_merge(settings_dict, set_network_details(args))
    utils.dict_merge(settings_dict, set_image(args))
    utils.dict_merge(settings_dict, set_storage(args))
    net_template = yaml.load(
        open(set_network_template(args["network-template"],
                                  os.path.join(get_settings_dir(args),
                                               "network", "templates"))))
    settings_dict["installer"]["overcloud"]["network"]["template"] = \
        net_template
    storage_template = yaml.load(
        open(set_network_template(
            settings_dict["installer"]["overcloud"]["storage"]["template"],
            os.path.join(get_settings_dir(args),
                         "storage", "templates"))))
    settings_dict["installer"]["overcloud"]["storage"]["template"] = \
        storage_template

    LOG.debug("All settings files to be loaded:\n%s" % settings_files)
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
        vars(args)['settings'] = yaml.load(yaml.safe_dump(
            cli.yamls.Lookup.settings, default_flow_style=False))
        vars(args)['install'] = True

        cli.execute.ansible_wrapper(args)


def set_product_repo(args):
    """Get Arguments for repo. """

    product = {"rpm": args["rpm"]}
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


def set_network_template(filename, path):
    """Find network template. search default path first.

    :param filename: template filename
    :param path: default path to search first
    :returns: absolute path to template file
    """
    filename = os.path.join(path, filename) if os.path.exists(
        os.path.join(path, filename)) else filename
    if os.path.exists(os.path.abspath(filename)):
        LOG.debug("Loading Heat template: %s" %
                  os.path.abspath(filename))
        return os.path.abspath(filename)
    raise exceptions.IRFileNotFoundException(
        file_path=os.path.abspath(filename))


def set_image(args):
    # todo(yfried): add support for build image mode
    if not args["image-server"]:
        raise exceptions.IRNotImplemented(message="No support for "
                                                  "build images")
    LOG.debug("Import files from server: %s" % args["image-server"])
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


def set_storage(args):
    """Set storage type and default template. """

    return {"installer": {
        "overcloud": {
            "storage": {"type": args["storage-type"],
                        "template":
                            args["storage-template"] or
                            args["storage-type"] + ".yml"}}}}


if __name__ == '__main__':
    main()
