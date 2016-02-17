from configure import Configuration, ConfigurationError
from ksgen import docstring, yaml_utils, utils
from ksgen.tree import OrderedTree
from ksgen.yaml_utils import LookupDirective
from docopt import docopt, DocoptExit
import logging
import os
import re
import yaml


VALUES_KEY = '!value'
DEFAULTS_TAG = 'defaults'
logger = logging.getLogger(__name__)


class KeyValueError(Exception):
    def __init__(self, arg, reason, *args, **kwargs):
        super(KeyValueError, self).__init__(*args, **kwargs)
        self.arg = arg
        self.reason = reason

    def __str__(self):
        return "Invalid key-value pair: %s, - %s" % (self.arg, self.reason)


class OptionError(Exception):
    def __init__(self, paths, *args, **kwargs):
        super(OptionError, self).__init__(*args, **kwargs)
        self._paths = paths

    def __str__(self):
        return "Invalid values passed, files : %s not found" % self._paths


class ArgsConflictError(Exception):
    pass


class Generator(object):
    """
Usage:
    generate [options] <output-file>
    generate [--extra-vars=KEY_PAIR]... [options] <output-file>

Options:
    --rules-file=<file>          Rules file that contains generation rules
                                 Process the rules first, so the additional
                                 args will override args in rules file
    --extra-vars=<val>...        Provide extra vars {options}
    """

    def __init__(self, config_dir, args):
        self.config_dir = config_dir
        self.args = _normalize_args(args)
        logger.debug("Generator: config_dir: %s, args: %s", config_dir, args)
        self._doc_string = Generator.__doc__.format(
            options=docstring.Generator(config_dir).generate())

        self.settings = None
        self.output_file = None
        self.rules_file = None
        self._rules = None
        self.parsed = None
        self.extra_vars = None
        self.all_settings = None
        self.defaults = []

    def run(self):
        if not self._parse():
            return 1
        loader = Loader(self.config_dir, self.settings)
        self._merge_rules_file_exports(loader)
        loader.load()
        self._merge_extra_vars(loader)
        self.all_settings = loader.settings()

        self._replace_in_string_lookup()

        logger.debug(yaml_utils.to_yaml("All Settings", self.all_settings))
        logger.info("Writing to file: %s", self.output_file)
        with open(self.output_file, 'w') as out:
            out.write(
                yaml.safe_dump(self.all_settings, default_flow_style=False))
        return 0

    def _prepare_defaults(self):
        for arg in self.args:
            if not arg.startswith('--'):
                continue
            arg = arg[2:].split('=')[0]
            if '-' not in arg:
                logging.debug("Preparing defaults for %s:" % arg)
                self._load_defaults(self.config_dir + os.sep + arg,
                                    self.parsed['--' + arg])

        self._merge_defaults()
        logger.info("Defaults \n%s", self.defaults)

    def _load_defaults(self, path, value):
        param = '-'.join(path[len(self.config_dir + os.sep):].split('/')[::2])
        if not self.parsed['--' + param]:
            logging.warning(
                "\'--%s\' hasn't been provided, using \'%s\' as default" % (
                    param, value))
            self.defaults.append(''.join(['--', param, '=', str(value)]))
        else:
            value = self.parsed['--' + param]

        file_path = path + os.sep + str(value) + '.yml'
        loaded_file = Configuration.from_file(file_path)

        if loaded_file.get(DEFAULTS_TAG):
            path += os.sep + str(value)
            for sub_key, sub_value in loaded_file[DEFAULTS_TAG].iteritems():
                self._load_defaults(path + os.sep + sub_key, sub_value)

    def _merge_defaults(self):

        for element in self.defaults:
            (option, value) = element.split('=')
            if not self.parsed[option]:
                self.parsed[option] = value

    def _merge_rules_file_exports(self, loader):
        if not self._rules:
            return

        try:
            logger.debug("Try loading exports in rules file %s",
                         self.rules_file)
            loader.merge(self._rules.export)
            logger.info('Loaded exports from rules file: %s', self.rules_file)
        except KeyError:
            logger.debug("No 'exports' in rules file %s", self.rules_file)

    def _parse(self):
        # create the settings tree and preserve the order in which arguments
        # are passed.  Convert all args into an ordered tree so that
        # --foo fooz  --too moo --foo-bar baaz  --foo-arg vali
        # will be like the ordered tree below
        # foo:
        #   <special-key>: fooz
        #   bar:       ###  <-- foo-bar is not foo/bar
        #     <special-key>: baaz
        #   arg:       ###  <-- arg comes after bar
        #     <special-key>: val
        # too:
        #   <special-key>: moo

        logger.debug("Parsing: %s", self.args)
        logger.debug("DocString for Generate: %s", self._doc_string)

        try:
            self.parsed = docopt(self._doc_string,
                                 options_first=True, argv=self.args)
        except DocoptExit:
            logger.error(self._doc_string)
            return False
        logger.info("Parsed \n%s", self.parsed)

        self._prepare_defaults()

        if not self._apply_rules():
            logger.error("Error while validating rules: check args %s",
                         '  \n'.join(self.args))
            return False

        logger.debug("New Args: %s", self.args)
        logger.info("After applying rules Parsed: \n%s", self.parsed)

        self.output_file = utils.extract_value(
            self.parsed, '<output-file>', optional=False)

        self.extra_vars = utils.extract_value(self.parsed, '--extra-vars')

        # filter only options; [ --foo, fooz, --bar baz ] -> [--foo, --bar]
        options = [x for x in self.args + self.defaults if x.startswith('--')]

        settings = OrderedTree(delimiter='-')
        for option in options:   # iterate options to preserve order of args
            option = option.split('=')[0]
            value = self.parsed.get(option)
            if not value:
                continue

            key = option[2:] + settings.delimiter + VALUES_KEY
            settings[key] = value
            logger.debug("%s: %s", key, value)

        logger.debug(yaml_utils.to_yaml(
            "Directory structure from args:", settings))
        self.settings = settings
        return True

    def _apply_rules(self):
        self.rules_file = utils.extract_value(self.parsed, '--rules-file')
        if not self.rules_file:
            return True    # No rules to be applied

        self.rules_file = os.path.abspath(self.rules_file)
        logger.debug('Rule file: %s', self.rules_file)
        self._rules = load_configuration(self.rules_file, os.path.curdir)

        # create --key=value pairs from the rules.args
        args_in_rules = self._rules.get('args', {})
        extra_vars = utils.extract_value(args_in_rules, 'extra-vars')
        args = ['--%s=%s' % (k, v) for k, v in args_in_rules.iteritems()]
        if extra_vars:
            extra_vars = utils.to_list(extra_vars)
            args.extend(['--extra-vars=%s' % x for x in extra_vars])

        logger.debug('Args in rules file: %s', args)
        logger.debug('Args in self: %s', self.args)
        logger.debug('Args in rules: %s', args_in_rules)

        # get the key part without first two -- from --key=value
        def _key(x):
            return x.split('=')[0][2:]

        # filter out all args present in rules file
        conflicting_keys = [_key(x) for x in self.args
                            if _key(x) in args_in_rules]

        if conflicting_keys:
            raise ArgsConflictError(
                "Command line args: '{0}' are in conflict with args defined "
                "in the rules file.".format(
                    ', '.join(conflicting_keys)))

        # prepend the args from the rules file and re-parse the args
        if args:
            self.args = args + self.args
            try:
                self.parsed = docopt(self._doc_string,
                                     options_first=True, argv=self.args)
            except DocoptExit:
                logger.error(self._doc_string)
                return False
            # remove rules-file from the parse tree
            del self.parsed['--rules-file']
        # validate args
        return self._validate_args()

    def _validate_args(self):
        # validate args
        try:
            mandatory_args = self._rules.validation.must_have
        except KeyError:
            logger.debug('No validations in rules file')
            return True

        if not mandatory_args:
            logger.debug('No validations in rules file')
            return True

        logger.debug('Must have args from rule: %s', mandatory_args)
        logger.debug("New Parsed \n%s", self.parsed)

        missing_args = [x for x in mandatory_args
                        if not self.parsed.get("--" + x)]

        logger.debug('Missing args: %s', missing_args)
        if missing_args:
            logger.error("Error: missing mandatory args: %s",
                         ', '.join(missing_args))
            return False
        return True

    def _merge_extra_vars(self, loader):
        if not self.extra_vars or len(self.extra_vars) == 0:
            return

        for var in self.extra_vars:
            if var.startswith('@'):
                loader.load_file(var[1:])  # remove @
            elif '=' in var:
                key, val = var.split('=', 1)
                tree = OrderedTree(delimiter='.')
                tree[key] = val
                loader.merge(tree)
            else:
                raise KeyValueError(var, "No = found between key and value")

    def _replace_in_string_lookup(self, sub_lookup_dict=None):
        """
        Search and replace 'in-string' !lookup
        Example:
            key: 'pre_string{{ !lookup key.sub_key.sub_sub_key }}post_string'
        """

        if sub_lookup_dict is None:
            sub_lookup_dict = self.all_settings

        my_iter = sub_lookup_dict.iteritems() if \
            isinstance(sub_lookup_dict, dict) else enumerate(sub_lookup_dict)

        for key, value in my_iter:
            if isinstance(value, OrderedTree):
                self._replace_in_string_lookup(sub_lookup_dict[key])
            elif isinstance(value, list):
                self._replace_in_string_lookup(value)
            elif isinstance(value, str):
                while True:
                    parser = re.compile('\{\{\s*!lookup\s[^\s]+\s*\}\}')
                    additional_lookups = parser.findall(value)

                    if not additional_lookups:
                        break

                    for additional_lookup in additional_lookups:
                        lookup_key = re.search('(\w+\.?)+ *?\}\}',
                                               additional_lookup)
                        lookup_key = lookup_key.group(0).strip()[:-2].strip()
                        lookup_value = str(
                            self.all_settings[lookup_key.replace('.', '!')])
                        sub_lookup_dict[key] = re.sub(additional_lookup,
                                                      lookup_value, value)
                        value = sub_lookup_dict[key]

