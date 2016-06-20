# -*- coding: utf-8 -*-

"""This module is a wrapper to ``argparse`` module. It allow to generate a
command-line from a predefined directory (ie: a YAML, JSON, ... file)."""

import os
import re
import sys
import imp
import copy
import pydoc
import argparse
from collections import OrderedDict

#
# Constants.
#
# Get current module.
_SELF = sys.modules[__name__]

# Get types.
_BUILTINS = sys.modules[
    'builtins' if sys.version_info.major == 3 else '__builtin__']
TYPES = {builtin: getattr(_BUILTINS, builtin) for builtin in vars(_BUILTINS)}
TYPES['suppress'] = argparse.SUPPRESS
# Allow custom actions.
ACTIONS = {}

# Keywords (argparse and clg).
KEYWORDS = {
    'parsers': {'argparse': ['prog', 'usage', 'description', 'epilog', 'help',
                             'add_help', 'formatter_class', 'argument_default',
                             'conflict_handler', 'allow_abbrev', 'print_help'],
                'clg': ['anchors', 'subparsers', 'options', 'args', 'groups',
                        'exclusive_groups', 'execute']},
    'subparsers': {
        'argparse': ['title', 'description', 'prog', 'help', 'metavar'],
        'clg': ['required', 'parsers']},
    'groups': {'argparse': ['title', 'description'],
               'clg': ['options', 'args', 'exclusive_groups']},
    'exclusive_groups': {'argparse': ['required'],
                         'clg': ['options']},
    'options': {'argparse': ['action', 'nargs', 'const', 'default', 'choices',
                             'required', 'help', 'metavar', 'type', 'version'],
                'clg': ['short'],
                'post': ['match', 'need', 'conflict']},
    'args': {'argparse': ['action', 'nargs', 'const', 'default', 'choices',
                          'required', 'help', 'metavar', 'type'],
             'clg': ['short'],
             'post': ['match', 'need', 'conflict']},
    'execute': {'clg': ['module', 'file', 'function']}}

# Help command description.
_HELP_PARSER = OrderedDict(
    {'help': {
        'help': "Print commands' tree with theirs descriptions.",
        'description': "Print commands' tree with theirs descriptions."}})

# Errors messages.
_INVALID_SECTION = "this section is not of type '{type}'"
_EMPTY_CONF = 'configuration is empty'
_INVALID_KEYWORD = "invalid keyword '{keyword}'"
_ONE_KEYWORDS = "this section need (only) one of theses keywords: '{keywords}'"
_MISSING_KEYWORD = "keyword '{keyword}' is missing"
_UNKNOWN_ARG = "unknown {type} '{arg}'"
_SHORT_ERR = 'this must be a single letter'
_NEED_ERR = "{type} '{arg}' need {need_type} '{need_arg}'"
_CONFLICT_ERR = "{type} '{arg}' conflict with {conflict_type} '{conflict_arg}'"
_MATCH_ERR = "value '{val}' of {type} '{arg}' does " \
             "not match pattern '{pattern}'"
_FILE_ERR = "Unable to load file: {err}"
_LOAD_ERR = "Unable to load module: {err}"

# Argparse group's methods.
_GRP_METHODS = {'groups': 'add_argument_group',
                'exclusive_groups': 'add_mutually_exclusive_group'}


#
# Exceptions.
#
class CLGError(Exception):
    """CLG exception."""

    def __init__(self, path, msg):
        Exception.__init__(self, msg)
        self.path = path
        self.msg = msg

    def __str__(self):
        return "/%s: %s" % ('/'.join(self.path), self.msg)


#
# Utils functions.
#
def _deepcopy(config):
    """When using YAML anchors, parts of configurations are just references to
    an other part. CLG parameters (like the 'short' parameter of an option or
    the title of a group) are deleted from the current configuration, so theses
    informations are lost in parts of configuration using anchors ... This
    function replace references by a copy of the datas.
    """
    new_config = copy.deepcopy(config)
    for key, value in new_config.items():
        if isinstance(value, dict):
            new_config[key] = _deepcopy(value)
    return new_config


