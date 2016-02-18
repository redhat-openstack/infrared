"""
This module is the building blocks for the options parsing tree.
It contains the data structures that hold available options & values in a
given directory.
"""

import os

import yaml

from kcli import conf
from kcli import exceptions
from kcli import logger

LOG = logger.LOG


class OptionNode(object):
    """
    represents an option and its properties:
      - parent option
      - available values
      - option's path
      - sub options
    """
    def __init__(self, path, parent=None):
        self.path = path
        self.option = self.path.split("/")[-1]
        self.parent = parent
        self.parent_value = None
        if parent:
            self.option = "-".join([self.parent.option, self.option])
        self.values = self._get_values()
        self.children = {i: dict() for i in self._get_sub_options()}

        if self.parent:
            self.parent_value = self.path.split("/")[-2]
            self.parent.children[self.parent_value][self.option] = self

    def _get_values(self):
        """Returns a sorted list of values available for the current option"""
        values = [a_file.split(conf.YAML_EXT)[0]
                  for a_file in os.listdir(self.path)
                  if os.path.isfile(os.path.join(self.path, a_file)) and
                  a_file.endswith(conf.YAML_EXT)]

        values.sort()
        return values

    def _get_sub_options(self):
        """
        Returns a sorted list of sup-options available for the current option
        """
        options = [options_dir for options_dir in os.listdir(self.path)
                   if os.path.isdir(os.path.join(self.path, options_dir)) and
                   options_dir in self.values]

        options.sort()
        return options


class OptionsTree(object):
    """
    Tree represents hierarchy of options from rhe same kind (provisioner,
    installer etc...)
    """
    def __init__(self, settings_dir, option):
        self.root = None
        self.name = option
        self.action = option[:-2] if option.endswith('er') else option
        self.options_dict = {}
        self.root_dir = os.path.join(settings_dir, self.name)

        self.build_tree()
        self.init_options_dict(self.root)

    def build_tree(self):
        """Builds the OptionsTree"""
        self.add_node(self.root_dir, None)

    def add_node(self, path, parent):
        """
        Adds OptionNode object to the tree
        :param path: Path to option dir
        :param parent: Parent option (OptionNode)
        """
        node = OptionNode(path, parent)

        if not self.root:
            self.root = node

        for child in node.children:
            sub_options_dir = os.path.join(node.path, child)
            sub_options = [a_dir for a_dir in os.listdir(sub_options_dir) if
                           os.path.isdir(os.path.join(sub_options_dir, a_dir))]

            for sub_option in sub_options:
                self.add_node(os.path.join(sub_options_dir, sub_option), node)

    def init_options_dict(self, node):
        """
        Initialize "options_dict" dictionary to store all options and their
        valid values
        :param node: OptionNode object
        """
        if node.option not in self.options_dict:
            self.options_dict[node.option] = {}

        if node.parent_value:
            self.options_dict[node.option][node.parent_value] = node.values

        if 'ALL' not in self.options_dict[node.option]:
            self.options_dict[node.option]['ALL'] = set()

        self.options_dict[node.option]['ALL'].update(node.values)

        for pre_value in node.children:
            for child in node.children[pre_value].values():
                self.init_options_dict(child)

    def get_options_ymls(self, options):
        """return list of paths to settings YAML files for a given options
        dictionary

        :param options: dictionary of options to get path of their settings
        files
        :return: list of paths to settings files of 'options'
        """
        ymls = []
        if not options:
            return ymls

        keys = options.keys()
        keys.sort()

        def step_in(key, node):
            """recursive method that returns the settings files of a given
            options
            """
            keys.remove(key)
            if node.option != key.replace("_", "-"):
                raise exceptions.IRMissingAncestorException(key)

            ymls.append(os.path.join(node.path, options[key] + ".yml"))
            child_keys = [child_key for child_key in keys
                          if child_key.startswith(key) and
                          len(child_key.split("_")) == len(key.split("_")) + 1
                          ]

            for child_key in child_keys:
                step_in(child_key, node.children[options[key]][
                    child_key.replace("_", "-")])

        step_in(keys[0], self.root)
        LOG.debug("%s tree settings files:\n%s" % (self.name, ymls))

        return ymls

    def __str__(self):
        return yaml.safe_dump(self.options_dict, default_flow_style=False)