class Loader(object):
    def __init__(self, config_dir, settings):
        self._settings = settings
        self._config_dir = config_dir
        self._loaded = False
        self._all_settings = None
        self._file_list = None
        self._invalid_paths = None
        self._all_settings = OrderedTree('!')

    def settings(self):
        self.load()
        LookupDirective.lookup_table = self._all_settings
        return self._all_settings

    def load_file(self, f):
        self.load()
        cfg = load_configuration(f, self._config_dir)
        self._all_settings.merge(cfg)

    def merge(self, tree):
        self._all_settings.merge(tree)

    def load(self):
        if self._loaded:
            return

        self._file_list = []
        self._invalid_paths = []
        self._create_file_list(self._settings, self._file_list)

        logger.info(
            "\nList of files to load :\n  - %s",
            '\n  - '.join([
                x[len(self._config_dir) + 1:] for x in self._file_list
            ]))

        if self._invalid_paths:
            logger.info("invalid files :\n %s", '\n'.join(self._invalid_paths))
            raise OptionError(self._invalid_paths)

        all_cfg = Configuration.from_dict({})
        for f in self._file_list:
            cfg = load_configuration(f, self._config_dir)

            try:
                del cfg[DEFAULTS_TAG]
            except KeyError:
                pass
            else:
                logger.debug("Successfully removed default traces from %s" % f)

            all_cfg.merge(cfg)
        self._all_settings.merge(all_cfg)
        self._loaded = True

    def _create_file_list(self, settings, file_list, parent_path=""):
        """ Appends list of files to be process to self._file_list
            and list of invalid file paths to self._invalid_paths
        """
        logger.debug('settings:\n %s \n parent: %s \n files: %s',
                     settings, parent_path, file_list)

        for key, sub_tree in settings.items():
            # ignore the special key value
            if key == VALUES_KEY:
                continue

            logger.debug("key: %s, subtree: %s", key, sub_tree)
            path = "%(parent_path)s%(key)s%(sep)s%(file)s" % {
                'parent_path': parent_path,
                'key': key,
                'sep': os.sep,
                'file': sub_tree[VALUES_KEY]
            }

            abs_file_path = os.path.abspath(
                self._config_dir + os.sep + path + '.yml')
            file_list.append(abs_file_path)
            logger.debug('path: %s', abs_file_path)

            if not os.path.exists(abs_file_path):
                self._invalid_paths.append(abs_file_path)

            # recurse if there are sub settings
            if (isinstance(sub_tree, dict)
                    and len(sub_tree.keys()) > 1):
                logger.debug('recursing into: sub-tree: %s', sub_tree)
                self._create_file_list(sub_tree, file_list, path + os.sep)


def _normalize_args(args):
    """
    Converts all --key val to --key=val
    """
    args_normalized = []
    merge_with_prev = False
    for arg in args:
        if merge_with_prev:
            # add the val part to last --key to get --key=val
            args_normalized[-1] += '=%s' % arg
            merge_with_prev = False
            continue

        first_two_chars = arg[:2]
        if first_two_chars == '--' and '=' not in arg:
            merge_with_prev = True
        args_normalized.append(arg)

    return args_normalized


def load_configuration(file_path, rel_dir=None):
    """ Return the Configuration for the file_path. Also logs an error if
        there is an error while parsing the file.
        If the optional rel_dir is passed the error message would print
        the file_path relative to rel_dir instead of current directory
    """

    logger.debug('Loading file: %s', file_path)
    try:
        return Configuration.from_file(file_path).configure()
    except (yaml.scanner.ScannerError,
            yaml.parser.ParserError,
            TypeError,
            ConfigurationError) as e:
        rel_dir = rel_dir or os.curdir
        logger.error("Error loading: %s; reason: %s",
                     os.path.relpath(file_path, rel_dir), e)
        raise
    return None