def _gen_parser(parser_conf, subparser=False):
    """Retrieve arguments pass to **argparse.ArgumentParser** from
    **parser_conf**. A subparser can take an extra 'help' keyword."""
    formatter_class = parser_conf.get('formatter_class', 'HelpFormatter')
    conf = {'prog': parser_conf.get('prog', None),
            'usage': None,
            'description': parser_conf.get('description', None),
            'epilog': parser_conf.get('epilog', None),
            'formatter_class': getattr(argparse, formatter_class),
            'argument_default': parser_conf.get('argument_default', None),
            'conflict_handler': parser_conf.get('conflict_handler', 'error'),
            'add_help': parser_conf.get('add_help', True)}

    if subparser and 'help' in parser_conf:
        conf.update(help=parser_conf['help'])
    return conf


def _get_args(parser_conf):
    """Get options and arguments from a parser configuration."""
    args = OrderedDict()
    args.update((arg, (arg_type, OrderedDict(arg_conf)))
                for arg_type in ('options', 'args')
                for arg, arg_conf in parser_conf.get(arg_type, {}).items())
    for grp_type in ('groups', 'exclusive_groups'):
        for group in parser_conf.get(grp_type, {}):
            args.update(_get_args(group))
    return args


def _set_builtin(value):
    """Replace configuration values which begin and end by ``__`` by the
    respective builtin function."""
    try:
        return TYPES[re.search('^__([A-Z]*)__$', value).group(1).lower()]
    except (AttributeError, TypeError):
        return (value.replace('__FILE__', sys.path[0])
                if isinstance(value, str)
                else value)


def _print_help(parser):
    """Manage 'print_help' parameter of a (sub)command. It monkey patch the
    `_parse_known_args` method of the **parser** instance for simulating the
    use of the --help option if no arguments is supplied for the command."""
    default_method = parser._parse_known_args

    def _parse_known_args(arg_strings, namespace):
        if not arg_strings:
            arg_strings = ['--help']
        return default_method(arg_strings, namespace)

    parser._parse_known_args = _parse_known_args


#
# Formatting functions.
#
def _format_usage(prog, usage):
    """Format usage."""
    spaces = re.sub('.', ' ', 'usage: ')
    usage_elts = [prog]
    usage_elts.extend(
        ['%s %s' % (spaces, elt) for elt in usage.split('\n')[:-1]])
    return '\n'.join(usage_elts)


def _format_optname(value):
    """Format the name of an option in the configuration file to a more
    readable option in the command-line."""
    return value.replace('_', '-').replace(' ', '-')


def _format_optdisplay(value, conf):
    """Format the display of an option in error message (short and long option
    with dash(es) separated by a slash."""
    return ('-%s/--%s' % (conf['short'], _format_optname(value))
            if 'short' in conf
            else '--%s' % _format_optname(value))


def _format_arg(arg, arg_conf, arg_type):
    return _format_optdisplay(arg, arg_conf) if arg_type == 'options' else arg


#
# Check functions.
#
def _check_empty(path, conf):
    """Check **conf** is not ``None`` or an empty iterable."""
    if conf is None or (hasattr(conf, '__iter__') and not len(conf)):
        raise CLGError(path, _EMPTY_CONF)


def _check_type(path, conf, conf_type=dict):
    """Check the **conf** is of **conf_type** type
    and raise an error if not."""
    if not isinstance(conf, conf_type):
        type_str = str(conf_type).split()[1][1:-2]
        raise CLGError(path, _INVALID_SECTION.format(type=type_str))


def _check_keywords(path, conf, section, one=None, need=None):
    """Check items of **conf** from **KEYWORDS[section]**. **one** indicate
    whether a check must be done on the number of elements or not."""
    valid_keywords = [keyword
                      for keywords in KEYWORDS[section].values()
                      for keyword in keywords]

    for keyword in conf:
        if keyword not in valid_keywords:
            raise CLGError(path, _INVALID_KEYWORD.format(keyword=keyword))
        _check_empty(path + [keyword], conf[keyword])

    if one and len([arg for arg in conf if arg in one]) != 1:
        raise CLGError(path, _ONE_KEYWORDS.format(keywords="', '".join(one)))

    if need:
        for keyword in need:
            if keyword not in conf:
                raise CLGError(path, _MISSING_KEYWORD.format(keyword=keyword))


def _check_section(path, conf, section, one=None, need=None):
    """Check section is not empty, is a dict and have not extra keywords."""
    _check_empty(path, conf)
    _check_type(path, conf, dict)
    _check_keywords(path, conf, section, one=one, need=need)


