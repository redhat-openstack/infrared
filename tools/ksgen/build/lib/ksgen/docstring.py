"""
Generates options list based on the directory structure so that it
can be used with docstring
"""

from collections import OrderedDict
import logging
import os


logger = logging.getLogger(__name__)


class Generator(object):
    def __init__(self, config_path):
        self._config_dir = os.path.abspath(config_path)
        self._parse_tree = None

    def parse_tree(self):
        self._parse_tree = OrderedDict()
        if not os.path.isdir(self._config_dir):
            logger.error("Error: config dir %s does not exist",
                         self._config_dir)
            raise OSError("No such directory: %s", self._config_dir)

        for dir_path, subdirs, files in os.walk(self._config_dir):
            logger.debug("Walking dir: %s", dir_path)
            if dir_path == self._config_dir:
                logger.debug("  ... skipping root dirs")
                continue

            yml_files = {
                os.path.splitext(x)[0] for x in files
                if x.endswith('.yml')}
            logger.debug("  files: %s", yml_files)

            # don't process dirs without yml files
            # but traverse deeper if it is a data dir
            if len(yml_files) == 0:
                if not self._is_data_dir(dir_path):
                    logger.warning(
                        "... skipping dir: [%s]: empty dir "
                        " and not data dir", dir_path)
                    subdirs[:] = []
                else:
                    logger.debug("... skipping: data_dir: %s", dir_path)
                continue

            # add the dir as an option
            self._add_option(dir_path, yml_files)

            logger.debug("yaml files: %s", yml_files)
            # filter the subdirs which has the same name as the
            # files
            subdirs[:] = [d for d in subdirs if d in yml_files]

            logger.debug('sub dirs matching : %s', subdirs)
        return self._parse_tree

    def generate(self):
        args = self.parse_tree()
        logger.debug("args: %s", args)

        equals_val = '=<val>'
        longest_key = max(args.keys(), key=len)
        key_width = len(longest_key) + len(equals_val)

        doc_string = ""
        for key, value in args.items():
            doc_string += "\n    --{0:{width}} {1}".format(
                key.replace('/', '-') + equals_val,
                '[' + ', '.join(value) + ']',
                width=key_width
            )
        return doc_string

    # ### private ###
    def _add_option(self, dir_path, values):
        # remove all data-dirs from the dir_path
        logger.debug("Add option - dir: '%s': %s", dir_path, values)

        dirname = os.path.dirname(dir_path)
        parent_option = self._remove_data_dirs(dirname)

        basename = os.path.basename(dir_path)
        key = os.path.join(parent_option, basename)
        logger.debug("cleaned up arg: '%s': %s", key, values)

        if key not in self._parse_tree:
            self._parse_tree[key] = values
        else:
            self._parse_tree[key].update(values)

        logger.info("Adding %s: [%s]", key, ', '.join(values))

    def _is_data_dir(self, path):
        # is a data dir if  basepath is one of the values of
        # the parent arg_path
        path = os.path.normpath(path)
        basename = os.path.basename(path)
        logger.debug("is '%s' is a data_dir ?", basename)

        # top level dirs are not data dirs
        if os.path.relpath(path, self._config_dir) == basename:
            logger.debug("'%s' is a top_dir, not a data-dir", basename)
            return False

        parent_dir = os.path.dirname(path)
        logger.debug("path: %s, parent_dir: %s", path, parent_dir)
        parent_option = self._remove_data_dirs(parent_dir)
        logger.debug("Checking if '%s' is a data of '%s': %s",
                     basename, parent_option,
                     self._parse_tree[parent_option])

        return basename in self._parse_tree[parent_option]

    def _remove_data_dirs(self, path):
        """
        Given a path parent-arg/value/child-arg/value/grand-child-arg/...
        returns parent-arg/child-arg/grand-child-arg/...
        """
        arg_path = os.path.relpath(path, self._config_dir)
        logger.debug("args path for %s : %s", path, arg_path)

        dirs = arg_path.split(os.sep)
        args = []    # store parent-dir, child-dir, grand-child-dir

        for d in dirs:
            logger.debug(" .... checking dir: %s", d)
            arg_path_for_dir = os.path.join(*(args + [d]))

            logger.debug(" .... arg path for %s : %s",
                         d, arg_path_for_dir)

            if arg_path_for_dir in self._parse_tree:
                logger.debug(" .... found %s, in parse_trees",
                             arg_path_for_dir)
                args.append(d)
            logger.debug(" .... args: %s", args)
        return os.sep.join(args)
