from argparse import ArgumentParser, RawTextHelpFormatter

from kcli import conf, execute, utils


def create_parser(options_trees):
    """
    Creates and return a parser dynamically
    :param options_trees: An iterable with OptionsTree objects
    :return: Namespace object
    """
    parser = ArgumentParser(prog="kcli",
                            formatter_class=RawTextHelpFormatter)

    sub_parsers = parser.add_subparsers()

    execute_parser = sub_parsers.add_parser('execute')
    execute_parser.add_argument('-i', '--inventory', default=None,
                                type=lambda file_path: utils.normalize_file(
                                    file_path),
                                help="Inventory file to use. "
                                     "Default: {lcl}. "
                                     "NOTE: to reuse old environment use {"
                                     "host}".
                                format(lcl=execute.LOCAL_HOSTS,
                                       host=execute.HOSTS_FILE))
    execute_parser.add_argument("-v", "--verbose", help="verbosity",
                                action='count', default=0)
    execute_parser.add_argument("--provision", action="store_true",
                                help="provision fresh nodes from server")
    execute_parser.add_argument("--install", action="store_true",
                                help="install Openstack on nodes")
    execute_parser.add_argument("--test", action="store_true",
                                help="execute tests")
    execute_parser.add_argument("--collect-logs", action="store_true",
                                help="Pull logs from nodes")
    execute_parser.add_argument("--cleanup", action="store_true",
                                help="cleanup nodes")
    execute_parser.add_argument("--settings",
                                type=lambda file_path: utils.normalize_file(
                                    file_path),
                                help="settings file to use. default: %s"
                                     % conf.KCLI_SETTINGS_YML)
    execute_parser.set_defaults(func=execute.ansible_wrapper)
    execute_parser.set_defaults(which='execute')

    for options_tree in options_trees:
        sub_parser = sub_parsers.add_parser(
            options_tree.action, formatter_class=RawTextHelpFormatter)
        options = options_tree.options_dict.keys()
        options.sort()

        sub_parser.add_argument("-d", "--dry-run", action='store_true',
                                help="skip playbook execution stage")
        sub_parser.add_argument("-e", "--extra-vars", default=list(),
                                action='append', help="Provide extra vars. "
                                                      "(key=value, or a path "
                                                      "to settings file if "
                                                      "starts with '@')")
        sub_parser.add_argument("-n", "--input", action='append',
                                help="Settings files to be loaded first,"
                                     " other settings files will be"
                                     " merged with them", default=list())
        sub_parser.add_argument("-o", "--output-file",
                                help="file to dump the settings into")
        sub_parser.add_argument("-v", "--verbose", help="verbosity",
                                action='count', default=0)

        for option in options:
            choices = None
            help_msg = ""
            for prev_value, cur_value in \
                    options_tree.options_dict[option].iteritems():
                if prev_value == 'ALL':
                    choices = cur_value
                    continue
                help_msg += "%s - %s\n" % (prev_value, cur_value)

            required = True if option == options[0] else False
            sub_parser.add_argument("--" + option, type=str, help=help_msg,
                                    choices=choices, required=required)

        # for sub-parser recognition purpose only
        sub_parser.set_defaults(which=options_tree.action)

    return parser