#
# Post processing functions.
#
def _has_value(value, conf):
    """The value of an argument not passed in the command is *None*, except:
        * if **action** is ``store_true`` or ``store_false``: in this case, the
          value is respectively ``False`` and ``True``.
    This function take theses cases in consideration and check if an argument
    really has a value.
    """
    if value is None:
        return False

    action = conf.get('action', None)
    return ((not action and value) or
            (action and action == 'store_true' and value) or
            (action and action == 'store_false' and not value))


def _post_need(parser, parser_args, args_values, arg):
    """Post processing that check all for needing options."""
    arg_type, arg_conf = parser_args[arg]
    for cur_arg in arg_conf['need']:
        cur_arg_type, cur_arg_conf = parser_args[cur_arg]
        if not _has_value(args_values[cur_arg], cur_arg_conf):
            strings = {'type': arg_type[:-1],
                       'arg': _format_arg(arg, arg_conf, arg_type),
                       'need_type': cur_arg_type[:-1],
                       'need_arg': _format_arg(cur_arg, cur_arg_conf,
                                               cur_arg_type)}
            parser.error(_NEED_ERR.format(**strings))


def _post_conflict(parser, parser_args, args_values, arg):
    """Post processing that check for conflicting options."""
    arg_type, arg_conf = parser_args[arg]
    for cur_arg in arg_conf['conflict']:
        cur_arg_type, cur_arg_conf = parser_args[cur_arg]
        if _has_value(args_values[cur_arg], cur_arg_conf):
            strings = {'type': arg_type[:-1],
                       'arg': _format_arg(arg, arg_conf, arg_type),
                       'conflict_type': cur_arg_type[:-1],
                       'conflict_arg': _format_arg(cur_arg, cur_arg_conf,
                                                   cur_arg_type)}
            parser.error(_CONFLICT_ERR.format(**strings))


def _post_match(parser, parser_args, args_values, arg):
    """Post processing that check the value."""
    arg_type, arg_conf = parser_args[arg]
    pattern = arg_conf['match']

    msg_elts = {'type': arg_type, 'arg': arg, 'pattern': pattern}
    if arg_conf.get('nargs', None) in ('*', '+'):
        for value in args_values[arg] or []:
            if not re.match(pattern, value):
                parser.error(_MATCH_ERR.format(val=value, **msg_elts))
    elif not re.match(pattern, args_values[arg]):
        parser.error(_MATCH_ERR.format(val=args_values[arg], **msg_elts))


def _exec_module(path, exec_conf, args_values):
    """Load and execute a function of a module according to **exec_conf**."""
    mdl_func = exec_conf.get('function', 'main')
    mdl_tree = exec_conf['module'].split('.')
    mdl = None

    for mdl_idx, mdl_name in enumerate(mdl_tree):
        try:
            imp_args = imp.find_module(mdl_name, mdl.__path__ if mdl else None)
            mdl = imp.load_module('.'.join(mdl_tree[:mdl_idx + 1]), *imp_args)
        except (ImportError, AttributeError) as err:
            raise CLGError(path, _LOAD_ERR.format(err=err))
    getattr(mdl, mdl_func)(args_values)


def _exec_file(path, exec_conf, args_values):
    """Load and execute a function of a file according to **exec_conf**."""
    mdl_path = os.path.abspath(exec_conf['file'])
    mdl_name = os.path.splitext(os.path.basename(mdl_path))[0]
    mdl_func = exec_conf.get('function', 'main')

    try:
        getattr(imp.load_source(mdl_name, mdl_path), mdl_func)(args_values)
    except (IOError, ImportError, AttributeError) as err:
        raise CLGError(path, _FILE_ERR.format(err=err))


#
# Classes.
#
class NoAbbrevParser(argparse.ArgumentParser):
    """Child class of **ArgumentParser** allowing to disable abbravetions."""

    def _get_option_tuples(self, option_string):
        result = []

        # option strings starting with two prefix characters are only
        # split at the '='
        chars = self.prefix_chars
        if option_string[0] in chars and option_string[1] in chars:
            if '=' in option_string:
                option_prefix, explicit_arg = option_string.split('=', 1)
            else:
                option_prefix = option_string
                explicit_arg = None
            for option_string in self._option_string_actions:
                if option_string == option_prefix:
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, explicit_arg
                    result.append(tup)

        # single character options can be concatenated with their arguments
        # but multiple character options always have to have their argument
        # separate
        elif option_string[0] in chars and option_string[1] not in chars:
            option_prefix = option_string
            explicit_arg = None
            short_option_prefix = option_string[:2]
            short_explicit_arg = option_string[2:]

            for option_string in self._option_string_actions:
                if option_string == short_option_prefix:
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, short_explicit_arg
                    result.append(tup)
                elif option_string.startswith(option_prefix):
                    action = self._option_string_actions[option_string]
                    tup = action, option_string, explicit_arg
                    result.append(tup)

        # shouldn't ever get here
        else:
            self.error('unexpected option string: %s' % option_string)

        # return the collected option tuples
        return result


