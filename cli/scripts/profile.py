#!/usr/bin/env python

import argparse
import logging

from cli import profile_manager
from cli.logger import LOG

# TODO(yfried): Refactor this for IR2


def parse_args(args=None):
    """

    :param args: list. argv. Use for testing to bypass sys.argv
    :return:
    """
    """
    Parses the command line arguments using 'argparse' module

    :return: Namespace object
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument('--suffix', type=str,
    #                     help='suffix to be added to the archive file')
    # parser.add_argument('--inventory', type=str, default='hosts',
    #                     help='inventory file to be archived')
    # parser.add_argument('--ssh-conf', type=str, default='ansible.ssh.config',
    #                     help='SSH config file to be archived')
    # parser.add_argument('--dest-dir', type=str, default=os.getcwd(),
    #                     help='Directory to save the archive file in')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='run in debug mode')
    subparsers = parser.add_subparsers(help='Profile Commands',
                                       metavar="COMMAND")

    parse_list = subparsers.add_parser("list", help="list available profiles")
    parse_list.set_defaults(func=profile_list)

    parse_active = subparsers.add_parser("active",
                                         help="Manage active profile")
    parse_active.add_argument("--profile",
                              help="Activate this profile")
    parse_active.set_defaults(func=profile_active)

    parse_create = subparsers.add_parser("create",
                                         help="Create a new profile")
    parse_create.add_argument("--name",
                              help="Profile name. Use timestamp as default")
    # todo(yfried): add file type validator
    parse_create.add_argument("--inventory",
                              help="initial inventory file")
    parse_create.set_defaults(func=profile_create)

    parse_delete = subparsers.add_parser("delete",
                                         help="delete profile")
    parse_delete.add_argument("name")
    parse_delete.set_defaults(func=profile_delete)

    return parser.parse_args(args=args)


def profile_list(*args, **kwargs):
    profiles = profile_manager.ProfileManager.list()
    active = profile_manager.ProfileManager.get_active()
    active = active.name if active else None
    print "\n".join("{}".format("\t*\t" if p == active else
                                "\t\t")
                    + p for p in profiles)


def profile_create(name="", *args, **kwargs):
    profile = profile_manager.ProfileManager.create(name=name)
    print "Profile '{}' created".format(profile.name)


def profile_delete(name, *args, **kwargs):
    profile_manager.ProfileManager.delete(name=name)
    print "Profile '{}' deleted".format(name)


def profile_active(profile=None, *args, **kwargs):
    if profile:
        profile = profile_manager.ProfileManager.set_active(name=profile)
        print "Profile '{}' is active".format(profile.name)
    else:
        profile = profile_manager.ProfileManager.get_active()
        print profile.name


def main(args=None):
    parsed_args = parse_args(args=args)
    if parsed_args.debug:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)
    parsed_args.func(**vars(parsed_args))


if __name__ == '__main__':
    main()