#  Use Pager for showing help.
class HelpPager(argparse.Action):
    """Action allowing to page help."""

    def __init__(self, option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        argparse.Action.__init__(self,
                                 option_strings=option_strings,
                                 dest=dest,
                                 default=default,
                                 nargs=0,
                                 help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        """Page help using `pydoc.pager` method (which use $PAGER environment
        variable)."""
        os.environ['PAGER'] = 'less -c'
        pydoc.pager(parser.format_help())
        parser.exit()


ACTIONS.update(page_help=HelpPager)


class Namespace(argparse.Namespace):
    """Iterable namespace."""

    def __init__(self, args):
        argparse.Namespace.__init__(self)
        self.__dict__.update(args)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        if key not in self.__dict__:
            raise KeyError(key)
        self.__dict__[key] = value

    def __iter__(self):
        return ((key, value) for key, value in self.__dict__.items())


class CommandLine(object):
    """CommandLine object that parse a preformatted dictionnary and generate
    ``argparse`` parser."""

    def __init__(self, config, keyword='command', deepcopy=True):
        """Initialize the command from **config** which is a dictionnary
        (preferably an OrderedDict). **keyword** is the name use for knowing
        the path of subcommands (ie: 'command0', 'command1', ...
        in the namespace of arguments)."""
        self.config = _deepcopy(config) if deepcopy else config
        self.keyword = keyword
        self._parsers = OrderedDict()
        self.parser = None

        #  Allows to page to all helps by replacing the default 'help' action.
        if self.config.pop('page_help', False):
            ACTIONS.update(help=HelpPager)

        # Manage the case when we want a help command that prints
        # a description of all commands.
        self.help_cmd = self.config.pop('add_help_cmd', False)
        if self.help_cmd:
            subparsers_conf = self.config.get('subparsers', None)
            if not subparsers_conf:
                raise CLGError([], 'unable to add help command: no subparsers')

            if 'parsers' in subparsers_conf:
                subparsers_conf['parsers'].update(_HELP_PARSER)
                subparsers_conf['parsers'] = (
                    OrderedDict(sorted(subparsers_conf['parsers'].items())))
            else:
                subparsers_conf.update(_HELP_PARSER)
                subparsers_conf = OrderedDict(sorted(subparsers_conf.items()))
            self.config['subparsers'] = subparsers_conf

        self._add_parser([])

    def _get_config(self, path, ignore=True):
        """Retrieve an element configuration (based on **path**) in the
        configuration."""
        config = self.config
        for idx, elt in enumerate(path):
            if elt.startswith('#'):
                config = config[int(elt[1:])]
            elif not ignore and path[
                        idx - 1] == 'subparsers' and 'parsers' in config:
                config = config['parsers'][elt]
            else:
                config = config[elt]
        return config

    def _add_parser(self, path, parser=None):
        """Add a subparser to a parser. If **parser** is ``None``, the subparser
        is in fact the main parser."""
        # Get configuration.
        parser_conf = self._get_config(path)

        # Check parser configuration.
        _check_section(path, parser_conf, 'parsers')
        if 'execute' in parser_conf:
            exec_path, exec_conf = path + ['execute'], parser_conf['execute']
            _check_section(exec_path, exec_conf, 'execute',
                           one=('module', 'file'))

        # Initialize parent parser.
        if parser is None:
            parser_obj = (argparse.ArgumentParser
                          if parser_conf.pop('allow_abbrev', False)
                          else NoAbbrevParser)
            self.parser = parser_obj(**_gen_parser(parser_conf))
            parser = self.parser

        # Add custom actions.
        for name, obj in ACTIONS.items():
            parser.register('action', name, obj)

        # Index parser (based on path) as it may be necessary to access it
        # later (manage case where subparsers does not have configuration).
        parser_path = [elt
                       for idx, elt in enumerate(path)
                       if not (path[idx - 1] == 'subparsers' and
                               elt == 'parsers')]
        self._parsers['/'.join(parser_path)] = parser

        # Manage 'print_help' parameter which force the use '--help' if no
        #  arguments is supplied.
        if parser_conf.get('print_help', False):
            _print_help(parser)

        # Add custom usage.
        if 'usage' in parser_conf:
            parser.usage = _format_usage(parser.prog, parser_conf['usage'])

        # Add subparsers.
        if 'subparsers' in parser_conf:
            self._add_subparsers(parser, path + ['subparsers'],
                                 parser_conf['subparsers'])

        #  Get all arguments and options of the parser for some later checks.
        #  If there is an error, the configuration is bad and an error will be
        # raised later.
        if isinstance(parser, (NoAbbrevParser, argparse.ArgumentParser)):
            try:
                self._parser_args = _get_args(parser_conf)
            except Exception:
                self._parser_args = OrderedDict()

        # Add options and arguments.
        for arg_type in ('options', 'args'):
            arg_type_path = path + [arg_type]
            arg_type_conf = parser_conf.get(arg_type, {})
            _check_type(arg_type_path, arg_type_conf, dict)
            for arg, arg_conf in arg_type_conf.items():
                self._add_arg(parser, arg_type_path + [arg], arg, arg_type,
                              arg_conf)

        # Add groups.
        for grp_type in ('groups', 'exclusive_groups'):
            if grp_type in parser_conf:
                _check_empty(path, parser_conf[grp_type])
                _check_type(path, parser_conf[grp_type], list)
                for index, group in enumerate(parser_conf[grp_type]):
                    grp_path = path + [grp_type, '#%d' % index]
                    self._add_group(parser, grp_path, group, grp_type)

    def _add_subparsers(self, parser, path, subparsers_conf):
        """Add subparsers. Subparsers can have a global configuration or
        directly parsers configuration. This is the keyword **parsers** that
        indicate it."""
        # Get arguments to pass to add_subparsers method.
        required = True
        subparsers_params = {'dest': '%s%d' % (self.keyword, len(path) / 2)}
        if 'parsers' in subparsers_conf:
            _check_section(path, subparsers_conf, 'subparsers')

            keywords = KEYWORDS['subparsers']['argparse']
            subparsers_params.update({keyword: subparsers_conf[keyword]
                                      for keyword in keywords
                                      if keyword in subparsers_conf})
            required = subparsers_conf.get('required', True)

            subparsers_conf = subparsers_conf['parsers']
            path.append('parsers')

        # Initialize subparsers.
        subparsers = parser.add_subparsers(**subparsers_params)
        subparsers.required = required

        # Add subparsers.
        for parser_name, parser_conf in subparsers_conf.items():
            _check_section(path + [parser_name], parser_conf, 'parsers')
            subparser_params = _gen_parser(parser_conf, subparser=True)
            subparser = subparsers.add_parser(parser_name, **subparser_params)
            self._add_parser(path + [parser_name], subparser)

    def _add_group(self, parser, path, conf, grp_type):
        """Add a group (normal or exclusive) to **parser**"""
        _check_section(path, conf, grp_type)
        params = {keyword: conf.pop(keyword)
                  for keyword in KEYWORDS[grp_type]['argparse']
                  if keyword in conf}
        group = getattr(parser, _GRP_METHODS[grp_type])(**params)
        self._add_parser(path, group)

    def _add_arg(self, parser, path, arg, arg_type, arg_conf):
        """Add an option/argument to **parser**."""
        # Check configuration.
        _check_section(path, arg_conf, arg_type)
        for keyword in ('need', 'conflict'):
            if keyword in arg_conf:
                _check_type(path + [keyword], arg_conf[keyword], list)
                for cur_arg in arg_conf[keyword]:
                    if cur_arg not in self._parser_args:
                        err_str = _UNKNOWN_ARG.format(type='option/argument',
                                                      arg=cur_arg)
                        raise CLGError(path + [keyword], err_str)

        # Get argument parameters.
        arg_args, arg_params = [], {}
        if arg_type == 'options':
            if 'short' in arg_conf:
                if len(arg_conf['short']) != 1:
                    raise CLGError(path + ['short'], _SHORT_ERR)
                arg_args.append('-%s' % arg_conf['short'])
                del arg_conf['short']
            arg_args.append('--%s' % _format_optname(arg))
            arg_params['dest'] = arg
        elif arg_type == 'args':
            arg_args.append(arg)

        default = str(arg_conf.get('default', '?'))
        match = str(arg_conf.get('match', '?'))
        choices = ', '.join(map(str, arg_conf.get('choices', ['?'])))
        for param, value in sorted(arg_conf.items()):
            if param not in KEYWORDS[arg_type]['post']:
                arg_params[param] = {'type': lambda: TYPES[value],
                                     'help': lambda: value.replace(
                                         '__DEFAULT__', default).replace(
                                         '__CHOICES__', choices).replace(
                                         '__MATCH__', match).replace(
                                         '__FILE__', sys.path[0])
                                     }.get(param,
                                           lambda: _set_builtin(value))()

        # Add argument to parser.
        parser.add_argument(*arg_args, **arg_params)

    def parse(self, args=None):
        """Parse command-line."""
        #  Parse command-line.
        args_values = Namespace(self.parser.parse_args(args).__dict__)
        if self.help_cmd and args_values['command0'] == 'help':
            self.print_help()

        # Get command configuration.
        path = [elt
                for arg, value in sorted(args_values) if value
                for elt in ('subparsers', value)
                if re.match('^%s[0-9]*$' % self.keyword, arg)]
        parser_conf = self._get_config(path, ignore=False)
        parser = self._parsers['/'.join(path)]

        # Post processing.
        parser_args = _get_args(parser_conf)
        for arg, (arg_type, arg_conf) in parser_args.items():
            if any((arg_conf.get('default', '') == '__SUPPRESS__',
                    arg_conf.get('action', '') == 'version')):
                continue
            if not _has_value(args_values[arg], arg_conf):
                continue

            for keyword in KEYWORDS[arg_type]['post']:
                if keyword in arg_conf:
                    post_args = (parser, parser_args, args_values, arg)
                    getattr(_SELF, '_post_%s' % keyword)(*post_args)

        # Execute.
        if 'execute' in parser_conf:
            for keyword in ('module', 'file'):
                if keyword in parser_conf['execute']:
                    exec_method = getattr(_SELF, '_exec_%s' % keyword)
                    exec_method(path + ['execute'], parser_conf['execute'],
                                args_values)

        return args_values

    def print_help(self):
        """Print commands' tree with theirs descriptions."""
        # Get column at which we must start printing the description.
        lengths = []
        for path in self._parsers:
            cmds = [elt for elt in path.split('/') if elt != 'subparsers']
            lengths.append(3 * (len(cmds)) + len(cmds[-1]))
        start = max(lengths) + 4
        desc_len = 80 - start

        # Print arboresence of commands with their descriptions. This use
        #  closures so we don't have to pass whatmille arguments to functions.
        def parse_conf(cmd_conf, last):
            def print_line(cmd, line, first_line, has_childs):
                symbols = ['  ' if elt else '│ ' for elt in last[:-1]]
                symbols.append(('└─' if last[-1] else '├─')
                               if first_line
                               else ('  ' if last[-1] else '│ '))
                if not first_line and has_childs:
                    symbols.append('│ ')
                print('%s%s %s' % (''.join(symbols),
                                   cmd if first_line else '',
                                   '\033[%sG%s' % (start, line)))

            if 'subparsers' not in cmd_conf:
                return

            subparsers_conf = (cmd_conf['subparsers']['parsers']
                               if 'parsers' in cmd_conf['subparsers']
                               else cmd_conf['subparsers'])
            last = last + [False]
            nb_cmds = len(subparsers_conf) - 1
            for index, cmd in enumerate(subparsers_conf):
                cmd_conf = subparsers_conf[cmd]
                desc = cmd_conf.get('help', '').strip().split()
                has_childs = 'subparsers' in cmd_conf

                first_line = True
                last[-1] = index == nb_cmds
                cur_line = ''
                while desc:
                    cur_word = desc.pop(0)
                    if (len(cur_line) + 1 + len(cur_word)) > desc_len:
                        print_line(cmd, cur_line, first_line, has_childs)
                        first_line = False
                        cur_line = ''
                    cur_line += ' ' + cur_word
                print_line(cmd, cur_line, first_line, has_childs)
                parse_conf(cmd_conf, last)

        parse_conf(self.config, [])
        sys.exit(0)
